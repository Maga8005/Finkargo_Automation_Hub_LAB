"""
Excel Merge Service for Colombia (CO)

Service for merging new invoice data with existing master Excel in Drive.
Prevents duplicates by using numero_factura as unique key.
"""

import logging
import io
from typing import List, Dict, Tuple, Optional
import openpyxl
from openpyxl import Workbook

logger = logging.getLogger(__name__)


class MergeValidationError(Exception):
    """Error cuando los datos para merge no pasan validación."""
    pass


class ExcelMergeServiceCO:
    """
    Service for merging Colombia invoice Excel data.

    Handles:
    - Reading existing master Excel from Drive
    - Merging new records with existing ones
    - Preventing duplicates by numero_factura
    - Maintaining separate sheets (Costos Fijos, Mandato)
    """

    def __init__(self):
        """Initialize the merge service."""
        self.costos_fijos_sheet = "Relacion facturas Costos Fijos"
        self.mandato_sheet = "Relación facturas mandato"

    def read_excel_from_bytes(self, excel_bytes: bytes) -> Dict[str, List[Dict]]:
        """
        Read Excel file from bytes and return data from both sheets.

        Args:
            excel_bytes: Excel file content as bytes

        Returns:
            Dict with sheet names as keys and list of row dicts as values
        """
        try:
            wb = openpyxl.load_workbook(io.BytesIO(excel_bytes), data_only=True)
            result = {}

            for sheet_name in [self.costos_fijos_sheet, self.mandato_sheet]:
                if sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                    rows = list(ws.iter_rows(values_only=True))

                    if len(rows) < 2:  # No data rows
                        result[sheet_name] = []
                        continue

                    headers = [str(h) if h else f"col_{i}" for i, h in enumerate(rows[0])]
                    data = []

                    for row in rows[1:]:
                        if any(cell is not None for cell in row):  # Skip empty rows
                            row_dict = dict(zip(headers, row))
                            data.append(row_dict)

                    result[sheet_name] = data
                    logger.info(f"Read {len(data)} records from sheet '{sheet_name}'")
                else:
                    result[sheet_name] = []
                    logger.warning(f"Sheet '{sheet_name}' not found in Excel")

            return result

        except Exception as e:
            logger.error(f"Error reading Excel from bytes: {e}")
            return {self.costos_fijos_sheet: [], self.mandato_sheet: []}

    def merge_sheet_data(
        self,
        existing_records: List[Dict],
        new_records: List[Dict],
        key_column: str = "# Factura"
    ) -> Tuple[List[Dict], Dict[str, int]]:
        """
        Merge new records with existing ones, avoiding duplicates.

        Args:
            existing_records: Records from master Excel
            new_records: New records to merge
            key_column: Column to use as unique identifier

        Returns:
            Tuple of (merged records, stats dict)
        """
        stats = {
            "existing": len(existing_records),
            "new_input": len(new_records),
            "added": 0,
            "updated": 0,
            "unchanged": 0
        }

        # Create index of existing records by key
        existing_index = {}
        for record in existing_records:
            key = record.get(key_column)
            if key:
                existing_index[str(key)] = record

        # Process new records
        merged = list(existing_records)  # Start with existing

        for new_record in new_records:
            key = new_record.get(key_column)
            if not key:
                continue

            key_str = str(key)

            if key_str in existing_index:
                # Record exists - update it
                idx = next(
                    (i for i, r in enumerate(merged) if str(r.get(key_column)) == key_str),
                    None
                )
                if idx is not None:
                    merged[idx] = new_record
                    stats["updated"] += 1
            else:
                # New record - add it
                merged.append(new_record)
                existing_index[key_str] = new_record
                stats["added"] += 1

        stats["unchanged"] = stats["existing"] - stats["updated"]
        stats["total"] = len(merged)

        logger.info(
            f"Merge complete: {stats['added']} added, {stats['updated']} updated, "
            f"{stats['unchanged']} unchanged. Total: {stats['total']}"
        )

        return merged, stats

    def merge_excel_data(
        self,
        existing_data: Dict[str, List[Dict]],
        new_costos_fijos: List[Dict],
        new_mandato: List[Dict]
    ) -> Tuple[Dict[str, List[Dict]], Dict[str, Dict[str, int]]]:
        """
        Merge data for both sheets.

        Args:
            existing_data: Data from master Excel (both sheets)
            new_costos_fijos: New Costos Fijos records
            new_mandato: New Mandato records

        Returns:
            Tuple of (merged data dict, stats per sheet)
        """
        all_stats = {}

        # Merge Costos Fijos
        merged_costos, stats_costos = self.merge_sheet_data(
            existing_data.get(self.costos_fijos_sheet, []),
            new_costos_fijos,
            key_column="# Factura"
        )
        all_stats[self.costos_fijos_sheet] = stats_costos

        # Merge Mandato
        merged_mandato, stats_mandato = self.merge_sheet_data(
            existing_data.get(self.mandato_sheet, []),
            new_mandato,
            key_column="# Factura"
        )
        all_stats[self.mandato_sheet] = stats_mandato

        merged_data = {
            self.costos_fijos_sheet: merged_costos,
            self.mandato_sheet: merged_mandato
        }

        return merged_data, all_stats

    def convert_records_to_dicts(
        self,
        records: List,
        sheet_type: str
    ) -> List[Dict]:
        """
        Convert ConsolidatedRecord objects to dictionaries for merging.

        Args:
            records: List of ConsolidatedRecord objects
            sheet_type: "costos_fijos" or "mandato"

        Returns:
            List of dictionaries matching Excel column structure
        """
        from src.interface.finance_dtos_co import (
            ProductCategory
        )

        result = []

        # Month names for Mandato
        meses = {
            1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr',
            5: 'may', 6: 'jun', 7: 'jul', 8: 'ago',
            9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
        }

        # Debug tracking
        records_with_values = 0
        sample_values = []

        for record in records:
            if sheet_type == "costos_fijos":
                # Calculate values by category
                valores = {
                    "Valor Costos Fijos": 0.0,
                    "Seguro + Iva": 0.0,
                    "Int. Corriente Facturado FK": 0.0,
                    "Int. Mora Facturado FK": 0.0,
                    "Otros Valor": 0.0
                }

                if record.categoria and record.valor_netsuite:
                    records_with_values += 1
                    if len(sample_values) < 3:
                        sample_values.append(
                            f"factura={record.numero_factura}, categoria={record.categoria}, valor={record.valor_netsuite}"
                        )
                    if record.categoria == ProductCategory.COSTOS_FIJOS:
                        valores["Valor Costos Fijos"] = record.valor_netsuite
                    elif record.categoria == ProductCategory.SEGURO_IVA:
                        valores["Seguro + Iva"] = record.valor_netsuite
                    elif record.categoria == ProductCategory.INTERESES_CORRIENTE:
                        valores["Int. Corriente Facturado FK"] = record.valor_netsuite
                    elif record.categoria == ProductCategory.INTERESES_MORA:
                        valores["Int. Mora Facturado FK"] = record.valor_netsuite
                    elif record.categoria == ProductCategory.OTROS:
                        valores["Otros Valor"] = record.valor_netsuite

                valor_neto = sum(valores.values())

                row_dict = {
                    "Codigo del desembolso": record.codigo_operacion or "",
                    "Valor Costos Fijos": valores["Valor Costos Fijos"],
                    "Seguro + Iva": valores["Seguro + Iva"],
                    "Int. Corriente Facturado FK": valores["Int. Corriente Facturado FK"],
                    "Int. Mora Facturado FK": valores["Int. Mora Facturado FK"],
                    "(-) Retencion en la Fuente": 0.0,
                    "Valor Neto Facturado": valor_neto,
                    "Fecha Facturacion": record.fecha.strftime("%Y-%m-%d") if record.fecha else "",
                    "# Factura": record.numero_factura or "",
                    "Moneda": record.moneda or "",
                    "Nit": record.nit or "",
                    "Otros Valor": valores["Otros Valor"]
                }
                result.append(row_dict)

            elif sheet_type == "mandato":
                # Reset for mandato tracking
                if record.categoria and record.valor_netsuite:
                    records_with_values += 1
                    if len(sample_values) < 3:
                        sample_values.append(
                            f"factura={record.numero_factura}, categoria={record.categoria}, valor={record.valor_netsuite}"
                        )
                # Calculate values by category
                valores = {
                    "Interes Corriente Facturado": 0.0,
                    "Interes Mora Facturado Mandato": 0.0,
                    "Otros Valor": 0.0
                }

                if record.categoria and record.valor_netsuite:
                    if record.categoria == ProductCategory.INTERESES_CORRIENTE:
                        valores["Interes Corriente Facturado"] = record.valor_netsuite
                    elif record.categoria == ProductCategory.INTERESES_MORA:
                        valores["Interes Mora Facturado Mandato"] = record.valor_netsuite
                    elif record.categoria == ProductCategory.OTROS:
                        valores["Otros Valor"] = record.valor_netsuite

                valor_neto = sum(valores.values())

                # Format mes facturacion
                mes_facturacion = ""
                if record.fecha:
                    mes = meses.get(record.fecha.month, "")
                    año = str(record.fecha.year)[-2:]
                    mes_facturacion = f"{mes}-{año}"

                row_dict = {
                    "Codigo del desembolso": record.codigo_operacion or "",
                    "Mes facturacion": mes_facturacion,
                    "Interes Corriente Facturado": valores["Interes Corriente Facturado"],
                    "Interes Mora Facturado Mandato": valores["Interes Mora Facturado Mandato"],
                    "Valor Neto Facturado": valor_neto,
                    "Fecha Factura": record.fecha.strftime("%Y-%m-%d") if record.fecha else "",
                    "# Factura": record.numero_factura or "",
                    "Moneda": record.moneda or "",
                    "Nit": record.nit or "",
                    "Otros Valor": valores["Otros Valor"]
                }
                result.append(row_dict)

        # Log debug stats
        logger.info(
            f"[convert_records_to_dicts] Sheet type: {sheet_type}, "
            f"Total records: {len(records)}, "
            f"Records with values: {records_with_values}"
        )
        if sample_values:
            logger.info(f"[convert_records_to_dicts] Sample values: {sample_values}")

        return result

    def validate_merged_data(
        self,
        merged_data: Dict[str, List[Dict]],
        existing_data: Optional[Dict[str, List[Dict]]] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Valida los datos antes de escribir el Excel.

        Verifica:
        - Que haya al menos un registro en total
        - Que los datos no estén degradados respecto al existente
        - Que los registros tengan campos requeridos

        Args:
            merged_data: Datos combinados para escribir.
            existing_data: Datos existentes para comparación (opcional).

        Returns:
            Tuple[bool, str, Dict]: (es_válido, mensaje, estadísticas)
        """
        stats = {
            "costos_fijos_count": 0,
            "mandato_count": 0,
            "total_records": 0,
            "existing_costos_fijos": 0,
            "existing_mandato": 0,
            "existing_total": 0
        }

        costos_data = merged_data.get(self.costos_fijos_sheet, [])
        mandato_data = merged_data.get(self.mandato_sheet, [])

        stats["costos_fijos_count"] = len(costos_data)
        stats["mandato_count"] = len(mandato_data)
        stats["total_records"] = len(costos_data) + len(mandato_data)

        # Si tenemos datos existentes, verificar que no estamos reduciendo
        if existing_data:
            existing_costos = existing_data.get(self.costos_fijos_sheet, [])
            existing_mandato = existing_data.get(self.mandato_sheet, [])

            stats["existing_costos_fijos"] = len(existing_costos)
            stats["existing_mandato"] = len(existing_mandato)
            stats["existing_total"] = len(existing_costos) + len(existing_mandato)

            # Advertir si los datos nuevos son significativamente menores
            if stats["existing_total"] > 0:
                reduction_threshold = 0.5  # 50% de reducción es sospechoso
                reduction_ratio = stats["total_records"] / stats["existing_total"]

                if reduction_ratio < reduction_threshold:
                    return (
                        False,
                        f"Los datos nuevos ({stats['total_records']} registros) representan "
                        f"una reducción de más del 50% respecto a los existentes "
                        f"({stats['existing_total']} registros). "
                        "Esto podría indicar pérdida de datos. "
                        "Verifique los archivos de entrada.",
                        stats
                    )

        # Verificar que tenemos datos válidos
        if stats["total_records"] == 0:
            return (
                False,
                "No hay registros para escribir. "
                "El merge resultó en un archivo vacío. "
                "Verifique los archivos de entrada.",
                stats
            )

        # Verificar campos requeridos en los registros
        required_costos_fields = ["# Factura", "Nit"]
        required_mandato_fields = ["# Factura", "Nit"]

        for record in costos_data[:10]:  # Verificar primeros 10
            missing = [f for f in required_costos_fields if not record.get(f)]
            if missing:
                logger.warning(f"Registro Costos Fijos sin campos requeridos: {missing}")

        for record in mandato_data[:10]:  # Verificar primeros 10
            missing = [f for f in required_mandato_fields if not record.get(f)]
            if missing:
                logger.warning(f"Registro Mandato sin campos requeridos: {missing}")

        logger.info(
            f"Validación de merge exitosa: {stats['total_records']} registros totales "
            f"(Costos Fijos: {stats['costos_fijos_count']}, Mandato: {stats['mandato_count']})"
        )

        return (True, "Datos válidos", stats)

    def write_merged_excel(
        self,
        merged_data: Dict[str, List[Dict]],
        existing_data: Optional[Dict[str, List[Dict]]] = None,
        validate: bool = True
    ) -> bytes:
        """
        Write merged data to Excel bytes.

        Args:
            merged_data: Dict with sheet names and their records
            existing_data: Datos existentes para validación de comparación.
            validate: Si True, valida los datos antes de escribir.

        Returns:
            Excel file as bytes

        Raises:
            MergeValidationError: Si la validación falla y validate=True.
        """
        from src.interface.finance_dtos_co import COSTOS_FIJOS_COLUMNS, MANDATO_COLUMNS
        from openpyxl.styles import Font, PatternFill, Alignment

        # Validar datos antes de escribir
        if validate:
            is_valid, message, stats = self.validate_merged_data(
                merged_data,
                existing_data
            )

            if not is_valid:
                logger.error(f"Validación de merge fallida: {message}")
                raise MergeValidationError(
                    f"Los datos no pasaron la validación: {message}. "
                    f"Estadísticas: {stats}"
                )

        wb = Workbook()
        # Remove default sheet
        if "Sheet" in wb.sheetnames:
            del wb["Sheet"]

        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        # Write Costos Fijos sheet
        ws_costos = wb.create_sheet(self.costos_fijos_sheet)
        costos_data = merged_data.get(self.costos_fijos_sheet, [])

        # Headers
        for col_idx, header in enumerate(COSTOS_FIJOS_COLUMNS, start=1):
            cell = ws_costos.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Data rows
        for row_idx, record in enumerate(costos_data, start=2):
            for col_idx, header in enumerate(COSTOS_FIJOS_COLUMNS, start=1):
                value = record.get(header, "")
                ws_costos.cell(row=row_idx, column=col_idx, value=value)

        # Auto-size columns
        for col_idx in range(1, len(COSTOS_FIJOS_COLUMNS) + 1):
            column_letter = openpyxl.utils.get_column_letter(col_idx)
            ws_costos.column_dimensions[column_letter].width = 20

        # Write Mandato sheet
        ws_mandato = wb.create_sheet(self.mandato_sheet)
        mandato_data = merged_data.get(self.mandato_sheet, [])

        # Headers
        for col_idx, header in enumerate(MANDATO_COLUMNS, start=1):
            cell = ws_mandato.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Data rows
        for row_idx, record in enumerate(mandato_data, start=2):
            for col_idx, header in enumerate(MANDATO_COLUMNS, start=1):
                value = record.get(header, "")
                ws_mandato.cell(row=row_idx, column=col_idx, value=value)

        # Auto-size columns
        for col_idx in range(1, len(MANDATO_COLUMNS) + 1):
            column_letter = openpyxl.utils.get_column_letter(col_idx)
            ws_mandato.column_dimensions[column_letter].width = 20

        # Save to bytes
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        logger.info(
            f"Wrote merged Excel: {len(costos_data)} Costos Fijos, "
            f"{len(mandato_data)} Mandato records"
        )

        return buffer.getvalue()


# Singleton instance
_merge_service_co_instance: Optional[ExcelMergeServiceCO] = None


def get_excel_merge_service_co() -> ExcelMergeServiceCO:
    """
    Get singleton instance of Excel merge service for CO.

    Returns:
        ExcelMergeServiceCO instance
    """
    global _merge_service_co_instance
    if _merge_service_co_instance is None:
        _merge_service_co_instance = ExcelMergeServiceCO()
    return _merge_service_co_instance
