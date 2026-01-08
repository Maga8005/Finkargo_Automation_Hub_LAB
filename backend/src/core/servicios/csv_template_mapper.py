"""
CSV Template Mapper Service
Handles multiple CSV template formats with intelligent column mapping
"""
from typing import Dict, List, Tuple
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class CSVTemplateMapper:
    """
    Maps different CSV template formats to standardized database fields.
    Supports:
    1. Simple template (direct column names)
    2. FinCargo export template (complex with many columns)
    """

    # Column mappings for different templates
    FINKARGO_TEMPLATE_MAPPING = {
        'NIT': 'nit',
        'Customer Name': 'nombre_importador',
        'LEGAL_REPRESENTATIVE': 'representante_legal',
        'LEGAL_REPRESENTATIVE_ID': 'cedula_representante',
        'city': 'ciudad_domicilio',
        'approved quota': 'cupo_plataforma',
        'address': 'direccion_comercial',
        'kam': 'kam_nombre',
    }

    # Simple template uses direct column names (no mapping needed)
    SIMPLE_TEMPLATE_COLUMNS = [
        'nit',
        'nombre_importador',
        'representante_legal',
        'cedula_representante',
        'ciudad_domicilio',
        'cupo_plataforma',
        'direccion_comercial',
        'tipo_identificacion_representante',
        'nombre_contrato_marco',
        'kam_nombre',
        'kam_email',
        'destinatario_nombre',
        'destinatario_email'
    ]

    # Required fields that must be present (after mapping)
    REQUIRED_FIELDS = [
        'nit',
        'nombre_importador',
        'representante_legal',
        'cedula_representante',
        'ciudad_domicilio',
        'cupo_plataforma'
    ]

    # Default values for missing fields
    DEFAULT_VALUES = {
        'kam_email': 'legalcol@finkargo.com',
        'cupo_plataforma': 0,
    }

    @staticmethod
    def detect_template_type(columns: List[str]) -> str:
        """
        Detect which template format is being used.

        Args:
            columns: List of column names from CSV

        Returns:
            str: 'finkargo' or 'simple'
        """
        # FinCargo template signature columns
        finkargo_signatures = ['NIT', 'Customer Name', 'LEGAL_REPRESENTATIVE', 'approved quota']

        # Check if FinCargo signature columns are present
        matches = sum(1 for sig in finkargo_signatures if sig in columns)

        if matches >= 3:
            logger.info("Detected FinCargo export template")
            return 'finkargo'
        else:
            logger.info("Detected simple template")
            return 'simple'

    @classmethod
    def map_columns(cls, df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
        """
        Map CSV columns to standardized database fields.

        Args:
            df: DataFrame with original column names

        Returns:
            Tuple[pd.DataFrame, str]: Mapped DataFrame and template type
        """
        # Detect template type
        template_type = cls.detect_template_type(list(df.columns))

        if template_type == 'finkargo':
            logger.info("Applying FinCargo template mapping")
            df_mapped = cls._map_finkargo_template(df)
        else:
            logger.info("Using simple template (no mapping needed)")
            df_mapped = df.copy()

        # Apply default values for missing fields
        df_mapped = cls._apply_default_values(df_mapped)

        # Validate required fields are present
        cls._validate_required_fields(df_mapped)

        return df_mapped, template_type

    @classmethod
    def _map_finkargo_template(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Map FinCargo export columns to database fields.

        Args:
            df: DataFrame with FinCargo columns

        Returns:
            pd.DataFrame: Mapped DataFrame
        """
        # Create new DataFrame with mapped columns
        mapped_data = {}

        for finkargo_col, db_field in cls.FINKARGO_TEMPLATE_MAPPING.items():
            if finkargo_col in df.columns:
                mapped_data[db_field] = df[finkargo_col]
                logger.debug(f"Mapped '{finkargo_col}' → '{db_field}'")
            else:
                logger.warning(f"FinCargo column '{finkargo_col}' not found in CSV")

        # Create DataFrame from mapped data
        df_mapped = pd.DataFrame(mapped_data)

        # Keep any columns that already match our field names
        for col in df.columns:
            if col in cls.SIMPLE_TEMPLATE_COLUMNS and col not in df_mapped.columns:
                df_mapped[col] = df[col]
                logger.debug(f"Kept original column '{col}'")

        return df_mapped

    @classmethod
    def _apply_default_values(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply default values for missing optional fields.

        Args:
            df: DataFrame

        Returns:
            pd.DataFrame: DataFrame with defaults applied
        """
        for field, default_value in cls.DEFAULT_VALUES.items():
            if field not in df.columns:
                df[field] = default_value
                logger.info(f"Applied default value for '{field}': {default_value}")

        return df

    @classmethod
    def _validate_required_fields(cls, df: pd.DataFrame) -> None:
        """
        Validate that all required fields are present.

        Args:
            df: Mapped DataFrame

        Raises:
            ValueError: If required fields are missing
        """
        missing_fields = [field for field in cls.REQUIRED_FIELDS if field not in df.columns]

        if missing_fields:
            error_msg = f"Missing required fields after mapping: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("All required fields present after mapping")

    @classmethod
    def get_template_info(cls) -> Dict[str, any]:
        """
        Get information about supported templates.

        Returns:
            Dict with template information
        """
        return {
            'supported_templates': ['simple', 'finkargo'],
            'simple_template': {
                'required_columns': cls.REQUIRED_FIELDS,
                'optional_columns': [col for col in cls.SIMPLE_TEMPLATE_COLUMNS
                                    if col not in cls.REQUIRED_FIELDS],
                'description': 'Minimal template with direct column names'
            },
            'finkargo_template': {
                'signature_columns': list(cls.FINKARGO_TEMPLATE_MAPPING.keys()),
                'mapped_to': list(cls.FINKARGO_TEMPLATE_MAPPING.values()),
                'description': 'FinCargo export template with comprehensive customer data'
            },
            'default_values': cls.DEFAULT_VALUES
        }
