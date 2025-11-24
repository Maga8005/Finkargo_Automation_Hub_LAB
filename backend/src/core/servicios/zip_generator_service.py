"""
ZIP Generator Service

Servicio para generar paquetes ZIP con facturas (PDF, XML) y reporte Excel.
Orquesta la descarga de archivos desde Google Drive y la generación del reporte.
"""

import io
import logging
import zipfile
from typing import List, Dict, Optional
from datetime import datetime

from .google_drive_service import get_drive_service
from .excel_report_service import get_excel_service

logger = logging.getLogger(__name__)


class ZipGeneratorService:
    """
    Servicio para generar paquetes ZIP de facturación.

    Funcionalidad:
    - Descarga PDFs y XMLs desde Google Drive
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
        metadata: Optional[Dict] = None
    ) -> io.BytesIO:
        """
        Genera un paquete ZIP con facturas y reporte Excel.

        Args:
            invoices: Lista de facturas con datos completos.
                Cada factura debe tener: uuid, fecha_emision, codigo_operacion, etc.
            metadata: Metadata del paquete (código operación, RFC, fechas, etc.).

        Returns:
            BytesIO: Contenido del archivo ZIP.

        Raises:
            Exception: Si falla la generación del ZIP.
        """
        try:
            logger.info(f"Iniciando generación de paquete ZIP para {len(invoices)} facturas")

            # 1. Descargar archivos de Google Drive
            logger.info("Descargando archivos desde Google Drive...")
            file_downloads = self._download_invoice_files(invoices)

            # 2. Generar reporte Excel
            logger.info("Generando reporte Excel...")
            file_status = {item["uuid"]: {"pdf_found": item["pdf_found"], "xml_found": item["xml_found"]} for item in file_downloads}
            excel_buffer = self.excel_service.generate_invoice_report(
                invoices,
                file_status,
                metadata
            )

            # 3. Crear archivo ZIP
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

    def _download_invoice_files(self, invoices: List[Dict]) -> List[Dict]:
        """
        Descarga archivos PDF y XML de todas las facturas.

        Args:
            invoices: Lista de facturas.

        Returns:
            List[Dict]: Lista con información de descargas.
        """
        download_results = []

        for invoice in invoices:
            uuid = invoice.get("uuid")
            fecha_emision = invoice.get("fecha_emision")

            if not uuid or not fecha_emision:
                logger.warning(f"Factura sin UUID o fecha: {invoice}")
                continue

            # Convertir fecha a datetime si es string
            if isinstance(fecha_emision, str):
                try:
                    fecha_emision = datetime.fromisoformat(fecha_emision.replace('Z', '+00:00'))
                except Exception as e:
                    logger.error(f"Error al parsear fecha {fecha_emision}: {str(e)}")
                    continue

            # Descargar archivos
            pdf_content, xml_content = self.drive_service.get_invoice_files(uuid, fecha_emision)

            download_results.append({
                "uuid": uuid,
                "codigo_operacion": invoice.get("codigo_operacion", ""),
                "pdf_content": pdf_content,
                "xml_content": xml_content,
                "pdf_found": pdf_content is not None,
                "xml_found": xml_content is not None,
            })

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
