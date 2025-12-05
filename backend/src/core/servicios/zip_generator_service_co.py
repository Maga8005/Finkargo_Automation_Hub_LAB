"""
ZIP Generator Service for Colombia (CO)

Servicio para generar paquetes ZIP con facturas PDF y reporte Excel filtrado.
Orquesta la descarga de archivos desde Google Drive y la generación del paquete.

Optimizado con:
- Descargas paralelas usando ThreadPoolExecutor
- Pre-caché de carpetas antes de las descargas
- Compresión ZIP en memoria (streaming)
"""

import io
import logging
import zipfile
from typing import List, Dict, Optional
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed

from .google_drive_service_co import get_drive_service_co

logger = logging.getLogger(__name__)

# Número máximo de descargas paralelas
# Con cache de archivos, podemos usar 8 hilos ya que las búsquedas son instantáneas
MAX_PARALLEL_DOWNLOADS = 8


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

            # 2. Descargar PDFs de Google Drive (EN PARALELO)
            logger.info("Descargando PDFs desde Google Drive (paralelo)...")
            pdf_downloads = self._download_invoice_pdfs_parallel(records)

            # 3. Crear archivo ZIP (en memoria)
            logger.info("Creando archivo ZIP...")
            zip_buffer = self._create_zip_package(
                records,
                pdf_downloads,
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
            try:
                fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
            except ValueError:
                try:
                    fecha = datetime.strptime(fecha, "%d/%m/%Y").date()
                except ValueError:
                    logger.warning(f"No se pudo parsear fecha: {fecha}")
                    return {
                        "numero_factura": numero_factura,
                        "pdf_content": None,
                        "pdf_found": False
                    }

        try:
            # Descargar PDF
            pdf_content = self.drive_service.get_invoice_pdf(numero_factura, fecha)

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

        download_results = []

        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
            # Enviar todas las tareas de descarga
            future_to_invoice = {
                executor.submit(self._download_single_invoice, invoice): invoice
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
