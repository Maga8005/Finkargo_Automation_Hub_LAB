"""
Colombia File Processor Service

Service for processing Colombia invoicing files (Netsuite + Noova).
Implements LEFT JOIN consolidation, product classification, and Excel generation.
"""

import logging
import json
import io
from typing import List, Dict, Tuple, Optional
from datetime import date, datetime
from pathlib import Path
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from fastapi import UploadFile

from src.interface.finance_dtos_co import (
    NetsuiteRecord,
    NoovaRecord,
    ConsolidatedRecord,
    COProcessingStats,
    COReportSheet,
    FileType,
    SheetDestination,
    ProductCategory,
    COValidationError,
    COSTOS_FIJOS_COLUMNS,
    MANDATO_COLUMNS
)

logger = logging.getLogger(__name__)


class COFileProcessor:
    """
    Processes Colombia invoicing files.

    Workflow:
    1. Read 4 Excel files (2 Netsuite + 2 Noova)
    2. Map columns using configuration
    3. Consolidate with LEFT JOIN by numero_factura
    4. Classify by product code (primary) and keywords (fallback)
    5. Separate into 2 output sheets by invoice prefix
    6. Generate Excel with 2 sheets
    """

    def __init__(self):
        """Initialize the CO file processor with configuration."""
        self.config_dir = Path(__file__).parent.parent.parent.parent / "config" / "colombia"
        self.column_mapping = self._load_json_config("column_mapping.json")
        self.classification_rules = self._load_json_config("classification_rules.json")
        self.product_classification = self._load_json_config("product_classification.json")
        logger.info("COFileProcessor initialized with configs")

    def _load_json_config(self, filename: str) -> Dict:
        """Load JSON configuration file."""
        config_path = self.config_dir / filename
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config {filename}: {e}")
            raise ValueError(f"No se pudo cargar configuración: {filename}")

    async def read_excel_file(
        self,
        file: UploadFile,
        file_type: FileType
    ) -> Tuple[List[Dict], List[COValidationError]]:
        """
        Read Excel file and map columns according to file type.

        Args:
            file: Uploaded Excel file
            file_type: Type of file (netsuite, noova_facturas, etc.)

        Returns:
            Tuple of (records, validation_errors)
        """
        try:
            # Reset file pointer
            await file.seek(0)
            contents = await file.read()
            await file.seek(0)

            # Load workbook
            workbook = openpyxl.load_workbook(io.BytesIO(contents))

            # Get config for this file type
            config = self.column_mapping.get(file_type.value)
            if not config:
                raise ValueError(f"No hay configuración para tipo de archivo: {file_type}")

            # Get sheet
            sheet_name = config.get("sheet_name")
            if sheet_name not in workbook.sheetnames:
                raise ValueError(f"Hoja '{sheet_name}' no encontrada en archivo {file_type}")

            sheet = workbook[sheet_name]
            column_map = config.get("columns", {})

            # Read header row
            header_row = [cell.value for cell in sheet[1]]

            # Create reverse mapping (Excel column name -> standardized field name)
            col_index_map = {}
            for std_field, excel_col_name in column_map.items():
                try:
                    col_idx = header_row.index(excel_col_name)
                    col_index_map[std_field] = col_idx
                except ValueError:
                    logger.warning(
                        f"Columna '{excel_col_name}' no encontrada en {file_type}"
                    )

            # Read data rows
            records = []
            errors = []

            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):  # Skip empty rows
                    continue

                try:
                    record = {}
                    for std_field, col_idx in col_index_map.items():
                        value = row[col_idx] if col_idx < len(row) else None

                        # Type conversion based on field
                        if value is not None:
                            if std_field == "fecha":
                                if isinstance(value, datetime):
                                    value = value.date()
                                elif isinstance(value, str):
                                    try:
                                        value = datetime.strptime(value, "%Y-%m-%d").date()
                                    except:
                                        pass
                            elif std_field == "valor":
                                value = float(value) if value else 0.0
                            else:
                                value = str(value).strip()

                        record[std_field] = value

                    records.append(record)

                except Exception as e:
                    error = COValidationError(
                        file_type=file_type,
                        row=row_idx,
                        message=f"Error leyendo fila: {str(e)}"
                    )
                    errors.append(error)
                    logger.warning(f"Error en fila {row_idx} de {file_type}: {e}")

            logger.info(f"Leídos {len(records)} registros de {file_type}")
            return records, errors

        except Exception as e:
            logger.error(f"Error leyendo archivo {file_type}: {e}", exc_info=True)
            raise ValueError(f"Error procesando archivo {file_type}: {str(e)}")

    def consolidate_data(
        self,
        noova_records: List[Dict],
        netsuite_records: List[Dict]
    ) -> List[ConsolidatedRecord]:
        """
        Consolidate Noova and Netsuite data with LEFT JOIN.

        Logic:
        - Noova is the main dataset (all records preserved)
        - Netsuite data is joined by numero_factura
        - If no match, Netsuite fields are None

        Args:
            noova_records: Records from Noova files
            netsuite_records: Records from Netsuite files

        Returns:
            List of consolidated records
        """
        logger.info(
            f"Consolidating {len(noova_records)} Noova with "
            f"{len(netsuite_records)} Netsuite records"
        )

        # Create index of Netsuite by numero_factura
        netsuite_by_factura = {
            record["numero_factura"]: record
            for record in netsuite_records
            if record.get("numero_factura")
        }

        consolidated = []
        matched_count = 0

        for noova in noova_records:
            numero_factura = noova.get("numero_factura")

            # LEFT JOIN with Netsuite
            netsuite_match = netsuite_by_factura.get(numero_factura)

            record = ConsolidatedRecord(
                fecha=noova.get("fecha"),
                numero_factura=numero_factura,
                nit=noova.get("nit", ""),
                nombre_cliente=noova.get("nombre_cliente", ""),
                email=noova.get("email", ""),
                estado=noova.get("estado", ""),
                envio=noova.get("envio", ""),
                codigo_operacion=noova.get("codigo_operacion", ""),
                codigo_producto=noova.get("codigo_producto", ""),
                concepto=noova.get("concepto", ""),
                moneda=netsuite_match.get("moneda") if netsuite_match else None,
                valor_netsuite=netsuite_match.get("valor") if netsuite_match else None
            )

            if netsuite_match:
                matched_count += 1

            consolidated.append(record)

        logger.info(
            f"Consolidación completa: {len(consolidated)} registros, "
            f"{matched_count} con match Netsuite, "
            f"{len(consolidated) - matched_count} sin match"
        )

        return consolidated

    def classify_records(
        self,
        records: List[ConsolidatedRecord]
    ) -> List[ConsolidatedRecord]:
        """
        Classify records by product code and determine destination sheet.

        Classification priority:
        1. Product code (primary method) - 146 codes mapped in config
        2. Concept keywords (fallback) - if code not found
        3. Invoice prefix - determines destination sheet

        Args:
            records: Consolidated records to classify

        Returns:
            Records with categoria, hoja_destino, and tipo_factura filled
        """
        logger.info(f"Clasificando {len(records)} registros")

        product_map = self.product_classification.get("clasificacion_productos", {})
        category_column_map = self.product_classification.get("mapeo_categoria_columna", {})
        prefix_rules = self.classification_rules.get("tipo_factura_por_prefijo", {})
        concept_keywords = self.classification_rules.get("clasificacion_conceptos", {})

        for record in records:
            # Step 1: Classify by product code (primary)
            codigo_producto = record.codigo_producto
            if codigo_producto and str(codigo_producto) in product_map:
                product_info = product_map[str(codigo_producto)]
                categoria_str = product_info.get("categoria", "otros")
                record.categoria = ProductCategory(categoria_str)
            else:
                # Fallback: Classify by concept keywords
                record.categoria = self._classify_by_keywords(
                    record.concepto,
                    concept_keywords
                )

            # Step 2: Extract invoice prefix and determine destination sheet
            numero_factura = record.numero_factura or ""
            prefix = self._extract_prefix(numero_factura)

            if prefix and prefix in prefix_rules:
                rule = prefix_rules[prefix]
                record.tipo_factura = rule.get("tipo", "Desconocido")
                hoja_str = rule.get("hoja_destino", "Relacion facturas Costos Fijos")

                # Debug logging
                logger.debug(
                    f"Factura {numero_factura}: prefix={prefix}, "
                    f"hoja_destino={hoja_str!r}"
                )

                try:
                    record.hoja_destino = SheetDestination(hoja_str)
                except ValueError as e:
                    logger.warning(
                        f"Could not map hoja_destino '{hoja_str}' to enum. "
                        f"Error: {e}. Defaulting to COSTOS_FIJOS"
                    )
                    record.hoja_destino = SheetDestination.COSTOS_FIJOS
            else:
                # Default to Costos Fijos if prefix not recognized
                logger.debug(
                    f"Factura {numero_factura}: prefix '{prefix}' not in rules. "
                    f"Defaulting to COSTOS_FIJOS"
                )
                record.tipo_factura = "Desconocido"
                record.hoja_destino = SheetDestination.COSTOS_FIJOS

        logger.info("Clasificación completada")
        return records

    def _classify_by_keywords(
        self,
        concepto: str,
        concept_keywords: Dict
    ) -> ProductCategory:
        """
        Classify by concept keywords (fallback method).

        Args:
            concepto: Concept text to classify
            concept_keywords: Keyword rules from config

        Returns:
            ProductCategory
        """
        if not concepto:
            return ProductCategory.OTROS

        concepto_lower = concepto.lower()

        # Check exact matches first
        for categoria_str, rules in concept_keywords.items():
            exact_matches = rules.get("exact_match", [])
            if concepto in exact_matches:
                return ProductCategory(categoria_str)

        # Check keyword matches
        for categoria_str, rules in concept_keywords.items():
            keywords = rules.get("keywords", [])
            if any(keyword.lower() in concepto_lower for keyword in keywords):
                return ProductCategory(categoria_str)

        return ProductCategory.OTROS

    def _extract_prefix(self, numero_factura: str) -> Optional[str]:
        """
        Extract prefix from invoice number.

        Handles both formats:
        - With dash: FE-12345 -> FE, NCFE-67890 -> NCFE, ITPA-11111 -> ITPA
        - Without dash: FE12345 -> FE, NCFE67890 -> NCFE, ITPA27212 -> ITPA

        Args:
            numero_factura: Invoice number

        Returns:
            Prefix string (letters before first digit) or None
        """
        if not numero_factura:
            return None

        # First try splitting by dash (if present)
        if "-" in numero_factura:
            parts = numero_factura.split("-")
            return parts[0].upper() if parts else None

        # If no dash, extract letters before first digit
        # Examples: ITPA27212 -> ITPA, FE11199 -> FE, NCFE941 -> NCFE
        prefix = ""
        for char in numero_factura:
            if char.isalpha():
                prefix += char
            elif char.isdigit():
                break  # Stop at first digit

        return prefix.upper() if prefix else None

    def separate_by_sheet(
        self,
        records: List[ConsolidatedRecord]
    ) -> Tuple[List[ConsolidatedRecord], List[ConsolidatedRecord]]:
        """
        Separate records into two sheets based on hoja_destino.

        Args:
            records: Classified consolidated records

        Returns:
            Tuple of (costos_fijos_records, mandato_records)
        """
        costos_fijos = [
            r for r in records
            if r.hoja_destino == SheetDestination.COSTOS_FIJOS
        ]
        mandato = [
            r for r in records
            if r.hoja_destino == SheetDestination.MANDATO
        ]

        logger.info(
            f"Separación por hoja: {len(costos_fijos)} Costos Fijos, "
            f"{len(mandato)} Mandato"
        )

        # Debug: Log some sample records for Mandato
        if mandato:
            logger.info(f"Mandato samples: {[r.numero_factura for r in mandato[:5]]}")
        else:
            logger.warning("No records assigned to Mandato sheet!")
            # Log all unique prefixes found
            prefixes = set()
            for r in records:
                prefix = self._extract_prefix(r.numero_factura or "")
                if prefix:
                    prefixes.add(prefix)
            logger.warning(f"Found invoice prefixes: {sorted(prefixes)}")

        return costos_fijos, mandato

    def generate_excel_report(
        self,
        costos_fijos_records: List[ConsolidatedRecord],
        mandato_records: List[ConsolidatedRecord]
    ) -> bytes:
        """
        Generate Excel report with 2 sheets.

        Sheet 1: "Relacion facturas Costos Fijos" (18 columns)
        Sheet 2: "Relación facturas mandato" (16 columns)

        Args:
            costos_fijos_records: Records for Costos Fijos sheet
            mandato_records: Records for Mandato sheet

        Returns:
            Excel file as bytes
        """
        logger.info("Generando reporte Excel")

        workbook = Workbook()

        # Remove default sheet
        if "Sheet" in workbook.sheetnames:
            del workbook["Sheet"]

        # Create Sheet 1: Costos Fijos (18 columns)
        self._create_costos_fijos_sheet(workbook, costos_fijos_records)

        # Create Sheet 2: Mandato (16 columns)
        self._create_mandato_sheet(workbook, mandato_records)

        # Save to bytes
        excel_buffer = io.BytesIO()
        workbook.save(excel_buffer)
        excel_buffer.seek(0)
        excel_bytes = excel_buffer.read()

        logger.info(f"Reporte generado: {len(excel_bytes)} bytes")
        return excel_bytes

    def _create_costos_fijos_sheet(
        self,
        workbook: Workbook,
        records: List[ConsolidatedRecord]
    ):
        """Create Costos Fijos sheet with 11 columns."""
        sheet = workbook.create_sheet("Relacion facturas Costos Fijos")

        # Header styling
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        # Write headers
        for col_idx, header in enumerate(COSTOS_FIJOS_COLUMNS, start=1):
            cell = sheet.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Column mapping
        category_column_map = self.product_classification.get("mapeo_categoria_columna", {})

        # Write data rows
        for row_idx, record in enumerate(records, start=2):
            # Determine which value column to populate based on category
            valores = {
                "Valor Costos Fijos": 0.0,
                "Seguro + Iva": 0.0,
                "Int. Corriente Facturado FK": 0.0,
                "Int. Mora Facturado FK": 0.0,
                "Otros Valor": 0.0
            }

            if record.categoria and record.valor_netsuite:
                target_column = category_column_map.get(record.categoria.value)
                if target_column and target_column in valores:
                    valores[target_column] = record.valor_netsuite

            # Calculate Valor Neto Facturado (sum of all value columns)
            valor_neto = sum(valores.values())

            # Write row data (12 columns)
            row_data = [
                record.codigo_operacion or "",  # Codigo del desembolso
                valores["Valor Costos Fijos"],  # Valor Costos Fijos
                valores["Seguro + Iva"],  # Seguro + Iva
                valores["Int. Corriente Facturado FK"],  # Int. Corriente Facturado FK
                valores["Int. Mora Facturado FK"],  # Int. Mora Facturado FK
                0.0,  # (-) Retencion en la Fuente (siempre 0)
                valor_neto,  # Valor Neto Facturado
                record.fecha.strftime("%Y-%m-%d") if record.fecha else "",  # Fecha Facturacion
                record.numero_factura or "",  # # Factura
                record.moneda or "",  # Moneda
                record.nit or "",  # Nit
                valores["Otros Valor"]  # Otros Valor (última columna)
            ]

            for col_idx, value in enumerate(row_data, start=1):
                sheet.cell(row=row_idx, column=col_idx, value=value)

        # Auto-size columns
        for col_idx in range(1, len(COSTOS_FIJOS_COLUMNS) + 1):
            column_letter = openpyxl.utils.get_column_letter(col_idx)
            if col_idx == 1:  # Codigo del desembolso
                sheet.column_dimensions[column_letter].width = 30
            elif col_idx == 9:  # # Factura
                sheet.column_dimensions[column_letter].width = 15
            else:
                sheet.column_dimensions[column_letter].width = 20

    def _create_mandato_sheet(
        self,
        workbook: Workbook,
        records: List[ConsolidatedRecord]
    ):
        """Create Mandato sheet with 9 columns."""
        sheet = workbook.create_sheet("Relación facturas mandato")

        # Header styling
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        # Write headers
        for col_idx, header in enumerate(MANDATO_COLUMNS, start=1):
            cell = sheet.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Column mapping
        category_column_map = self.product_classification.get("mapeo_categoria_columna", {})

        # Meses en español
        meses = {
            1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr',
            5: 'may', 6: 'jun', 7: 'jul', 8: 'ago',
            9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
        }

        # Write data rows
        for row_idx, record in enumerate(records, start=2):
            # Determine which value column to populate based on category
            valores = {
                "Interes Corriente Facturado": 0.0,
                "Interes Mora Facturado Mandato": 0.0,
                "Otros Valor": 0.0
            }

            if record.categoria and record.valor_netsuite:
                target_column = category_column_map.get(record.categoria.value)
                # Map to Mandato column names
                if record.categoria.value == "intereses_corriente":
                    valores["Interes Corriente Facturado"] = record.valor_netsuite
                elif record.categoria.value == "intereses_mora":
                    valores["Interes Mora Facturado Mandato"] = record.valor_netsuite
                elif record.categoria.value == "otros":
                    valores["Otros Valor"] = record.valor_netsuite

            # Calculate Valor Neto Facturado (sum of all value columns)
            valor_neto = sum(valores.values())

            # Format Mes facturacion (e.g., "ago-25")
            mes_facturacion = ""
            if record.fecha:
                mes = meses.get(record.fecha.month, "")
                año = str(record.fecha.year)[-2:]  # Últimos 2 dígitos
                mes_facturacion = f"{mes}-{año}"

            # Write row data (10 columns)
            row_data = [
                record.codigo_operacion or "",  # Codigo del desembolso
                mes_facturacion,  # Mes facturacion (ej: "ago-25")
                valores["Interes Corriente Facturado"],  # Interes Corriente Facturado
                valores["Interes Mora Facturado Mandato"],  # Interes Mora Facturado Mandato
                valor_neto,  # Valor Neto Facturado
                record.fecha.strftime("%Y-%m-%d") if record.fecha else "",  # Fecha Factura
                record.numero_factura or "",  # # Factura
                record.moneda or "",  # Moneda
                record.nit or "",  # Nit
                valores["Otros Valor"]  # Otros Valor (última columna)
            ]

            for col_idx, value in enumerate(row_data, start=1):
                sheet.cell(row=row_idx, column=col_idx, value=value)

        # Auto-size columns
        for col_idx in range(1, len(MANDATO_COLUMNS) + 1):
            column_letter = openpyxl.utils.get_column_letter(col_idx)
            if col_idx == 1:  # Codigo del desembolso
                sheet.column_dimensions[column_letter].width = 30
            elif col_idx == 7:  # # Factura
                sheet.column_dimensions[column_letter].width = 15
            else:
                sheet.column_dimensions[column_letter].width = 20


# Singleton instance
_co_file_processor: Optional[COFileProcessor] = None


def get_co_file_processor() -> COFileProcessor:
    """
    Get or create the CO file processor singleton.

    Returns:
        COFileProcessor instance
    """
    global _co_file_processor
    if _co_file_processor is None:
        _co_file_processor = COFileProcessor()
    return _co_file_processor
