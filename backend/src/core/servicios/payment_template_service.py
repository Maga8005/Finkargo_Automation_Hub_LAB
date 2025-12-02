"""
Payment Template Service for Treasury Module.

Handles validation and conversion of Historial de Pagos files to
NetSuite payment application templates.
"""

import pandas as pd
import io
import logging
import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from fastapi import UploadFile

from src.interface.tesoreria_dtos import (
    HistorialValidationResponse,
    HistorialValidationError,
    ColumnValidationStatus,
    ConceptStats,
    ConversionStats,
)
from src.core.servicios.catalogs.payment_catalogs import (
    get_ar_account,
    get_bank_account_id,
    get_required_columns,
    get_concept_columns,
    get_optional_columns,
    OUTPUT_TEMPLATE_COLUMNS,
)

logger = logging.getLogger(__name__)


class PaymentTemplateService:
    """
    Service for converting Historial de Pagos files to NetSuite templates.

    Supports Colombia and México with country-specific:
    - Column mappings
    - Concept types
    - AR account lookups
    - Adjustment calculations
    """

    def __init__(self):
        """Initialize the service."""
        self.preview_rows = 5  # Number of rows to include in preview

    async def validate_historial(
        self,
        file: UploadFile,
        country: str
    ) -> HistorialValidationResponse:
        """
        Validate a Historial de Pagos Excel file.

        Args:
            file: Uploaded Excel file
            country: Country code ('colombia' or 'mexico')

        Returns:
            Validation response with column status, errors, and preview
        """
        logger.info(f"Validating Historial de Pagos for {country}")

        errors: List[HistorialValidationError] = []
        column_status: List[ColumnValidationStatus] = []

        try:
            # Read file contents
            contents = await file.read()
            await file.seek(0)  # Reset for potential reuse

            # Load Excel file
            df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
            logger.info(f"Loaded Excel with {len(df)} rows and {len(df.columns)} columns")

            # Get required columns for country
            required_columns = get_required_columns(country)
            concept_columns = get_concept_columns(country)

            # Normalize column names for matching (strip whitespace, lowercase)
            df_columns_normalized = {
                col.strip().lower(): col for col in df.columns
            }

            # Validate required columns
            for internal_name, expected_name in required_columns.items():
                expected_normalized = expected_name.strip().lower()
                found = expected_normalized in df_columns_normalized

                column_status.append(ColumnValidationStatus(
                    column_name=expected_name,
                    found=found,
                    source_column=df_columns_normalized.get(expected_normalized) if found else None
                ))

                if not found:
                    errors.append(HistorialValidationError(
                        row=0,
                        column=expected_name,
                        message=f"Columna requerida '{expected_name}' no encontrada"
                    ))

            # Check concept columns (at least some should exist)
            concepts_found = 0
            for concept_type, expected_name in concept_columns.items():
                expected_normalized = expected_name.strip().lower()
                if expected_normalized in df_columns_normalized:
                    concepts_found += 1

            if concepts_found == 0:
                errors.append(HistorialValidationError(
                    row=0,
                    column="Conceptos",
                    message="No se encontraron columnas de conceptos de pago"
                ))

            # Calculate statistics
            total_rows = len(df)
            valid_rows = total_rows  # Start assuming all valid

            # Count non-empty rows (rows with at least customer_external_id)
            customer_col = None
            for internal_name, expected_name in required_columns.items():
                if internal_name == "customer_external_id":
                    expected_normalized = expected_name.strip().lower()
                    customer_col = df_columns_normalized.get(expected_normalized)
                    break

            if customer_col:
                valid_rows = df[customer_col].notna().sum()

            # Estimate output rows (count non-zero concept values)
            estimated_output_rows = self._estimate_output_rows(
                df, concept_columns, df_columns_normalized
            )

            # Calculate concept statistics
            concept_stats = self._calculate_concept_stats(
                df, concept_columns, df_columns_normalized
            )

            # Prepare preview data
            preview_data = None
            if len(errors) == 0 or all(e.row == 0 for e in errors):  # Only column errors
                preview_data = self._get_preview_data(df)

            success = len([e for e in errors if e.row == 0]) == 0  # No critical column errors

            return HistorialValidationResponse(
                success=success,
                country=country,
                total_rows=total_rows,
                valid_rows=valid_rows,
                estimated_output_rows=estimated_output_rows,
                column_status=column_status,
                concept_stats=concept_stats,
                errors=errors,
                preview_data=preview_data
            )

        except Exception as e:
            logger.error(f"Error validating file: {e}")
            errors.append(HistorialValidationError(
                row=0,
                column="Archivo",
                message=f"Error al procesar archivo: {str(e)}"
            ))

            return HistorialValidationResponse(
                success=False,
                country=country,
                total_rows=0,
                valid_rows=0,
                estimated_output_rows=0,
                column_status=column_status,
                errors=errors,
                preview_data=None
            )

    async def convert_to_netsuite_template(
        self,
        file: UploadFile,
        country: str
    ) -> Tuple[bytes, ConversionStats]:
        """
        Convert Historial de Pagos to NetSuite template format.

        Args:
            file: Uploaded Excel file
            country: Country code ('colombia' or 'mexico')

        Returns:
            Tuple of (Excel file bytes, ConversionStats)
        """
        logger.info(f"Converting Historial de Pagos to NetSuite template for {country}")

        # Read file contents
        contents = await file.read()

        # Load Excel file
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
        logger.info(f"Loaded {len(df)} rows for conversion")

        # Get column mappings
        required_columns = get_required_columns(country)
        concept_columns = get_concept_columns(country)
        optional_columns = get_optional_columns(country)

        # Normalize column names
        df_columns_normalized = {
            col.strip().lower(): col for col in df.columns
        }

        # Track payment groups to ensure only first row gets comision_banco and spread values
        payment_groups_seen: set = set()

        # Process each row
        output_rows: List[Dict] = []
        concepts_breakdown: Dict[str, int] = {}
        skipped_rows = 0
        errors_count = 0

        for idx, row in df.iterrows():
            try:
                # Extract payment_ref to track payment groups
                payment_ref = None
                payment_ref_col = required_columns.get("payment_ref", "")
                if payment_ref_col:
                    normalized = payment_ref_col.strip().lower()
                    source_col = df_columns_normalized.get(normalized)
                    if source_col and source_col in row.index:
                        val = row[source_col]
                        if pd.notna(val):
                            payment_ref = str(val)

                # Check if this is the first row for this payment group
                is_first_row_in_group = payment_ref and payment_ref not in payment_groups_seen
                if payment_ref:
                    payment_groups_seen.add(payment_ref)

                row_results = self._process_row(
                    row,
                    country,
                    required_columns,
                    concept_columns,
                    optional_columns,
                    df_columns_normalized,
                    is_first_row_in_group
                )

                if not row_results:
                    skipped_rows += 1
                else:
                    for result_row in row_results:
                        output_rows.append(result_row)
                        concept_type = result_row.get('concept_type', 'UNKNOWN')
                        concepts_breakdown[concept_type] = concepts_breakdown.get(concept_type, 0) + 1

            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
                errors_count += 1

        # Create output DataFrame
        output_df = pd.DataFrame(output_rows, columns=OUTPUT_TEMPLATE_COLUMNS)

        # Convert to Excel bytes
        output_buffer = io.BytesIO()
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            output_df.to_excel(writer, index=False, sheet_name='Aplicacion_Pagos')

        output_bytes = output_buffer.getvalue()

        stats = ConversionStats(
            source_rows=len(df),
            output_rows=len(output_rows),
            concepts_breakdown=concepts_breakdown,
            skipped_rows=skipped_rows,
            errors_count=errors_count
        )

        logger.info(
            f"Conversion complete: {stats.source_rows} source rows -> "
            f"{stats.output_rows} output rows, {skipped_rows} skipped, {errors_count} errors"
        )

        return output_bytes, stats

    def _process_row(
        self,
        row: pd.Series,
        country: str,
        required_columns: Dict[str, str],
        concept_columns: Dict[str, str],
        optional_columns: Dict[str, str],
        df_columns_normalized: Dict[str, str],
        is_first_row_in_group: bool = False
    ) -> List[Dict]:
        """
        Process a single row and generate output rows for each non-zero concept.

        Args:
            row: Source row data
            country: Country code
            required_columns: Required column mappings
            concept_columns: Concept column mappings
            optional_columns: Optional column mappings
            df_columns_normalized: Normalized column name mapping
            is_first_row_in_group: Whether this is the first row in a payment group

        Returns:
            List of output row dictionaries
        """
        output_rows = []

        # Extract common fields
        def get_value(internal_name: str, columns: Dict[str, str]) -> Optional[str]:
            expected_name = columns.get(internal_name, "")
            normalized = expected_name.strip().lower()
            source_col = df_columns_normalized.get(normalized)
            if source_col and source_col in row.index:
                val = row[source_col]
                if pd.notna(val):
                    return str(val)
            return None

        # Get common values
        customer_external_id = get_value("customer_external_id", required_columns) or ""
        invoice_core_id = get_value("invoice_core_id", required_columns) or ""
        payment_ref = get_value("payment_ref", required_columns) or ""
        currency = get_value("currency", required_columns) or "COP"

        # Parse payment date
        payment_date_raw = get_value("payment_date", required_columns)
        payment_date = self._format_date(payment_date_raw)

        # Check for NT flag (Colombia only)
        is_nt = False
        if country.lower() == "colombia":
            nt_col_normalized = "nt"
            for col_name, source_col in df_columns_normalized.items():
                if col_name == nt_col_normalized:
                    nt_value = row.get(source_col)
                    is_nt = pd.notna(nt_value) and str(nt_value).strip() != ""
                    break

        # Get exchange rate (optional)
        exchangerate = None
        exchangerate_raw = get_value("exchangerate", optional_columns)
        if exchangerate_raw:
            try:
                exchangerate = float(exchangerate_raw)
            except (ValueError, TypeError):
                pass

        # Extract optional fields for spread and comision calculations
        referencia_bancaria = get_value("referencia_bancaria", optional_columns)
        cuenta_remitente = get_value("cuenta_remitente", optional_columns)

        # Extract spread value from input file (column AX "Spread")
        spread_value_raw = get_value("spread", optional_columns)
        spread_value = None
        if spread_value_raw:
            try:
                spread_value = float(spread_value_raw)
            except (ValueError, TypeError):
                pass

        # Extract NT flag value for spread routing (column "NT")
        nt_value_for_spread = get_value("nt_flag", optional_columns)

        # Calculate comision_banco (México only, first row of payment group)
        comision_banco = None
        if country.lower() == "mexico" and is_first_row_in_group and referencia_bancaria:
            comision_banco = self._parse_comision_banco(referencia_bancaria)
            if comision_banco is not None:
                logger.debug(f"Extracted comision_banco: {comision_banco} from '{referencia_bancaria}'")

        # Determine spread column based on NT column containing "NT"
        # If NT contains "NT" -> Spread PA, otherwise -> Spread FK
        spread_pa = None
        spread_fk = None
        spread_supra = None  # Keep for compatibility but will be None

        if spread_value is not None:
            # Check if NT column contains "NT" text (case-insensitive)
            is_nt_spread = nt_value_for_spread and "NT" in str(nt_value_for_spread).upper()

            if is_nt_spread:
                spread_pa = spread_value
                logger.debug(f"Spread value {spread_value} -> Spread PA (NT column contains NT)")
            else:
                spread_fk = spread_value
                logger.debug(f"Spread value {spread_value} -> Spread FK (NT column does not contain NT)")

        # Process each concept column
        processed_concepts = self._process_concepts(
            row, country, concept_columns, df_columns_normalized, is_nt
        )

        # Get bank account ID from cuenta_remitente
        account_id = get_bank_account_id(cuenta_remitente, country)

        # Generate output rows for non-zero concepts
        for idx, (concept_type, amount) in enumerate(processed_concepts.items()):
            if abs(amount) > 0.001:  # Skip zero or near-zero amounts
                ar_account = get_ar_account(concept_type, country, is_nt)
                if ar_account is None:
                    ar_account = get_ar_account("COSTOS_FIJOS", country, is_nt) or 0

                # Only the first output row from this payment group gets spread/comision values
                row_comision_banco = comision_banco if idx == 0 else None
                # Multiply spread by payment amount for the first row
                row_spread_pa = round(spread_pa * amount, 2) if idx == 0 and spread_pa is not None else None
                row_spread_fk = round(spread_fk * amount, 2) if idx == 0 and spread_fk is not None else None
                row_spread_supra = spread_supra if idx == 0 else None

                output_rows.append({
                    "customer_external_id": customer_external_id,
                    "invoice_core_id": invoice_core_id,
                    "concept_type": concept_type,
                    "payment_date": payment_date,
                    "payment_amount": round(amount, 2),
                    "currency": currency,
                    "payment_ref": payment_ref,
                    "account": account_id,
                    "araccount": ar_account,
                    "exchangerate": exchangerate,
                    "comision_banco": row_comision_banco,
                    "Spread PA": row_spread_pa,
                    "Spread FK": row_spread_fk,
                    "Spread Supra": row_spread_supra,
                })

        return output_rows

    def _process_concepts(
        self,
        row: pd.Series,
        country: str,
        concept_columns: Dict[str, str],
        df_columns_normalized: Dict[str, str],
        is_nt: bool
    ) -> Dict[str, float]:
        """
        Process concept columns and calculate final amounts.

        Handles INTERESES and MORATORIOS adjustment calculations:
        - INTERESES = Corrientes - Descuento - Condonación
        - MORATORIOS = Sum(PAR columns) - Sum(Condonación Mora columns)

        Args:
            row: Source row data
            country: Country code
            concept_columns: Concept column mappings
            df_columns_normalized: Normalized column name mapping
            is_nt: Whether this is Operaciones Cedidas

        Returns:
            Dictionary of concept_type -> calculated amount
        """
        concepts: Dict[str, float] = {}

        def get_numeric_value(col_name: str) -> float:
            normalized = col_name.strip().lower()
            source_col = df_columns_normalized.get(normalized)
            if source_col and source_col in row.index:
                val = row[source_col]
                if pd.notna(val):
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        pass
            return 0.0

        # Process simple concepts first (direct values)
        simple_concepts = [
            "CAPITAL", "4X1000", "FONDO_GARANTIAS", "IVA_FONDO_GARANTIAS",
            "SEGUROS", "SERVICIO_ORIGINACION", "SERVICIO_GIRO", "COSTOS_ADICIONALES",
            "COMISION_DESEMBOLSO", "COMISION_DISPOSICION", "COMISION_SWIFT",
            "COMISION_ADMINISTRACION", "COMISION_APERTURA"
        ]

        for concept_type in simple_concepts:
            col_name = concept_columns.get(concept_type, "")
            if col_name:
                value = get_numeric_value(col_name)
                if value != 0:
                    concepts[concept_type] = value

        # Calculate INTERESES (with adjustments)
        intereses_corrientes = get_numeric_value(
            concept_columns.get("INTERESES_CORRIENTES", "")
        )
        descuento_aplicado = get_numeric_value(
            concept_columns.get("DESCUENTO_APLICADO", "")
        )
        condonacion_intereses = get_numeric_value(
            concept_columns.get("CONDONACION_INTERESES_CORRIENTES", "")
        )

        intereses_final = intereses_corrientes - descuento_aplicado - condonacion_intereses
        if abs(intereses_final) > 0.001:
            concepts["INTERESES"] = intereses_final

        # Calculate MORATORIOS (sum of PAR columns minus condonaciones)
        mora_par_30 = get_numeric_value(
            concept_columns.get("INTERESES_MORA_PAR_30", "")
        )
        mora_par_60 = get_numeric_value(
            concept_columns.get("INTERESES_MORA_PAR_60", "")
        )
        mora_par_90 = get_numeric_value(
            concept_columns.get("INTERESES_MORA_PAR_90", "")
        )
        mora_par_120 = get_numeric_value(
            concept_columns.get("INTERESES_MORA_PAR_120", "")
        )

        cond_mora_30 = get_numeric_value(
            concept_columns.get("CONDONACION_MORA_30", "")
        )
        cond_mora_60 = get_numeric_value(
            concept_columns.get("CONDONACION_MORA_60", "")
        )
        cond_mora_90 = get_numeric_value(
            concept_columns.get("CONDONACION_MORA_90", "")
        )
        cond_mora_120 = get_numeric_value(
            concept_columns.get("CONDONACION_MORA_120", "")
        )

        total_mora = mora_par_30 + mora_par_60 + mora_par_90 + mora_par_120
        total_cond_mora = cond_mora_30 + cond_mora_60 + cond_mora_90 + cond_mora_120
        moratorios_final = total_mora - total_cond_mora

        if abs(moratorios_final) > 0.001:
            concepts["MORATORIOS"] = moratorios_final

        return concepts

    def _format_date(self, date_value: Optional[str]) -> str:
        """
        Format date value to dd/mm/yyyy format.

        Args:
            date_value: Raw date value from Excel

        Returns:
            Formatted date string
        """
        if not date_value:
            return ""

        try:
            # Try parsing as datetime
            if isinstance(date_value, datetime):
                return date_value.strftime("%d/%m/%Y")

            # Try common formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                try:
                    dt = datetime.strptime(str(date_value), fmt)
                    return dt.strftime("%d/%m/%Y")
                except ValueError:
                    continue

            return str(date_value)

        except Exception:
            return str(date_value)

    def _estimate_output_rows(
        self,
        df: pd.DataFrame,
        concept_columns: Dict[str, str],
        df_columns_normalized: Dict[str, str]
    ) -> int:
        """
        Estimate the number of output rows that will be generated.

        Args:
            df: Source DataFrame
            concept_columns: Concept column mappings
            df_columns_normalized: Normalized column name mapping

        Returns:
            Estimated output row count
        """
        count = 0

        for concept_type, col_name in concept_columns.items():
            normalized = col_name.strip().lower()
            source_col = df_columns_normalized.get(normalized)
            if source_col and source_col in df.columns:
                # Count non-zero values
                non_zero = df[source_col].apply(
                    lambda x: pd.notna(x) and float(x) != 0 if pd.notna(x) else False
                ).sum()
                count += non_zero

        return int(count)

    def _calculate_concept_stats(
        self,
        df: pd.DataFrame,
        concept_columns: Dict[str, str],
        df_columns_normalized: Dict[str, str]
    ) -> List[ConceptStats]:
        """
        Calculate statistics for each concept type.

        Args:
            df: Source DataFrame
            concept_columns: Concept column mappings
            df_columns_normalized: Normalized column name mapping

        Returns:
            List of ConceptStats
        """
        stats = []

        for concept_type, col_name in concept_columns.items():
            normalized = col_name.strip().lower()
            source_col = df_columns_normalized.get(normalized)
            if source_col and source_col in df.columns:
                try:
                    series = pd.to_numeric(df[source_col], errors='coerce')
                    non_zero = series.notna() & (series != 0)
                    count = non_zero.sum()
                    total = series[non_zero].sum() if count > 0 else 0

                    if count > 0:
                        stats.append(ConceptStats(
                            concept_type=concept_type,
                            count=int(count),
                            total_amount=round(float(total), 2)
                        ))
                except Exception as e:
                    logger.warning(f"Error calculating stats for {concept_type}: {e}")

        # Sort by count descending
        stats.sort(key=lambda x: x.count, reverse=True)

        return stats

    def _parse_comision_banco(self, referencia_bancaria: Optional[str]) -> Optional[float]:
        """
        Parse bank commission from 'Referencia bancaria' field.

        Handles various numeric formats:
        - "$1,234.56" (with dollar sign and comma thousands separator)
        - "1234.56" (plain decimal)
        - "1.234,56" (European format with comma decimal separator)

        Args:
            referencia_bancaria: Raw string value from 'Referencia bancaria' column

        Returns:
            Parsed float value or None if parsing fails
        """
        if not referencia_bancaria or not isinstance(referencia_bancaria, str):
            return None

        try:
            # Remove dollar sign and whitespace
            cleaned = referencia_bancaria.strip().replace("$", "").strip()

            # Try to extract numeric value using regex
            # Match patterns like: 1234.56, 1,234.56, 1.234,56
            pattern = r'[-+]?\d+(?:[.,]\d+)*'
            match = re.search(pattern, cleaned)

            if match:
                value_str = match.group(0)

                # Determine if it's European format (comma as decimal separator)
                # European format: has comma as last separator or only one comma
                if ',' in value_str and '.' not in value_str:
                    # Only commas, last one is decimal separator
                    value_str = value_str.replace(',', '.')
                elif ',' in value_str and '.' in value_str:
                    # Both present, determine which is decimal separator
                    last_comma = value_str.rfind(',')
                    last_dot = value_str.rfind('.')
                    if last_comma > last_dot:
                        # European: 1.234,56
                        value_str = value_str.replace('.', '').replace(',', '.')
                    else:
                        # US: 1,234.56
                        value_str = value_str.replace(',', '')
                else:
                    # Only dots, remove thousands separators if multiple dots
                    # or keep as is if single dot (decimal separator)
                    if value_str.count('.') > 1:
                        # Multiple dots, all are thousands separators
                        value_str = value_str.replace('.', '')

                return float(value_str)

        except (ValueError, AttributeError) as e:
            logger.warning(f"Error parsing comision_banco from '{referencia_bancaria}': {e}")

        return None

    def _get_preview_data(self, df: pd.DataFrame) -> List[Dict]:
        """
        Get preview data (first few rows) from DataFrame.

        Args:
            df: Source DataFrame

        Returns:
            List of row dictionaries
        """
        preview_df = df.head(self.preview_rows)
        preview_data = []

        for _, row in preview_df.iterrows():
            row_dict = {}
            for col in row.index:
                val = row[col]
                if pd.notna(val):
                    # Convert to JSON-serializable types
                    if isinstance(val, (pd.Timestamp, datetime)):
                        row_dict[col] = val.strftime("%Y-%m-%d")
                    else:
                        row_dict[col] = str(val)
                else:
                    row_dict[col] = None
            preview_data.append(row_dict)

        return preview_data


# Singleton instance
payment_template_service = PaymentTemplateService()
