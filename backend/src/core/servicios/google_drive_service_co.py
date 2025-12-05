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
from typing import Optional, Dict, List, Tuple, Set
from datetime import datetime, date
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from googleapiclient.errors import HttpError

from src.config.settings import get_settings


class ExcelValidationError(Exception):
    """Error cuando el Excel no pasa las validaciones antes de subir."""
    pass

# Configurar logging
logger = logging.getLogger(__name__)


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

            self.service = build("drive", "v3", credentials=creds)
            logger.info("Autenticación con Google Drive CO exitosa")
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

    def download_file(self, file_id: str) -> Optional[bytes]:
        """
        Descarga un archivo de Google Drive.

        Args:
            file_id: ID del archivo en Google Drive.

        Returns:
            bytes: Contenido del archivo, o None si falla la descarga.
        """
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
