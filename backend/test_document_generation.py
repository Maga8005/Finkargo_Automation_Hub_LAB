"""
Test script for document generation
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.servicios.document_service import DocumentService
from datetime import datetime

# Mock contract data
mock_contract_data = {
    'id': 'test-uuid-123',
    'contract_id': 'ACT-2025-001',
    'generated_at': datetime.now().isoformat(),
    'data_snapshot': {
        'nit': '900123456-1',
        'nombre_importador': 'IMPORTADORA TEST S.A.S',
        'representante_legal': 'Juan Carlos Pérez',
        'cedula_representante': '123456789',
        'ciudad_domicilio': 'Bogotá D.C.',
        'cupo_plataforma': 50000000,  # 50 million pesos
        'contract_id': 'ACT-2025-001',
        'generation_date': datetime.now().strftime('%Y-%m-%d'),
        'email': 'info@importadoratest.com'
    }
}

def test_document_generation():
    """Test DOCX generation"""
    print("=" * 60)
    print("TESTING DOCUMENT GENERATION")
    print("=" * 60)

    try:
        # Initialize service
        doc_service = DocumentService()

        # Generate document
        print("\n1. Generating DOCX document...")
        docx_bytes = doc_service.generate_contract_document(mock_contract_data)
        print(f"   [OK] Generated DOCX: {len(docx_bytes)} bytes")

        # Save test file
        output_path = "test_contract_output.docx"
        with open(output_path, 'wb') as f:
            f.write(docx_bytes)
        print(f"   [OK] Saved to: {output_path}")

        # Try PDF conversion
        print("\n2. Testing PDF conversion...")
        try:
            pdf_bytes = doc_service.convert_to_pdf(docx_bytes)
            print(f"   [OK] Generated PDF: {len(pdf_bytes)} bytes")

            pdf_output_path = "test_contract_output.pdf"
            with open(pdf_output_path, 'wb') as f:
                f.write(pdf_bytes)
            print(f"   [OK] Saved to: {pdf_output_path}")
        except Exception as e:
            print(f"   [WARN] PDF conversion failed (requires MS Word): {e}")
            print("   [INFO] DOCX generation successful, PDF optional on Windows")

        print("\n" + "=" * 60)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nCheck the generated files:")
        print(f"  - {output_path}")
        print(f"  - test_contract_output.pdf (if PDF conversion succeeded)")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_document_generation()
    sys.exit(0 if success else 1)
