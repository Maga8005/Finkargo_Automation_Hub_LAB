"""
Google Drive Service

Servicio para interactuar con Google Drive API.
Permite buscar y descargar archivos PDF y XML de facturas.
"""

import os
import io
import json
import base64
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from src.config.settings import get_settings
from src.config.supabase_config import get_supabase_client

# Configurar logging
logger = logging.getLogger(__name__)

# Cache repository (lazy initialization)
_file_cache_repo = None


def _get_file_cache_repo():
    """Get or initialize the file cache repository."""
    global _file_cache_repo
    if _file_cache_repo is None:
        try:
            from src.repositorio.drive_file_cache_repository import DriveFileCacheRepository
            supabase_wrapper = get_supabase_client()
            # Use admin_client (service_role) for full cache access (read/write)
            # RLS policy grants service_role full access to drive_file_cache table
            _file_cache_repo = DriveFileCacheRepository(supabase_wrapper.admin_client)
            logger.info("Drive file cache repository initialized with admin_client")
        except Exception as e:
            logger.warning(f"Could not initialize file cache repository: {e}")
            _file_cache_repo = None
    return _file_cache_repo


class GoogleDriveService:
    """
    Servicio para interactuar con Google Drive API.

    Proporciona funcionalidad para:
    - Autenticación con Service Account
    - Búsqueda de archivos por UUID
    - Descarga de archivos PDF y XML
    - Manejo de errores y reintentos
    """

    def __init__(self):
        """Inicializa el servicio de Google Drive."""
        settings = get_settings()
        self.credentials_json = settings.GOOGLE_DRIVE_CREDENTIALS_JSON
        self.credentials_path = settings.GOOGLE_DRIVE_CREDENTIALS_PATH
        self.folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        self.master_excel_name = settings.GOOGLE_DRIVE_MASTER_EXCEL_NAME

        # Parse scopes from JSON string
        self.scopes = json.loads(settings.GOOGLE_DRIVE_SCOPES)
        self.service: Optional[Resource] = None

        # Cache para folder IDs (evita búsquedas repetidas)
        self._year_folder_cache: Dict[int, str] = {}
        self._month_folder_cache: Dict[str, str] = {}  # key: "year_month"
        # Cache de archivos por carpeta de mes (evita búsquedas repetidas)
        # key: month_folder_id, value: {filename: file_id}
        self._files_cache: Dict[str, Dict[str, str]] = {}

        # Log credential source
        if self.credentials_json:
            creds_length = len(self.credentials_json)
            logger.info(f"GoogleDriveService initialized with env-based credentials ({creds_length} chars)")
        else:
            logger.info(f"GoogleDriveService initialized with file-based credentials: {self.credentials_path}")

        if self.folder_id:
            logger.info(f"GoogleDriveService folder_id: {self.folder_id[:20]}...")

        # Mapeo de meses para búsqueda en carpetas
        self.month_folders = {
            1: "01 ENERO",
            2: "02 FEBRERO",
            3: "03 MARZO",
            4: "04 ABRIL",
            5: "05 MAYO",
            6: "06 JUNIO",
            7: "07 JULIO",
            8: "08 AGOSTO",
            9: "09 SEPTIEMBRE",
            10: "10 OCTUBRE",
            11: "11 NOVIEMBRE",
            12: "12 DICIEMBRE",
        }

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
        # Replace literal newlines with escaped newlines in string values
        credentials_string = credentials_string.replace('\n', '\\n')
        credentials_string = credentials_string.replace('\r', '\\r')
        credentials_string = credentials_string.replace('\t', '\\t')

        # Try to parse as raw JSON
        try:
            credentials_dict = json.loads(credentials_string)
            logger.debug(f"Credentials parsed from raw JSON string (project_id: {credentials_dict.get('project_id', 'unknown')})")
            return credentials_dict
        except json.JSONDecodeError as e:
            # Log the position and surrounding characters for debugging
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

        Supports two credential sources:
        1. Environment variable (GOOGLE_DRIVE_CREDENTIALS_JSON): base64-encoded or raw JSON
        2. File path (GOOGLE_DRIVE_CREDENTIALS_PATH): fallback for local development

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
            logger.info("Autenticación con Google Drive exitosa")
            return self.service

        except Exception as e:
            logger.error(f"Error al autenticar con Google Drive: {str(e)}")
            raise

    def _reset_service(self):
        """Resetea el servicio para forzar reconexión en caso de problemas."""
        self.service = None
        logger.debug("Servicio de Google Drive reseteado")

    def _get_year_folder_id(self, year: int, retries: int = 2) -> Optional[str]:
        """
        Obtiene el ID de la carpeta del año con cache y reintentos.

        Args:
            year: Año de la carpeta.
            retries: Número de reintentos en caso de error.

        Returns:
            str: ID de la carpeta del año, o None si no se encuentra.
        """
        # Verificar cache primero
        if year in self._year_folder_cache:
            logger.debug(f"Usando cache para carpeta año {year}")
            return self._year_folder_cache[year]

        for attempt in range(retries + 1):
            try:
                service = self.authenticate()

                year_query = (
                    f"'{self.folder_id}' in parents and "
                    f"name = '{year}' and "
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
                # Guardar en cache
                self._year_folder_cache[year] = year_folder_id
                logger.info(f"Carpeta año {year} encontrada y cacheada: {year_folder_id}")
                return year_folder_id

            except Exception as e:
                if attempt < retries:
                    import time
                    wait_time = (attempt + 1) * 2  # 2s, 4s
                    logger.warning(f"Error al buscar carpeta año {year}, reintento {attempt + 1}/{retries} en {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Error al buscar carpeta del año después de {retries} reintentos: {str(e)}")
                    return None

        return None

    def get_month_folder_id(self, month: int, year: int = 2025) -> Optional[str]:
        """
        Obtiene el ID de la carpeta del mes específico con cache y reintentos.

        Args:
            month: Número del mes (1-12).
            year: Año de la carpeta (default: 2025).

        Returns:
            str: ID de la carpeta del mes, o None si no se encuentra.
        """
        # Verificar cache primero
        cache_key = f"{year}_{month}"
        if cache_key in self._month_folder_cache:
            logger.debug(f"Usando cache para carpeta {month}/{year}")
            return self._month_folder_cache[cache_key]

        try:
            # Obtener carpeta del año (con cache)
            year_folder_id = self._get_year_folder_id(year)
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
                logger.warning(f"Carpeta del mes {month_name} no encontrada")
                return None

            month_folder_id = month_files[0]["id"]
            # Guardar en cache
            self._month_folder_cache[cache_key] = month_folder_id
            logger.debug(f"Carpeta {month_name} {year} cacheada: {month_folder_id}")
            return month_folder_id

        except HttpError as e:
            logger.error(f"Error HTTP al buscar carpeta del mes: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al buscar carpeta del mes: {str(e)}")
            return None

    def _cache_folder_files(self, folder_id: str) -> Dict[str, str]:
        """
        Lista y cachea todos los archivos de una carpeta.

        Esto evita hacer una búsqueda por cada archivo individual.

        Args:
            folder_id: ID de la carpeta en Google Drive.

        Returns:
            Dict[str, str]: Mapeo de nombre de archivo a file_id.
        """
        if folder_id in self._files_cache:
            return self._files_cache[folder_id]

        try:
            service = self.authenticate()
            files_map: Dict[str, str] = {}
            page_token = None

            while True:
                query = f"'{folder_id}' in parents and trashed = false"
                results = service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name)",
                    pageSize=1000,  # Máximo permitido
                    pageToken=page_token
                ).execute()

                for file_info in results.get("files", []):
                    files_map[file_info["name"]] = file_info["id"]

                page_token = results.get("nextPageToken")
                if not page_token:
                    break

            self._files_cache[folder_id] = files_map
            logger.info(f"Cacheados {len(files_map)} archivos de carpeta {folder_id[:10]}...")
            return files_map

        except Exception as e:
            logger.error(f"Error al cachear archivos de carpeta {folder_id}: {str(e)}")
            return {}

    def _precache_all_month_folders(self, year: int = 2025) -> None:
        """
        Pre-cachea todas las carpetas de meses del año y sus archivos.

        Esto permite buscar archivos en cualquier carpeta de mes sin hacer
        múltiples llamadas a la API.

        Args:
            year: Año a pre-cachear (default: 2025).
        """
        if hasattr(self, '_all_months_cached') and self._all_months_cached.get(year):
            logger.debug(f"Carpetas del año {year} ya están cacheadas")
            return

        logger.info(f"Pre-cacheando todas las carpetas de meses del año {year}...")

        for month in range(1, 13):
            try:
                month_folder_id = self.get_month_folder_id(month, year)
                if month_folder_id:
                    self._cache_folder_files(month_folder_id)
            except Exception as e:
                logger.warning(f"Error al pre-cachear carpeta {month}/{year}: {str(e)}")

        # Marcar como cacheado
        if not hasattr(self, '_all_months_cached'):
            self._all_months_cached: Dict[int, bool] = {}
        self._all_months_cached[year] = True
        logger.info(f"Pre-cache de carpetas {year} completado")

    def search_file_by_uuid(
        self,
        uuid: str,
        fecha_emision: datetime,
        extension: str = "pdf"
    ) -> Optional[Dict]:
        """
        Busca un archivo (PDF o XML) en Drive por UUID.

        Optimizado: Usa cache de archivos por carpeta para evitar búsquedas individuales.

        Args:
            uuid: UUID del documento.
            fecha_emision: Fecha de emisión del documento (para determinar la carpeta).
            extension: Extensión del archivo ('pdf' o 'xml').

        Returns:
            Dict con información del archivo encontrado, o None si no existe.
            Formato: {'id': str, 'name': str, 'mimeType': str}
        """
        try:
            # Obtener carpeta del mes correspondiente
            month = fecha_emision.month
            year = fecha_emision.year

            month_folder_id = self.get_month_folder_id(month, year)
            if not month_folder_id:
                logger.warning(
                    f"No se encontró carpeta para {self.month_folders.get(month)} {year}"
                )
                return None

            # Usar cache de archivos de la carpeta
            filename = f"{uuid}.{extension}"
            files_map = self._cache_folder_files(month_folder_id)

            if filename in files_map:
                file_id = files_map[filename]
                logger.debug(f"Archivo encontrado en cache: {filename}")
                return {"id": file_id, "name": filename}
            else:
                logger.debug(f"Archivo no encontrado: {filename}")
                return None

        except HttpError as e:
            logger.error(f"Error HTTP al buscar archivo {uuid}.{extension}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al buscar archivo {uuid}.{extension}: {str(e)}")
            return None

    def search_file_global(
        self,
        uuid: str,
        extension: str = "pdf",
        max_retries: int = 2,
        country: str = "MX"
    ) -> Optional[Dict]:
        """
        Busca un archivo en TODO el Drive usando CACHE PRIMERO, luego búsqueda global.

        Estrategia:
        1. Primero busca en el cache de base de datos (instantáneo)
        2. Si no está en cache, busca en Drive (una llamada API)
        3. Si lo encuentra, guarda el ID en cache para futuras consultas

        Args:
            uuid: UUID del documento.
            extension: Extensión del archivo ('pdf' o 'xml').
            max_retries: Número máximo de reintentos en caso de timeout.
            country: País ('MX' o 'CO') para el cache.

        Returns:
            Dict con información del archivo encontrado, o None si no existe.
            Formato: {'id': str, 'name': str}
        """
        import time
        filename = f"{uuid}.{extension}"

        # 1. PRIMERO: Buscar en cache de base de datos (INSTANTÁNEO)
        cache_repo = _get_file_cache_repo()
        if cache_repo:
            try:
                cached_id = cache_repo.get_file_id(uuid, extension, country)
                if cached_id:
                    logger.debug(f"Cache HIT: {filename} -> {cached_id[:15]}...")
                    return {"id": cached_id, "name": filename}
            except Exception as e:
                logger.warning(f"Error checking cache for {filename}: {e}")

        # 2. FALLBACK: Buscar en Google Drive API
        logger.debug(f"Cache MISS: {filename}, buscando en Drive...")

        for attempt in range(max_retries + 1):
            try:
                service = self.authenticate()

                # Búsqueda global: buscar por nombre exacto (recursivo en todo el Drive)
                query = (
                    f"name = '{filename}' and "
                    f"trashed = false"
                )

                results = service.files().list(
                    q=query,
                    fields="files(id, name)",
                    pageSize=1  # Solo necesitamos uno
                ).execute()

                files = results.get("files", [])
                if files:
                    file_info = files[0]
                    file_id = file_info["id"]
                    logger.debug(f"Archivo {filename} encontrado via búsqueda global")

                    # 3. GUARDAR EN CACHE para futuras consultas (async-safe)
                    if cache_repo:
                        try:
                            cache_repo.cache_file_id(
                                uuid=uuid,
                                file_type=extension,
                                drive_file_id=file_id,
                                drive_file_name=file_info["name"],
                                country=country
                            )
                            logger.debug(f"Cache STORED: {filename}")
                        except Exception as e:
                            logger.warning(f"Error caching {filename}: {e}")

                    return {"id": file_id, "name": file_info["name"]}

                logger.debug(f"Archivo {filename} no encontrado en búsqueda global")
                return None

            except HttpError as e:
                logger.error(f"Error HTTP en búsqueda global de {filename}: {str(e)}")
                return None
            except Exception as e:
                # Timeout u otro error - reintentar
                self._reset_service()  # Resetear conexión
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 1  # 1s, 2s
                    logger.warning(f"Timeout buscando {filename}, reintento {attempt + 1}/{max_retries} en {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Error en búsqueda global de {filename} después de {max_retries + 1} intentos: {str(e)}")
                    return None

        return None

    def search_file_in_all_months(
        self,
        uuid: str,
        year: int = 2025,
        extension: str = "pdf"
    ) -> Optional[Dict]:
        """
        Busca un archivo usando búsqueda global de Drive (fallback al método anterior).

        Args:
            uuid: UUID del documento.
            year: Año donde buscar (no usado, mantenido por compatibilidad).
            extension: Extensión del archivo ('pdf' o 'xml').

        Returns:
            Dict con información del archivo encontrado, o None si no existe.
        """
        # Usar búsqueda global - mucho más rápido
        return self.search_file_global(uuid, extension)

    def _search_and_download(self, uuid: str, extension: str, country: str = "MX") -> Optional[bytes]:
        """
        Busca y descarga un archivo en una sola operación.

        Args:
            uuid: UUID del documento.
            extension: Extensión del archivo ('pdf' o 'xml').
            country: País ('MX' o 'CO') para el cache.

        Returns:
            bytes: Contenido del archivo, o None si no se encuentra.
        """
        file_info = self.search_file_global(uuid, extension, country=country)
        if file_info:
            return self.download_file(file_info["id"])
        else:
            logger.warning(f"{extension.upper()} no encontrado para UUID: {uuid}")
            return None

    def get_invoice_files_extended(
        self,
        uuid: str,
        fecha_emision: datetime,
        search_all_months: bool = True,
        country: str = "MX"
    ) -> Tuple[Optional[bytes], Optional[bytes]]:
        """
        Obtiene los archivos PDF y XML de una factura usando búsqueda global EN PARALELO.

        Busca PDF y XML simultáneamente para mejor rendimiento.
        Usa cache de base de datos para evitar búsquedas costosas en Drive.

        Args:
            uuid: UUID del documento.
            fecha_emision: Fecha de emisión del documento (no usado, mantenido por compatibilidad).
            search_all_months: No usado, mantenido por compatibilidad.
            country: País ('MX' o 'CO') para el cache.

        Returns:
            Tuple[Optional[bytes], Optional[bytes]]: (PDF content, XML content)
        """
        from concurrent.futures import ThreadPoolExecutor

        pdf_content = None
        xml_content = None

        # Buscar y descargar PDF y XML en paralelo
        with ThreadPoolExecutor(max_workers=2) as executor:
            pdf_future = executor.submit(self._search_and_download, uuid, "pdf", country)
            xml_future = executor.submit(self._search_and_download, uuid, "xml", country)

            # Esperar resultados
            pdf_content = pdf_future.result()
            xml_content = xml_future.result()

        return pdf_content, xml_content

    def download_file(self, file_id: str, max_retries: int = 2) -> Optional[bytes]:
        """
        Descarga un archivo de Google Drive con reintentos automáticos.

        Args:
            file_id: ID del archivo en Google Drive.
            max_retries: Número máximo de reintentos en caso de timeout.

        Returns:
            bytes: Contenido del archivo, o None si falla la descarga.
        """
        import time

        for attempt in range(max_retries):
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

                logger.debug(f"Archivo descargado (ID: {file_id[:10]}..., {len(content)} bytes)")
                return content

            except HttpError as e:
                logger.warning(f"Error HTTP descargando {file_id[:10]}...: {str(e)}")
                return None
            except Exception as e:
                # Timeout u otro error - reintentar solo una vez
                self._reset_service()
                if attempt < max_retries - 1:
                    logger.warning(f"Error descargando {file_id[:10]}..., reintento {attempt + 1}/{max_retries}")
                    time.sleep(1)  # Solo 1 segundo de espera
                else:
                    logger.warning(f"Omitiendo archivo {file_id[:10]}... después de {max_retries} intentos")
                    return None

        return None

    def get_invoice_files(
        self,
        uuid: str,
        fecha_emision: datetime
    ) -> Tuple[Optional[bytes], Optional[bytes]]:
        """
        Obtiene los archivos PDF y XML de una factura.

        Args:
            uuid: UUID del documento.
            fecha_emision: Fecha de emisión del documento.

        Returns:
            Tuple[Optional[bytes], Optional[bytes]]: (PDF content, XML content)
            Retorna None para archivos no encontrados.
        """
        pdf_content = None
        xml_content = None

        # Buscar y descargar PDF
        pdf_file = self.search_file_by_uuid(uuid, fecha_emision, "pdf")
        if pdf_file:
            pdf_content = self.download_file(pdf_file["id"])
        else:
            logger.warning(f"PDF no encontrado para UUID: {uuid}")

        # Buscar y descargar XML
        xml_file = self.search_file_by_uuid(uuid, fecha_emision, "xml")
        if xml_file:
            xml_content = self.download_file(xml_file["id"])
        else:
            logger.warning(f"XML no encontrado para UUID: {uuid}")

        return pdf_content, xml_content

    def batch_get_invoice_files(
        self,
        invoices: List[Dict]
    ) -> List[Dict]:
        """
        Obtiene archivos de múltiples facturas en batch.

        Args:
            invoices: Lista de dicts con 'uuid' y 'fecha_emision'.

        Returns:
            List[Dict]: Lista con información de archivos descargados.
            Formato: [
                {
                    'uuid': str,
                    'pdf_content': Optional[bytes],
                    'xml_content': Optional[bytes],
                    'pdf_found': bool,
                    'xml_found': bool
                }
            ]
        """
        results = []

        for invoice in invoices:
            uuid = invoice.get("uuid")
            fecha_emision = invoice.get("fecha_emision")

            if not uuid or not fecha_emision:
                logger.warning(f"Factura con datos incompletos: {invoice}")
                continue

            pdf_content, xml_content = self.get_invoice_files(uuid, fecha_emision)

            results.append({
                "uuid": uuid,
                "pdf_content": pdf_content,
                "xml_content": xml_content,
                "pdf_found": pdf_content is not None,
                "xml_found": xml_content is not None,
            })

        return results

    def find_master_excel_file(self, max_retries: int = 2) -> Optional[Dict]:
        """
        Busca el archivo maestro de Excel en la carpeta raíz de Drive.

        Args:
            max_retries: Número máximo de reintentos en caso de timeout.

        Returns:
            Dict: Información del archivo encontrado (id, name, mimeType), o None si no existe.
        """
        import time

        for attempt in range(max_retries + 1):
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
                    logger.info(f"Master Excel encontrado: {file_info['name']} (ID: {file_info['id']})")
                    return file_info
                else:
                    logger.warning(f"Master Excel no encontrado: {self.master_excel_name}")
                    return None

            except HttpError as e:
                logger.error(f"Error HTTP al buscar master Excel: {str(e)}")
                return None
            except Exception as e:
                # Timeout u otro error - reintentar
                self._reset_service()
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Timeout buscando master Excel, reintento {attempt + 1}/{max_retries} en {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Error al buscar master Excel después de {max_retries + 1} intentos: {str(e)}")
                    return None

        return None

    def download_master_excel(self) -> Optional[bytes]:
        """
        Descarga el archivo maestro de Excel desde Drive.

        Returns:
            bytes: Contenido del archivo Excel, o None si no existe o falla la descarga.
        """
        try:
            file_info = self.find_master_excel_file()
            if not file_info:
                logger.warning("No se puede descargar: Master Excel no encontrado")
                return None

            file_id = file_info["id"]
            content = self.download_file(file_id)

            if content:
                logger.info(f"Master Excel descargado: {len(content)} bytes")
            return content

        except Exception as e:
            logger.error(f"Error al descargar master Excel: {str(e)}")
            return None

    def upload_master_excel(self, excel_content: bytes) -> bool:
        """
        Sube o actualiza el archivo maestro de Excel en Drive.

        Si el archivo ya existe, lo actualiza. Si no existe, lo crea.

        Args:
            excel_content: Contenido del archivo Excel en bytes.

        Returns:
            bool: True si la subida fue exitosa, False en caso contrario.
        """
        try:
            from googleapiclient.http import MediaIoBaseUpload

            service = self.authenticate()

            # Buscar si el archivo ya existe
            existing_file = self.find_master_excel_file()

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
                logger.info(f"Master Excel actualizado: {updated_file['name']} (ID: {updated_file['id']})")
            else:
                # Crear nuevo archivo
                file_metadata["parents"] = [self.folder_id]
                created_file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name"
                ).execute()
                logger.info(f"Master Excel creado: {created_file['name']} (ID: {created_file['id']})")

            return True

        except HttpError as e:
            logger.error(f"Error HTTP al subir master Excel: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error al subir master Excel: {str(e)}")
            return False


    def precache_drive_file_ids(
        self,
        uuids: List[str],
        country: str = "MX",
        max_workers: int = 4
    ) -> Dict[str, int]:
        """
        Pre-cachea los file IDs de Drive para una lista de UUIDs.

        OPTIMIZADO: Lista todos los archivos del Drive una sola vez
        y hace el match en memoria (segundos en lugar de horas).

        Args:
            uuids: Lista de UUIDs a pre-cachear.
            country: País ('MX' o 'CO') para el cache.
            max_workers: No usado en versión optimizada.

        Returns:
            Dict con estadísticas: {'total': int, 'cached': int, 'not_found': int, 'already_cached': int}
        """
        cache_repo = _get_file_cache_repo()
        if not cache_repo:
            logger.warning("Cache repository not available, skipping precache")
            return {'total': len(uuids), 'cached': 0, 'not_found': 0, 'already_cached': 0}

        stats = {
            'total': len(uuids),
            'cached': 0,
            'not_found': 0,
            'already_cached': 0
        }

        logger.info(f"Starting OPTIMIZED precache for {len(uuids)} UUIDs (country={country})...")

        # 1. Verificar cuáles ya están en cache
        existing_cache = cache_repo.get_bulk_file_ids(uuids, country)
        uuids_to_search = set()

        for uuid in uuids:
            if uuid in existing_cache:
                cached_types = existing_cache[uuid]
                if 'pdf' in cached_types and 'xml' in cached_types:
                    stats['already_cached'] += 1
                    continue
            uuids_to_search.add(uuid)

        if not uuids_to_search:
            logger.info(f"All {len(uuids)} UUIDs already in cache")
            return stats

        logger.info(f"Need to search Drive for {len(uuids_to_search)} UUIDs not in cache...")

        # 2. OPTIMIZACIÓN: Listar TODOS los archivos del Drive una sola vez
        logger.info("Listing ALL files from Google Drive (this may take a moment)...")
        all_drive_files = self._list_all_drive_files()
        logger.info(f"Found {len(all_drive_files)} files in Drive")

        # 3. Crear índice por nombre de archivo para búsqueda O(1)
        # Formato: {"uuid.pdf": {"id": "...", "name": "..."}, ...}
        file_index: Dict[str, Dict[str, str]] = {}
        for file_info in all_drive_files:
            filename = file_info.get('name', '')
            if filename:
                file_index[filename.lower()] = {
                    'id': file_info['id'],
                    'name': filename
                }

        logger.info(f"Indexed {len(file_index)} files for fast lookup")

        # 4. Match UUIDs con archivos en memoria (muy rápido)
        all_files_to_cache = []
        uuids_found = set()

        for uuid in uuids_to_search:
            found_any = False
            for ext in ['pdf', 'xml']:
                filename = f"{uuid}.{ext}".lower()
                if filename in file_index:
                    file_info = file_index[filename]
                    all_files_to_cache.append({
                        'uuid': uuid,
                        'file_type': ext,
                        'drive_file_id': file_info['id'],
                        'drive_file_name': file_info['name']
                    })
                    found_any = True

            if found_any:
                uuids_found.add(uuid)
            else:
                stats['not_found'] += 1

        logger.info(f"Matched {len(uuids_found)} UUIDs with {len(all_files_to_cache)} files")

        # 5. Guardar en cache en batch
        if all_files_to_cache:
            cached_count = cache_repo.cache_bulk_file_ids(all_files_to_cache, country)
            stats['cached'] = cached_count
            logger.info(f"Cached {cached_count} file IDs for {len(uuids_found)} UUIDs")
        else:
            logger.warning("No files found to cache")

        return stats

    def _list_all_drive_files(self) -> List[Dict]:
        """
        Lista TODOS los archivos del Google Drive (recursivamente).

        Usa paginación para obtener todos los archivos sin límite.

        Returns:
            Lista de dicts con {id, name, mimeType} de cada archivo.
        """
        service = self.authenticate()
        all_files = []
        page_token = None
        page_count = 0

        # Buscar solo PDFs y XMLs para optimizar
        query = "(mimeType='application/pdf' or mimeType='text/xml' or mimeType='application/xml' or name contains '.xml') and trashed=false"

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
                    logger.info(f"Listed {len(all_files)} files so far (page {page_count})...")

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            except HttpError as e:
                logger.error(f"Error listing files (page {page_count}): {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error listing files: {e}")
                break

        logger.info(f"Finished listing: {len(all_files)} total files in {page_count} pages")
        return all_files

    def _search_file_in_drive_only(
        self,
        uuid: str,
        extension: str = "pdf"
    ) -> Optional[Dict]:
        """
        Busca un archivo SOLO en Drive (sin cache).

        Usado internamente para pre-caching.

        Args:
            uuid: UUID del documento.
            extension: Extensión del archivo ('pdf' o 'xml').

        Returns:
            Dict con información del archivo, o None si no existe.
        """
        import time
        filename = f"{uuid}.{extension}"
        max_retries = 2

        for attempt in range(max_retries + 1):
            try:
                service = self.authenticate()

                query = (
                    f"name = '{filename}' and "
                    f"trashed = false"
                )

                results = service.files().list(
                    q=query,
                    fields="files(id, name)",
                    pageSize=1
                ).execute()

                files = results.get("files", [])
                if files:
                    return {"id": files[0]["id"], "name": files[0]["name"]}

                return None

            except Exception as e:
                self._reset_service()
                if attempt < max_retries:
                    time.sleep((attempt + 1) * 0.5)
                else:
                    logger.debug(f"Error searching {filename}: {e}")
                    return None

        return None


# Singleton instance
_drive_service_instance: Optional[GoogleDriveService] = None


def get_drive_service() -> GoogleDriveService:
    """
    Obtiene la instancia singleton del servicio de Google Drive.

    Returns:
        GoogleDriveService: Instancia del servicio.
    """
    global _drive_service_instance
    if _drive_service_instance is None:
        _drive_service_instance = GoogleDriveService()
    return _drive_service_instance
