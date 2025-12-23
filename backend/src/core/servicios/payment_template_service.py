"""
Payment Template Service for Treasury Module.

Handles validation and conversion of Historial de Pagos files to
NetSuite payment application templates.
"""

import pandas as pd
import io
import logging
import re
from typing import List, Dict, Tuple, Optional, Set
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
from src.core.servicios.trm_service import trm_service

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

    def _calculate_manual_cop_spread(
        self,
        tasa_fincargo: Optional[float],
        tasa_trm: Optional[float],
        total_pagado_usd: Optional[float]
    ) -> Optional[float]:
        """
        Calculate spread for manual COP payments.

        Formula: (Tasa Fincargo - Tasa TRM) × Total Pagado USD

        Args:
            tasa_fincargo: Fincargo exchange rate from source file
            tasa_trm: Official TRM rate from Banco de la República
            total_pagado_usd: Payment amount in USD

        Returns:
            Calculated spread amount, or None if inputs missing
        """
        if tasa_fincargo is None or tasa_trm is None or total_pagado_usd is None:
            return None

        if total_pagado_usd <= 0:
            return None

        spread = (tasa_fincargo - tasa_trm) * total_pagado_usd
        return round(spread, 2)

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

        # PRE-PROCESSING PHASE: Collect payment group-level information
        # This allows group-level decisions (like whether to create separate SPREAD line)
        payment_group_info = self._collect_payment_group_info(
            df=df,
            country=country,
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized
        )
        logger.info(f"Pre-processing complete: {len(payment_group_info)} payment groups identified")

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

                # Log payment grouping info (INFO level for key grouping decisions)
                logger.info(
                    f"Payment group: customer={customer_external_id}, "
                    f"ref='{payment_ref}', is_first_in_group={is_first_row_in_group}, "
                    f"currency='{currency}', cuenta_remitente='{cuenta_remitente}'"
                )

                # Get the group info for this payment_ref
                group_info = payment_group_info.get(payment_ref)

                row_results = self._process_row(
                    row,
                    country,
                    required_columns,
                    concept_columns,
                    optional_columns,
                    df_columns_normalized,
                    is_first_row_in_group,
                    group_info=group_info  # Pass group-level context
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

        # Log comprehensive conversion summary with all statistics
        logger.info(
            f"Conversion summary: country={country}, "
            f"source_rows={len(df)}, output_rows={len(output_rows)}, "
            f"payment_groups={len(payment_groups_seen)}, "
            f"skipped={skipped_rows}, errors={errors_count}, "
            f"concepts_breakdown={concepts_breakdown}"
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
        is_first_row_in_group: bool = False,
        group_info: Optional[Dict] = None
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
            group_info: Optional group-level context containing:
                - concepts: Set of all concepts in the payment group
                - medio_pago: Payment method for the group
                - total_pagado_usd: Total USD paid across the group
                - spread_assigned: Whether spread has been assigned to a row
                - first_cop_non_capital_row_idx: Index of first COP non-CAPITAL row

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

        # Check for Recompra flag (Colombia only)
        # Recomprada operations revert to Fincargo Colombia AR accounts even if NT is populated
        is_recomprada = False
        if country.lower() == "colombia":
            recompra_raw = get_value("recompra", optional_columns)
            if recompra_raw is not None:
                recompra_str = str(recompra_raw).strip().lower()
                is_recomprada = recompra_str in ['si', 'sí', 'yes', 'true', '1', 'recomprada']

        # Log recompra detection if it affects AR account selection
        if is_recomprada and is_nt:
            logger.info(
                f"Recompra detected: customer={customer_external_id}, "
                f"is_nt={is_nt}, is_recomprada={is_recomprada}, "
                f"ar_account will use Fincargo Colombia accounts"
            )

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

        # Determine payment type classification for logging
        is_pago_en_linea = medio_pago and "pago en l" in medio_pago.lower()
        is_manual = medio_pago and medio_pago.lower() == "manual"
        logger.info(
            f"Payment type: customer={customer_external_id}, "
            f"medio_pago='{medio_pago}', is_pago_en_linea={is_pago_en_linea}, "
            f"is_manual={is_manual}"
        )

        # Store original exchange rate for logging
        original_exchangerate = exchangerate

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

        # Clear exchange rate for Manual payments - NetSuite will use TRM from Banco de la Republica
        if medio_pago and medio_pago.lower() == "manual":
            exchangerate = None
            logger.debug(
                "Cleared exchangerate for Manual payment - NetSuite will apply TRM"
            )

        # Log exchange rate decision summary
        rate_was_adjusted = original_exchangerate != exchangerate
        if original_exchangerate is not None or exchangerate is not None:
            adjustment_reason = "none"
            if is_manual:
                adjustment_reason = "manual_cleared"
            elif rate_was_adjusted and is_pago_en_linea:
                adjustment_reason = "spread_subtraction"
            logger.info(
                f"Exchange rate decision: customer={customer_external_id}, "
                f"medio_pago='{medio_pago}', currency='{currency}', "
                f"original_rate={original_exchangerate}, applied_rate={exchangerate}, "
                f"adjustment_reason={adjustment_reason}"
            )

        # Extract Total Pagado (USD) for spread calculation
        total_pagado_usd_raw = get_value("total_pagado_usd", optional_columns)
        total_pagado_usd = None
        if total_pagado_usd_raw:
            try:
                total_pagado_usd = float(total_pagado_usd_raw)
            except (ValueError, TypeError):
                pass

        # Extract Retención (withholding tax) for Colombia output
        retencion_value = None
        if country.lower() == "colombia":
            retencion_raw = get_value("retencion", optional_columns)
            if retencion_raw:
                try:
                    retencion_value = float(retencion_raw)
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

        # Determine spread column based on NT column and recomprada flag
        # Spread goes to Spread PA only if NT column contains "NT" AND NOT recomprada
        # If recomprada=True, spread goes to Spread FK (Fincargo Colombia takes back ownership)
        spread_pa = None
        spread_fk = None
        spread_supra = None  # Keep for compatibility but will be None

        if spread_value is not None:
            # Check if NT column contains "NT" text (case-insensitive)
            is_nt_spread = nt_value_for_spread and "NT" in str(nt_value_for_spread).upper()

            # Spread goes to PA only if NT and NOT recomprada
            if is_nt_spread and not is_recomprada:
                spread_pa = spread_value
                logger.debug(f"Spread value {spread_value} -> Spread PA (NT column contains NT, not recomprada)")
            else:
                spread_fk = spread_value
                if is_recomprada and is_nt_spread:
                    logger.debug(f"Spread value {spread_value} -> Spread FK (recomprada overrides NT)")
                else:
                    logger.debug(f"Spread value {spread_value} -> Spread FK (NT column does not contain NT)")

        # Log spread calculation details (INFO level for key decision)
        if spread_value is not None:
            is_nt_spread_flag = nt_value_for_spread and "NT" in str(nt_value_for_spread).upper()
            logger.info(
                f"Spread calculation: customer={customer_external_id}, "
                f"payment_ref='{payment_ref}', total_pagado_usd={total_pagado_usd}, "
                f"spread_value={spread_value}, is_nt_spread={is_nt_spread_flag}, "
                f"is_recomprada={is_recomprada}, spread_pa={spread_pa}, spread_fk={spread_fk}"
            )

        # Manual COP payment spread handling (Colombia only)
        # For Manual COP payments, calculate spread using: (Tasa Fincargo - TRM) × Total Pagado USD
        # Spread routing still depends on NT flag: NT="NT" -> Spread PA, else -> Spread FK
        manual_cop_spread_calculated = False
        if country.lower() == "colombia" and is_manual and currency.upper() == "COP":
            # Parse payment date for TRM lookup
            payment_date_parsed = None
            if payment_date_raw:
                try:
                    if isinstance(payment_date_raw, datetime):
                        payment_date_parsed = payment_date_raw
                    elif hasattr(payment_date_raw, 'to_pydatetime'):
                        payment_date_parsed = payment_date_raw.to_pydatetime()
                    else:
                        # Try common date formats
                        date_str = str(payment_date_raw).split()[0]
                        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                            try:
                                payment_date_parsed = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                except Exception as e:
                    logger.warning(f"Could not parse payment date for TRM lookup: {e}")

            tasa_trm = None
            if payment_date_parsed:
                tasa_trm = trm_service.get_trm_for_date(payment_date_parsed)

            # Use group total USD for aggregated spread calculation
            # This ensures spread is calculated across ALL rows in the payment group
            group_total_usd_for_spread = group_info["total_pagado_usd"] if group_info else total_pagado_usd

            manual_spread = self._calculate_manual_cop_spread(
                tasa_fincargo=original_exchangerate,
                tasa_trm=tasa_trm,
                total_pagado_usd=group_total_usd_for_spread
            )

            if manual_spread is not None:
                # Override spread_value with calculated manual spread
                # Spread goes to PA only if NT and NOT recomprada (same logic as non-manual)
                is_nt_spread = nt_value_for_spread and "NT" in str(nt_value_for_spread).upper()
                if is_nt_spread and not is_recomprada:
                    spread_pa = manual_spread
                    spread_fk = None
                else:
                    spread_fk = manual_spread
                    spread_pa = None
                spread_supra = None
                manual_cop_spread_calculated = True
                logger.info(
                    f"Manual COP spread calculated: customer={customer_external_id}, "
                    f"tasa_fincargo={original_exchangerate}, tasa_trm={tasa_trm}, "
                    f"row_total_usd={total_pagado_usd}, group_total_usd={group_total_usd_for_spread}, "
                    f"is_nt={is_nt_spread}, is_recomprada={is_recomprada}, "
                    f"spread_pa={spread_pa}, spread_fk={spread_fk}"
                )
            else:
                # If manual spread couldn't be calculated, clear all spread values
                spread_pa = None
                spread_fk = None
                spread_supra = None
                logger.debug(
                    f"Manual COP spread skipped (missing data): customer={customer_external_id}, "
                    f"tasa_fincargo={original_exchangerate}, tasa_trm={tasa_trm}, "
                    f"total_pagado_usd={total_pagado_usd}"
                )
        elif country.lower() == "colombia" and is_manual and currency.upper() != "COP":
            # Manual USD: No spread calculation for USD payments
            spread_pa = None
            spread_fk = None
            spread_supra = None
            logger.debug(f"Manual USD payment - no spread: customer={customer_external_id}")

        # Process each concept column
        processed_concepts = self._process_concepts(
            row, country, concept_columns, df_columns_normalized, is_nt
        )

        # Get bank account ID from cuenta_remitente
        account_id = get_bank_account_id(cuenta_remitente, country)

        # Check if this is a capital-only Pago en Linea (Colombia only)
        # In this case, spread should be output as a separate SPREAD row instead of columns
        # CRITICAL: This decision is now made at the PAYMENT GROUP LEVEL, not individual row level
        if group_info:
            # Use group-level decision based on ALL concepts across the payment group
            should_create_separate_spread_line = self._is_capital_only_pago_en_linea_for_group(
                group_info["medio_pago"], group_info["concepts"], country
            )
        else:
            # Fallback for backward compatibility (single-row groups or when group_info not provided)
            row_concepts_set = set(k for k, v in processed_concepts.items() if abs(v) > 0.001)
            should_create_separate_spread_line = self._is_capital_only_pago_en_linea_for_group(
                medio_pago, row_concepts_set, country
            )

        # Log separate SPREAD line decision (INFO level for key decision)
        group_concepts_str = str(group_info["concepts"]) if group_info else str(list(processed_concepts.keys()))
        logger.info(
            f"Separate SPREAD line (GROUP-LEVEL): customer={customer_external_id}, "
            f"should_create={should_create_separate_spread_line}, "
            f"medio_pago='{medio_pago}', group_concepts={group_concepts_str}"
        )

        # Calculate spread amount for separate line if needed
        # Use aggregated total_pagado_usd from group_info if available (sum across all rows in payment group)
        separate_spread_amount = None
        group_total_usd = group_info["total_pagado_usd"] if group_info else total_pagado_usd
        if should_create_separate_spread_line and spread_value is not None and group_total_usd:
            separate_spread_amount = spread_value * group_total_usd
            logger.debug(
                f"Creating separate SPREAD line for capital-only Pago en linea: "
                f"customer={customer_external_id}, spread_amount={separate_spread_amount}, "
                f"row_total_usd={total_pagado_usd}, group_total_usd={group_total_usd}"
            )

        # Determine which row should get spread values (first non-CAPITAL for Colombia)
        spread_target_index = self._get_spread_target_index(processed_concepts, country)

        # For group context: check if this row should receive spread
        # When group has mixed concepts, spread should go to first non-CAPITAL row in group
        # If this row only has CAPITAL but group has other concepts, spread goes elsewhere
        row_should_receive_spread = True
        if group_info and not should_create_separate_spread_line:
            # Group has mixed concepts - spread goes to column
            # Check if this row has any non-CAPITAL concepts
            row_has_non_capital = any(
                c != "CAPITAL" for c, amt in processed_concepts.items() if abs(amt) > 0.001
            )
            # If this row only has CAPITAL and group has other concepts (INTERESES, etc.),
            # then spread should NOT go to this row - it will go to another row with non-CAPITAL
            if not row_has_non_capital and group_info["concepts"] != {"CAPITAL"}:
                row_should_receive_spread = False
                logger.info(
                    f"Spread placement: customer={customer_external_id}, "
                    f"row_has_only_capital=True, group_has_mixed_concepts=True, "
                    f"row_should_receive_spread=False (spread goes to non-CAPITAL row)"
                )

        # Generate output rows for non-zero concepts
        for idx, (concept_type, amount) in enumerate(processed_concepts.items()):
            if abs(amount) > 0.001:  # Skip zero or near-zero amounts
                ar_account = get_ar_account(concept_type, country, is_nt, is_recomprada)
                if ar_account is None:
                    ar_account = get_ar_account("COSTOS_FIJOS", country, is_nt, is_recomprada) or 0

                # Log AR account selection (DEBUG level for detailed tracing)
                logger.debug(
                    f"AR account: customer={customer_external_id}, "
                    f"concept='{concept_type}', is_nt={is_nt}, is_recomprada={is_recomprada}, "
                    f"ar_account={ar_account}"
                )

                # comision_banco always goes to first row (idx == 0)
                row_comision_banco = comision_banco if idx == 0 else None

                # Spread goes to spread_target_index (first non-CAPITAL for Colombia)
                is_spread_target = (idx == spread_target_index) and row_should_receive_spread

                # For capital-only Pago en Linea, spread goes to separate line, not columns
                if should_create_separate_spread_line:
                    row_spread_pa = None
                    row_spread_fk = None
                else:
                    # Check if spread was already assigned to another row in this payment group
                    spread_already_assigned = group_info.get("spread_assigned", False) if group_info else False

                    # Spread goes to spread_target_index row
                    if is_spread_target and not spread_already_assigned:
                        # For Manual COP payments, spread values are already the final calculated amount
                        # (not a rate to be multiplied by total_pagado_usd)
                        if manual_cop_spread_calculated:
                            # Manual COP: spread values are already final amounts
                            row_spread_pa = spread_pa
                            row_spread_fk = spread_fk
                        else:
                            # Standard behavior: multiply rate by group total USD
                            row_spread_pa = round(spread_pa * group_total_usd, 2) if spread_pa is not None and group_total_usd else None
                            row_spread_fk = round(spread_fk * group_total_usd, 2) if spread_fk is not None and group_total_usd else None

                        # Mark spread as assigned for this payment group
                        if (row_spread_pa is not None or row_spread_fk is not None) and group_info:
                            group_info["spread_assigned"] = True
                            logger.info(
                                f"Spread assigned: customer={customer_external_id}, "
                                f"concept={concept_type}, manual_cop={manual_cop_spread_calculated}, "
                                f"spread_pa={row_spread_pa}, spread_fk={row_spread_fk}"
                            )
                    else:
                        row_spread_pa = None
                        row_spread_fk = None
                row_spread_supra = spread_supra if is_spread_target else None

                # subsidiary: always 4 for Colombia, None for other countries
                row_subsidiary = 4 if country.lower() == "colombia" else None

                # retencion_en_fuente: only on first output row (idx == 0), Colombia only
                row_retencion = retencion_value if idx == 0 and country.lower() == "colombia" else None

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
                    "subsidiary": row_subsidiary,
                    "retencion_en_fuente": row_retencion,
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
        3. Cuenta Remitente (cuenta_remitente) - optional for online payments
        4. Tasa de cambio (exchangerate) - exchange rate

        IMPORTANT: Currency is NOT included in the grouping key. Payments with
        the same customer, date, cuenta_remitente, and exchange rate belong to
        the same payment group regardless of whether individual line items are
        in USD or COP. This allows multi-currency payment groups (e.g., CAPITAL
        in USD + MORATORIOS in COP) to be correctly aggregated.

        Args:
            customer_external_id: Customer identification (NIT/RFC)
            payment_date_raw: Raw payment date value
            currency: Currency code (COP, USD, MXN, etc.) - kept for signature
                compatibility but NOT used in grouping
            cuenta_remitente: Sender's bank account (may be None for online payments)
            exchangerate: Exchange rate value (may be None)

        Returns:
            Composite payment reference string for grouping
        """
        # Format date as YYYYMMDD for consistent grouping
        date_key = self._format_date_for_grouping(payment_date_raw)

        # Build components list
        # NOTE: Currency is NOT included in the grouping key to allow multi-currency
        # payment groups (e.g., CAPITAL in USD + MORATORIOS in COP) to be grouped together
        components = [
            customer_external_id or "",
            date_key,
        ]

        # Only include cuenta_remitente if it's not empty
        # For online payments, cuenta_remitente will be None/empty
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
            f"currency={currency} (not in ref), cuenta={cuenta_remitente}, "
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

        DEPRECATED: Use _is_capital_only_pago_en_linea_for_group for group-level decisions.

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

    def _is_capital_only_pago_en_linea_for_group(
        self,
        medio_pago: Optional[str],
        group_concepts: Set[str],
        country: str
    ) -> bool:
        """
        Check if the ENTIRE payment group is capital-only Pago en Linea (Colombia only).

        This method evaluates at the PAYMENT GROUP LEVEL, considering ALL concepts
        across ALL rows in the payment group, not just the current row.

        Returns True if:
        1. Country is Colombia
        2. Payment method is "Pago en linea" (case-insensitive)
        3. CAPITAL is the ONLY concept across the ENTIRE payment group

        Args:
            medio_pago: Payment method for the group
            group_concepts: Set of ALL concept types with non-zero values across ALL rows in group
            country: Country code

        Returns:
            True only if ALL rows in the group only have CAPITAL concept
        """
        # Only applies to Colombia
        if country.lower() != "colombia":
            return False

        # Check payment method contains "pago en l" (handles "Pago en linea", "Pago en Linea", etc.)
        if not medio_pago or "pago en l" not in medio_pago.lower():
            return False

        # Check if CAPITAL is the ONLY concept across the entire group
        # Must have at least CAPITAL to be valid
        if not group_concepts:
            return False

        return group_concepts == {"CAPITAL"}

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
            "subsidiary": 4,  # Always 4 for Colombia (SPREAD rows are Colombia-only)
            "retencion_en_fuente": None,  # SPREAD rows never get retencion
        }

    def _collect_payment_group_info(
        self,
        df: pd.DataFrame,
        country: str,
        required_columns: Dict[str, str],
        concept_columns: Dict[str, str],
        optional_columns: Dict[str, str],
        df_columns_normalized: Dict[str, str]
    ) -> Dict[str, Dict]:
        """
        Pre-process all rows to collect payment group-level information.

        This method scans all rows to aggregate information at the payment group level,
        allowing group-level decisions (like whether to create a separate SPREAD line).

        Args:
            df: Source DataFrame
            country: Country code
            required_columns: Required column mappings
            concept_columns: Concept column mappings
            optional_columns: Optional column mappings
            df_columns_normalized: Normalized column name mapping

        Returns:
            Dictionary keyed by payment_ref containing group-level info:
            - concepts: Set of all concept types with non-zero values across the group
            - medio_pago: Payment method for the group
            - total_pagado_usd: Sum of Total pagado [USD] across the group
            - spread_assigned: Track if spread has been assigned to a row (for output generation)
            - first_cop_non_capital_row_idx: Index of first COP row with non-CAPITAL concepts
        """
        payment_group_info: Dict[str, Dict] = {}

        def get_value(row: pd.Series, internal_name: str, columns: Dict[str, str]) -> Optional[str]:
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

        def get_numeric_value(row: pd.Series, col_name: str) -> float:
            if not col_name:
                return 0.0
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

        for idx, row in df.iterrows():
            # Extract values needed for payment_ref generation
            customer_external_id = get_value(row, "customer_external_id", required_columns) or ""
            payment_date_raw = get_value(row, "payment_date", required_columns)
            currency = get_value(row, "currency", required_columns) or "COP"
            cuenta_remitente = get_value(row, "cuenta_remitente", optional_columns)
            exchangerate_raw = get_value(row, "exchangerate", optional_columns)

            # Generate payment_ref for grouping
            payment_ref = self._generate_payment_ref(
                customer_external_id,
                payment_date_raw,
                currency,
                cuenta_remitente,
                exchangerate_raw
            )

            # Initialize group info if first row with this payment_ref
            if payment_ref not in payment_group_info:
                medio_pago = get_value(row, "medio_pago", optional_columns)
                payment_group_info[payment_ref] = {
                    "concepts": set(),
                    "medio_pago": medio_pago,
                    "total_pagado_usd": 0.0,
                    "spread_assigned": False,
                    "first_cop_non_capital_row_idx": None,
                }

            # Get total_pagado_usd for this row
            total_pagado_usd_raw = get_value(row, "total_pagado_usd", optional_columns)
            if total_pagado_usd_raw:
                try:
                    payment_group_info[payment_ref]["total_pagado_usd"] += float(total_pagado_usd_raw)
                except (ValueError, TypeError):
                    pass

            # Process concepts for this row and add to group
            # Check for NT flag (Colombia only)
            is_nt = False
            if country.lower() == "colombia":
                nt_col_normalized = "nt"
                for col_name, source_col in df_columns_normalized.items():
                    if col_name == nt_col_normalized:
                        nt_value = row.get(source_col)
                        is_nt = pd.notna(nt_value) and str(nt_value).strip() != ""
                        break

            row_concepts = self._process_concepts(
                row, country, concept_columns, df_columns_normalized, is_nt
            )

            # Add non-zero concepts to the group's concept set
            for concept_type, amount in row_concepts.items():
                if abs(amount) > 0.001:
                    payment_group_info[payment_ref]["concepts"].add(concept_type)

            # Track first COP row with non-CAPITAL concepts (for spread placement)
            row_has_non_capital = any(
                c != "CAPITAL" for c, amt in row_concepts.items() if abs(amt) > 0.001
            )
            if (currency.upper() == "COP"
                    and row_has_non_capital
                    and payment_group_info[payment_ref]["first_cop_non_capital_row_idx"] is None):
                payment_group_info[payment_ref]["first_cop_non_capital_row_idx"] = idx

        # Log group info summary at INFO level
        for payment_ref, info in payment_group_info.items():
            logger.info(
                f"Payment group pre-processed: ref='{payment_ref}', "
                f"concepts={info['concepts']}, medio_pago='{info['medio_pago']}', "
                f"total_pagado_usd={info['total_pagado_usd']}"
            )

        return payment_group_info

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
