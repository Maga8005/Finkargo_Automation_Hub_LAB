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
                # Helper to extract column values for payment group key generation
                def get_row_value(internal_name: str, columns: Dict[str, str]) -> Optional[str]:
                    expected_name = columns.get(internal_name, "")
                    if not expected_name:
                        return None
                    normalized = expected_name.strip().lower()
                    source_col = df_columns_normalized.get(normalized)
                    if source_col and source_col in row.index:
                        val = row[source_col]
                        if pd.notna(val):
                            return str(val)
                    return None

                # Extract values needed for payment group key generation
                customer_external_id = get_row_value("customer_external_id", required_columns) or ""
                payment_date_raw = get_row_value("payment_date", required_columns)
                currency = get_row_value("currency", required_columns) or "COP"
                cuenta_remitente = get_row_value("cuenta_remitente", optional_columns)
                exchangerate_raw = get_row_value("exchangerate", optional_columns)

                # Generate payment_ref using grouping logic:
                # customer_external_id + payment_date + currency + cuenta_remitente + exchangerate
                payment_ref = self._generate_payment_ref(
                    customer_external_id,
                    payment_date_raw,
                    currency,
                    cuenta_remitente,
                    exchangerate_raw
                )

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

        # Generate payment_ref using grouping logic:
        # customer_external_id + payment_date + currency + cuenta_remitente + exchangerate
        # For online payments (no cuenta_remitente), currency differentiates accounts
        payment_ref = self._generate_payment_ref(
            customer_external_id,
            payment_date_raw,
            currency,
            cuenta_remitente,
            exchangerate_raw
        )

        # Extract spread value from input file (column AX "Spread")
        spread_value_raw = get_value("spread", optional_columns)
        spread_value = None
        if spread_value_raw:
            try:
                spread_value = float(spread_value_raw)
            except (ValueError, TypeError):
                pass

        # Extract payment method for exchange rate adjustment
        medio_pago = get_value("medio_pago", optional_columns)

        # Adjust exchange rate for "Pago en línea" with COP currency
        # Business rule: When Medio de pago is "Pago en línea" and currency is COP,
        # subtract the spread from the exchange rate
        if (exchangerate is not None
                and spread_value is not None
                and medio_pago
                and "pago en l" in medio_pago.lower()
                and currency.upper() == "COP"):
            original_rate = exchangerate
            exchangerate = exchangerate - spread_value
            logger.debug(
                f"Adjusted exchangerate for Pago en línea COP: "
                f"original={original_rate}, spread={spread_value}, adjusted={exchangerate}"
            )

        # Extract Total Pagado (USD) for spread calculation
        total_pagado_usd_raw = get_value("total_pagado_usd", optional_columns)
        total_pagado_usd = None
        if total_pagado_usd_raw:
            try:
                total_pagado_usd = float(total_pagado_usd_raw)
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

        # Log spread calculation details
        if spread_value is not None and total_pagado_usd is not None:
            logger.debug(f"Spread calculation: {spread_value} × {total_pagado_usd} USD")

        # Process each concept column
        processed_concepts = self._process_concepts(
            row, country, concept_columns, df_columns_normalized, is_nt
        )

        # Get bank account ID from cuenta_remitente
        account_id = get_bank_account_id(cuenta_remitente, country)

        # Check if this is a capital-only Pago en Linea (Colombia only)
        # In this case, spread should be output as a separate SPREAD row instead of columns
        should_create_separate_spread_line = self._is_capital_only_pago_en_linea(
            medio_pago, processed_concepts, country
        )

        # Calculate spread amount for separate line if needed
        separate_spread_amount = None
        if should_create_separate_spread_line and spread_value is not None and total_pagado_usd is not None:
            separate_spread_amount = spread_value * total_pagado_usd
            logger.debug(
                f"Creating separate SPREAD line for capital-only Pago en linea: "
                f"customer={customer_external_id}, spread_amount={separate_spread_amount}"
            )

        # Determine which row should get spread values (first non-CAPITAL for Colombia)
        spread_target_index = self._get_spread_target_index(processed_concepts, country)

        # Generate output rows for non-zero concepts
        for idx, (concept_type, amount) in enumerate(processed_concepts.items()):
            if abs(amount) > 0.001:  # Skip zero or near-zero amounts
                ar_account = get_ar_account(concept_type, country, is_nt)
                if ar_account is None:
                    ar_account = get_ar_account("COSTOS_FIJOS", country, is_nt) or 0

                # comision_banco always goes to first row (idx == 0)
                row_comision_banco = comision_banco if idx == 0 else None

                # Spread goes to spread_target_index (first non-CAPITAL for Colombia)
                is_spread_target = (idx == spread_target_index)

                # For capital-only Pago en Linea, spread goes to separate line, not columns
                if should_create_separate_spread_line:
                    row_spread_pa = None
                    row_spread_fk = None
                else:
                    # Spread goes to spread_target_index row
                    row_spread_pa = round(spread_pa * total_pagado_usd, 2) if is_spread_target and spread_pa is not None and total_pagado_usd is not None else None
                    row_spread_fk = round(spread_fk * total_pagado_usd, 2) if is_spread_target and spread_fk is not None and total_pagado_usd is not None else None
                row_spread_supra = spread_supra if is_spread_target else None

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

        # Add separate SPREAD row for capital-only Pago en Linea
        if should_create_separate_spread_line and separate_spread_amount is not None and abs(separate_spread_amount) > 0.001:
            spread_row = self._create_spread_output_row(
                customer_external_id=customer_external_id,
                invoice_core_id=invoice_core_id,
                payment_date=payment_date,
                payment_ref=payment_ref,
                exchangerate=exchangerate,
                spread_amount=separate_spread_amount
            )
            output_rows.append(spread_row)

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

        # Process simple concepts based on country
        # Colombia: Aggregates cost columns into COSTOS_FIJOS
        # México: Processes each concept individually
        if country.lower() == "colombia":
            # Colombia simple concepts: CAPITAL and SEGUROS only
            colombia_simple_concepts = ["CAPITAL", "SEGUROS"]
            for concept_type in colombia_simple_concepts:
                col_name = concept_columns.get(concept_type, "")
                if col_name:
                    value = get_numeric_value(col_name)
                    if value != 0:
                        concepts[concept_type] = value

            # Colombia: Aggregate cost columns into COSTOS_FIJOS
            costos_fijos_components = [
                "4X1000", "FONDO_GARANTIAS", "IVA_FONDO_GARANTIAS",
                "SERVICIO_ORIGINACION", "SERVICIO_GIRO", "COSTOS_ADICIONALES"
            ]
            costos_fijos_total = 0.0
            for component in costos_fijos_components:
                col_name = concept_columns.get(component, "")
                if col_name:
                    costos_fijos_total += get_numeric_value(col_name)

            if abs(costos_fijos_total) > 0.001:
                concepts["COSTOS_FIJOS"] = costos_fijos_total
        else:
            # México: Process each concept individually with space-separated names
            mexico_simple_concepts = [
                "CAPITAL", "SEGUROS", "COSTOS ADICIONALES",
                "COMISION DESEMBOLSO", "COMISION DISPOSICION", "COMISION SWIFT",
                "COMISION ADMINISTRACION", "COMISION APERTURA"
            ]
            for concept_type in mexico_simple_concepts:
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

        # Calculate MORATORIOS (sum of PAR 60/61 columns minus condonaciones)
        # Both Colombia and México use: PAR 60/61 with Tasa corriente and Tasa restante de mora
        mora_col_60 = concept_columns.get("INTERESES_MORA_TASA_CORRIENTE_PAR_60", "")
        mora_tasa_corriente_60 = get_numeric_value(mora_col_60)

        mora_col_60_rest = concept_columns.get("INTERESES_MORA_TASA_RESTANTE_PAR_60", "")
        mora_tasa_restante_60 = get_numeric_value(mora_col_60_rest)

        mora_col_61 = concept_columns.get("INTERESES_MORA_TASA_CORRIENTE_PAR_61", "")
        mora_tasa_corriente_61 = get_numeric_value(mora_col_61)

        mora_col_61_rest = concept_columns.get("INTERESES_MORA_TASA_RESTANTE_PAR_61", "")
        mora_tasa_restante_61 = get_numeric_value(mora_col_61_rest)

        cond_mora_tasa_corriente_60 = get_numeric_value(
            concept_columns.get("CONDONACION_MORA_TASA_CORRIENTE_PAR_60", "")
        )
        cond_mora_tasa_restante_60 = get_numeric_value(
            concept_columns.get("CONDONACION_MORA_TASA_RESTANTE_PAR_60", "")
        )
        cond_mora_tasa_corriente_61 = get_numeric_value(
            concept_columns.get("CONDONACION_MORA_TASA_CORRIENTE_PAR_61", "")
        )
        cond_mora_tasa_restante_61 = get_numeric_value(
            concept_columns.get("CONDONACION_MORA_TASA_RESTANTE_PAR_61", "")
        )

        total_mora = (mora_tasa_corriente_60 + mora_tasa_restante_60 +
                      mora_tasa_corriente_61 + mora_tasa_restante_61)
        total_cond_mora = (cond_mora_tasa_corriente_60 + cond_mora_tasa_restante_60 +
                          cond_mora_tasa_corriente_61 + cond_mora_tasa_restante_61)
        moratorios_final = total_mora - total_cond_mora

        # Debug logging for first few rows
        if total_mora > 0 or total_cond_mora > 0:
            logger.info(f"MORATORIOS DEBUG: mora={total_mora}, cond={total_cond_mora}, final={moratorios_final}")

        if abs(moratorios_final) > 0.001:
            concepts["MORATORIOS"] = moratorios_final

        return concepts

    def _generate_payment_ref(
        self,
        customer_external_id: str,
        payment_date_raw: Optional[str],
        currency: str,
        cuenta_remitente: Optional[str],
        exchangerate: Optional[str] = None
    ) -> str:
        """
        Generate a composite payment reference for grouping payments.

        The grouping logic is based on the combination of:
        1. Identificación del cliente (customer_external_id)
        2. Fecha de pago (payment_date) - formatted as YYYYMMDD
        3. Moneda (currency)
        4. Cuenta Remitente (cuenta_remitente) - optional for online payments
        5. Tasa de cambio (exchangerate) - exchange rate

        For online payments where no bank account is registered, the currency
        differentiates between payments going to different accounts
        (compensation account vs peso account).

        Args:
            customer_external_id: Customer identification (NIT/RFC)
            payment_date_raw: Raw payment date value
            currency: Currency code (COP, USD, MXN, etc.)
            cuenta_remitente: Sender's bank account (may be None for online payments)
            exchangerate: Exchange rate value (may be None)

        Returns:
            Composite payment reference string for grouping
        """
        # Format date as YYYYMMDD for consistent grouping
        date_key = self._format_date_for_grouping(payment_date_raw)

        # Build components list
        components = [
            customer_external_id or "",
            date_key,
            currency.upper() if currency else "COP"
        ]

        # Only include cuenta_remitente if it's not empty
        # For online payments, cuenta_remitente will be None/empty
        # and currency will differentiate between accounts
        if cuenta_remitente and str(cuenta_remitente).strip():
            components.append(str(cuenta_remitente).strip())

        # Add exchange rate to grouping key (format to 4 decimal places for consistency)
        if exchangerate is not None and str(exchangerate).strip():
            try:
                rate_value = float(exchangerate)
                components.append(f"{rate_value:.4f}")
            except (ValueError, TypeError):
                components.append(str(exchangerate).strip())

        # Join with pipe separator (unlikely to appear in values)
        payment_ref = "|".join(components)

        logger.debug(
            f"Generated payment_ref: {payment_ref} from "
            f"customer={customer_external_id}, date={date_key}, "
            f"currency={currency}, cuenta={cuenta_remitente}, "
            f"exchangerate={exchangerate}"
        )

        return payment_ref

    def _format_date_for_grouping(self, date_value: Optional[str]) -> str:
        """
        Format date value to YYYYMMDD format for consistent grouping.

        Args:
            date_value: Raw date value from Excel

        Returns:
            Date string in YYYYMMDD format, or empty string if invalid
        """
        if not date_value:
            return ""

        try:
            # Try parsing as datetime object directly
            if isinstance(date_value, datetime):
                return date_value.strftime("%Y%m%d")

            # Handle pandas Timestamp
            if hasattr(date_value, 'strftime'):
                return date_value.strftime("%Y%m%d")

            # Try common date formats
            date_str = str(date_value).strip()
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
                        "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"]:
                try:
                    dt = datetime.strptime(date_str.split()[0] if ' ' in date_str else date_str, fmt.split()[0])
                    return dt.strftime("%Y%m%d")
                except ValueError:
                    continue

            # If all parsing fails, return as-is (may cause grouping issues)
            return date_str

        except Exception:
            return str(date_value) if date_value else ""

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

    def _is_capital_only_pago_en_linea(
        self,
        medio_pago: Optional[str],
        processed_concepts: Dict[str, float],
        country: str
    ) -> bool:
        """
        Check if this is a capital-only Pago en Linea payment (Colombia only).

        Returns True if:
        1. Country is Colombia
        2. Payment method is "Pago en linea" (case-insensitive)
        3. CAPITAL is the only non-zero concept

        Args:
            medio_pago: Payment method string
            processed_concepts: Dictionary of concept_type -> amount
            country: Country code

        Returns:
            True if this is a capital-only Pago en Linea payment
        """
        # Only applies to Colombia
        if country.lower() != "colombia":
            return False

        # Check payment method contains "pago en l" (handles "Pago en linea", "Pago en Linea", etc.)
        if not medio_pago or "pago en l" not in medio_pago.lower():
            return False

        # Check if only CAPITAL has a non-zero value
        non_zero_concepts = [k for k, v in processed_concepts.items() if abs(v) > 0.001]
        return non_zero_concepts == ["CAPITAL"]

    def _get_spread_target_index(
        self,
        processed_concepts: Dict[str, float],
        country: str
    ) -> int:
        """
        Determine which output row index should receive spread values.

        For Colombia:
        - If multiple concepts exist, return index of first non-CAPITAL concept
        - If only CAPITAL exists, return 0 (will be handled separately or go to CAPITAL)

        For México:
        - Always return 0 (standard behavior, spread on first row)

        Args:
            processed_concepts: Dictionary of concept_type -> amount
            country: Country code

        Returns:
            Index of the row that should receive spread values
        """
        if country.lower() != "colombia":
            return 0  # México uses standard behavior (first row)

        # Get list of non-zero concepts in order
        non_zero_concepts = [k for k, v in processed_concepts.items() if abs(v) > 0.001]

        # Find first non-CAPITAL concept
        for idx, concept in enumerate(non_zero_concepts):
            if concept != "CAPITAL":
                return idx

        # If only CAPITAL exists, return 0
        return 0

    def _create_spread_output_row(
        self,
        customer_external_id: str,
        invoice_core_id: str,
        payment_date: str,
        payment_ref: str,
        exchangerate: Optional[float],
        spread_amount: float
    ) -> Dict:
        """
        Create a separate SPREAD output row for capital-only Pago en Linea payments.

        The SPREAD row has blank account and araccount fields.

        Args:
            customer_external_id: Customer identifier
            invoice_core_id: Invoice/desembolso code
            payment_date: Formatted payment date
            payment_ref: Payment reference for grouping
            exchangerate: Exchange rate value
            spread_amount: Calculated spread amount (spread_value * total_pagado_usd)

        Returns:
            Dictionary representing the SPREAD output row
        """
        return {
            "customer_external_id": customer_external_id,
            "invoice_core_id": invoice_core_id,
            "concept_type": "SPREAD",
            "payment_date": payment_date,
            "payment_amount": round(spread_amount, 2),
            "currency": "COP",  # Spread is always in COP for Colombia
            "payment_ref": payment_ref,
            "account": None,  # Blank for SPREAD
            "araccount": None,  # Blank for SPREAD
            "exchangerate": exchangerate,
            "comision_banco": None,
            "Spread PA": None,
            "Spread FK": None,
            "Spread Supra": None,
        }

    def _parse_comision_banco(self, referencia_bancaria) -> Optional[float]:
        """
        Parse bank commission from 'Referencia bancaria' field.

        Handles various formats:
        - Numeric values (int, float) - returned directly
        - "$1,234.56" (with dollar sign and comma thousands separator)
        - "1234.56" (plain decimal)
        - "1.234,56" (European format with comma decimal separator)

        Args:
            referencia_bancaria: Raw value from 'Referencia bancaria' column (string or numeric)

        Returns:
            Parsed float value or None if parsing fails
        """
        if referencia_bancaria is None:
            return None

        # Handle numeric values directly (from Excel)
        if isinstance(referencia_bancaria, (int, float)):
            return float(referencia_bancaria)

        # Handle string values
        if not isinstance(referencia_bancaria, str):
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
