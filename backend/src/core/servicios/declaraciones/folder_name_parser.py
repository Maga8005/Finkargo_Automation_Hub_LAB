"""
Folder Name Parser Utility Module

This module provides utility functions for parsing dates, amounts, and customer names
from Google Drive folder and file names in the Declaraciones matching system.

Expected folder structure: FINKARGO DCS/{CUSTOMER_NAME}/{DATE}/{AMOUNT}.pdf
Example: FINKARGO DCS/BIIRTUALSCORE SAS/12-09-2025/11.081,50.pdf
"""

from datetime import datetime
from typing import Optional
import re


# Spanish month names mapping
SPANISH_MONTH_NAMES = {
    # Full month names
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
    # Abbreviated month names
    'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4,
    'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
    'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dic': 12
}


def parse_month_from_folder_name(folder_name: str) -> Optional[int]:
    """
    Parse Spanish month name from folder name.

    Supported formats:
    - Full month names: "Enero", "Septiembre", "Diciembre"
    - Abbreviated: "Ene", "Sep", "Sept", "Dic"
    - Case-insensitive

    Args:
        folder_name: Folder name that may contain a Spanish month name

    Returns:
        Month number (1-12) if parsing succeeds, None otherwise

    Examples:
        >>> parse_month_from_folder_name("Septiembre")
        9

        >>> parse_month_from_folder_name("sept")
        9

        >>> parse_month_from_folder_name("InvalidMonth")
        None
    """
    if not folder_name:
        return None

    # Normalize folder name for case-insensitive matching
    folder_lower = folder_name.lower().strip()

    # Try to match full month name or abbreviation
    for month_name, month_num in SPANISH_MONTH_NAMES.items():
        if month_name in folder_lower:
            print(f"INFO [FolderNameParser]: Parsed month name '{folder_name}' as month {month_num}")
            return month_num

    return None


def parse_date_from_folder_name(folder_name: str) -> Optional[datetime]:
    """
    Parse date from folder name supporting multiple formats.

    Supported formats:
    - DD-MM-YYYY (e.g., "12-09-2025")
    - DD/MM/YYYY (e.g., "12/09/2025")
    - YYYY-MM-DD (e.g., "2025-09-12")
    - MM-DD-YYYY (e.g., "09-12-2025")

    Args:
        folder_name: Folder name that may contain a date

    Returns:
        datetime object if parsing succeeds, None otherwise

    Examples:
        >>> parse_date_from_folder_name("12-09-2025")
        datetime(2025, 9, 12, 0, 0)

        >>> parse_date_from_folder_name("not-a-date")
        None
    """
    if not folder_name:
        print(f"WARNING [FolderNameParser]: Empty folder name provided for date parsing")
        return None

    # Clean folder name
    folder_name = folder_name.strip()

    # List of date format patterns to try
    date_patterns = [
        (r'(\d{2})-(\d{2})-(\d{4})', '%d-%m-%Y'),  # DD-MM-YYYY
        (r'(\d{2})/(\d{2})/(\d{4})', '%d/%m/%Y'),  # DD/MM/YYYY
        (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),  # YYYY-MM-DD
        (r'(\d{2})-(\d{2})-(\d{4})', '%m-%d-%Y'),  # MM-DD-YYYY (fallback)
    ]

    for pattern, date_format in date_patterns:
        match = re.search(pattern, folder_name)
        if match:
            try:
                parsed_date = datetime.strptime(folder_name, date_format)
                print(f"INFO [FolderNameParser]: Successfully parsed date '{folder_name}' as {parsed_date.date()}")
                return parsed_date
            except ValueError:
                # Invalid date (e.g., 32-13-2025), try next pattern
                continue

    # Try parsing as month name (fallback)
    # This returns a month number, but we need a full date. We'll use the 1st day of the current year
    month_num = parse_month_from_folder_name(folder_name)
    if month_num:
        # Use first day of the month, current year as default
        current_year = datetime.now().year
        try:
            parsed_date = datetime(current_year, month_num, 1)
            print(f"INFO [FolderNameParser]: Parsed month name '{folder_name}' as {parsed_date.date()} (using year {current_year})")
            return parsed_date
        except ValueError:
            pass

    print(f"WARNING [FolderNameParser]: Could not parse date from folder name '{folder_name}'")
    return None


def parse_amount_from_filename(filename: str) -> Optional[float]:
    """
    Parse amount from PDF filename supporting multiple formats.

    Supported formats:
    - European: "11.081,50" (thousands separator: dot, decimal: comma)
    - US: "11,081.50" (thousands separator: comma, decimal: dot)
    - No separators: "11081.50"
    - With currency symbols: "$11,081.50", "€11.081,50"

    Args:
        filename: PDF filename that may contain an amount

    Returns:
        float amount if parsing succeeds, None otherwise

    Examples:
        >>> parse_amount_from_filename("11.081,50.pdf")
        11081.5

        >>> parse_amount_from_filename("$11,081.50.pdf")
        11081.5

        >>> parse_amount_from_filename("no-amount.pdf")
        None
    """
    if not filename:
        print(f"WARNING [FolderNameParser]: Empty filename provided for amount parsing")
        return None

    # Remove file extension
    filename = filename.replace('.pdf', '').replace('.PDF', '')

    # Try European format: 11.081,50 or 11081,50
    # Pattern: optional digits with dots as thousands sep, followed by comma and 2 decimal digits
    european_pattern = r'[\$€£]?\s*(\d{1,3}(?:\.\d{3})*,\d{2})'
    european_match = re.search(european_pattern, filename)
    if european_match:
        amount_str = european_match.group(1)
        # Remove thousands separator (dot) and replace comma with dot for decimal
        amount_str = amount_str.replace('.', '').replace(',', '.')
        try:
            amount = float(amount_str)
            print(f"INFO [FolderNameParser]: Parsed European format amount '{european_match.group(1)}' as {amount}")
            return amount
        except ValueError:
            pass

    # Try US format: 11,081.50 or 11081.50
    # Pattern: optional digits with commas as thousands sep, followed by dot and decimal digits
    us_pattern = r'[\$€£]?\s*(\d{1,3}(?:,\d{3})*\.\d{2,})'
    us_match = re.search(us_pattern, filename)
    if us_match:
        amount_str = us_match.group(1)
        # Remove thousands separator (comma)
        amount_str = amount_str.replace(',', '')
        try:
            amount = float(amount_str)
            print(f"INFO [FolderNameParser]: Parsed US format amount '{us_match.group(1)}' as {amount}")
            return amount
        except ValueError:
            pass

    # Try simple decimal format: 11081.50 or 11081,50
    simple_pattern = r'(\d+[.,]\d{2,})'
    simple_match = re.search(simple_pattern, filename)
    if simple_match:
        amount_str = simple_match.group(1).replace(',', '.')
        try:
            amount = float(amount_str)
            print(f"INFO [FolderNameParser]: Parsed simple format amount '{simple_match.group(1)}' as {amount}")
            return amount
        except ValueError:
            pass

    print(f"WARNING [FolderNameParser]: Could not parse amount from filename '{filename}'")
    return None


def normalize_customer_folder_name(folder_name: str) -> str:
    """
    Normalize customer folder name for fuzzy matching.

    Normalization steps:
    1. Convert to uppercase
    2. Remove legal entity suffixes: "SA", "S.A.", "SAS", "S.A.S", "LTDA", "S.A.C.", etc.
    3. Remove special characters (keep alphanumeric and spaces)
    4. Trim and normalize whitespace

    Args:
        folder_name: Raw customer folder name from Drive

    Returns:
        Normalized customer name for matching

    Examples:
        >>> normalize_customer_folder_name("BIIRTUALSCORE SAS")
        "BIIRTUALSCORE"

        >>> normalize_customer_folder_name("Company Name S.A.")
        "COMPANY NAME"

        >>> normalize_customer_folder_name("Company-Name@123")
        "COMPANY NAME 123"
    """
    if not folder_name:
        return ""

    # Convert to uppercase
    normalized = folder_name.upper()

    # Remove legal entity suffixes (word boundaries ensure we don't remove partial matches)
    legal_suffixes = [
        r'\bS\.A\.S\.?\b',  # S.A.S or S.A.S.
        r'\bS\.A\.C\.?\b',  # S.A.C or S.A.C.
        r'\bS\.A\.?\b',     # S.A or S.A.
        r'\bSAS\b',         # SAS
        r'\bSAC\b',         # SAC
        r'\bS\.L\.?\b',     # S.L or S.L.
        r'\bLTDA\.?\b',     # LTDA or LTDA.
        r'\bLTD\.?\b',      # LTD or LTD.
        r'\bINC\.?\b',      # INC or INC.
        r'\bCORP\.?\b',     # CORP or CORP.
        r'\bLLC\b',         # LLC
        r'\bSA\b',          # SA (standalone)
    ]

    for suffix_pattern in legal_suffixes:
        normalized = re.sub(suffix_pattern, '', normalized)

    # Remove special characters (keep letters, numbers, spaces)
    normalized = re.sub(r'[^A-Z0-9\s]', ' ', normalized)

    # Normalize whitespace (replace multiple spaces with single space)
    normalized = re.sub(r'\s+', ' ', normalized)

    # Trim
    normalized = normalized.strip()

    print(f"INFO [FolderNameParser]: Normalized '{folder_name}' to '{normalized}'")
    return normalized
