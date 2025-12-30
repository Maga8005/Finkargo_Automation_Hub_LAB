"""
PA Report Service - Orchestrates the full PA report processing flow.

Handles:
- NetSuite file upload and parsing
- Step 1: Data cleanup and filtering
- Step 2: Classification application
- Excel file generation for download
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from io import BytesIO
from datetime import datetime, date
import pandas as pd
import uuid

from src.interface.pa_dtos import (
    PAUploadResponse,
    PACleanedPreview,
    PAClassifiedPreview,
    PAProcessingStats,
    PAProcessingStatus
)
from src.repositorio.pa_rules_repository import PARulesRepository
from src.core.servicios.pa_classification_engine import (
    PAClassificationEngine,
    create_classification_engine
)

logger = logging.getLogger(__name__)


# In-memory session storage (for development)
# In production, use Redis or persistent storage
_processing_sessions: Dict[str, Dict] = {}


class PAReportService:
    """Service for processing PA reports."""

    # Expected source file columns (mapping from Excel to internal names)
    SOURCE_COLUMN_MAPPING = {
        "Cuenta (línea): Número": "cuenta_linea_numero",
        "Cuenta (línea): Nombre": "cuenta_linea_nombre",
        "Fecha": "fecha",
        "Fecha de creación": "fecha_creacion",
        "Tipo de Transacción": "tipo_transaccion",
        "Tipo de comprobante": "tipo_comprobante",
        "Número de documento": "numero_documento",
        "Entidad": "entidad",
        "Notas": "notas",
        "Débito": "debito",
        "Crédito": "credito",
        "Saldo": "saldo",  # Will be renamed to valor_cop
        "Moneda: Nombre": "moneda_nombre",
        "Tipo de cambio": "tipo_cambio",
        "Importe (moneda extranjera)": "importe_moneda_extranjera",  # Will be renamed to valor_usd
    }

    # Output columns to add
    OUTPUT_COLUMNS = [
        "pa",
        "categoria",
        "subcategoria",
        "clasificacion",
        "nexo",
        "comprobacion_saldos",
        "cuenta_homologacion",
        "nombre_homologacion"
    ]

    def __init__(self, repository: PARulesRepository):
        """
        Initialize service with repository.

        Args:
            repository: PA rules repository instance.
        """
        self.repository = repository

    async def upload_netsuite_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> PAUploadResponse:
        """
        Upload and validate NetSuite movements file.

        This is the first step: parses the file and creates a processing session.

        Args:
            file_content: Excel file bytes.
            filename: Original filename.
            user_id: User ID.
            user_email: User email.

        Returns:
            Upload response with session ID and stats.
        """
        try:
            # Parse file based on extension
            df = self._parse_file(file_content, filename)
            total_rows = len(df)

            # Validate required columns
            missing_cols = self._validate_columns(df.columns.tolist())
            if missing_cols:
                return PAUploadResponse(
                    success=False,
                    session_id="",
                    filename=filename,
                    message=f"Faltan columnas requeridas: {', '.join(missing_cols)}",
                    errors=missing_cols
                )

            # Rename columns to internal names
            df = self._rename_columns(df)

            # Get PA account catalog
            catalog_accounts = await self.repository.get_all_catalog_accounts()
            if not catalog_accounts:
                return PAUploadResponse(
                    success=False,
                    session_id="",
                    filename=filename,
                    message="No hay catálogo de cuentas PA cargado. Por favor suba el catálogo primero.",
                    errors=["Catálogo de cuentas PA vacío"]
                )

            # Filter to PA accounts only
            df["cuenta_linea_numero"] = df["cuenta_linea_numero"].astype(str).str.strip()
            pa_df = df[df["cuenta_linea_numero"].isin(catalog_accounts)].copy()
            pa_rows = len(pa_df)

            if pa_rows == 0:
                return PAUploadResponse(
                    success=False,
                    session_id="",
                    filename=filename,
                    message="No se encontraron registros que coincidan con cuentas PA del catálogo.",
                    errors=["Sin registros PA"]
                )

            # Create session
            session_id = await self.repository.create_processing_session(
                filename=filename,
                file_size=len(file_content),
                processed_by=user_id,
                processed_by_email=user_email
            )

            if not session_id:
                # Fallback session ID
                session_id = f"PA-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:4]}"

            # Store data in memory session
            _processing_sessions[session_id] = {
                "original_df": df,
                "pa_df": pa_df,
                "filename": filename,
                "total_rows": total_rows,
                "pa_rows": pa_rows,
                "status": PAProcessingStatus.UPLOADING,
                "cleaned_df": None,
                "classified_df": None
            }

            # Update session status
            await self.repository.update_processing_session(
                session_id,
                {
                    "status": "uploading",
                    "stats": {
                        "total_rows": total_rows,
                        "pa_rows": pa_rows
                    }
                }
            )

            return PAUploadResponse(
                success=True,
                session_id=session_id,
                filename=filename,
                total_rows=total_rows,
                pa_rows=pa_rows,
                message=f"Archivo cargado correctamente. {pa_rows} registros PA de {total_rows} totales."
            )

        except Exception as e:
            logger.error(f"Error uploading NetSuite file: {e}")
            return PAUploadResponse(
                success=False,
                session_id="",
                filename=filename,
                message=f"Error al procesar archivo: {str(e)}",
                errors=[str(e)]
            )

    async def clean_data(self, session_id: str) -> PACleanedPreview:
        """
        Step 1: Clean and prepare PA data.

        - Renames columns (Saldo → Valor COP, Importe → Valor USD)
        - Adds empty output columns
        - Fills homologation from catalog
        - Validates balance

        Args:
            session_id: Processing session ID.

        Returns:
            Cleaned data preview with stats.
        """
        try:
            session = _processing_sessions.get(session_id)
            if not session:
                return PACleanedPreview(
                    session_id=session_id,
                    status=PAProcessingStatus.FAILED,
                    stats=PAProcessingStats(warnings=["Sesión no encontrada"])
                )

            pa_df = session["pa_df"].copy()

            # Update session status
            await self.repository.update_processing_session(
                session_id,
                {"status": "cleaning"}
            )

            # Get account catalog for homologation
            catalog_entries, _ = await self.repository.get_account_catalog(limit=10000)
            catalog_dict = {
                entry["cuenta_finkargo"]: entry
                for entry in catalog_entries
            }

            # Rename columns
            pa_df = pa_df.rename(columns={
                "saldo": "valor_cop",
                "importe_moneda_extranjera": "valor_usd"
            })

            # Clean numeric columns
            for col in ["debito", "credito", "valor_cop", "valor_usd"]:
                if col in pa_df.columns:
                    pa_df[col] = pd.to_numeric(pa_df[col], errors="coerce").fillna(0)

            # Add PA marker column
            pa_df["pa"] = "X"

            # Add empty classification columns
            for col in ["categoria", "subcategoria", "clasificacion", "nexo", "comprobacion_saldos"]:
                pa_df[col] = None

            # Add homologation columns
            pa_df["cuenta_homologacion"] = pa_df["cuenta_linea_numero"].apply(
                lambda x: catalog_dict.get(str(x), {}).get("cuenta_homologacion")
            )
            pa_df["nombre_homologacion"] = pa_df["cuenta_linea_numero"].apply(
                lambda x: catalog_dict.get(str(x), {}).get("nombre_homologacion")
            )

            # Calculate stats
            debito_sum = pa_df["debito"].sum()
            credito_sum = pa_df["credito"].sum()
            valor_cop_sum = pa_df["valor_cop"].sum()
            valor_usd_sum = pa_df["valor_usd"].sum()

            # Validate balance (allow small floating point differences)
            balance_valid = abs(valor_cop_sum) < 0.01 and abs(valor_usd_sum) < 0.01

            # Count missing homologation
            missing_homologacion = pa_df["cuenta_homologacion"].isna().sum()

            warnings = []
            if not balance_valid:
                warnings.append(f"Balance no cuadra: Valor COP suma {valor_cop_sum:.2f}, Valor USD suma {valor_usd_sum:.2f}")
            if missing_homologacion > 0:
                warnings.append(f"{missing_homologacion} registros sin cuenta homologación")

            stats = PAProcessingStats(
                total_rows=session["total_rows"],
                pa_rows=len(pa_df),
                non_pa_rows=session["total_rows"] - len(pa_df),
                debito_sum=debito_sum,
                credito_sum=credito_sum,
                valor_cop_sum=valor_cop_sum,
                valor_usd_sum=valor_usd_sum,
                balance_valid=balance_valid,
                missing_homologacion_count=missing_homologacion,
                warnings=warnings
            )

            # Store cleaned data
            session["cleaned_df"] = pa_df
            session["status"] = PAProcessingStatus.CLEANED

            # Update database session
            await self.repository.update_processing_session(
                session_id,
                {
                    "status": "cleaned",
                    "stats": stats.model_dump(),
                    "cleaned_at": datetime.utcnow().isoformat()
                }
            )

            # Get sample rows for preview
            sample_rows = pa_df.head(10).to_dict("records")

            # Clean sample rows for JSON serialization
            sample_rows = self._clean_for_json(sample_rows)

            return PACleanedPreview(
                session_id=session_id,
                status=PAProcessingStatus.CLEANED,
                stats=stats,
                sample_rows=sample_rows,
                column_headers=pa_df.columns.tolist()
            )

        except Exception as e:
            logger.error(f"Error cleaning data: {e}")
            return PACleanedPreview(
                session_id=session_id,
                status=PAProcessingStatus.FAILED,
                stats=PAProcessingStats(warnings=[str(e)])
            )

    async def classify_data(self, session_id: str) -> PAClassifiedPreview:
        """
        Step 2: Apply classification rules to cleaned data.

        Args:
            session_id: Processing session ID.

        Returns:
            Classified data preview with stats.
        """
        try:
            session = _processing_sessions.get(session_id)
            if not session:
                return PAClassifiedPreview(
                    session_id=session_id,
                    status=PAProcessingStatus.FAILED,
                    stats=PAProcessingStats(warnings=["Sesión no encontrada"])
                )

            cleaned_df = session.get("cleaned_df")
            if cleaned_df is None:
                return PAClassifiedPreview(
                    session_id=session_id,
                    status=PAProcessingStatus.FAILED,
                    stats=PAProcessingStats(warnings=["Datos no limpiados. Ejecute el paso 1 primero."])
                )

            # Update session status
            await self.repository.update_processing_session(
                session_id,
                {"status": "classifying"}
            )

            # Load all rules
            catalog_entries, _ = await self.repository.get_account_catalog(limit=10000)
            classification_rules = await self.repository.get_classification_rules()
            clasificacion_cuenta_rules = await self.repository.get_clasificacion_cuenta_rules()
            nexo_rules = await self.repository.get_nexo_rules()

            # Create classification engine
            engine = create_classification_engine(
                catalog_entries=catalog_entries,
                classification_rules=classification_rules,
                clasificacion_cuenta_rules=clasificacion_cuenta_rules,
                nexo_rules=nexo_rules
            )

            # Apply classification to each row
            classified_df = cleaned_df.copy()

            for idx, row in classified_df.iterrows():
                record = row.to_dict()
                classification = engine.classify_record(record)

                for col, value in classification.items():
                    classified_df.at[idx, col] = value

            # Calculate classification stats
            classified_count = classified_df["categoria"].notna().sum()
            unclassified_count = classified_df["categoria"].isna().sum()
            missing_homologacion = classified_df["cuenta_homologacion"].isna().sum()

            # Calculate balance stats
            debito_sum = classified_df["debito"].sum()
            credito_sum = classified_df["credito"].sum()
            valor_cop_sum = classified_df["valor_cop"].sum()
            valor_usd_sum = classified_df["valor_usd"].sum()
            balance_valid = abs(valor_cop_sum) < 0.01 and abs(valor_usd_sum) < 0.01

            warnings = []
            if unclassified_count > 0:
                warnings.append(f"{unclassified_count} registros sin clasificación")
            if missing_homologacion > 0:
                warnings.append(f"{missing_homologacion} registros sin cuenta homologación")

            # Calculate classification summary
            classification_summary = classified_df["categoria"].value_counts().to_dict()

            stats = PAProcessingStats(
                total_rows=session["total_rows"],
                pa_rows=len(classified_df),
                non_pa_rows=session["total_rows"] - len(classified_df),
                debito_sum=debito_sum,
                credito_sum=credito_sum,
                valor_cop_sum=valor_cop_sum,
                valor_usd_sum=valor_usd_sum,
                balance_valid=balance_valid,
                classified_count=classified_count,
                unclassified_count=unclassified_count,
                missing_homologacion_count=missing_homologacion,
                warnings=warnings
            )

            # Store classified data
            session["classified_df"] = classified_df
            session["status"] = PAProcessingStatus.CLASSIFIED

            # Update database session
            await self.repository.update_processing_session(
                session_id,
                {
                    "status": "classified",
                    "stats": stats.model_dump(),
                    "classified_at": datetime.utcnow().isoformat()
                }
            )

            # Get sample rows for preview
            sample_rows = classified_df.head(10).to_dict("records")
            sample_rows = self._clean_for_json(sample_rows)

            return PAClassifiedPreview(
                session_id=session_id,
                status=PAProcessingStatus.CLASSIFIED,
                stats=stats,
                sample_rows=sample_rows,
                column_headers=classified_df.columns.tolist(),
                classification_summary=classification_summary
            )

        except Exception as e:
            logger.error(f"Error classifying data: {e}")
            return PAClassifiedPreview(
                session_id=session_id,
                status=PAProcessingStatus.FAILED,
                stats=PAProcessingStats(warnings=[str(e)])
            )

    async def get_cleaned_excel(self, session_id: str) -> Optional[bytes]:
        """
        Generate cleaned Excel file for download.

        Args:
            session_id: Processing session ID.

        Returns:
            Excel file bytes or None.
        """
        session = _processing_sessions.get(session_id)
        if not session or session.get("cleaned_df") is None:
            return None

        try:
            df = session["cleaned_df"]
            output = BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Reporte PA Limpio", index=False)

            output.seek(0)
            return output.getvalue()

        except Exception as e:
            logger.error(f"Error generating cleaned Excel: {e}")
            return None

    async def get_classified_excel(self, session_id: str) -> Optional[bytes]:
        """
        Generate classified Excel file for download.

        Args:
            session_id: Processing session ID.

        Returns:
            Excel file bytes or None.
        """
        session = _processing_sessions.get(session_id)
        if not session or session.get("classified_df") is None:
            return None

        try:
            df = session["classified_df"]
            output = BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Reporte PA Clasificado", index=False)

            output.seek(0)
            return output.getvalue()

        except Exception as e:
            logger.error(f"Error generating classified Excel: {e}")
            return None

    async def get_session_stats(self, session_id: str) -> Optional[PAProcessingStats]:
        """
        Get processing stats for a session.

        Args:
            session_id: Processing session ID.

        Returns:
            Stats or None.
        """
        session_data = await self.repository.get_processing_session(session_id)
        if not session_data:
            return None

        stats_data = session_data.get("stats", {})
        return PAProcessingStats(**stats_data)

    def _parse_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """
        Parse file based on extension (Excel or CSV).

        Args:
            file_content: File content as bytes.
            filename: Original filename to detect extension.

        Returns:
            Parsed DataFrame.

        Raises:
            ValueError: If file cannot be parsed.
        """
        filename_lower = filename.lower()

        if filename_lower.endswith(".csv"):
            return self._parse_csv(file_content)
        else:
            # Excel file (.xlsx, .xls)
            return pd.read_excel(BytesIO(file_content))

    def _parse_csv(self, file_content: bytes) -> pd.DataFrame:
        """
        Parse CSV file with encoding and delimiter detection.

        Tries multiple encodings, detects delimiter automatically, and
        auto-detects header row position (skipping title rows if present).

        Args:
            file_content: CSV file content as bytes.

        Returns:
            Parsed DataFrame.

        Raises:
            ValueError: If CSV cannot be parsed with any encoding.
        """
        # Encoding priority order
        encodings = ["utf-8", "utf-8-sig", "latin-1", "iso-8859-1"]

        # Detect delimiter from file content
        delimiter = self._detect_csv_delimiter(file_content)

        # Detect header row (may have title rows before actual headers)
        header_row = self._detect_header_row(file_content, delimiter)
        if header_row > 0:
            logger.info(f"Detected {header_row} title rows before header, will skip them")

        for encoding in encodings:
            try:
                df = pd.read_csv(
                    BytesIO(file_content),
                    encoding=encoding,
                    delimiter=delimiter,
                    quotechar='"',
                    thousands=None,  # Don't interpret commas as thousands separators
                    skiprows=header_row  # Skip title rows before header
                )

                # Validate that we got meaningful data
                if len(df.columns) > 1 and len(df) > 0:
                    logger.info(f"CSV parsed successfully with encoding={encoding}, delimiter='{delimiter}', skiprows={header_row}")
                    return df

            except UnicodeDecodeError:
                continue
            except pd.errors.ParserError as e:
                logger.warning(f"CSV parser error with encoding={encoding}: {e}")
                continue

        raise ValueError("Error de codificación en archivo CSV. Asegúrese de usar UTF-8.")

    def _detect_header_row(self, file_content: bytes, delimiter: str) -> int:
        """
        Detect the row number where actual column headers are located.

        Some files have title/header rows before the actual column headers.
        This method scans the first 20 lines looking for the expected
        header column "Cuenta (línea): Número" or variants.

        Args:
            file_content: CSV file content as bytes.
            delimiter: CSV delimiter character.

        Returns:
            Row number (0-indexed) where headers are found, or 0 if not found.
        """
        # Header patterns to search for (handle encoding variations)
        header_patterns = [
            "Cuenta (línea): Número",
            "Cuenta (linea): Numero",
            "Cuenta (línea): Numero",
            "Cuenta (linea): Número",
        ]

        # Try different encodings to decode the file
        encodings = ["utf-8", "utf-8-sig", "latin-1", "iso-8859-1"]

        for encoding in encodings:
            try:
                text = file_content.decode(encoding)
                lines = text.split("\n")

                # Scan first 20 lines
                for row_idx, line in enumerate(lines[:20]):
                    # Check if any header pattern is in this line
                    for pattern in header_patterns:
                        if pattern in line:
                            logger.info(f"Found header pattern '{pattern}' at row {row_idx}")
                            return row_idx

                # If we decoded successfully but didn't find header in first 20 rows,
                # return 0 (no skip) for backward compatibility
                return 0

            except UnicodeDecodeError:
                continue

        # If all encodings failed, return 0 (no skip)
        return 0

    def _detect_csv_delimiter(self, file_content: bytes) -> str:
        """
        Detect CSV delimiter by analyzing the first line.

        Args:
            file_content: CSV file content as bytes.

        Returns:
            Detected delimiter (comma or semicolon).
        """
        try:
            # Try to decode first line
            first_line = file_content.split(b"\n")[0].decode("utf-8", errors="ignore")

            # Count occurrences
            semicolons = first_line.count(";")
            commas = first_line.count(",")

            # If more semicolons than commas, use semicolon
            if semicolons > commas:
                return ";"
            return ","
        except Exception:
            return ","

    def _validate_columns(self, columns: List[str]) -> List[str]:
        """
        Validate that required columns are present.

        Returns list of missing columns.
        """
        required = [
            "Cuenta (línea): Número",
            "Cuenta (línea): Nombre",
            "Débito",
            "Crédito",
            "Saldo"
        ]

        # Normalize columns for comparison
        normalized_cols = [c.strip() for c in columns]

        missing = []
        for req in required:
            if req not in normalized_cols:
                missing.append(req)

        return missing

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rename columns to internal names.
        """
        # Build mapping from actual columns to internal names
        mapping = {}
        for col in df.columns:
            col_stripped = col.strip()
            if col_stripped in self.SOURCE_COLUMN_MAPPING:
                mapping[col] = self.SOURCE_COLUMN_MAPPING[col_stripped]

        return df.rename(columns=mapping)

    def _clean_for_json(self, records: List[Dict]) -> List[Dict]:
        """
        Clean records for JSON serialization.

        Converts dates and handles NaN values.
        """
        cleaned = []
        for record in records:
            clean_record = {}
            for key, value in record.items():
                if pd.isna(value):
                    clean_record[key] = None
                elif isinstance(value, (date, datetime)):
                    clean_record[key] = value.isoformat()
                elif isinstance(value, pd.Timestamp):
                    clean_record[key] = value.isoformat()
                else:
                    clean_record[key] = value
            cleaned.append(clean_record)
        return cleaned


# Factory function
def get_pa_report_service(repository: PARulesRepository) -> PAReportService:
    """
    Create PA report service instance.

    Args:
        repository: PA rules repository.

    Returns:
        PAReportService instance.
    """
    return PAReportService(repository)
