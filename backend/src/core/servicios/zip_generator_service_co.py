"""
ZIP Generator Service for Colombia (CO)

Servicio para generar paquetes ZIP con facturas PDF y reporte Excel filtrado.
Orquesta la descarga de archivos desde Google Drive y la generación del paquete.

Optimizado con:
- Descargas paralelas usando ThreadPoolExecutor
- Pre-caché de carpetas antes de las descargas
- Compresión ZIP en memoria (streaming)
- Bulk query a Supabase para obtener file_ids
- Backoff exponencial (2s, 4s, 8s) para reintentos
- ZIP streaming: agrega archivos conforme se descargan
"""

import io
import logging
import zipfile
import queue
import threading
import time
from typing import List, Dict, Optional
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed

from .google_drive_service_co import get_drive_service_co

logger = logging.getLogger(__name__)

# Número máximo de descargas paralelas
# Reducido a 1 para evitar timeouts por competencia de recursos
# Con 1 hilo, cada archivo tiene el timeout completo sin interferencia
MAX_PARALLEL_DOWNLOADS = 1

# Delay entre descargas para evitar rate limiting de Google Drive (en segundos)
# Un pequeño delay reduce la presión sobre el API y evita throttling
DOWNLOAD_DELAY_SECONDS = 0.5


class ZipGeneratorServiceCO:
    """
    Servicio para generar paquetes ZIP de facturación Colombia.

    Funcionalidad:
    - Descarga PDFs de facturas desde Google Drive (en paralelo)
    - Pre-cachea carpetas para optimizar búsquedas
    - Genera reporte Excel con datos filtrados
    - Crea archivo ZIP con estructura organizada
    - Maneja archivos faltantes sin fallar

    Optimizaciones:
    - ThreadPoolExecutor para descargas paralelas (8 hilos)
    - Pre-caché de carpetas mes/año antes de las descargas
    - Búsquedas instantáneas en caché
    """

    def __init__(self):
        """Inicializa el servicio de generación de ZIP."""
        self.drive_service = get_drive_service_co()

    def generate_invoice_package(
        self,
        records: List[Dict],
        excel_content: bytes,
        metadata: Optional[Dict] = None
    ) -> io.BytesIO:
        """
        Genera un paquete ZIP con facturas PDF y reporte Excel.
        Optimizado con pre-caché y descargas paralelas.

        Args:
            records: Lista de registros filtrados con numero_factura y fecha.
            excel_content: Contenido del Excel de reporte ya generado.
            metadata: Metadata del paquete (NIT, operaciones, fechas, etc.).

        Returns:
            BytesIO: Contenido del archivo ZIP.

        Raises:
            Exception: Si falla la generación del ZIP.
        """
        try:
            logger.info(f"Iniciando generación de paquete ZIP CO para {len(records)} facturas")
            start_time = datetime.now()

            # 1. Pre-cachear carpetas de meses (OPTIMIZACIÓN CRÍTICA)
            logger.info("Pre-cacheando carpetas de Google Drive...")
            self._precache_month_folders(records)

            # 2. Usar generación streaming (descarga + ZIP simultáneo)
            logger.info("Generando ZIP con streaming (descarga + compresión simultánea)...")
            zip_buffer = self._generate_zip_streaming(
                records,
                excel_content,
                metadata
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Paquete ZIP CO generado exitosamente en {elapsed:.1f}s")
            return zip_buffer

        except Exception as e:
            logger.error(f"Error al generar paquete ZIP CO: {str(e)}")
            raise

    def _precache_month_folders(self, records: List[Dict]) -> None:
        """
        Pre-cachea las carpetas de meses y sus archivos antes de las descargas paralelas.
        Esto evita que múltiples hilos intenten cachear la misma carpeta simultáneamente,
        y reduce drásticamente el número de llamadas a la API.

        Args:
            records: Lista de registros con fecha.
        """
        # Extraer fechas de los registros
        dates: List[date] = []
        for record in records:
            fecha = record.get("fecha")
            if not fecha:
                continue

            # Convertir fecha si es string
            if isinstance(fecha, str):
                try:
                    fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
                except ValueError:
                    try:
                        fecha = datetime.strptime(fecha, "%d/%m/%Y").date()
                    except ValueError:
                        continue

            if isinstance(fecha, date):
                dates.append(fecha)

        # Llamar al método de pre-cache del drive service
        self.drive_service.precache_month_folders(dates)

    def _download_single_invoice(self, invoice: Dict) -> Optional[Dict]:
        """
        Descarga el PDF de una sola factura.
        OPTIMIZADO: Usa cache de Supabase para evitar búsquedas en Drive.

        Args:
            invoice: Diccionario con numero_factura y fecha.

        Returns:
            Dict con resultado de descarga o None si hay error.
        """
        numero_factura = invoice.get("numero_factura")
        fecha = invoice.get("fecha")

        if not numero_factura or not fecha:
            logger.warning(f"Factura con datos incompletos: {invoice}")
            return {
                "numero_factura": numero_factura or "UNKNOWN",
                "pdf_content": None,
                "pdf_found": False
            }

        # Convertir fecha si es string
        if isinstance(fecha, str):
            parsed = False
            # Intentar múltiples formatos de fecha
            date_formats = [
                "%Y-%m-%d",              # 2022-12-30
                "%Y-%m-%d %H:%M:%S",     # 2022-12-30 00:00:00
                "%d/%m/%Y",              # 30/12/2022
                "%d/%m/%Y %H:%M:%S",     # 30/12/2022 00:00:00
            ]
            for fmt in date_formats:
                try:
                    fecha = datetime.strptime(fecha, fmt).date()
                    parsed = True
                    break
                except ValueError:
                    continue

            if not parsed:
                logger.warning(f"No se pudo parsear fecha: {fecha}")
                return {
                    "numero_factura": numero_factura,
                    "pdf_content": None,
                    "pdf_found": False
                }

        try:
            # OPTIMIZADO: Usar método con cache de Supabase
            pdf_content = self.drive_service.get_invoice_pdf_optimized(numero_factura, fecha)

            return {
                "numero_factura": numero_factura,
                "pdf_content": pdf_content,
                "pdf_found": pdf_content is not None
            }
        except Exception as e:
            logger.error(f"Error descargando PDF para {numero_factura}: {str(e)}")
            return {
                "numero_factura": numero_factura,
                "pdf_content": None,
                "pdf_found": False
            }

    def _download_invoice_pdfs_parallel(self, records: List[Dict]) -> List[Dict]:
        """
        Descarga archivos PDF de todas las facturas en PARALELO.
        Usa ThreadPoolExecutor para descargas concurrentes.

        OPTIMIZACIÓN v2: Hace bulk query a Supabase primero para obtener
        todos los file_ids en una sola consulta, luego descarga en paralelo
        usando los IDs pre-obtenidos.

        Args:
            records: Lista de registros con numero_factura y fecha.

        Returns:
            List[Dict]: Lista con información de descargas.
        """
        # Preparar lista de facturas para búsqueda
        invoices_to_search = []
        for record in records:
            numero_factura = record.get("numero_factura")
            fecha = record.get("fecha")

            if numero_factura and fecha:
                invoices_to_search.append({
                    "numero_factura": numero_factura,
                    "fecha": fecha
                })

        if not invoices_to_search:
            logger.warning("No hay facturas válidas para buscar PDFs")
            return []

        total_invoices = len(invoices_to_search)
        logger.info(f"Iniciando descarga paralela de {total_invoices} PDFs (max {MAX_PARALLEL_DOWNLOADS} hilos)")
        start_time = datetime.now()

        # OPTIMIZACIÓN: Bulk query a Supabase para obtener todos los file_ids de una vez
        numeros_factura = [inv["numero_factura"] for inv in invoices_to_search]
        logger.info(f"[BULK] Consultando {len(numeros_factura)} file_ids en Supabase...")
        bulk_start = datetime.now()
        file_ids_cache = self.drive_service.get_bulk_file_ids_from_cache(numeros_factura)
        bulk_elapsed = (datetime.now() - bulk_start).total_seconds()
        logger.info(f"[BULK] Bulk query completado en {bulk_elapsed:.2f}s: {len(file_ids_cache)} en cache")

        # Agregar file_id pre-obtenido a cada invoice
        for invoice in invoices_to_search:
            invoice["cached_file_id"] = file_ids_cache.get(invoice["numero_factura"])

        download_results = []

        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
            # Enviar todas las tareas de descarga
            future_to_invoice = {
                executor.submit(self._download_single_invoice_optimized, invoice): invoice
                for invoice in invoices_to_search
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

        logger.info(
            f"Descarga paralela completada en {elapsed:.1f}s: {total} facturas, "
            f"{pdf_found} PDFs encontrados, {total - pdf_found} no encontrados"
        )

        return download_results

    def _download_single_invoice_optimized(self, invoice: Dict) -> Optional[Dict]:
        """
        Descarga el PDF de una factura usando file_id pre-obtenido si disponible.

        OPTIMIZADO: Si ya tenemos el file_id del bulk query, descarga directamente.
        Si no, usa el método tradicional de búsqueda.

        Args:
            invoice: Dict con numero_factura, fecha, y opcionalmente cached_file_id.

        Returns:
            Dict con resultado de descarga o None si hay error.
        """
        numero_factura = invoice.get("numero_factura")
        cached_file_id = invoice.get("cached_file_id")

        if not numero_factura:
            return {
                "numero_factura": "UNKNOWN",
                "pdf_content": None,
                "pdf_found": False
            }

        # Si tenemos file_id pre-obtenido, descargar directamente con retry
        if cached_file_id:
            try:
                pdf_content = self.drive_service.download_file_with_retry(
                    file_id=cached_file_id,
                    file_name=f"{numero_factura}.pdf",
                    max_retries=3
                )
                return {
                    "numero_factura": numero_factura,
                    "pdf_content": pdf_content,
                    "pdf_found": pdf_content is not None
                }
            except Exception as e:
                logger.error(f"Error descargando PDF {numero_factura} con cached_file_id: {e}")
                return {
                    "numero_factura": numero_factura,
                    "pdf_content": None,
                    "pdf_found": False
                }

        # Si no hay cached_file_id, usar método tradicional (fallback)
        return self._download_single_invoice(invoice)

    def _generate_zip_streaming(
        self,
        records: List[Dict],
        excel_content: bytes,
        metadata: Optional[Dict] = None
    ) -> io.BytesIO:
        """
        Genera el ZIP con streaming: descarga y agrega archivos simultáneamente.

        OPTIMIZACIÓN: En lugar de esperar a que todas las descargas terminen,
        crea el ZIP y agrega archivos conforme se van descargando. Esto reduce
        el uso de memoria y el tiempo total de procesamiento.

        Args:
            records: Lista de registros con numero_factura y fecha.
            excel_content: Contenido del Excel de reporte.
            metadata: Metadata del paquete.

        Returns:
            BytesIO: Buffer con contenido del ZIP.
        """
        zip_buffer = io.BytesIO()
        missing_pdfs = []
        pdf_count = 0
        lock = threading.Lock()

        # Preparar lista de facturas
        invoices_to_search = []
        for record in records:
            numero_factura = record.get("numero_factura")
            fecha = record.get("fecha")
            if numero_factura and fecha:
                invoices_to_search.append({
                    "numero_factura": numero_factura,
                    "fecha": fecha
                })

        if not invoices_to_search:
            logger.warning("No hay facturas válidas para generar ZIP")
            # Crear ZIP vacío con solo el Excel
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                excel_filename = self._generate_excel_filename(metadata)
                zip_file.writestr(excel_filename, excel_content)
            zip_buffer.seek(0)
            return zip_buffer

        total_invoices = len(invoices_to_search)
        logger.info(f"[STREAMING] Iniciando generación de ZIP para {total_invoices} facturas")
        start_time = datetime.now()

        # PASO 1: Bulk query a Supabase
        numeros_factura = [inv["numero_factura"] for inv in invoices_to_search]
        logger.info(f"[STREAMING] Consultando {len(numeros_factura)} file_ids en Supabase...")
        bulk_start = datetime.now()
        file_ids_cache = self.drive_service.get_bulk_file_ids_from_cache(numeros_factura)
        bulk_elapsed = (datetime.now() - bulk_start).total_seconds()
        logger.info(f"[STREAMING] Bulk query: {len(file_ids_cache)} en cache ({bulk_elapsed:.2f}s)")

        # Agregar cached_file_id a cada invoice
        for invoice in invoices_to_search:
            invoice["cached_file_id"] = file_ids_cache.get(invoice["numero_factura"])

        # PASO 2: Crear ZIP y agregar archivos conforme se descargan
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Agregar Excel primero
            excel_filename = self._generate_excel_filename(metadata)
            zip_file.writestr(excel_filename, excel_content)
            logger.debug(f"[STREAMING] Excel agregado: {excel_filename}")

            def download_and_add_to_zip(invoice: Dict) -> Optional[str]:
                """Descarga un PDF y lo agrega al ZIP. Retorna numero_factura si falta."""
                nonlocal pdf_count
                numero_factura = invoice.get("numero_factura")
                cached_file_id = invoice.get("cached_file_id")

                # Pequeño delay para evitar saturar Google Drive API
                time.sleep(DOWNLOAD_DELAY_SECONDS)

                pdf_content = None

                if cached_file_id:
                    # Descargar con retry usando file_id pre-obtenido
                    pdf_content = self.drive_service.download_file_with_retry(
                        file_id=cached_file_id,
                        file_name=f"{numero_factura}.pdf",
                        max_retries=3
                    )
                else:
                    # Fallback: usar método tradicional
                    result = self._download_single_invoice(invoice)
                    if result and result.get("pdf_found"):
                        pdf_content = result.get("pdf_content")

                if pdf_content:
                    # Agregar al ZIP (thread-safe)
                    with lock:
                        pdf_filename = f"PDFs/{numero_factura}.pdf"
                        zip_file.writestr(pdf_filename, pdf_content)
                        pdf_count += 1
                    return None  # Éxito
                else:
                    return numero_factura  # Faltante

            # Descargar en paralelo y agregar al ZIP
            completed = 0
            with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
                future_to_invoice = {
                    executor.submit(download_and_add_to_zip, inv): inv
                    for inv in invoices_to_search
                }

                for future in as_completed(future_to_invoice):
                    completed += 1
                    try:
                        missing_factura = future.result()
                        if missing_factura:
                            missing_pdfs.append(missing_factura)
                    except Exception as e:
                        inv = future_to_invoice[future]
                        logger.error(f"[STREAMING] Error procesando {inv.get('numero_factura')}: {e}")
                        missing_pdfs.append(inv.get("numero_factura", "UNKNOWN"))

                    # Log progreso cada 10 o al final
                    if completed % 10 == 0 or completed == total_invoices:
                        logger.info(f"[STREAMING] Progreso: {completed}/{total_invoices} ({pdf_count} PDFs agregados)")

            # Agregar archivo de PDFs faltantes si hay
            if missing_pdfs:
                missing_content = "PDFs no encontrados en Google Drive:\n\n"
                missing_content += "\n".join(f"- {factura}.pdf" for factura in missing_pdfs)
                missing_content += f"\n\nTotal: {len(missing_pdfs)} archivos no encontrados"
                zip_file.writestr("PDFs_no_encontrados.txt", missing_content)

        zip_buffer.seek(0)

        # Estadísticas finales
        elapsed = (datetime.now() - start_time).total_seconds()
        zip_size_mb = len(zip_buffer.getvalue()) / (1024 * 1024)
        logger.info(
            f"[STREAMING] ZIP completado en {elapsed:.1f}s: "
            f"{pdf_count} PDFs, {len(missing_pdfs)} faltantes, {zip_size_mb:.2f} MB"
        )

        return zip_buffer

    def _download_invoice_pdfs(self, records: List[Dict]) -> List[Dict]:
        """
        Descarga archivos PDF de todas las facturas (versión secuencial).
        Mantenida para compatibilidad. Usar _download_invoice_pdfs_parallel para mejor rendimiento.

        Args:
            records: Lista de registros con numero_factura y fecha.

        Returns:
            List[Dict]: Lista con información de descargas.
        """
        # Preparar lista de facturas para búsqueda
        invoices_to_search = []
        for record in records:
            numero_factura = record.get("numero_factura")
            fecha = record.get("fecha")

            if numero_factura and fecha:
                invoices_to_search.append({
                    "numero_factura": numero_factura,
                    "fecha": fecha
                })

        if not invoices_to_search:
            logger.warning("No hay facturas válidas para buscar PDFs")
            return []

        # Usar batch_get_invoice_pdfs del drive service (secuencial)
        download_results = self.drive_service.batch_get_invoice_pdfs(invoices_to_search)

        # Estadísticas de descarga
        total = len(download_results)
        pdf_found = sum(1 for item in download_results if item["pdf_found"])

        logger.info(
            f"Descarga completada: {total} facturas, "
            f"{pdf_found} PDFs encontrados, "
            f"{total - pdf_found} no encontrados"
        )

        return download_results

    def _create_zip_package(
        self,
        records: List[Dict],
        pdf_downloads: List[Dict],
        excel_content: bytes,
        metadata: Optional[Dict] = None
    ) -> io.BytesIO:
        """
        Crea el archivo ZIP con todos los archivos.

        Estructura del ZIP:
        /
        ├── Reporte_Filtrado_CO_YYYYMMDD.xlsx
        └── PDFs/
            ├── FE12345.pdf
            ├── ITGC846.pdf
            └── ...

        Args:
            records: Lista de registros.
            pdf_downloads: Resultado de descargas de PDFs.
            excel_content: Contenido del Excel de reporte.
            metadata: Metadata del paquete.

        Returns:
            BytesIO: Buffer con contenido del ZIP.
        """
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Agregar reporte Excel
            excel_filename = self._generate_excel_filename(metadata)
            zip_file.writestr(excel_filename, excel_content)
            logger.debug(f"Agregado al ZIP: {excel_filename}")

            # 2. Agregar PDFs
            pdf_count = 0
            missing_pdfs = []

            for item in pdf_downloads:
                numero_factura = item.get("numero_factura", "UNKNOWN")
                if item["pdf_content"]:
                    pdf_filename = f"PDFs/{numero_factura}.pdf"
                    zip_file.writestr(pdf_filename, item["pdf_content"])
                    pdf_count += 1
                else:
                    missing_pdfs.append(numero_factura)

            logger.debug(f"Agregados {pdf_count} archivos PDF al ZIP")

            # 3. Agregar archivo de PDFs faltantes (si hay)
            if missing_pdfs:
                missing_content = "PDFs no encontrados en Google Drive:\n\n"
                missing_content += "\n".join(f"- {factura}.pdf" for factura in missing_pdfs)
                missing_content += f"\n\nTotal: {len(missing_pdfs)} archivos no encontrados"
                zip_file.writestr("PDFs_no_encontrados.txt", missing_content)
                logger.info(f"{len(missing_pdfs)} PDFs no encontrados")

        zip_buffer.seek(0)

        # Estadísticas finales
        zip_size_mb = len(zip_buffer.getvalue()) / (1024 * 1024)
        logger.info(
            f"ZIP creado: {pdf_count} PDFs, "
            f"{len(missing_pdfs)} faltantes, "
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
            if metadata.get("nit"):
                nit = metadata["nit"].replace(".", "").replace("-", "")
                return f"Reporte_CO_{nit}_{timestamp}.xlsx"
            elif metadata.get("operaciones"):
                ops = metadata["operaciones"]
                if isinstance(ops, list) and len(ops) > 0:
                    # Usar primera operación como identificador
                    op = ops[0].replace(":", "-").replace("/", "-")
                    suffix = f"_y_{len(ops)-1}_mas" if len(ops) > 1 else ""
                    return f"Reporte_CO_{op}{suffix}_{timestamp}.xlsx"

        return f"Reporte_Filtrado_CO_{timestamp}.xlsx"

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
            if metadata.get("nit"):
                nit = metadata["nit"].replace(".", "").replace("-", "")
                return f"Facturacion_CO_{nit}_{timestamp}.zip"
            elif metadata.get("operaciones"):
                ops = metadata["operaciones"]
                if isinstance(ops, list) and len(ops) > 0:
                    op = ops[0].replace(":", "-").replace("/", "-")
                    return f"Facturacion_CO_{op}_{timestamp}.zip"

        return f"Facturacion_CO_{timestamp}.zip"


# Singleton instance
_zip_service_co_instance: Optional[ZipGeneratorServiceCO] = None


def get_zip_service_co() -> ZipGeneratorServiceCO:
    """
    Obtiene la instancia singleton del servicio de generación de ZIP CO.

    Returns:
        ZipGeneratorServiceCO: Instancia del servicio.
    """
    global _zip_service_co_instance
    if _zip_service_co_instance is None:
        _zip_service_co_instance = ZipGeneratorServiceCO()
    return _zip_service_co_instance
