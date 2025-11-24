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

# Configurar logging
logger = logging.getLogger(__name__)


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

        # Log credential source
        if self.credentials_json:
            logger.info("GoogleDriveService initialized with env-based credentials (GOOGLE_DRIVE_CREDENTIALS_JSON)")
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

        # Try to parse as raw JSON
        try:
            credentials_dict = json.loads(credentials_string)
            logger.debug("Credentials parsed from raw JSON string")
            return credentials_dict
        except json.JSONDecodeError as e:
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

    def get_month_folder_id(self, month: int, year: int = 2025) -> Optional[str]:
        """
        Obtiene el ID de la carpeta del mes específico.

        Args:
            month: Número del mes (1-12).
            year: Año de la carpeta (default: 2025).

        Returns:
            str: ID de la carpeta del mes, o None si no se encuentra.
        """
        try:
            service = self.authenticate()

            # Buscar carpeta del año (ej: "2025")
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

            return month_files[0]["id"]

        except HttpError as e:
            logger.error(f"Error HTTP al buscar carpeta del mes: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al buscar carpeta del mes: {str(e)}")
            return None

    def search_file_by_uuid(
        self,
        uuid: str,
        fecha_emision: datetime,
        extension: str = "pdf"
    ) -> Optional[Dict]:
        """
        Busca un archivo (PDF o XML) en Drive por UUID.

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

            service = self.authenticate()

            # Buscar archivo por nombre
            filename = f"{uuid}.{extension}"
            query = (
                f"'{month_folder_id}' in parents and "
                f"name = '{filename}' and "
                f"trashed = false"
            )

            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType, size)",
                pageSize=1
            ).execute()

            files = results.get("files", [])

            if files:
                file_info = files[0]
                logger.info(f"Archivo encontrado: {filename} (ID: {file_info['id']})")
                return file_info
            else:
                logger.warning(f"Archivo no encontrado: {filename}")
                return None

        except HttpError as e:
            logger.error(f"Error HTTP al buscar archivo {uuid}.{extension}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al buscar archivo {uuid}.{extension}: {str(e)}")
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

    def find_master_excel_file(self) -> Optional[Dict]:
        """
        Busca el archivo maestro de Excel en la carpeta raíz de Drive.

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
                logger.info(f"Master Excel encontrado: {file_info['name']} (ID: {file_info['id']})")
                return file_info
            else:
                logger.warning(f"Master Excel no encontrado: {self.master_excel_name}")
                return None

        except HttpError as e:
            logger.error(f"Error HTTP al buscar master Excel: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error al buscar master Excel: {str(e)}")
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
