"""
PA Report Service - Orchestrates the full PA report processing flow.

Handles:
- NetSuite file upload and parsing
- Step 1: Data cleanup and filtering
- Step 2: Classification application
- Excel file generation for download
- File persistence to Supabase Storage
"""

import logging
from typing import Dict, Optional, List
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
    create_classification_engine
)
from src.config.supabase_config import get_supabase_client

logger = logging.getLogger(__name__)


# In-memory session storage (for development)
# In production, use Redis or persistent storage
_processing_sessions: Dict[str, Dict] = {}

# Supabase Storage bucket for PA reports
PA_REPORTS_BUCKET = "pa-reports"


class PAReportService:
    """Service for processing PA reports."""

    # Expected source file columns (mapping from Excel to internal names)
    # Note: Column names are normalized before matching (whitespace collapsed, trimmed)
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

    # Alternative column names (variations found in real CSV files)
    # Maps alternative names to the canonical name in SOURCE_COLUMN_MAPPING
    COLUMN_ALIASES = {
        # Double space variant in "Tipo de Transacción"
        "Tipo  de Transacción": "Tipo de Transacción",
        # Singular variant of "Notas"
        "Nota": "Notas",
        # Alternative name for notes column
        "Mensaje": "Notas",
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
        self._supabase = get_supabase_client()

    async def _upload_excel_to_storage(
        self,
        excel_bytes: bytes,
        session_id: str,
        file_type: str
    ) -> Optional[str]:
        """
        Upload Excel file to Supabase Storage.

        Args:
            excel_bytes: Excel file content as bytes.
            session_id: Processing session ID.
            file_type: Type of file ('cleaned' or 'classified').

        Returns:
            Public URL of uploaded file, or None if upload fails.
        """
        try:
            # Generate unique file path
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_path = f"{session_id}/PA_{file_type.capitalize()}_{timestamp}.xlsx"

            logger.info(f"Uploading {file_type} Excel to storage: {file_path}")

            # Upload to Supabase Storage
            response = self._supabase.storage.from_(PA_REPORTS_BUCKET).upload(
                path=file_path,
                file=excel_bytes,
                file_options={
                    "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "upsert": "true"
                }
            )

            logger.debug(f"Storage upload response: {response}")

            # Get public URL
            public_url = self._supabase.storage.from_(PA_REPORTS_BUCKET).get_public_url(file_path)
            logger.info(f"File uploaded successfully: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Error uploading {file_type} Excel to storage: {e}", exc_info=True)
            return None

    async def _download_from_storage(self, file_url: str) -> Optional[bytes]:
        """
        Download file from Supabase Storage.

        Args:
            file_url: Public URL of the file.

        Returns:
            File bytes, or None if download fails.
        """
        try:
            # Extract file path from URL
            # URL format: https://<project>.supabase.co/storage/v1/object/public/pa-reports/<path>
            if PA_REPORTS_BUCKET not in file_url:
                logger.error(f"Invalid storage URL: {file_url}")
                return None

            # Extract path after bucket name
            path_start = file_url.find(f"{PA_REPORTS_BUCKET}/") + len(PA_REPORTS_BUCKET) + 1
            file_path = file_url[path_start:]

            logger.info(f"Downloading file from storage: {file_path}")

            # Download from storage
            file_bytes = self._supabase.storage.from_(PA_REPORTS_BUCKET).download(file_path)

            logger.info(f"File downloaded successfully: {len(file_bytes)} bytes")
            return file_bytes

        except Exception as e:
            logger.error(f"Error downloading from storage: {e}", exc_info=True)
            return None

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

            # Validate critical column exists after renaming
            if "cuenta_linea_numero" not in df.columns:
                actual_columns = df.columns.tolist()
                logger.error(f"Critical column 'cuenta_linea_numero' not found after renaming. Columns present: {actual_columns}")
                return PAUploadResponse(
                    success=False,
                    session_id="",
                    filename=filename,
                    message=f"La columna 'Cuenta (línea): Número' no se encontró en el archivo. "
                           f"Columnas encontradas: {', '.join(actual_columns[:10])}{'...' if len(actual_columns) > 10 else ''}",
                    errors=["Columna cuenta_linea_numero no encontrada"]
                )

            # Get PA account catalog
            catalog_accounts = await self.repository.get_all_catalog_accounts()
            catalog_count = len(catalog_accounts)
            logger.info(f"Retrieved {catalog_count} accounts from PA catalog")

            if not catalog_accounts:
                return PAUploadResponse(
                    success=False,
                    session_id="",
                    filename=filename,
                    message="No hay catálogo de cuentas PA cargado. Por favor suba el catálogo primero.",
                    errors=["Catálogo de cuentas PA vacío"]
                )

            # Filter to PA accounts only
            # Normalize account numbers to clean strings (handles float .0 suffix issue)
            df["cuenta_linea_numero"] = df["cuenta_linea_numero"].apply(
                self._normalize_account_number
            )
            file_accounts = df["cuenta_linea_numero"].unique().tolist()
            file_account_count = len(file_accounts)
            logger.info(f"Found {file_account_count} unique accounts in uploaded file")

            # Log sample accounts for debugging
            if file_accounts:
                sample_file_accounts = file_accounts[:5]
                logger.debug(f"Sample normalized accounts from file: {sample_file_accounts}")
            if catalog_accounts:
                sample_catalog_accounts = catalog_accounts[:5]
                logger.debug(f"Sample accounts from catalog: {sample_catalog_accounts}")

            pa_df = df[df["cuenta_linea_numero"].isin(catalog_accounts)].copy()
            pa_rows = len(pa_df)

            if pa_rows == 0:
                # Provide detailed error message to help diagnose the issue
                message = (
                    f"No se encontraron coincidencias. "
                    f"Cuentas en archivo: {file_account_count}, "
                    f"Cuentas en catálogo: {catalog_count}. "
                    f"Verifique que el catálogo contenga las cuentas correctas."
                )
                logger.warning(
                    f"No PA account matches found. "
                    f"File accounts (sample): {file_accounts[:5]}, "
                    f"Catalog accounts (sample): {catalog_accounts[:5]}"
                )
                return PAUploadResponse(
                    success=False,
                    session_id="",
                    filename=filename,
                    message=message,
                    errors=["Sin coincidencias de cuentas PA"]
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

            # Generate and persist Excel file to storage
            cleaned_file_url = None
            try:
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    pa_df.to_excel(writer, sheet_name="Reporte PA Limpio", index=False)
                output.seek(0)
                excel_bytes = output.getvalue()

                # Upload to Supabase Storage
                cleaned_file_url = await self._upload_excel_to_storage(
                    excel_bytes, session_id, "cleaned"
                )
                if cleaned_file_url:
                    logger.info(f"Cleaned Excel persisted to storage: {cleaned_file_url}")
                else:
                    logger.warning(f"Failed to persist cleaned Excel to storage for session {session_id}")
            except Exception as excel_err:
                logger.error(f"Error generating/persisting cleaned Excel: {excel_err}", exc_info=True)

            # Update database session with file URL
            update_data = {
                "status": "cleaned",
                "stats": stats.model_dump(),
                "cleaned_at": datetime.utcnow().isoformat()
            }
            if cleaned_file_url:
                update_data["cleaned_file_url"] = cleaned_file_url

            await self.repository.update_processing_session(session_id, update_data)

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

            # Generate and persist Excel file to storage
            classified_file_url = None
            try:
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    classified_df.to_excel(writer, sheet_name="Reporte PA Clasificado", index=False)
                output.seek(0)
                excel_bytes = output.getvalue()

                # Upload to Supabase Storage
                classified_file_url = await self._upload_excel_to_storage(
                    excel_bytes, session_id, "classified"
                )
                if classified_file_url:
                    logger.info(f"Classified Excel persisted to storage: {classified_file_url}")
                else:
                    logger.warning(f"Failed to persist classified Excel to storage for session {session_id}")
            except Exception as excel_err:
                logger.error(f"Error generating/persisting classified Excel: {excel_err}", exc_info=True)

            # Update database session with file URL
            update_data = {
                "status": "classified",
                "stats": stats.model_dump(),
                "classified_at": datetime.utcnow().isoformat()
            }
            if classified_file_url:
                update_data["classified_file_url"] = classified_file_url

            await self.repository.update_processing_session(session_id, update_data)

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
            logger.error(f"Error classifying data: {e}", exc_info=True)
            return PAClassifiedPreview(
                session_id=session_id,
                status=PAProcessingStatus.FAILED,
                stats=PAProcessingStats(warnings=[str(e)])
            )

    async def get_cleaned_excel(self, session_id: str) -> Optional[bytes]:
        """
        Generate cleaned Excel file for download.

        First attempts to generate from in-memory session data.
        Falls back to Supabase Storage if session is not found.

        Args:
            session_id: Processing session ID.

        Returns:
            Excel file bytes or None.
        """
        logger.info(f"get_cleaned_excel called for session: {session_id}")

        # Try in-memory session first
        session = _processing_sessions.get(session_id)
        if session and session.get("cleaned_df") is not None:
            logger.info(f"Found session {session_id} in memory, generating Excel from DataFrame")
            try:
                df = session["cleaned_df"]
                output = BytesIO()

                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, sheet_name="Reporte PA Limpio", index=False)

                output.seek(0)
                excel_bytes = output.getvalue()
                logger.info(f"Generated cleaned Excel from memory: {len(excel_bytes)} bytes")
                return excel_bytes

            except Exception as e:
                logger.error(f"Error generating cleaned Excel from memory: {e}", exc_info=True)

        # Log why in-memory failed
        if not session:
            logger.warning(f"Session {session_id} not found in memory. Available sessions: {list(_processing_sessions.keys())}")
        elif session.get("cleaned_df") is None:
            logger.warning(f"Session {session_id} found but cleaned_df is None. Session status: {session.get('status')}")

        # Fallback to Supabase Storage
        logger.info(f"Attempting to retrieve cleaned Excel from storage for session {session_id}")
        try:
            session_data = await self.repository.get_processing_session(session_id)
            if not session_data:
                logger.error(f"Session {session_id} not found in database either")
                return None

            cleaned_file_url = session_data.get("cleaned_file_url")
            if not cleaned_file_url:
                logger.warning(f"Session {session_id} found in database but no cleaned_file_url stored")
                return None

            logger.info(f"Found cleaned_file_url in database: {cleaned_file_url}")
            file_bytes = await self._download_from_storage(cleaned_file_url)
            if file_bytes:
                logger.info(f"Successfully retrieved cleaned Excel from storage: {len(file_bytes)} bytes")
            return file_bytes

        except Exception as e:
            logger.error(f"Error retrieving cleaned Excel from storage: {e}", exc_info=True)
            return None

    async def get_classified_excel(self, session_id: str) -> Optional[bytes]:
        """
        Generate classified Excel file for download.

        First attempts to generate from in-memory session data.
        Falls back to Supabase Storage if session is not found.

        Args:
            session_id: Processing session ID.

        Returns:
            Excel file bytes or None.
        """
        logger.info(f"get_classified_excel called for session: {session_id}")

        # Try in-memory session first
        session = _processing_sessions.get(session_id)
        if session and session.get("classified_df") is not None:
            logger.info(f"Found session {session_id} in memory, generating Excel from DataFrame")
            try:
                df = session["classified_df"]
                output = BytesIO()

                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, sheet_name="Reporte PA Clasificado", index=False)

                output.seek(0)
                excel_bytes = output.getvalue()
                logger.info(f"Generated classified Excel from memory: {len(excel_bytes)} bytes")
                return excel_bytes

            except Exception as e:
                logger.error(f"Error generating classified Excel from memory: {e}", exc_info=True)

        # Log why in-memory failed
        if not session:
            logger.warning(f"Session {session_id} not found in memory. Available sessions: {list(_processing_sessions.keys())}")
        elif session.get("classified_df") is None:
            logger.warning(f"Session {session_id} found but classified_df is None. Session status: {session.get('status')}")

        # Fallback to Supabase Storage
        logger.info(f"Attempting to retrieve classified Excel from storage for session {session_id}")
        try:
            session_data = await self.repository.get_processing_session(session_id)
            if not session_data:
                logger.error(f"Session {session_id} not found in database either")
                return None

            classified_file_url = session_data.get("classified_file_url")
            if not classified_file_url:
                logger.warning(f"Session {session_id} found in database but no classified_file_url stored")
                return None

            logger.info(f"Found classified_file_url in database: {classified_file_url}")
            file_bytes = await self._download_from_storage(classified_file_url)
            if file_bytes:
                logger.info(f"Successfully retrieved classified Excel from storage: {len(file_bytes)} bytes")
            return file_bytes

        except Exception as e:
            logger.error(f"Error retrieving classified Excel from storage: {e}", exc_info=True)
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
            MemoryError: If file is too large to fit in memory.
        """
        file_size_mb = len(file_content) / (1024 * 1024)
        logger.info(f"Parsing file: {filename} ({file_size_mb:.2f} MB)")

        filename_lower = filename.lower()

        try:
            if filename_lower.endswith(".csv"):
                return self._parse_csv(file_content)
            else:
                # Excel file (.xlsx, .xls)
                return pd.read_excel(BytesIO(file_content))
        except MemoryError:
            logger.error(f"Memory error parsing file: {filename} ({file_size_mb:.2f} MB)")
            raise ValueError(f"El archivo es demasiado grande para procesar ({file_size_mb:.1f} MB). Intente dividirlo en partes más pequeñas.")

    def _parse_csv(self, file_content: bytes) -> pd.DataFrame:
        """
        Parse CSV file with encoding and delimiter detection.

        Tries multiple encodings, detects delimiter automatically, and
        auto-detects header row position (skipping title rows if present).
        Optimized for large files (12+ MB) with memory-efficient parsing.

        For semicolon-delimited CSVs (common in European/Latin regions),
        prioritizes Latin-1 encoding since these regions typically use
        Latin-1/ISO-8859-1 encoding.

        Args:
            file_content: CSV file content as bytes.

        Returns:
            Parsed DataFrame.

        Raises:
            ValueError: If CSV cannot be parsed with any encoding.
        """
        file_size_mb = len(file_content) / (1024 * 1024)
        logger.info(f"Parsing CSV file ({file_size_mb:.2f} MB)")

        # Detect delimiter from file content
        delimiter = self._detect_csv_delimiter(file_content)
        logger.info(f"Detected delimiter: '{delimiter}'")

        # Encoding priority order - prioritize Latin-1 for semicolon-delimited files
        # Semicolon CSVs are common in European/Latin regions that use Latin-1
        if delimiter == ";":
            encodings = ["latin-1", "iso-8859-1", "utf-8", "utf-8-sig"]
            logger.info("Semicolon delimiter detected, prioritizing Latin-1 encoding")
        else:
            encodings = ["utf-8", "utf-8-sig", "latin-1", "iso-8859-1"]

        # Detect header row (may have title rows before actual headers)
        header_row = self._detect_header_row(file_content, delimiter)
        if header_row > 0:
            logger.info(f"Detected {header_row} title rows before header, will skip them")

        last_error = None
        for encoding in encodings:
            try:
                # Pre-validate encoding by decoding first 1000 bytes
                # This catches encoding issues early before pandas processing
                sample_size = min(1000, len(file_content))
                try:
                    file_content[:sample_size].decode(encoding)
                except UnicodeDecodeError as decode_err:
                    logger.debug(f"Pre-validation failed for encoding={encoding}: {decode_err}")
                    continue

                # Use low_memory=False for consistent dtype inference
                # This is actually more memory-efficient for large files with mixed types
                df = pd.read_csv(
                    BytesIO(file_content),
                    encoding=encoding,
                    delimiter=delimiter,
                    quotechar='"',
                    thousands=None,  # Don't interpret commas as thousands separators
                    skiprows=header_row,  # Skip title rows before header
                    low_memory=False,  # Avoid dtype warnings and mixed type issues
                    on_bad_lines='warn'  # Log but don't fail on malformed lines
                )

                # Validate that we got meaningful data
                if len(df.columns) > 1 and len(df) > 0:
                    logger.info(f"CSV parsed successfully: encoding={encoding}, delimiter='{delimiter}', skiprows={header_row}, rows={len(df)}, cols={len(df.columns)}")
                    logger.debug(f"Columns found: {df.columns.tolist()}")
                    return df

            except UnicodeDecodeError as e:
                last_error = e
                logger.debug(f"UnicodeDecodeError with encoding={encoding}: {e}")
                continue
            except pd.errors.ParserError as e:
                logger.warning(f"CSV parser error with encoding={encoding}: {e}")
                last_error = e
                continue
            except MemoryError as e:
                logger.error(f"Memory error parsing CSV ({file_size_mb:.2f} MB): {e}")
                raise ValueError(f"El archivo CSV es demasiado grande ({file_size_mb:.1f} MB). Intente dividirlo en partes más pequeñas.")
            except Exception as e:
                logger.error(f"Unexpected error parsing CSV with encoding={encoding}: {e}")
                last_error = e
                continue

        error_msg = "Error de codificación en archivo CSV. Asegúrese de usar UTF-8 o Latin-1."
        if last_error:
            logger.error(f"CSV parsing failed after all attempts: {last_error}")
        raise ValueError(error_msg)

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

    def _normalize_column_name(self, col: str) -> str:
        """
        Normalize a column name for consistent matching.

        - Strips leading/trailing whitespace
        - Collapses multiple spaces to single space
        - Applies column aliases to map variations to canonical names

        Args:
            col: Column name to normalize.

        Returns:
            Normalized column name.
        """
        import re

        # Strip whitespace and collapse multiple spaces
        normalized = col.strip()
        normalized = re.sub(r'\s+', ' ', normalized)

        # Apply aliases to map variations to canonical names
        if normalized in self.COLUMN_ALIASES:
            normalized = self.COLUMN_ALIASES[normalized]

        return normalized

    def _normalize_account_number(self, value) -> str:
        """
        Normalize account number to a clean string.

        Handles:
        - Float values (removes .0 suffix from pandas float parsing)
        - Integer values
        - String values (strips whitespace)
        - NaN/None values (returns empty string)

        Args:
            value: Account number value (may be float, int, or str).

        Returns:
            Normalized account number as string.
        """
        if pd.isna(value):
            return ""

        # Convert to string first
        str_value = str(value).strip()

        # Remove trailing .0 from float representations
        # This handles pandas parsing account numbers as floats
        if str_value.endswith('.0'):
            str_value = str_value[:-2]

        return str_value

    def _validate_columns(self, columns: List[str]) -> List[str]:
        """
        Validate that required columns are present.

        Uses normalized column matching to handle whitespace variations.

        Returns list of missing columns.
        """
        required = [
            "Cuenta (línea): Número",
            "Cuenta (línea): Nombre",
            "Débito",
            "Crédito",
            "Saldo"
        ]

        # Normalize actual columns for comparison
        normalized_actual = {self._normalize_column_name(c) for c in columns}

        # Log actual vs expected for debugging
        logger.debug(f"Validating columns. Actual (normalized): {sorted(normalized_actual)}")
        logger.debug(f"Required columns: {required}")

        missing = []
        for req in required:
            # Normalize the required column name as well
            req_normalized = self._normalize_column_name(req)
            if req_normalized not in normalized_actual:
                missing.append(req)
                logger.warning(f"Missing column: '{req}' (normalized: '{req_normalized}')")

        return missing

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rename columns to internal names.

        Uses normalized column matching to handle whitespace variations
        and column aliases (e.g., "Nota" -> "Notas").
        """
        # Build mapping from actual columns to internal names
        mapping = {}

        # Log original columns for debugging
        logger.debug(f"Original columns before renaming: {df.columns.tolist()}")

        for col in df.columns:
            # Normalize the column name (handles whitespace and aliases)
            normalized = self._normalize_column_name(col)

            # Check if normalized name exists in SOURCE_COLUMN_MAPPING
            if normalized in self.SOURCE_COLUMN_MAPPING:
                mapping[col] = self.SOURCE_COLUMN_MAPPING[normalized]
                if col != normalized:
                    logger.debug(f"Column '{col}' normalized to '{normalized}' -> '{self.SOURCE_COLUMN_MAPPING[normalized]}'")

        # Log the mapping for debugging
        logger.debug(f"Column rename mapping: {mapping}")

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
