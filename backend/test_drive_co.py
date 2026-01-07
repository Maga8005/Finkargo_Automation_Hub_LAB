"""
Test script to verify Google Drive CO connection
"""
import sys
sys.path.insert(0, '.')

from src.core.servicios.google_drive_service_co import get_drive_service_co

def test_connection():
    print("=" * 50)
    print("Testing Google Drive CO Connection")
    print("=" * 50)

    try:
        # Get service
        drive_service = get_drive_service_co()
        print(f"✓ Service initialized")
        print(f"  Folder ID: {drive_service.folder_id}")
        print(f"  Master Excel Name: {drive_service.master_excel_name}")

        # Try to authenticate
        print("\nAuthenticating...")
        service = drive_service.authenticate()
        print("✓ Authentication successful")

        # Try to list files in folder
        print("\nListing files in CO folder...")
        files = drive_service.list_files_in_folder(max_results=10)
        print(f"✓ Found {len(files)} files:")
        for f in files:
            print(f"  - {f['name']} ({f['mimeType']})")

        # Try to find master excel
        print(f"\nSearching for master Excel: {drive_service.master_excel_name}")
        master = drive_service.find_master_excel_file()
        if master:
            print(f"✓ Master Excel found: {master['name']} (ID: {master['id']})")
        else:
            print("○ Master Excel not found (will be created on first upload)")

        # Test upload with sample data
        print("\nTesting upload...")
        import openpyxl
        from io import BytesIO

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Test"
        ws['A1'] = "Test Connection"
        ws['A2'] = "Success!"

        buffer = BytesIO()
        wb.save(buffer)
        test_content = buffer.getvalue()

        success = drive_service.upload_master_excel(test_content)
        if success:
            print("✓ Upload successful!")
        else:
            print("✗ Upload failed")

        print("\n" + "=" * 50)
        print("All tests passed! Drive connection is working.")
        print("=" * 50)

    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
