"""
ZIP Generator Service

Servicio para generar paquetes ZIP con facturas (PDF, XML) y reporte Excel.
Orquesta la descarga de archivos desde Google Drive y la generación del reporte.

Optimizado con descargas paralelas usando ThreadPoolExecutor para mejor rendimiento.
"""

import io
import logging
import zipfile
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .google_drive_service import get_drive_service
from .excel_report_service import get_excel_service

logger = logging.getLogger(__name__)

# Número máximo de descargas paralelas
# Cambiado a 1 (secuencial) para evitar bloqueos con Google Drive API
MAX_PARALLEL_DOWNLOADS = 1


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
            country: País ('MX' o 'CO') para el cache de IDs de Drive.

        Returns:
            BytesIO: Contenido del archivo ZIP.

        Raises:
            Exception: Si falla la generación del ZIP.
        """
        try:
            logger.info(f"Iniciando generación de paquete ZIP para {len(invoices)} facturas (país={country})")

            # 1. Descargar archivos de Google Drive (en paralelo, con cache)
            # Usa cache de base de datos para evitar búsquedas costosas en Drive
            logger.info("Descargando archivos desde Google Drive (paralelo + cache)...")
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
        Pre-cachea TODAS las carpetas de meses del año para búsqueda extendida.

        Esto permite encontrar archivos que estén en carpetas diferentes a la
        fecha de emisión (por errores de descarga o diferencias entre fechas).

        Args:
            invoices: Lista de facturas con fecha_emision.
        """
        # Identificar los años únicos necesarios
        years_needed: set = set()
        for invoice in invoices:
            fecha_emision = invoice.get("fecha_emision")
            if not fecha_emision:
                continue

            if isinstance(fecha_emision, str):
                try:
                    fecha_emision = datetime.fromisoformat(fecha_emision.replace('Z', '+00:00'))
                except Exception:
                    continue

            years_needed.add(fecha_emision.year)

        # Si no hay años identificados, usar el año actual
        if not years_needed:
            years_needed.add(datetime.now().year)

        logger.info(f"Pre-cacheando TODAS las carpetas de meses para años: {sorted(years_needed)}")

        # Pre-cachear TODAS las carpetas de cada año (para búsqueda extendida)
        for year in years_needed:
            try:
                self.drive_service._precache_all_month_folders(year)
            except Exception as e:
                logger.warning(f"Error al pre-cachear carpetas del año {year}: {str(e)}")

        logger.info("Pre-cache de todas las carpetas completado")

    def _download_single_invoice(
        self,
        invoice: Dict,
        search_all_months: bool = True,
        country: str = "MX"
    ) -> Optional[Dict]:
        """
        Descarga los archivos de una sola factura.

        Args:
            invoice: Diccionario con uuid, fecha_emision, codigo_operacion.
            search_all_months: Si True, busca en todas las carpetas de meses si no
                              encuentra en la carpeta correspondiente a la fecha.
            country: País ('MX' o 'CO') para el cache de IDs de Drive.

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
            # Descargar archivos con búsqueda global + cache
            # Usa cache de base de datos primero, luego búsqueda global en Drive
            pdf_content, xml_content = self.drive_service.get_invoice_files_extended(
                uuid, fecha_emision, search_all_months=search_all_months, country=country
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

        OPTIMIZADO:
        1. Consulta bulk a Supabase para obtener todos los drive_file_ids de una vez
        2. Descargas paralelas usando los IDs pre-cacheados

        Args:
            invoices: Lista de facturas.
            country: País ('MX' o 'CO') para el cache de IDs de Drive.

        Returns:
            List[Dict]: Lista con información de descargas.
        """
        from src.repositorio.drive_file_cache_repository import DriveFileCacheRepository
        from src.config.supabase_config import get_supabase_client

        download_results = []
        total_invoices = len(invoices)
        start_time = datetime.now()

        # 1. OPTIMIZACIÓN: Obtener TODOS los file_ids de Supabase en UNA sola consulta
        logger.info(f"Obteniendo {total_invoices} file_ids desde cache de Supabase...")
        uuids = [inv.get("uuid") for inv in invoices if inv.get("uuid")]

        try:
            supabase = get_supabase_client()
            cache_repo = DriveFileCacheRepository(supabase.admin_client)
            cached_ids = cache_repo.get_bulk_file_ids(uuids, country)
            logger.info(f"Cache bulk lookup: {len(cached_ids)} UUIDs encontrados en cache")
        except Exception as e:
            logger.warning(f"Error en bulk lookup, usando fallback: {e}")
            cached_ids = {}

        # 2. Preparar lista de descargas con IDs pre-cacheados
        download_tasks = []
        for invoice in invoices:
            uuid = invoice.get("uuid")
            if not uuid:
                continue

            # Obtener IDs del cache bulk
            uuid_cache = cached_ids.get(uuid, {})
            pdf_id = uuid_cache.get("pdf")
            xml_id = uuid_cache.get("xml")

            download_tasks.append({
                "invoice": invoice,
                "pdf_id": pdf_id,
                "xml_id": xml_id
            })

        # 3. Descargar archivos usando IDs directos (sin consultas adicionales a Supabase)
        logger.info(f"Iniciando descarga de {len(download_tasks)} facturas (max {MAX_PARALLEL_DOWNLOADS} hilos)")

        def download_with_cached_ids(task: Dict) -> Dict:
            """Descarga archivos usando IDs pre-cacheados."""
            invoice = task["invoice"]
            uuid = invoice.get("uuid")
            pdf_id = task.get("pdf_id")
            xml_id = task.get("xml_id")

            pdf_content = None
            xml_content = None

            # Descargar PDF si tenemos el ID
            if pdf_id:
                try:
                    pdf_content = self.drive_service.download_file(pdf_id)
                except Exception as e:
                    logger.warning(f"Error descargando PDF {uuid}: {e}")

            # Descargar XML si tenemos el ID
            if xml_id:
                try:
                    xml_content = self.drive_service.download_file(xml_id)
                except Exception as e:
                    logger.warning(f"Error descargando XML {uuid}: {e}")

            return {
                "uuid": uuid,
                "codigo_operacion": invoice.get("codigo_operacion", ""),
                "pdf_content": pdf_content,
                "xml_content": xml_content,
                "pdf_found": pdf_content is not None,
                "xml_found": xml_content is not None,
            }

        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
            future_to_task = {
                executor.submit(download_with_cached_ids, task): task
                for task in download_tasks
            }

            completed = 0
            for future in as_completed(future_to_task):
                completed += 1
                try:
                    result = future.result()
                    if result:
                        download_results.append(result)
                except Exception as e:
                    logger.warning(f"Error en descarga: {e}")

                if completed % 10 == 0 or completed == len(download_tasks):
                    logger.info(f"Progreso de descarga: {completed}/{len(download_tasks)}")

        # Estadísticas
        elapsed = (datetime.now() - start_time).total_seconds()
        pdf_found = sum(1 for item in download_results if item["pdf_found"])
        xml_found = sum(1 for item in download_results if item["xml_found"])

        logger.info(
            f"Descarga completada en {elapsed:.1f}s: {len(download_results)} facturas, "
            f"{pdf_found} PDFs, {xml_found} XMLs"
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
