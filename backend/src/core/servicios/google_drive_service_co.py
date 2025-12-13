"""
Google Drive Service for Colombia (CO)

Servicio para interactuar con Google Drive API para la facturación de Colombia.
Permite subir y actualizar el reporte maestro de facturación CO.

Optimizado con:
- Caché de carpetas año/mes para reducir llamadas API
- Caché de archivos por carpeta para búsquedas instantáneas
- Soporte para descargas paralelas (thread-safe)
"""

import os
import io
import json
import base64
import logging
import openpyxl
import threading
import time
import httplib2
from typing import Optional, Dict, List, Tuple, Set
from datetime import datetime, date
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
from google_auth_httplib2 import AuthorizedHttp

from src.config.settings import get_settings
from src.config.supabase_config import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)

# Cache repository (lazy initialization)
_file_cache_repo_co = None


def _get_file_cache_repo():
    """Get or initialize the file cache repository for CO."""
    global _file_cache_repo_co
    if _file_cache_repo_co is None:
        try:
            from src.repositorio.drive_file_cache_repository import DriveFileCacheRepository
            supabase_wrapper = get_supabase_client()
            # Use admin_client (service_role) for full cache access (read/write)
            _file_cache_repo_co = DriveFileCacheRepository(supabase_wrapper.admin_client)
            logger.info("Drive file cache repository initialized for CO with admin_client")
        except Exception as e:
            logger.warning(f"Could not initialize file cache repository for CO: {e}")
            _file_cache_repo_co = None
    return _file_cache_repo_co


class ExcelValidationError(Exception):
    """Error cuando el Excel no pasa las validaciones antes de subir."""
    pass


class GoogleDriveServiceCO:
    """
    Servicio para interactuar con Google Drive API para Colombia.

    Proporciona funcionalidad para:
    - Autenticación con Service Account
    - Subida y actualización del reporte maestro
    - Listado de archivos en la carpeta
    - Búsqueda optimizada de PDFs con caché

    Optimizaciones implementadas:
    - Caché de carpetas año/mes (evita búsquedas repetidas)
    - Caché de archivos por carpeta (búsquedas instantáneas)
    - Thread-safe para descargas paralelas
    """

    def __init__(self):
        """Inicializa el servicio de Google Drive para Colombia."""
        settings = get_settings()
        self.credentials_json = settings.GOOGLE_DRIVE_CREDENTIALS_JSON
        self.credentials_path = settings.GOOGLE_DRIVE_CREDENTIALS_PATH
        self.folder_id = settings.GOOGLE_DRIVE_CO_FOLDER_ID
        self.master_excel_name = settings.GOOGLE_DRIVE_CO_MASTER_EXCEL_NAME
        self.historical_excel_name = settings.GOOGLE_DRIVE_CO_HISTORICAL_EXCEL_NAME

        # Parse scopes from JSON string
        self.scopes = json.loads(settings.GOOGLE_DRIVE_SCOPES)
        self.service: Optional[Resource] = None

        # Log credential source
        if self.credentials_json:
            creds_length = len(self.credentials_json)
            logger.info(f"GoogleDriveServiceCO initialized with env-based credentials ({creds_length} chars)")
        else:
            logger.info(f"GoogleDriveServiceCO initialized with file-based credentials: {self.credentials_path}")

        if self.folder_id:
            logger.info(f"GoogleDriveServiceCO folder_id: {self.folder_id[:20]}...")

        # Mapeo de meses para búsqueda en carpetas
        self.month_folders = {
            1: "01. Enero",
            2: "02. Febrero",
            3: "03. Marzo",
            4: "04. Abril",
            5: "05. Mayo",
            6: "06. Junio",
            7: "07. Julio",
            8: "08. Agosto",
            9: "09. Septiembre",
            10: "10. Octubre",
            11: "11. Noviembre",
            12: "12. Diciembre",
        }

        # ============ SISTEMA DE CACHÉ PARA OPTIMIZACIÓN ============
        # Caché de carpetas de año: {year: folder_id}
        self._year_folder_cache: Dict[int, str] = {}

        # Caché de carpetas de mes: {"year_month": folder_id}
        self._month_folder_cache: Dict[str, str] = {}

        # Caché de archivos por carpeta: {folder_id: {filename: file_id}}
        # Permite búsquedas instantáneas sin llamadas API
        self._files_cache: Dict[str, Dict[str, str]] = {}

        # Lock para thread-safety en operaciones de caché
        self._cache_lock = threading.Lock()

    def _parse_credentials_json(self, credentials_string: str) -> dict:
        """
        Parse credentials from string (base64-encoded or raw JSON).

        Args:
            credentials_string: Base64-encoded JSON or raw JSON string.

        Returns:
            dict: Parsed credentials dictionary.

        Raises:
            ValueError: If credentials cannot be parsed.
        """
        # Try to decode as base64 first
        try:
            decoded_bytes = base64.b64decode(credentials_string)
            credentials_dict = json.loads(decoded_bytes.decode('utf-8'))
            logger.debug("Credentials parsed from base64-encoded JSON")
            return credentials_dict
        except Exception:
            pass  # Not base64, try raw JSON

        # Sanitize control characters before JSON parsing
        credentials_string = credentials_string.replace('\n', '\\n')
        credentials_string = credentials_string.replace('\r', '\\r')
        credentials_string = credentials_string.replace('\t', '\\t')

        # Try to parse as raw JSON
        try:
            credentials_dict = json.loads(credentials_string)
            logger.debug(f"Credentials parsed from raw JSON string (project_id: {credentials_dict.get('project_id', 'unknown')})")
            return credentials_dict
        except json.JSONDecodeError as e:
            pos = e.pos
            start = max(0, pos - 20)
            end = min(len(credentials_string), pos + 20)
            context = credentials_string[start:end]
            logger.error(f"JSON parse error at position {pos}: {e.msg}")
            logger.error(f"Context around error: ...{repr(context)}...")
            raise ValueError(f"Failed to parse credentials JSON: {str(e)}")

    def authenticate(self) -> Resource:
        """
        Autentica con Google Drive usando Service Account.

        Returns:
            Resource: Servicio de Google Drive autenticado.

        Raises:
            FileNotFoundError: Si no se encuentra el archivo de credenciales.
            ValueError: Si las credenciales JSON son inválidas.
            Exception: Si falla la autenticación.
        """
        if self.service:
            return self.service

        try:
            creds = None

            # Priority 1: Environment variable with JSON credentials
            if self.credentials_json:
                logger.info("Authenticating with env-based credentials (GOOGLE_DRIVE_CREDENTIALS_JSON)")
                credentials_dict = self._parse_credentials_json(self.credentials_json)

                # Validate required fields
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                missing_fields = [f for f in required_fields if f not in credentials_dict]
                if missing_fields:
                    raise ValueError(f"Credentials JSON missing required fields: {missing_fields}")

                creds = Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=self.scopes
                )

            # Priority 2: File-based credentials (local development fallback)
            else:
                logger.info(f"Authenticating with file-based credentials: {self.credentials_path}")
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Archivo de credenciales no encontrado: {self.credentials_path}. "
                        "Set GOOGLE_DRIVE_CREDENTIALS_JSON env var for production."
                    )

                creds = Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=self.scopes
                )

            # Create HTTP client with timeout of 90 seconds
            # 90s: Realistic for large PDF files on slow connections
            # Google Drive can be slow, especially for files in cold storage
            http = httplib2.Http(timeout=90)
            authorized_http = AuthorizedHttp(creds, http=http)

            self.service = build("drive", "v3", http=authorized_http)
            logger.info("Autenticación con Google Drive CO exitosa (timeout=90s)")
            return self.service

        except Exception as e:
            logger.error(f"Error al autenticar con Google Drive CO: {str(e)}")
            raise

    def find_master_excel_file(self) -> Optional[Dict]:
        """
        Busca el archivo maestro de Excel en la carpeta raíz de Drive CO.

        Returns:
            Dict: Información del archivo encontrado (id, name, mimeType), o None si no existe.
        """
        try:
            service = self.authenticate()

            query = (
                f"'{self.folder_id}' in parents and "
                f"name = '{self.master_excel_name}' and "
                f"trashed = false"
            )

            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime, size)",
                pageSize=1
            ).execute()

            files = results.get("files", [])

            if files:
                file_info = files[0]
                logger.info(f"Master Excel CO encontrado: {file_info['name']} (ID: {file_info['id']})")
                return file_info
            else:
                logger.warning(f"Master Excel CO no encontrado: {self.master_excel_name}")
                return None

        except HttpError as e:
            logger.error(f"Error HTTP al buscar master Excel CO: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al buscar master Excel CO: {str(e)}")
            return None

    def download_master_excel(self) -> Optional[bytes]:
        """
        Descarga el archivo maestro de Excel desde Drive CO.

        Returns:
            bytes: Contenido del archivo Excel, o None si no existe o falla la descarga.
        """
        try:
            file_info = self.find_master_excel_file()
            if not file_info:
                logger.warning("No se puede descargar: Master Excel CO no encontrado")
                return None

            file_id = file_info["id"]
            content = self.download_file(file_id)

            if content:
                logger.info(f"Master Excel CO descargado: {len(content)} bytes")
            return content

        except Exception as e:
            logger.error(f"Error al descargar master Excel CO: {str(e)}")
            return None

    def find_historical_excel_file(self) -> Optional[Dict]:
        """
        Busca el archivo histórico de Excel en la carpeta raíz de Drive CO.
        Este es el "Archivo control facturacion mensual Finkargo Def.xlsx"
        que contiene todo el historial de facturación.

        Returns:
            Dict: Información del archivo encontrado (id, name, mimeType), o None si no existe.
        """
        try:
            service = self.authenticate()

            query = (
                f"'{self.folder_id}' in parents and "
                f"name = '{self.historical_excel_name}' and "
                f"trashed = false"
            )

            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime, size)",
                pageSize=1
            ).execute()

            files = results.get("files", [])
            if files:
                file_info = files[0]
                logger.info(f"Archivo histórico CO encontrado: {file_info['name']} (ID: {file_info['id'][:20]}...)")
                return file_info

            logger.warning(f"Archivo histórico CO no encontrado: {self.historical_excel_name}")
            return None

        except HttpError as e:
            logger.error(f"Error HTTP buscando archivo histórico CO: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error buscando archivo histórico CO: {str(e)}")
            return None

    def download_historical_excel(self) -> Optional[bytes]:
        """
        Descarga el archivo histórico de Excel desde Drive CO.
        Este es el "Archivo control facturacion mensual Finkargo Def.xlsx"
        que contiene todo el historial de facturación (solo lectura).

        Returns:
            bytes: Contenido del archivo Excel, o None si no existe o falla la descarga.
        """
        try:
            file_info = self.find_historical_excel_file()
            if not file_info:
                logger.warning("No se puede descargar: Archivo histórico CO no encontrado")
                return None

            file_id = file_info["id"]
            content = self.download_file(file_id)

            if content:
                logger.info(f"Archivo histórico CO descargado: {len(content)} bytes")
            return content

        except Exception as e:
            logger.error(f"Error al descargar archivo histórico CO: {str(e)}")
            return None

    def download_file(self, file_id: str, timeout: int = 90) -> Optional[bytes]:
        """
        Descarga un archivo de Google Drive.

        Args:
            file_id: ID del archivo en Google Drive.
            timeout: Timeout en segundos para la descarga (default: 90s).
                     90s es realista para archivos grandes en Google Drive.

        Returns:
            bytes: Contenido del archivo, o None si falla la descarga.
        """
        file_buffer = None
        try:
            service = self.authenticate()

            request = service.files().get_media(fileId=file_id)
            file_buffer = io.BytesIO()

            downloader = MediaIoBaseDownload(file_buffer, request)
            done = False

            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Descarga progreso: {int(status.progress() * 100)}%")

            file_buffer.seek(0)
            content = file_buffer.read()

            logger.info(f"Archivo descargado exitosamente (ID: {file_id}, Tamaño: {len(content)} bytes)")
            return content

        except HttpError as e:
            logger.error(f"Error HTTP al descargar archivo {file_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al descargar archivo {file_id}: {str(e)}")
            return None
        finally:
            # Asegurar que el buffer se cierre correctamente
            if file_buffer is not None:
                try:
                    file_buffer.close()
                except Exception:
                    pass

    def validate_excel_content(
        self,
        excel_content: bytes,
        min_rows_per_sheet: int = 1,
        min_columns: int = 5
    ) -> Tuple[bool, str, Dict]:
        """
        Valida que el contenido del Excel sea válido antes de subir.

        Verifica:
        - Que el archivo sea un Excel válido
        - Que contenga las hojas requeridas
        - Que cada hoja tenga al menos min_rows_per_sheet filas de datos
        - Que tenga al menos min_columns columnas

        Args:
            excel_content: Contenido del Excel en bytes.
            min_rows_per_sheet: Mínimo de filas de datos requeridas por hoja.
            min_columns: Mínimo de columnas requeridas.

        Returns:
            Tuple[bool, str, Dict]: (es_válido, mensaje, estadísticas)
        """
        stats = {
            "sheets_found": [],
            "rows_per_sheet": {},
            "columns_per_sheet": {},
            "total_rows": 0
        }

        try:
            # Intentar abrir como Excel
            wb = openpyxl.load_workbook(io.BytesIO(excel_content), data_only=True)
            stats["sheets_found"] = wb.sheetnames

            # Nombres esperados de hojas
            expected_sheets = [
                "Relacion facturas Costos Fijos",
                "Relación facturas mandato"
            ]

            # Verificar que tenga al menos una hoja esperada
            found_expected = [s for s in expected_sheets if s in wb.sheetnames]
            if not found_expected:
                return (
                    False,
                    f"El Excel no contiene las hojas esperadas. "
                    f"Hojas encontradas: {wb.sheetnames}. "
                    f"Hojas esperadas: {expected_sheets}",
                    stats
                )

            # Verificar cada hoja esperada
            empty_sheets = []
            for sheet_name in found_expected:
                ws = wb[sheet_name]
                rows = list(ws.iter_rows(values_only=True))

                # Contar columnas en la primera fila (headers)
                if rows:
                    headers = rows[0]
                    non_empty_cols = sum(1 for h in headers if h is not None)
                    stats["columns_per_sheet"][sheet_name] = non_empty_cols

                    if non_empty_cols < min_columns:
                        return (
                            False,
                            f"La hoja '{sheet_name}' tiene solo {non_empty_cols} columnas. "
                            f"Mínimo requerido: {min_columns}. "
                            "El archivo puede estar corrupto o vacío.",
                            stats
                        )

                # Contar filas de datos (excluyendo header y filas vacías)
                data_rows = 0
                if len(rows) > 1:
                    for row in rows[1:]:
                        if any(cell is not None for cell in row):
                            data_rows += 1

                stats["rows_per_sheet"][sheet_name] = data_rows
                stats["total_rows"] += data_rows

                if data_rows < min_rows_per_sheet:
                    empty_sheets.append(sheet_name)

            # Si todas las hojas están vacías, rechazar
            if len(empty_sheets) == len(found_expected):
                return (
                    False,
                    f"Todas las hojas esperadas están vacías o tienen menos de "
                    f"{min_rows_per_sheet} filas de datos. "
                    f"Hojas vacías: {empty_sheets}. "
                    "No se puede sobrescribir el archivo maestro con datos vacíos.",
                    stats
                )

            logger.info(
                f"Validación Excel exitosa: {stats['total_rows']} filas totales, "
                f"hojas: {stats['rows_per_sheet']}"
            )

            return (True, "Excel válido", stats)

        except Exception as e:
            return (
                False,
                f"Error al validar Excel: {str(e)}. "
                "El archivo puede estar corrupto o no ser un Excel válido.",
                stats
            )

    def create_backup(self, file_id: str) -> Optional[str]:
        """
        Crea o actualiza el backup del archivo actual antes de sobrescribir.

        Solo mantiene UN backup, sobrescribiendo el anterior si existe.
        El backup se nombra como "BACKUP_{nombre_original}".

        Args:
            file_id: ID del archivo a respaldar.

        Returns:
            str: ID del archivo de backup, o None si falla.
        """
        try:
            service = self.authenticate()

            # Obtener información del archivo original
            original = service.files().get(
                fileId=file_id,
                fields="name, parents"
            ).execute()

            # Nombre fijo del backup (sin timestamp para sobrescribir)
            backup_name = f"BACKUP_{original['name']}"
            parent_folder = original.get("parents", [self.folder_id])[0]

            # Buscar si ya existe un backup con ese nombre
            existing_backup_query = (
                f"'{parent_folder}' in parents and "
                f"name = '{backup_name}' and "
                f"trashed = false"
            )

            existing_results = service.files().list(
                q=existing_backup_query,
                fields="files(id, name)",
                pageSize=1
            ).execute()

            existing_backups = existing_results.get("files", [])

            if existing_backups:
                # Ya existe un backup - eliminarlo antes de crear uno nuevo
                old_backup_id = existing_backups[0]["id"]
                service.files().delete(fileId=old_backup_id).execute()
                logger.info(f"Backup anterior eliminado: {old_backup_id}")

            # Crear nuevo backup copiando el archivo actual
            backup_metadata = {
                "name": backup_name,
                "parents": [parent_folder]
            }

            backup_file = service.files().copy(
                fileId=file_id,
                body=backup_metadata,
                fields="id, name"
            ).execute()

            logger.info(f"Backup creado/actualizado: {backup_file['name']} (ID: {backup_file['id']})")
            return backup_file["id"]

        except HttpError as e:
            logger.error(f"Error HTTP al crear backup: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al crear backup: {str(e)}")
            return None

    def upload_master_excel(
        self,
        excel_content: bytes,
        validate: bool = True,
        create_backup: bool = True,
        min_rows_per_sheet: int = 0
    ) -> bool:
        """
        Sube o actualiza el archivo maestro de Excel en Drive CO.

        Si el archivo ya existe, lo actualiza. Si no existe, lo crea.
        Incluye validaciones de seguridad para evitar sobrescribir con datos vacíos.

        Args:
            excel_content: Contenido del archivo Excel en bytes.
            validate: Si True, valida el Excel antes de subir.
            create_backup: Si True, crea un backup antes de actualizar.
            min_rows_per_sheet: Mínimo de filas requeridas por hoja (0 = no validar).

        Returns:
            bool: True si la subida fue exitosa, False en caso contrario.

        Raises:
            ExcelValidationError: Si la validación falla y validate=True.
        """
        try:
            # Validar contenido del Excel antes de subir
            if validate:
                is_valid, message, stats = self.validate_excel_content(
                    excel_content,
                    min_rows_per_sheet=min_rows_per_sheet,
                    min_columns=5
                )

                if not is_valid:
                    logger.error(f"Validación fallida: {message}")
                    raise ExcelValidationError(
                        f"El Excel no pasó la validación: {message}. "
                        f"Estadísticas: {stats}"
                    )

                logger.info(f"Excel validado: {stats['total_rows']} filas en {len(stats['sheets_found'])} hojas")

            service = self.authenticate()

            # Buscar si el archivo ya existe
            existing_file = self.find_master_excel_file()

            # Crear backup si el archivo existe y se solicita
            if existing_file and create_backup:
                backup_id = self.create_backup(existing_file["id"])
                if backup_id:
                    logger.info(f"Backup creado antes de actualizar: {backup_id}")
                else:
                    logger.warning("No se pudo crear backup, continuando sin respaldo...")

            # Preparar metadata y media
            file_metadata = {
                "name": self.master_excel_name,
                "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }

            media = MediaIoBaseUpload(
                io.BytesIO(excel_content),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                resumable=True
            )

            if existing_file:
                # Actualizar archivo existente
                file_id = existing_file["id"]
                updated_file = service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
                logger.info(f"Master Excel CO actualizado: {updated_file['name']} (ID: {updated_file['id']})")
            else:
                # Crear nuevo archivo
                file_metadata["parents"] = [self.folder_id]
                created_file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name"
                ).execute()
                logger.info(f"Master Excel CO creado: {created_file['name']} (ID: {created_file['id']})")

            return True

        except ExcelValidationError:
            # Re-raise validation errors
            raise
        except HttpError as e:
            logger.error(f"Error HTTP al subir master Excel CO: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error al subir master Excel CO: {str(e)}")
            return False

    def upload_report(self, excel_content: bytes, filename: str) -> Optional[str]:
        """
        Sube un reporte específico a Drive CO.

        Args:
            excel_content: Contenido del archivo Excel en bytes.
            filename: Nombre del archivo a crear.

        Returns:
            str: ID del archivo creado, o None si falla.
        """
        try:
            service = self.authenticate()

            file_metadata = {
                "name": filename,
                "parents": [self.folder_id],
                "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }

            media = MediaIoBaseUpload(
                io.BytesIO(excel_content),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                resumable=True
            )

            created_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, name, webViewLink"
            ).execute()

            logger.info(f"Reporte CO subido: {created_file['name']} (ID: {created_file['id']})")
            return created_file['id']

        except HttpError as e:
            logger.error(f"Error HTTP al subir reporte CO: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al subir reporte CO: {str(e)}")
            return None

    def list_files_in_folder(self, max_results: int = 50) -> List[Dict]:
        """
        Lista los archivos en la carpeta de Colombia.

        Args:
            max_results: Número máximo de archivos a retornar.

        Returns:
            List[Dict]: Lista de archivos con id, name, mimeType, modifiedTime.
        """
        try:
            service = self.authenticate()

            query = (
                f"'{self.folder_id}' in parents and "
                f"trashed = false"
            )

            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime, size)",
                pageSize=max_results,
                orderBy="modifiedTime desc"
            ).execute()

            files = results.get("files", [])
            logger.info(f"Encontrados {len(files)} archivos en carpeta CO")
            return files

        except HttpError as e:
            logger.error(f"Error HTTP al listar archivos CO: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error al listar archivos CO: {str(e)}")
            return []

    def get_file_web_link(self, file_id: str) -> Optional[str]:
        """
        Obtiene el link web de un archivo en Drive.

        Args:
            file_id: ID del archivo.

        Returns:
            str: URL para ver el archivo en Drive, o None si falla.
        """
        try:
            service = self.authenticate()

            file_info = service.files().get(
                fileId=file_id,
                fields="webViewLink"
            ).execute()

            return file_info.get("webViewLink")

        except HttpError as e:
            logger.error(f"Error HTTP al obtener link del archivo {file_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al obtener link del archivo {file_id}: {str(e)}")
            return None


    def get_year_folder_id(self, year: int) -> Optional[str]:
        """
        Obtiene el ID de la carpeta del año específico.
        Usa caché para evitar llamadas API repetidas.

        Args:
            year: Año de la carpeta (ej: 2025).

        Returns:
            str: ID de la carpeta del año, o None si no se encuentra.
        """
        # Verificar caché primero (thread-safe)
        with self._cache_lock:
            if year in self._year_folder_cache:
                logger.debug(f"Carpeta Año {year} encontrada en caché")
                return self._year_folder_cache[year]

        try:
            service = self.authenticate()

            # Buscar carpeta del año (ej: "Año 2025")
            year_query = (
                f"'{self.folder_id}' in parents and "
                f"name = 'Año {year}' and "
                f"mimeType = 'application/vnd.google-apps.folder' and "
                f"trashed = false"
            )

            year_results = service.files().list(
                q=year_query,
                fields="files(id, name)",
                pageSize=1
            ).execute()

            year_files = year_results.get("files", [])
            if not year_files:
                logger.warning(f"Carpeta del año {year} no encontrada")
                return None

            year_folder_id = year_files[0]["id"]

            # Guardar en caché (thread-safe)
            with self._cache_lock:
                self._year_folder_cache[year] = year_folder_id

            logger.debug(f"Carpeta Año {year} encontrada: {year_folder_id}")
            return year_folder_id

        except HttpError as e:
            logger.error(f"Error HTTP al buscar carpeta del año: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al buscar carpeta del año: {str(e)}")
            return None

    def get_month_folder_id(self, month: int, year: int) -> Optional[str]:
        """
        Obtiene el ID de la carpeta del mes específico.
        Usa caché para evitar llamadas API repetidas.

        Args:
            month: Número del mes (1-12).
            year: Año de la carpeta.

        Returns:
            str: ID de la carpeta del mes, o None si no se encuentra.
        """
        # Clave de caché para el mes
        cache_key = f"{year}_{month}"

        # Verificar caché primero (thread-safe)
        with self._cache_lock:
            if cache_key in self._month_folder_cache:
                logger.debug(f"Carpeta mes {month}/{year} encontrada en caché")
                return self._month_folder_cache[cache_key]

        try:
            # Primero obtener carpeta del año (ya usa caché)
            year_folder_id = self.get_year_folder_id(year)
            if not year_folder_id:
                return None

            service = self.authenticate()

            # Buscar carpeta del mes dentro del año
            month_name = self.month_folders.get(month)
            if not month_name:
                logger.error(f"Mes inválido: {month}")
                return None

            month_query = (
                f"'{year_folder_id}' in parents and "
                f"name = '{month_name}' and "
                f"mimeType = 'application/vnd.google-apps.folder' and "
                f"trashed = false"
            )

            month_results = service.files().list(
                q=month_query,
                fields="files(id, name)",
                pageSize=1
            ).execute()

            month_files = month_results.get("files", [])
            if not month_files:
                logger.warning(f"Carpeta del mes {month_name} no encontrada en año {year}")
                return None

            month_folder_id = month_files[0]["id"]

            # Guardar en caché (thread-safe)
            with self._cache_lock:
                self._month_folder_cache[cache_key] = month_folder_id

            logger.debug(f"Carpeta {month_name} {year} encontrada: {month_folder_id}")
            return month_folder_id

        except HttpError as e:
            logger.error(f"Error HTTP al buscar carpeta del mes: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al buscar carpeta del mes: {str(e)}")
            return None

    def _cache_folder_files(self, folder_id: str) -> Dict[str, str]:
        """
        Cachea todos los archivos PDF de una carpeta y sus subcarpetas.
        Esto permite búsquedas instantáneas sin llamadas API adicionales.

        Args:
            folder_id: ID de la carpeta a cachear.

        Returns:
            Dict[str, str]: Diccionario {filename: file_id}
        """
        # Verificar si ya está cacheado (thread-safe)
        with self._cache_lock:
            if folder_id in self._files_cache:
                return self._files_cache[folder_id]

        try:
            service = self.authenticate()
            files_dict: Dict[str, str] = {}

            # Buscar todos los PDFs en esta carpeta
            pdf_query = (
                f"'{folder_id}' in parents and "
                f"mimeType = 'application/pdf' and "
                f"trashed = false"
            )

            page_token = None
            while True:
                results = service.files().list(
                    q=pdf_query,
                    fields="nextPageToken, files(id, name)",
                    pageSize=1000,
                    pageToken=page_token
                ).execute()

                for file in results.get("files", []):
                    files_dict[file["name"]] = file["id"]

                page_token = results.get("nextPageToken")
                if not page_token:
                    break

            # Buscar subcarpetas y cachear sus archivos también
            subfolder_query = (
                f"'{folder_id}' in parents and "
                f"mimeType = 'application/vnd.google-apps.folder' and "
                f"trashed = false"
            )

            subfolder_results = service.files().list(
                q=subfolder_query,
                fields="files(id, name)",
                pageSize=100
            ).execute()

            for subfolder in subfolder_results.get("files", []):
                # Cachear archivos de subcarpeta recursivamente
                subfolder_files = self._cache_folder_files(subfolder["id"])
                files_dict.update(subfolder_files)

            # Guardar en caché (thread-safe)
            with self._cache_lock:
                self._files_cache[folder_id] = files_dict

            logger.info(f"Cacheados {len(files_dict)} archivos de carpeta {folder_id[:15]}...")
            return files_dict

        except HttpError as e:
            logger.error(f"Error HTTP al cachear archivos: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error al cachear archivos: {str(e)}")
            return {}

    def precache_month_folders(self, dates: List[date]) -> None:
        """
        Pre-cachea las carpetas de meses y sus archivos antes de las búsquedas.
        Esto es crítico para optimizar descargas paralelas.

        Args:
            dates: Lista de fechas para determinar qué meses cachear.
        """
        # Identificar meses únicos
        months_needed: Set[Tuple[int, int]] = set()
        for fecha in dates:
            if fecha:
                months_needed.add((fecha.year, fecha.month))

        logger.info(f"Pre-cacheando {len(months_needed)} carpetas de mes...")

        for year, month in months_needed:
            try:
                month_folder_id = self.get_month_folder_id(month, year)
                if month_folder_id:
                    # Cachear todos los archivos de esta carpeta del mes
                    self._cache_folder_files(month_folder_id)
            except Exception as e:
                logger.warning(f"Error al pre-cachear carpeta {month}/{year}: {str(e)}")

        logger.info("Pre-cache de carpetas completado")

    def _search_file_in_cache(self, folder_id: str, filename: str) -> Optional[str]:
        """
        Busca un archivo en el caché de una carpeta.

        Args:
            folder_id: ID de la carpeta.
            filename: Nombre del archivo a buscar.

        Returns:
            str: ID del archivo si se encuentra, None si no.
        """
        with self._cache_lock:
            if folder_id in self._files_cache:
                return self._files_cache[folder_id].get(filename)
        return None

    def search_pdf_by_invoice_number(
        self,
        numero_factura: str,
        fecha: date,
        search_all_year: bool = False
    ) -> Optional[Dict]:
        """
        Busca un archivo PDF por número de factura en Google Drive.
        Optimizado: Primero busca en caché, luego hace búsqueda API si es necesario.

        Args:
            numero_factura: Número de factura (ej: FE10555, ITGC846).
            fecha: Fecha de la factura para determinar mes/año.
            search_all_year: Si True, busca en todo el año si no encuentra en el mes.

        Returns:
            Dict con información del archivo encontrado, o None si no existe.
            Formato: {'id': str, 'name': str, 'mimeType': str}
        """
        try:
            filename = f"{numero_factura}.pdf"

            # Primero obtener carpeta del mes
            month_folder_id = self.get_month_folder_id(fecha.month, fecha.year)

            if month_folder_id:
                # ===== OPTIMIZACIÓN: Buscar primero en caché =====
                cached_file_id = self._search_file_in_cache(month_folder_id, filename)
                if cached_file_id:
                    logger.debug(f"PDF encontrado en caché: {filename}")
                    return {
                        "id": cached_file_id,
                        "name": filename,
                        "mimeType": "application/pdf"
                    }

                # Si no está en caché, hacer búsqueda directa (sin recursión de subcarpetas)
                service = self.authenticate()
                file_query = (
                    f"'{month_folder_id}' in parents and "
                    f"name = '{filename}' and "
                    f"trashed = false"
                )

                file_results = service.files().list(
                    q=file_query,
                    fields="files(id, name, mimeType)",
                    pageSize=1
                ).execute()

                files = file_results.get("files", [])
                if files:
                    logger.info(f"PDF encontrado en mes {fecha.month}/{fecha.year}: {filename}")
                    return files[0]

            # Si no encuentra y search_all_year=True, buscar en carpeta del año
            if search_all_year:
                year_folder_id = self.get_year_folder_id(fecha.year)
                if year_folder_id:
                    # Buscar en caché del año
                    cached_file_id = self._search_file_in_cache(year_folder_id, filename)
                    if cached_file_id:
                        logger.debug(f"PDF encontrado en caché (año): {filename}")
                        return {
                            "id": cached_file_id,
                            "name": filename,
                            "mimeType": "application/pdf"
                        }

                    # Búsqueda recursiva como fallback
                    service = self.authenticate()
                    result = self._search_file_recursive(service, year_folder_id, filename)
                    if result:
                        logger.info(f"PDF encontrado en año {fecha.year}: {filename}")
                        return result

            logger.warning(f"PDF no encontrado: {filename}")
            return None

        except HttpError as e:
            logger.error(f"Error HTTP al buscar PDF {numero_factura}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al buscar PDF {numero_factura}: {str(e)}")
            return None

    def _search_file_recursive(
        self,
        service: Resource,
        folder_id: str,
        filename: str,
        max_depth: int = 5
    ) -> Optional[Dict]:
        """
        Búsqueda recursiva de un archivo en una carpeta y sus subcarpetas.

        Args:
            service: Servicio de Google Drive autenticado.
            folder_id: ID de la carpeta donde buscar.
            filename: Nombre del archivo a buscar.
            max_depth: Profundidad máxima de búsqueda.

        Returns:
            Dict con información del archivo o None.
        """
        if max_depth <= 0:
            return None

        try:
            # Buscar el archivo directamente en esta carpeta
            file_query = (
                f"'{folder_id}' in parents and "
                f"name = '{filename}' and "
                f"trashed = false"
            )

            file_results = service.files().list(
                q=file_query,
                fields="files(id, name, mimeType, size)",
                pageSize=1
            ).execute()

            files = file_results.get("files", [])
            if files:
                return files[0]

            # Si no está aquí, buscar en subcarpetas
            subfolder_query = (
                f"'{folder_id}' in parents and "
                f"mimeType = 'application/vnd.google-apps.folder' and "
                f"trashed = false"
            )

            subfolder_results = service.files().list(
                q=subfolder_query,
                fields="files(id, name)",
                pageSize=50
            ).execute()

            subfolders = subfolder_results.get("files", [])

            for subfolder in subfolders:
                result = self._search_file_recursive(
                    service,
                    subfolder["id"],
                    filename,
                    max_depth - 1
                )
                if result:
                    return result

            return None

        except HttpError as e:
            logger.error(f"Error HTTP en búsqueda recursiva: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error en búsqueda recursiva: {str(e)}")
            return None

    def get_invoice_pdf(
        self,
        numero_factura: str,
        fecha: date
    ) -> Optional[bytes]:
        """
        Obtiene el contenido de un PDF de factura.

        Args:
            numero_factura: Número de factura (ej: FE10555).
            fecha: Fecha de la factura.

        Returns:
            bytes: Contenido del PDF, o None si no se encuentra.
        """
        pdf_file = self.search_pdf_by_invoice_number(
            numero_factura,
            fecha,
            search_all_year=True  # Buscar en todo el año si no está en el mes
        )

        if pdf_file:
            return self.download_file(pdf_file["id"])

        return None

    def batch_get_invoice_pdfs(
        self,
        invoices: List[Dict]
    ) -> List[Dict]:
        """
        Obtiene PDFs de múltiples facturas en batch.

        Args:
            invoices: Lista de dicts con 'numero_factura' y 'fecha'.

        Returns:
            List[Dict]: Lista con información de archivos descargados.
            Formato: [
                {
                    'numero_factura': str,
                    'pdf_content': Optional[bytes],
                    'pdf_found': bool
                }
            ]
        """
        results = []
        total = len(invoices)

        for idx, invoice in enumerate(invoices, 1):
            numero_factura = invoice.get("numero_factura")
            fecha = invoice.get("fecha")

            if not numero_factura or not fecha:
                logger.warning(f"Factura con datos incompletos: {invoice}")
                results.append({
                    "numero_factura": numero_factura or "UNKNOWN",
                    "pdf_content": None,
                    "pdf_found": False
                })
                continue

            # Convertir fecha si es string
            if isinstance(fecha, str):
                try:
                    fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
                except ValueError:
                    try:
                        fecha = datetime.strptime(fecha, "%d/%m/%Y").date()
                    except ValueError:
                        logger.warning(f"No se pudo parsear fecha: {fecha}")
                        results.append({
                            "numero_factura": numero_factura,
                            "pdf_content": None,
                            "pdf_found": False
                        })
                        continue

            logger.info(f"Buscando PDF {idx}/{total}: {numero_factura}")
            pdf_content = self.get_invoice_pdf(numero_factura, fecha)

            results.append({
                "numero_factura": numero_factura,
                "pdf_content": pdf_content,
                "pdf_found": pdf_content is not None
            })

        # Estadísticas
        found_count = sum(1 for r in results if r["pdf_found"])
        logger.info(f"Búsqueda batch completada: {found_count}/{total} PDFs encontrados")

        return results

    # ============================================================================
    # OPTIMIZACIÓN: Cache Persistente en Supabase + Pre-cache Global
    # ============================================================================

    def search_pdf_global_with_cache(
        self,
        numero_factura: str,
        max_retries: int = 2
    ) -> Optional[Dict]:
        """
        Busca un PDF usando CACHE PRIMERO, luego búsqueda en Drive.

        Estrategia:
        1. Primero busca en el cache de base de datos (instantáneo)
        2. Si no está en cache, busca en Drive con múltiples variantes de nombre:
           - {numero_factura}.pdf (ej: FE10555.pdf)
           - dian_{numero_factura}.pdf (ej: dian_FE10555.pdf)
        3. Si lo encuentra, guarda el ID en cache para futuras consultas

        Args:
            numero_factura: Número de factura (ej: FE10555).
            max_retries: Número máximo de reintentos en caso de timeout.

        Returns:
            Dict con información del archivo encontrado, o None si no existe.
        """
        import time
        filename = f"{numero_factura}.pdf"

        # 1. PRIMERO: Buscar en cache de base de datos (INSTANTÁNEO)
        cache_repo = _get_file_cache_repo()
        if cache_repo:
            try:
                cached_id = cache_repo.get_file_id(numero_factura, "pdf", "CO")
                if cached_id:
                    logger.debug(f"Cache HIT CO: {filename} -> {cached_id[:15]}...")
                    return {"id": cached_id, "name": filename}
            except Exception as e:
                logger.warning(f"Error checking cache for {filename}: {e}")

        # 2. FALLBACK: Buscar en Google Drive API con múltiples variantes
        logger.info(f"[CO] Cache MISS: {numero_factura}, buscando en Drive API...")

        # Variantes de nombre a buscar (algunos PDFs tienen prefijo dian_)
        filename_variants = [
            f"{numero_factura}.pdf",           # FE10555.pdf
            f"dian_{numero_factura}.pdf",      # dian_FE10555.pdf
        ]

        for attempt in range(max_retries + 1):
            try:
                service = self.authenticate()

                # Buscar cada variante de nombre
                for variant_filename in filename_variants:
                    logger.info(f"[CO] Buscando variante: {variant_filename}")
                    query = (
                        f"name = '{variant_filename}' and "
                        f"trashed = false"
                    )

                    results = service.files().list(
                        q=query,
                        fields="files(id, name)",
                        pageSize=1
                    ).execute()

                    files = results.get("files", [])
                    if files:
                        file_info = files[0]
                        file_id = file_info["id"]
                        logger.info(f"[CO] ENCONTRADO: {variant_filename} -> {file_id[:20]}...")

                        # 3. GUARDAR EN CACHE para futuras consultas
                        if cache_repo:
                            try:
                                cache_repo.cache_file_id(
                                    uuid=numero_factura,
                                    file_type="pdf",
                                    drive_file_id=file_id,
                                    drive_file_name=file_info["name"],
                                    country="CO"
                                )
                                logger.info(f"[CO] Cache STORED: {numero_factura} -> {variant_filename}")
                            except Exception as e:
                                logger.warning(f"[CO] Error caching {variant_filename}: {e}")

                        return {"id": file_id, "name": file_info["name"]}
                    else:
                        logger.info(f"[CO] No encontrado: {variant_filename}")

                # Ninguna variante encontrada
                logger.warning(f"[CO] {numero_factura} NO EXISTE en Drive (probadas {len(filename_variants)} variantes)")
                return None

            except HttpError as e:
                logger.error(f"Error HTTP en búsqueda global de {filename}: {str(e)}")
                return None
            except Exception as e:
                # Timeout u otro error - reintentar
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 1
                    logger.warning(f"Timeout buscando {filename}, reintento {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Error en búsqueda global de {filename}: {str(e)}")
                    return None

        return None

    def get_invoice_pdf_optimized(
        self,
        numero_factura: str,
        fecha: date
    ) -> Optional[bytes]:
        """
        Obtiene el contenido de un PDF usando cache de Supabase.

        OPTIMIZADO: Usa search_pdf_global_with_cache que consulta el cache
        de Supabase primero, evitando búsquedas costosas en Google Drive.

        Si el archivo se encuentra en cache pero la descarga falla (timeout),
        reintenta hasta 3 veces antes de reportar como no encontrado.
        NO usa fallback al método lento por carpetas - si está en cache,
        el file_id es correcto y solo necesitamos reintentar la descarga.

        Args:
            numero_factura: Número de factura (ej: FE10555).
            fecha: Fecha de la factura (no usado, mantenido por compatibilidad).

        Returns:
            bytes: Contenido del PDF, o None si no se encuentra.
        """
        # Usar búsqueda global con cache (soporta variantes como dian_)
        pdf_file = self.search_pdf_global_with_cache(numero_factura)

        if pdf_file:
            file_id = pdf_file["id"]
            file_name = pdf_file.get("name", numero_factura)

            # Intentar descarga con reintentos (el timeout es el problema común)
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    content = self.download_file(file_id)
                    if content:
                        if attempt > 1:
                            logger.info(f"[CO] Descarga exitosa de {file_name} en intento {attempt}")
                        return content
                    else:
                        logger.warning(f"[CO] Intento {attempt}/{max_retries} falló para {file_name}")
                except Exception as e:
                    logger.warning(f"[CO] Intento {attempt}/{max_retries} error para {file_name}: {e}")

                # Esperar antes de reintentar (backoff exponencial)
                if attempt < max_retries:
                    wait_time = attempt * 2  # 2s, 4s
                    logger.info(f"[CO] Esperando {wait_time}s antes de reintentar...")
                    time.sleep(wait_time)

            # Si llegamos aquí, todos los intentos fallaron
            logger.error(f"[CO] Todos los intentos de descarga fallaron para {file_name} (ID: {file_id})")
            return None

        # Solo buscar por carpetas si NO está en cache (archivo nuevo o nunca indexado)
        # Esta búsqueda también soporta el prefijo dian_
        logger.info(f"[CO] {numero_factura} no está en cache, buscando por carpetas...")
        return self._search_pdf_by_folder_with_variants(numero_factura, fecha)

    def _search_pdf_by_folder_with_variants(
        self,
        numero_factura: str,
        fecha: date
    ) -> Optional[bytes]:
        """
        Busca un PDF por carpeta de mes/año con soporte para variantes de nombre.

        Soporta nombres como: FE10555.pdf, dian_FE10555.pdf

        Args:
            numero_factura: Número de factura.
            fecha: Fecha para determinar carpeta.

        Returns:
            bytes: Contenido del PDF o None si no se encuentra.
        """
        # Variantes de nombre a buscar
        filename_variants = [
            f"{numero_factura}.pdf",
            f"dian_{numero_factura}.pdf",
        ]

        for filename in filename_variants:
            try:
                # Usar el método existente de búsqueda por carpeta
                pdf_content = self._search_pdf_in_folder(filename, fecha)
                if pdf_content:
                    logger.info(f"[CO] Encontrado {filename} por búsqueda en carpeta")
                    return pdf_content
            except Exception as e:
                logger.debug(f"[CO] Error buscando {filename}: {e}")
                continue

        return None

    def _search_pdf_in_folder(
        self,
        filename: str,
        fecha: date
    ) -> Optional[bytes]:
        """
        Busca un PDF específico en la carpeta del mes/año correspondiente.

        Args:
            filename: Nombre completo del archivo (ej: FE10555.pdf).
            fecha: Fecha para determinar la carpeta.

        Returns:
            bytes: Contenido del PDF o None.
        """
        try:
            service = self.authenticate()

            # Obtener carpeta del mes/año usando método existente
            month_folder_id = self.get_month_folder_id(fecha.month, fecha.year)
            if not month_folder_id:
                return None

            # Buscar el archivo en la carpeta
            query = f"name='{filename}' and '{month_folder_id}' in parents and trashed=false"
            results = service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=1
            ).execute()

            files = results.get('files', [])
            if files:
                return self.download_file(files[0]['id'])

            return None

        except Exception as e:
            logger.debug(f"[CO] Error en _search_pdf_in_folder: {e}")
            return None

    def _list_all_drive_files(self) -> List[Dict]:
        """
        Lista TODOS los archivos PDF del Google Drive CO (recursivamente).

        Usa paginación para obtener todos los archivos sin límite.

        Returns:
            Lista de dicts con {id, name, mimeType} de cada archivo.
        """
        service = self.authenticate()
        all_files = []
        page_token = None
        page_count = 0

        # Buscar solo PDFs para optimizar
        query = "mimeType='application/pdf' and trashed=false"

        while True:
            try:
                page_count += 1
                results = service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType)",
                    pageSize=1000,  # Máximo permitido por API
                    pageToken=page_token
                ).execute()

                files = results.get('files', [])
                all_files.extend(files)

                if page_count % 5 == 0:
                    logger.info(f"[CO] Listed {len(all_files)} files so far (page {page_count})...")

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            except HttpError as e:
                logger.error(f"[CO] Error listing files (page {page_count}): {e}")
                break
            except Exception as e:
                logger.error(f"[CO] Unexpected error listing files: {e}")
                break

        logger.info(f"[CO] Finished listing: {len(all_files)} total files in {page_count} pages")
        return all_files

    def get_bulk_file_ids_from_cache(
        self,
        numeros_factura: List[str]
    ) -> Dict[str, str]:
        """
        Obtiene file_ids de Supabase en una sola consulta bulk.

        OPTIMIZACIÓN CRÍTICA: En lugar de hacer N consultas individuales,
        hace 1 consulta bulk que retorna todos los file_ids de una vez.
        Esto reduce drásticamente la latencia total.

        Args:
            numeros_factura: Lista de números de factura a buscar.

        Returns:
            Dict mapping numero_factura -> drive_file_id.
            Solo incluye facturas encontradas en cache.
        """
        if not numeros_factura:
            return {}

        cache_repo = _get_file_cache_repo()
        if not cache_repo:
            logger.warning("[CO] Cache repository not available for bulk lookup")
            return {}

        try:
            # Usar el método bulk del repositorio
            bulk_result = cache_repo.get_bulk_file_ids(numeros_factura, "CO")

            # Transformar de {uuid: {file_type: file_id}} a {uuid: file_id}
            result = {}
            for numero_factura, file_types in bulk_result.items():
                if "pdf" in file_types:
                    result[numero_factura] = file_types["pdf"]

            logger.info(
                f"[CO] Bulk cache lookup: {len(numeros_factura)} solicitados, "
                f"{len(result)} encontrados en cache ({len(result)*100//max(len(numeros_factura),1)}%)"
            )
            return result

        except Exception as e:
            logger.error(f"[CO] Error in bulk cache lookup: {e}")
            return {}

    def download_file_with_retry(
        self,
        file_id: str,
        file_name: str,
        max_retries: int = 2,
        max_total_time: int = 210
    ) -> Optional[bytes]:
        """
        Descarga un archivo de Google Drive con backoff exponencial.

        Implementa reintentos con tiempos de espera para manejar
        timeouts transitorios sin saturar la conexión.

        CONFIGURACIÓN:
        - Timeout por intento: 90s (configurado en httplib2)
        - Máximo 2 reintentos (total 3 intentos)
        - Tiempo total máximo: 210s (3.5 minutos)
        - Backoff: 3s, 6s entre intentos

        Args:
            file_id: ID del archivo en Google Drive.
            file_name: Nombre del archivo (para logging).
            max_retries: Número máximo de reintentos (default 2).
            max_total_time: Tiempo máximo total en segundos (default 210s).

        Returns:
            bytes: Contenido del archivo o None si falla.
        """
        start_time = time.time()

        for attempt in range(1, max_retries + 2):  # +2 porque max_retries=2 significa 3 intentos totales
            # Verificar si excedimos el tiempo total
            elapsed = time.time() - start_time
            if elapsed >= max_total_time:
                logger.warning(
                    f"[CO] Tiempo límite excedido para {file_name}: "
                    f"{elapsed:.1f}s >= {max_total_time}s (intento {attempt})"
                )
                break

            try:
                content = self.download_file(file_id)
                if content:
                    if attempt > 1:
                        logger.info(f"[CO] Descarga exitosa de {file_name} en intento {attempt} ({elapsed:.1f}s)")
                    return content
                else:
                    logger.warning(f"[CO] Intento {attempt}: descarga vacía para {file_name}")

            except Exception as e:
                logger.warning(f"[CO] Intento {attempt} error para {file_name}: {e}")

            # Backoff exponencial: 3s, 6s
            if attempt <= max_retries:
                # Verificar que tenemos tiempo para otro intento (necesitamos ~60s)
                remaining_time = max_total_time - (time.time() - start_time)
                if remaining_time < 30:
                    logger.warning(f"[CO] Sin tiempo suficiente para reintentar {file_name} ({remaining_time:.0f}s restantes)")
                    break

                wait_time = 3 * attempt  # 3s, 6s
                logger.info(f"[CO] Esperando {wait_time}s antes de reintentar {file_name}...")
                time.sleep(wait_time)

        total_elapsed = time.time() - start_time
        logger.error(f"[CO] Descarga fallida para {file_name} después de {total_elapsed:.1f}s (ID: {file_id})")
        return None


    def _list_all_pdf_files(self) -> List[Dict]:
        """
        Lista TODOS los archivos PDF del Google Drive CO con paginación.
        Busca en todas las carpetas de años y meses recursivamente.

        Returns:
            Lista de diccionarios con {id, name, mimeType}
        """
        try:
            service = self.authenticate()
            all_files = []

            # Query para PDFs solamente (CO no tiene XMLs)
            query = (
                "mimeType='application/pdf' and "
                "trashed=false"
            )

            page_token = None
            while True:
                results = service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType)",
                    pageSize=1000,
                    pageToken=page_token,
                    # Buscar en todo el drive compartido
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()

                files = results.get('files', [])
                all_files.extend(files)

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

                logger.info(f"Listed {len(all_files)} PDF files so far...")

            logger.info(f"Total PDF files listed from Drive CO: {len(all_files)}")
            return all_files

        except HttpError as e:
            logger.error(f"Error HTTP al listar archivos PDF CO: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error al listar archivos PDF CO: {str(e)}")
            return []

    def precache_drive_file_ids(
        self,
        invoice_numbers: List[str],
        country: str = "CO"
    ) -> Dict[str, int]:
        """
        Pre-cachea los IDs de archivos de Drive para facturas de Colombia.

        OPTIMIZADO: Lista todos los PDFs del Drive una sola vez
        y hace el match en memoria (segundos en lugar de horas).

        A diferencia de MX que usa UUIDs, CO usa números de factura
        como identificadores (FE10555, ITGC846, etc.).

        Args:
            invoice_numbers: Lista de números de factura a cachear.
            country: País ('CO').

        Returns:
            Dict con estadísticas: {total, cached, already_cached, not_found}
        """
        from src.repositorio.drive_file_cache_repository import DriveFileCacheRepository
        from src.config.supabase_config import get_supabase_client

        stats = {
            'total': len(invoice_numbers),
            'cached': 0,
            'already_cached': 0,
            'not_found': 0,
            'errors': 0
        }

        if not invoice_numbers:
            logger.warning("No invoice numbers provided for precache")
            return stats

        try:
            # Obtener repositorio de cache
            supabase = get_supabase_client()
            cache_repo = DriveFileCacheRepository(supabase.admin_client)

            # 1. Verificar cuáles ya están en cache
            logger.info(f"Checking existing cache for {len(invoice_numbers)} invoice numbers...")
            already_cached = cache_repo.get_bulk_file_ids(invoice_numbers, country)
            stats['already_cached'] = len(already_cached)

            # Filtrar los que ya están en cache
            invoice_numbers_to_process = [
                inv for inv in invoice_numbers
                if inv not in already_cached
            ]

            if not invoice_numbers_to_process:
                logger.info(f"All {len(invoice_numbers)} invoice numbers already in cache")
                return stats

            logger.info(f"Need to cache {len(invoice_numbers_to_process)} invoice numbers")

            # 2. OPTIMIZACIÓN: Listar TODOS los PDFs del Drive una sola vez
            logger.info("Listing ALL PDF files from Google Drive CO (this may take a moment)...")
            all_drive_files = self._list_all_pdf_files()
            logger.info(f"Found {len(all_drive_files)} PDF files in Drive CO")

            # 3. Crear índice por nombre de archivo para búsqueda O(1)
            # El nombre del archivo es "FE10555.pdf", la clave será "FE10555"
            file_index: Dict[str, Dict[str, str]] = {}
            for file_info in all_drive_files:
                filename = file_info.get('name', '')
                if filename and filename.lower().endswith('.pdf'):
                    # Extraer el número de factura del nombre del archivo
                    invoice_key = filename[:-4]  # Quitar ".pdf"
                    file_index[invoice_key.upper()] = {
                        'id': file_info['id'],
                        'name': filename
                    }

            logger.info(f"Created index with {len(file_index)} unique invoice PDFs")

            # 4. Match números de factura con archivos en memoria (muy rápido)
            all_files_to_cache = []
            not_found_invoices = []

            for invoice_number in invoice_numbers_to_process:
                # Normalizar el número de factura
                invoice_upper = invoice_number.upper().strip()

                # Buscar en el índice
                if invoice_upper in file_index:
                    file_data = file_index[invoice_upper]
                    all_files_to_cache.append({
                        'uuid': invoice_number,  # Usamos 'uuid' para compatibilidad con la tabla
                        'file_type': 'pdf',
                        'drive_file_id': file_data['id'],
                        'drive_file_name': file_data['name']
                    })
                else:
                    not_found_invoices.append(invoice_number)

            stats['not_found'] = len(not_found_invoices)

            if not_found_invoices and len(not_found_invoices) <= 20:
                logger.warning(f"PDFs not found for: {not_found_invoices}")
            elif not_found_invoices:
                logger.warning(f"PDFs not found for {len(not_found_invoices)} invoices (showing first 20): {not_found_invoices[:20]}")

            # 5. Guardar en cache en batch
            if all_files_to_cache:
                logger.info(f"Caching {len(all_files_to_cache)} file IDs to Supabase...")
                cached_count = cache_repo.cache_bulk_file_ids(all_files_to_cache, country)
                stats['cached'] = cached_count
                logger.info(f"Successfully cached {cached_count} file IDs")

            logger.info(f"Precache CO completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error in precache_drive_file_ids CO: {str(e)}", exc_info=True)
            stats['errors'] = 1
            return stats


# Singleton instance
_drive_service_co_instance: Optional[GoogleDriveServiceCO] = None


def get_drive_service_co() -> GoogleDriveServiceCO:
    """
    Obtiene la instancia singleton del servicio de Google Drive para Colombia.

    Returns:
        GoogleDriveServiceCO: Instancia del servicio.
    """
    global _drive_service_co_instance
    if _drive_service_co_instance is None:
        _drive_service_co_instance = GoogleDriveServiceCO()
    return _drive_service_co_instance
