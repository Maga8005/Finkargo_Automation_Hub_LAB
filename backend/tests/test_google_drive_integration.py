"""
Test Google Drive Integration

Script de testing para verificar la integración con Google Drive.
Valida autenticación, acceso a carpetas, búsqueda y descarga de archivos.

Usage:
    python -m tests.test_google_drive_integration
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables before importing services
os.environ["GOOGLE_DRIVE_CREDENTIALS_PATH"] = "./credentials/drive-service-account.json"
os.environ["GOOGLE_DRIVE_FOLDER_ID"] = "1A5fxY8LnJYs0QTO3aYHD10IuRIgebx46"

from src.core.servicios.google_drive_service import GoogleDriveService


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}[ERROR] {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}[WARNING] {text}{Colors.RESET}")


def check_authentication():
    """Test 1: Authentication with Google Drive."""
    print_header("TEST 1: Autenticación con Google Drive")

    try:
        service = GoogleDriveService()
        drive = service.authenticate()
        print_success("Autenticación exitosa")
        print_info(f"Credenciales: {service.credentials_path}")
        print_info(f"Folder ID: {service.folder_id}")
        return service
    except FileNotFoundError as e:
        print_error(f"Archivo de credenciales no encontrado: {e}")
        print_warning("Asegúrate de que el archivo drive-service-account.json existe en ./credentials/")
        return None
    except Exception as e:
        print_error(f"Error de autenticación: {e}")
        return None


def check_root_folder_access(service: GoogleDriveService):
    """Test 2: Access to root folder."""
    print_header("TEST 2: Acceso a Carpeta Raíz de Facturación MX")

    try:
        drive = service.authenticate()

        # List files in root folder
        query = f"'{service.folder_id}' in parents and trashed = false"
        results = drive.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            pageSize=20
        ).execute()

        files = results.get("files", [])

        if not files:
            print_warning("La carpeta está vacía o no hay permisos de lectura")
            print_warning(f"Verifica que la Service Account tenga acceso al Drive ID: {service.folder_id}")
            return False

        print_success(f"Acceso exitoso a la carpeta raíz")
        print_info(f"Archivos/Carpetas encontrados: {len(files)}")

        for file in files:
            file_type = "[DIR]" if file["mimeType"] == "application/vnd.google-apps.folder" else "[FILE]"
            print(f"  {file_type}: {file['name']} (ID: {file['id']})")

        # Check for 2025 folder
        year_folder = next((f for f in files if f["name"] == "2025"), None)
        if year_folder:
            print_success("Carpeta '2025' encontrada")
            return year_folder["id"]
        else:
            print_warning("Carpeta '2025' NO encontrada en la raíz")
            return None

    except Exception as e:
        print_error(f"Error al acceder a carpeta raíz: {e}")
        return None


def check_year_folder_navigation(service: GoogleDriveService, year_folder_id: str):
    """Test 3: Navigate into 2025 folder."""
    print_header("TEST 3: Navegación a Carpetas de Meses (2025)")

    try:
        drive = service.authenticate()

        # List month folders
        query = f"'{year_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = drive.files().list(
            q=query,
            fields="files(id, name)",
            pageSize=20
        ).execute()

        folders = results.get("files", [])

        if not folders:
            print_warning("No se encontraron carpetas de meses en 2025")
            return None

        print_success(f"Carpetas de meses encontradas: {len(folders)}")

        for folder in folders:
            print(f"  [DIR] {folder['name']} (ID: {folder['id']})")

        # Return first month folder for next test
        return folders[0] if folders else None

    except Exception as e:
        print_error(f"Error al navegar carpetas de meses: {e}")
        return None


def check_month_folder_files(service: GoogleDriveService, month_folder):
    """Test 4: List files in a month folder."""
    print_header(f"TEST 4: Archivos en Carpeta '{month_folder['name']}'")

    try:
        drive = service.authenticate()

        # List files in month folder
        query = f"'{month_folder['id']}' in parents and trashed = false"
        results = drive.files().list(
            q=query,
            fields="files(id, name, mimeType, size)",
            pageSize=10
        ).execute()

        files = results.get("files", [])

        if not files:
            print_warning(f"No se encontraron archivos en '{month_folder['name']}'")
            return None

        print_success(f"Archivos encontrados: {len(files)}")

        pdf_files = [f for f in files if f["name"].endswith(".pdf")]
        xml_files = [f for f in files if f["name"].endswith(".xml")]

        print_info(f"PDFs: {len(pdf_files)}")
        print_info(f"XMLs: {len(xml_files)}")

        # Show first few files
        print("\nPrimeros archivos:")
        for file in files[:5]:
            size_kb = int(file.get("size", 0)) / 1024 if "size" in file else 0
            print(f"  [FILE] {file['name']} ({size_kb:.1f} KB)")

        return files[0] if files else None

    except Exception as e:
        print_error(f"Error al listar archivos: {e}")
        return None


def check_search_by_uuid(service: GoogleDriveService):
    """Test 5: Search file by UUID."""
    print_header("TEST 5: Búsqueda de Archivo por UUID")

    # Use a test UUID (from the user's example)
    test_uuid = "029a7980-dd92-4e9f-a7f3-f3c5d6e37767"
    test_date = datetime(2025, 1, 30)  # Assuming January 2025

    print_info(f"Buscando UUID: {test_uuid}")
    print_info(f"Fecha: {test_date.strftime('%Y-%m-%d')}")

    try:
        # Search for PDF
        pdf_file = service.search_file_by_uuid(test_uuid, test_date, "pdf")
        if pdf_file:
            print_success(f"PDF encontrado: {pdf_file['name']}")
            print_info(f"  ID: {pdf_file['id']}")
            print_info(f"  Tamaño: {int(pdf_file.get('size', 0)) / 1024:.1f} KB")
        else:
            print_warning("PDF NO encontrado")
            print_info("Posibles razones:")
            print_info("  - El UUID no existe en esa fecha")
            print_info("  - El archivo está en un mes diferente")
            print_info("  - La Service Account no tiene permisos")

        # Search for XML
        xml_file = service.search_file_by_uuid(test_uuid, test_date, "xml")
        if xml_file:
            print_success(f"XML encontrado: {xml_file['name']}")
            print_info(f"  ID: {xml_file['id']}")
            print_info(f"  Tamaño: {int(xml_file.get('size', 0)) / 1024:.1f} KB")
        else:
            print_warning("XML NO encontrado")

        return pdf_file, xml_file

    except Exception as e:
        print_error(f"Error al buscar por UUID: {e}")
        return None, None


def check_download_file(service: GoogleDriveService, file_info):
    """Test 6: Download a file."""
    print_header("TEST 6: Descarga de Archivo")

    if not file_info:
        print_warning("No hay archivo para descargar (skipping test)")
        return

    print_info(f"Descargando: {file_info['name']}")

    try:
        content = service.download_file(file_info['id'])

        if content:
            print_success("Descarga exitosa")
            print_info(f"Tamaño descargado: {len(content) / 1024:.1f} KB")

            # Verify it's a valid file
            if file_info['name'].endswith('.pdf'):
                if content[:4] == b'%PDF':
                    print_success("Archivo PDF válido (magic number verificado)")
                else:
                    print_warning("El contenido NO parece ser un PDF válido")

            elif file_info['name'].endswith('.xml'):
                if content[:5] == b'<?xml' or content[:5] == b'<cfdi':
                    print_success("Archivo XML válido (header verificado)")
                else:
                    print_warning("El contenido NO parece ser un XML válido")

            return True
        else:
            print_error("La descarga retornó contenido vacío")
            return False

    except Exception as e:
        print_error(f"Error al descargar archivo: {e}")
        return False


def check_batch_download(service: GoogleDriveService):
    """Test 7: Batch download multiple invoices."""
    print_header("TEST 7: Descarga en Lote")

    # Test with sample invoice data
    test_invoices = [
        {
            "uuid": "029a7980-dd92-4e9f-a7f3-f3c5d6e37767",
            "fecha_emision": datetime(2025, 1, 30)
        }
    ]

    print_info(f"Intentando descargar {len(test_invoices)} facturas")

    try:
        results = service.batch_get_invoice_files(test_invoices)

        print_success(f"Proceso completado")

        for result in results:
            uuid = result['uuid'][:8] + "..."
            pdf_status = "YES" if result['pdf_found'] else "NO"
            xml_status = "YES" if result['xml_found'] else "NO"

            print(f"  UUID {uuid}: PDF {pdf_status} | XML {xml_status}")

        # Statistics
        total = len(results)
        pdfs_found = sum(1 for r in results if r['pdf_found'])
        xmls_found = sum(1 for r in results if r['xml_found'])

        print_info(f"\nEstadísticas:")
        print_info(f"  Total facturas: {total}")
        print_info(f"  PDFs encontrados: {pdfs_found}/{total}")
        print_info(f"  XMLs encontrados: {xmls_found}/{total}")

        return results

    except Exception as e:
        print_error(f"Error en descarga en lote: {e}")
        return None


def run_all_tests():
    """Run all integration tests."""
    print_header("GOOGLE DRIVE INTEGRATION TESTS - Facturación MX")
    print_info("Verificando integración con Google Drive")
    print_info(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Test 1: Authentication
    service = check_authentication()
    if not service:
        print_error("\n[ABORTED] TESTS ABORTADOS: No se pudo autenticar con Google Drive")
        return

    # Test 2: Root folder access
    year_folder_id = check_root_folder_access(service)
    if not year_folder_id:
        print_error("\n[ABORTED] TESTS ABORTADOS: No se pudo acceder a la carpeta raíz")
        print_warning("\n[ACTION REQUIRED]:")
        print_warning("   Compartir el Drive con: drive-and-sheets-access-sa@api-producto-476819.iam.gserviceaccount.com")
        print_warning("   Nivel de acceso: Editor o Lector")
        return

    # Test 3: Year folder navigation
    month_folder = check_year_folder_navigation(service, year_folder_id)
    if not month_folder:
        print_warning("\n[WARNING] No se encontraron carpetas de meses, continuando con otros tests...")

    # Test 4: Month folder files
    if month_folder:
        sample_file = check_month_folder_files(service, month_folder)
    else:
        sample_file = None

    # Test 5: Search by UUID
    pdf_file, xml_file = check_search_by_uuid(service)

    # Test 6: Download file
    if pdf_file:
        check_download_file(service, pdf_file)
    elif sample_file:
        check_download_file(service, sample_file)

    # Test 7: Batch download
    check_batch_download(service)

    # Final summary
    print_header("RESUMEN DE TESTS")
    print_success("Tests de integracion completados")
    print_info("\nProximos pasos:")
    print_info("  1. Verificar que todos los tests pasaron")
    print_info("  2. Si hay errores de permisos, compartir Drive con Service Account")
    print_info("  3. Probar con UUIDs reales del Excel de facturacion")
    print_info("  4. Integrar con endpoint /generate-zip en el backend")


if __name__ == "__main__":
    run_all_tests()
