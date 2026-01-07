"""
ZIP Generator Service

Servicio para generar paquetes ZIP con facturas (PDF, XML) y reporte Excel.
Orquesta la descarga de archivos desde Google Drive y la generación del reporte.

Optimizado con descargas paralelas usando ThreadPoolExecutor para mejor rendimiento.
"""

import io
import logging
import time
import zipfile
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .google_drive_service import get_drive_service, _get_file_cache_repo
from .excel_report_service import get_excel_service

logger = logging.getLogger(__name__)

# Tipo para cache de file_ids: {uuid: {'pdf': file_id, 'xml': file_id}}
FileIdCache = Dict[str, Dict[str, str]]

# Número máximo de descargas paralelas
# Reducido a 1 para evitar timeouts por competencia de recursos
# Con 1 hilo, cada archivo tiene el timeout completo sin interferencia
MAX_PARALLEL_DOWNLOADS = 1

# Delay entre descargas para evitar rate limiting de Google Drive (en segundos)
# Un pequeño delay reduce la presión sobre el API y evita throttling
DOWNLOAD_DELAY_SECONDS = 0.5


class ZipGeneratorService:
    """
    Servicio para generar paquetes ZIP de facturación.

    Funcionalidad:
    - Descarga PDFs y XMLs desde Google Drive (en paralelo)
    - Genera reporte Excel detallado
    - Crea archivo ZIP con estructura organizada
    - Maneja archivos faltantes sin fallar
    """

    def __init__(self):
        """Inicializa el servicio de generación de ZIP."""
        self.drive_service = get_drive_service()
        self.excel_service = get_excel_service()

    def generate_invoice_package(
        self,
        invoices: List[Dict],
        metadata: Optional[Dict] = None,
        country: str = "MX"
    ) -> io.BytesIO:
        """
        Genera un paquete ZIP con facturas y reporte Excel.

        Args:
            invoices: Lista de facturas con datos completos.
                Cada factura debe tener: uuid, fecha_emision, codigo_operacion, etc.
            metadata: Metadata del paquete (código operación, RFC, fechas, etc.).
            country: País para el cache de file_ids ('MX' o 'CO').

        Returns:
            BytesIO: Contenido del archivo ZIP.

        Raises:
            Exception: Si falla la generación del ZIP.
        """
        try:
            logger.info(f"Iniciando generación de paquete ZIP para {len(invoices)} facturas (country={country})")

            # 1. Pre-cachear carpetas de meses necesarias (optimización)
            logger.info("Pre-cacheando carpetas de Google Drive...")
            self._precache_month_folders(invoices)

            # 2. Descargar archivos de Google Drive (en paralelo, con cache pre-cargado)
            logger.info("Descargando archivos desde Google Drive (paralelo con cache)...")
            file_downloads = self._download_invoice_files_parallel(invoices, country=country)

            # 3. Generar reporte Excel
            logger.info("Generando reporte Excel...")
            file_status = {item["uuid"]: {"pdf_found": item["pdf_found"], "xml_found": item["xml_found"]} for item in file_downloads}
            excel_buffer = self.excel_service.generate_invoice_report(
                invoices,
                file_status,
                metadata
            )

            # 4. Crear archivo ZIP
            logger.info("Creando archivo ZIP...")
            zip_buffer = self._create_zip_package(
                invoices,
                file_downloads,
                excel_buffer,
                metadata
            )

            logger.info("Paquete ZIP generado exitosamente")
            return zip_buffer

        except Exception as e:
            logger.error(f"Error al generar paquete ZIP: {str(e)}")
            raise

    def _precache_month_folders(self, invoices: List[Dict]) -> None:
        """
        Pre-cachea las carpetas de meses y sus archivos antes de las descargas paralelas.

        Esto evita que múltiples hilos intenten cachear la misma carpeta simultáneamente,
        y reduce drásticamente el número de llamadas a la API.

        Args:
            invoices: Lista de facturas con fecha_emision.
        """
        # Identificar los meses únicos necesarios
        months_needed: set = set()
        for invoice in invoices:
            fecha_emision = invoice.get("fecha_emision")
            if not fecha_emision:
                continue

            if isinstance(fecha_emision, str):
                try:
                    fecha_emision = datetime.fromisoformat(fecha_emision.replace('Z', '+00:00'))
                except Exception:
                    continue

            months_needed.add((fecha_emision.year, fecha_emision.month))

        logger.info(f"Pre-cacheando {len(months_needed)} carpetas de mes...")

        # Pre-cachear cada carpeta de mes
        for year, month in months_needed:
            try:
                month_folder_id = self.drive_service.get_month_folder_id(month, year)
                if month_folder_id:
                    # Esto cacheará todos los archivos de la carpeta
                    self.drive_service._cache_folder_files(month_folder_id)
            except Exception as e:
                logger.warning(f"Error al pre-cachear carpeta {month}/{year}: {str(e)}")

        logger.info("Pre-cache completado")

    def _download_single_invoice(
        self,
        invoice: Dict,
        file_id_cache: Optional[FileIdCache] = None,
        country: str = "MX"
    ) -> Optional[Dict]:
        """
        Descarga los archivos de una sola factura.

        OPTIMIZADO: Si se proporciona file_id_cache, usa los IDs pre-cargados
        en lugar de consultar el cache de Supabase individualmente.

        Args:
            invoice: Diccionario con uuid, fecha_emision, codigo_operacion.
            file_id_cache: Cache pre-cargado de file_ids {uuid: {'pdf': id, 'xml': id}}.
            country: País para el cache ('MX' o 'CO').

        Returns:
            Dict con resultado de descarga o None si hay error.
        """
        uuid = invoice.get("uuid")
        fecha_emision = invoice.get("fecha_emision")

        if not uuid or not fecha_emision:
            logger.warning(f"Factura sin UUID o fecha: {invoice}")
            return None

        # Convertir fecha a datetime si es string
        if isinstance(fecha_emision, str):
            try:
                fecha_emision = datetime.fromisoformat(fecha_emision.replace('Z', '+00:00'))
            except Exception as e:
                logger.error(f"Error al parsear fecha {fecha_emision}: {str(e)}")
                return None

        try:
            # Pequeño delay para evitar saturar Google Drive API
            time.sleep(DOWNLOAD_DELAY_SECONDS)

            pdf_content = None
            xml_content = None

            # Si tenemos cache pre-cargado, usar los IDs directamente con retry
            if file_id_cache and uuid in file_id_cache:
                cached_ids = file_id_cache[uuid]

                # Descargar PDF si tenemos el ID (con retry y backoff)
                if 'pdf' in cached_ids:
                    pdf_content = self.drive_service.download_file_with_retry(
                        file_id=cached_ids['pdf'],
                        file_name=f"{uuid}.pdf",
                        max_retries=2
                    )

                # Descargar XML si tenemos el ID (con retry y backoff)
                if 'xml' in cached_ids:
                    xml_content = self.drive_service.download_file_with_retry(
                        file_id=cached_ids['xml'],
                        file_name=f"{uuid}.xml",
                        max_retries=2
                    )
            else:
                # Fallback: usar método normal (consulta cache individualmente)
                pdf_content, xml_content = self.drive_service.get_invoice_files(
                    uuid, fecha_emision, country=country
                )

            return {
                "uuid": uuid,
                "codigo_operacion": invoice.get("codigo_operacion", ""),
                "pdf_content": pdf_content,
                "xml_content": xml_content,
                "pdf_found": pdf_content is not None,
                "xml_found": xml_content is not None,
            }
        except Exception as e:
            logger.error(f"Error descargando archivos para UUID {uuid}: {str(e)}")
            return {
                "uuid": uuid,
                "codigo_operacion": invoice.get("codigo_operacion", ""),
                "pdf_content": None,
                "xml_content": None,
                "pdf_found": False,
                "xml_found": False,
            }

    def _download_invoice_files_parallel(
        self,
        invoices: List[Dict],
        country: str = "MX"
    ) -> List[Dict]:
        """
        Descarga archivos PDF y XML de todas las facturas en paralelo.

        OPTIMIZADO: Pre-carga TODOS los file_ids del cache en UNA sola consulta
        antes de iniciar las descargas paralelas. Esto evita rate limiting de Supabase.

        Args:
            invoices: Lista de facturas.
            country: País para el cache ('MX' o 'CO').

        Returns:
            List[Dict]: Lista con información de descargas.
        """
        download_results = []
        total_invoices = len(invoices)

        logger.info(f"Iniciando descarga paralela de {total_invoices} facturas (max {MAX_PARALLEL_DOWNLOADS} hilos)")
        start_time = datetime.now()

        # OPTIMIZACIÓN: Pre-cargar TODOS los file_ids en UNA sola consulta
        file_id_cache: FileIdCache = {}
        cache_repo = _get_file_cache_repo()
        if cache_repo:
            try:
                uuids = [inv.get("uuid") for inv in invoices if inv.get("uuid")]
                if uuids:
                    logger.info(f"Pre-cargando {len(uuids)} file_ids del cache...")
                    file_id_cache = cache_repo.get_bulk_file_ids(uuids, country)
                    logger.info(f"Cache pre-cargado: {len(file_id_cache)} UUIDs encontrados")
            except Exception as e:
                logger.warning(f"Error pre-cargando cache: {e}. Continuando sin cache pre-cargado.")

        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
            # Enviar todas las tareas CON el cache pre-cargado
            future_to_invoice = {
                executor.submit(
                    self._download_single_invoice,
                    invoice,
                    file_id_cache,
                    country
                ): invoice
                for invoice in invoices
            }

            # Recolectar resultados conforme se completan
            completed = 0
            for future in as_completed(future_to_invoice):
                completed += 1
                result = future.result()
                if result:
                    download_results.append(result)

                # Log progreso cada 10 descargas o al final
                if completed % 10 == 0 or completed == total_invoices:
                    logger.info(f"Progreso de descarga: {completed}/{total_invoices}")

        # Estadísticas de descarga
        elapsed = (datetime.now() - start_time).total_seconds()
        total = len(download_results)
        pdf_found = sum(1 for item in download_results if item["pdf_found"])
        xml_found = sum(1 for item in download_results if item["xml_found"])

        logger.info(
            f"Descarga paralela completada en {elapsed:.1f}s: {total} facturas, "
            f"{pdf_found} PDFs encontrados, {xml_found} XMLs encontrados"
        )

        return download_results

    def _download_invoice_files(self, invoices: List[Dict]) -> List[Dict]:
        """
        Descarga archivos PDF y XML de todas las facturas (versión secuencial).

        Mantenida para compatibilidad. Usar _download_invoice_files_parallel
        para mejor rendimiento.

        Args:
            invoices: Lista de facturas.

        Returns:
            List[Dict]: Lista con información de descargas.
        """
        download_results = []

        for invoice in invoices:
            result = self._download_single_invoice(invoice)
            if result:
                download_results.append(result)

        # Estadísticas de descarga
        total = len(download_results)
        pdf_found = sum(1 for item in download_results if item["pdf_found"])
        xml_found = sum(1 for item in download_results if item["xml_found"])

        logger.info(
            f"Descarga completada: {total} facturas, "
            f"{pdf_found} PDFs encontrados, {xml_found} XMLs encontrados"
        )

        return download_results

    def _create_zip_package(
        self,
        invoices: List[Dict],
        file_downloads: List[Dict],
        excel_buffer: io.BytesIO,
        metadata: Optional[Dict] = None
    ) -> io.BytesIO:
        """
        Crea el archivo ZIP con todos los archivos.

        Estructura del ZIP:
        /
        ├── Reporte_Facturacion.xlsx
        ├── PDFs/
        │   ├── {UUID}.pdf
        │   └── ...
        └── XMLs/
            ├── {UUID}.xml
            └── ...

        Args:
            invoices: Lista de facturas.
            file_downloads: Resultado de descargas.
            excel_buffer: Buffer con contenido del Excel.
            metadata: Metadata del paquete.

        Returns:
            BytesIO: Buffer con contenido del ZIP.
        """
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Agregar reporte Excel
            excel_filename = self._generate_excel_filename(metadata)
            zip_file.writestr(excel_filename, excel_buffer.getvalue())
            logger.debug(f"Agregado al ZIP: {excel_filename}")

            # 2. Agregar PDFs
            pdf_count = 0
            for item in file_downloads:
                if item["pdf_content"]:
                    pdf_filename = f"PDFs/{item['uuid']}.pdf"
                    zip_file.writestr(pdf_filename, item["pdf_content"])
                    pdf_count += 1

            logger.debug(f"Agregados {pdf_count} archivos PDF al ZIP")

            # 3. Agregar XMLs
            xml_count = 0
            for item in file_downloads:
                if item["xml_content"]:
                    xml_filename = f"XMLs/{item['uuid']}.xml"
                    zip_file.writestr(xml_filename, item["xml_content"])
                    xml_count += 1

            logger.debug(f"Agregados {xml_count} archivos XML al ZIP")

        zip_buffer.seek(0)

        # Estadísticas finales
        zip_size_mb = len(zip_buffer.getvalue()) / (1024 * 1024)
        logger.info(
            f"ZIP creado: {pdf_count} PDFs, {xml_count} XMLs, "
            f"Tamaño: {zip_size_mb:.2f} MB"
        )

        return zip_buffer

    def _generate_excel_filename(self, metadata: Optional[Dict] = None) -> str:
        """
        Genera el nombre del archivo Excel basado en metadata.

        Args:
            metadata: Metadata del reporte.

        Returns:
            str: Nombre del archivo Excel.
        """
        timestamp = datetime.now().strftime("%Y%m%d")

        if metadata:
            if metadata.get("codigo_operacion"):
                # Limpiar código de operación para nombre de archivo
                codigo = metadata["codigo_operacion"].replace(":", "-").replace("/", "-")
                return f"Reporte_Facturacion_{codigo}_{timestamp}.xlsx"
            elif metadata.get("rfc"):
                return f"Reporte_Facturacion_{metadata['rfc']}_{timestamp}.xlsx"

        return f"Reporte_Facturacion_{timestamp}.xlsx"

    def generate_zip_filename(self, metadata: Optional[Dict] = None) -> str:
        """
        Genera el nombre del archivo ZIP basado en metadata.

        Args:
            metadata: Metadata del paquete.

        Returns:
            str: Nombre del archivo ZIP.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if metadata:
            if metadata.get("codigo_operacion"):
                codigo = metadata["codigo_operacion"].replace(":", "-").replace("/", "-")
                return f"Facturacion_MX_{codigo}_{timestamp}.zip"
            elif metadata.get("rfc"):
                return f"Facturacion_MX_{metadata['rfc']}_{timestamp}.zip"

        return f"Facturacion_MX_{timestamp}.zip"


# Singleton instance
_zip_service_instance: Optional[ZipGeneratorService] = None


def get_zip_service() -> ZipGeneratorService:
    """
    Obtiene la instancia singleton del servicio de generación de ZIP.

    Returns:
        ZipGeneratorService: Instancia del servicio.
    """
    global _zip_service_instance
    if _zip_service_instance is None:
        _zip_service_instance = ZipGeneratorService()
    return _zip_service_instance
