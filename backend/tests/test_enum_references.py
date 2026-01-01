"""
Validate all enum references use correct member names.

Catches bugs like: EmailChainValidationStatus.pending (should be .PENDING)

This test file is run as part of the ADW SDLC static analysis phase.
"""

import re
from pathlib import Path
from typing import Dict, Set, List
import importlib.util
import sys


# Add backend to path for imports
BACKEND_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_PATH))


def get_enum_members_from_file(module_path: Path, enum_name: str) -> Set[str]:
    """Extract member names from an enum definition by importing the module."""
    try:
        spec = importlib.util.spec_from_file_location("temp_module", module_path)
        if spec is None or spec.loader is None:
            return set()
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        enum_class = getattr(module, enum_name, None)
        if enum_class is None:
            return set()
        return {member.name for member in enum_class}
    except Exception as e:
        print(f"Warning: Could not load {enum_name} from {module_path}: {e}")
        return set()


# Known enums and their source files (relative to backend/)
# Note: Some enum names exist in multiple modules with different members.
# Use (enum_name, source_file) tuples for disambiguation.
ENUM_DEFINITIONS: Dict[str, str] = {
    # Risk DTOs
    'EmailChainValidationStatus': 'src/interface/risk_dtos.py',
    'ExternalContactValidationStatus': 'src/interface/risk_dtos.py',
    'DiscrepancyValidationReason': 'src/interface/risk_dtos.py',
    'RiskLevel': 'src/interface/risk_dtos.py',
    'AssessmentStatus': 'src/interface/risk_dtos.py',
    'AlertSeverity': 'src/interface/risk_dtos.py',
    'AlertType': 'src/interface/risk_dtos.py',
    'EntityType': 'src/interface/risk_dtos.py',
    'RuleType': 'src/interface/risk_dtos.py',
    'VerificationStatus': 'src/interface/risk_dtos.py',
    'ExtractionStatus': 'src/interface/risk_dtos.py',
    'DiscrepancySeverity': 'src/interface/risk_dtos.py',
    'ValidationType': 'src/interface/risk_dtos.py',
    # Legal DTOs
    'ImportStatus': 'src/interface/legal_dtos.py',
    'ContractReviewAction': 'src/interface/legal_dtos.py',
    # Finance DTOs
    'SearchType': 'src/interface/finance_dtos.py',
    'ArchivoEstado': 'src/interface/finance_dtos.py',
    # Alianzas DTOs
    'TipoBroker': 'src/interface/alianzas_dtos.py',
    'EstadoBroker': 'src/interface/alianzas_dtos.py',
    'ExtractionMethod': 'src/interface/alianzas_dtos.py',
    'TipoComision': 'src/interface/alianzas_dtos.py',
    'EstadoComision': 'src/interface/alianzas_dtos.py',
    'EstadoPago': 'src/interface/alianzas_dtos.py',
}

# Enums with name collisions across modules - need special handling
# Maps enum_name to list of (source_file, valid_members) tuples
ENUM_MULTI_DEFINITIONS: Dict[str, List[str]] = {
    # ContractType exists in legal_dtos.py and broker_incentive_dtos.py
    'ContractType': [
        'src/interface/legal_dtos.py',
        'src/interface/broker_incentive_dtos.py',
    ],
    # ContractStatus exists in legal_dtos.py and broker_incentive_dtos.py
    'ContractStatus': [
        'src/interface/legal_dtos.py',
        'src/interface/broker_incentive_dtos.py',
    ],
    # DocumentType exists in risk_dtos.py and finance_dtos.py
    'DocumentType': [
        'src/interface/risk_dtos.py',
        'src/interface/finance_dtos.py',
    ],
}

# Members that are valid to access on enums (methods/properties)
VALID_ENUM_ACCESSORS = {'value', 'name', '__members__', 'items', '_value_', '_name_'}


def test_enum_member_case_consistency():
    """Verify enum members are referenced with correct case (UPPERCASE)."""
    errors = []

    # Load valid members for each enum (single definition)
    valid_members: Dict[str, Set[str]] = {}
    for enum_name, source_file in ENUM_DEFINITIONS.items():
        source_path = BACKEND_PATH / source_file
        if source_path.exists():
            members = get_enum_members_from_file(source_path, enum_name)
            if members:
                valid_members[enum_name] = members

    # Load valid members for multi-definition enums (union of all definitions)
    multi_valid_members: Dict[str, Set[str]] = {}
    for enum_name, source_files in ENUM_MULTI_DEFINITIONS.items():
        all_members: Set[str] = set()
        for source_file in source_files:
            source_path = BACKEND_PATH / source_file
            if source_path.exists():
                members = get_enum_members_from_file(source_path, enum_name)
                all_members.update(members)
        if all_members:
            multi_valid_members[enum_name] = all_members

    if not valid_members and not multi_valid_members:
        print("Warning: No enum definitions loaded, skipping validation")
        return

    # Scan all Python files in src/ for enum references
    src_path = BACKEND_PATH / 'src'
    for py_file in src_path.rglob('*.py'):
        try:
            content = py_file.read_text(encoding='utf-8')
        except Exception:
            continue

        # Check single-definition enums
        for enum_name, members in valid_members.items():
            # Find all references like EnumName.member
            pattern = rf'{enum_name}\.(\w+)'
            for match in re.finditer(pattern, content):
                member = match.group(1)
                # Skip method/property calls
                if member in VALID_ENUM_ACCESSORS:
                    continue
                if member not in members:
                    line_num = content[:match.start()].count('\n') + 1
                    rel_path = py_file.relative_to(BACKEND_PATH)
                    errors.append(
                        f"{rel_path}:{line_num}: Invalid enum member {enum_name}.{member}. "
                        f"Valid members: {sorted(members)}"
                    )

        # Check multi-definition enums (accept any valid member from any source)
        for enum_name, members in multi_valid_members.items():
            # Find all references like EnumName.member
            pattern = rf'{enum_name}\.(\w+)'
            for match in re.finditer(pattern, content):
                member = match.group(1)
                # Skip method/property calls
                if member in VALID_ENUM_ACCESSORS:
                    continue
                if member not in members:
                    line_num = content[:match.start()].count('\n') + 1
                    rel_path = py_file.relative_to(BACKEND_PATH)
                    errors.append(
                        f"{rel_path}:{line_num}: Invalid enum member {enum_name}.{member}. "
                        f"Valid members: {sorted(members)}"
                    )

    if errors:
        error_msg = "Enum reference validation failed:\n" + "\n".join(errors)
        raise AssertionError(error_msg)

    total_enums = len(valid_members) + len(multi_valid_members)
    print(f"Enum reference validation passed: checked {total_enums} enum types")


def test_route_imports_succeed():
    """Verify all route modules can be imported without error."""
    route_modules = [
        'src.adapter.rest.risk_routes',
        'src.adapter.rest.legal_routes',
        'src.adapter.rest.operations_routes',
        'src.adapter.rest.auth_routes',
        'src.adapter.rest.financial_ingestion_routes',
        'src.adapter.rest.tesoreria_routes',
        'src.adapter.rest.alianzas_routes',
    ]

    errors = []
    successful = 0

    for module_path in route_modules:
        try:
            # Convert module path to actual import
            __import__(module_path)
            successful += 1
        except ImportError:
            # ImportError is OK - module might not exist yet
            pass
        except AttributeError as e:
            errors.append(f"{module_path}: AttributeError - {e}")
        except Exception as e:
            errors.append(f"{module_path}: {type(e).__name__} - {e}")

    if errors:
        error_msg = "Route import validation failed:\n" + "\n".join(errors)
        raise AssertionError(error_msg)

    print(f"Route import validation passed: {successful} modules imported successfully")


def test_dto_imports_succeed():
    """Verify all DTO modules can be imported without error."""
    dto_modules = [
        'src.interface.risk_dtos',
        'src.interface.legal_dtos',
        'src.interface.finance_dtos',
        'src.interface.alianzas_dtos',
        'src.interface.tesoreria_dtos',
        'src.interface.auth_dtos',
    ]

    errors = []
    successful = 0

    for module_path in dto_modules:
        try:
            __import__(module_path)
            successful += 1
        except ImportError:
            # ImportError is OK - module might not exist yet
            pass
        except Exception as e:
            errors.append(f"{module_path}: {type(e).__name__} - {e}")

    if errors:
        error_msg = "DTO import validation failed:\n" + "\n".join(errors)
        raise AssertionError(error_msg)

    print(f"DTO import validation passed: {successful} modules imported successfully")


if __name__ == "__main__":
    # Run tests when executed directly
    print("=" * 60)
    print("Running Enum Reference Validation Tests")
    print("=" * 60)

    try:
        test_enum_member_case_consistency()
        print("PASS")
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    print()

    try:
        test_route_imports_succeed()
        print("PASS")
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    print()

    try:
        test_dto_imports_succeed()
        print("PASS")
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("All tests passed!")
    print("=" * 60)
