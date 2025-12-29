"""
PA Rules Service - Business logic for managing PA classification rules.

Handles:
- Parsing Excel files containing rules
- Validating rule data
- Orchestrating storage via repository
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO
import pandas as pd

from src.interface.pa_dtos import (
    PAAccountCatalogUploadResponse,
    PAClassificationRulesUploadResponse,
    PAClasificacionCuentaRulesUploadResponse,
    PANexoRulesUploadResponse,
    PARulesSummary,
    RuleUploadType
)
from src.repositorio.pa_rules_repository import PARulesRepository

logger = logging.getLogger(__name__)


class PARulesService:
    """Service for managing PA classification rules."""

    def __init__(self, repository: PARulesRepository):
        """
        Initialize service with repository.

        Args:
            repository: PA rules repository instance.
        """
        self.repository = repository

    # =========================================================================
    # Account Catalog Operations
    # =========================================================================

    async def upload_account_catalog(
        self,
        file_content: bytes,
        filename: str,
        created_by: Optional[str] = None,
        replace_existing: bool = True
    ) -> PAAccountCatalogUploadResponse:
        """
        Upload and parse PA account catalog Excel file.

        Expected columns:
        - Cuenta Finkargo: Account number in Finkargo/NetSuite
        - Cuenta Homologación: Homologated account number
        - Nombre Homologación: Homologated account name

        Args:
            file_content: Excel file bytes.
            filename: Original filename.
            created_by: User ID.
            replace_existing: If True, clear existing entries first.

        Returns:
            Upload response with stats.
        """
        try:
            # Parse Excel
            df = pd.read_excel(BytesIO(file_content))

            # Normalize column names (strip whitespace, lowercase)
            df.columns = df.columns.str.strip().str.lower()

            # Map expected columns (handle variations)
            column_mapping = self._get_catalog_column_mapping(df.columns.tolist())

            if not column_mapping:
                return PAAccountCatalogUploadResponse(
                    success=False,
                    message="No se encontraron las columnas requeridas. Se esperan: Cuenta Finkargo, Cuenta Homologación, Nombre Homologación",
                    errors=["Columnas no válidas"]
                )

            # Rename columns to standard names
            df = df.rename(columns=column_mapping)

            # Clean data
            df = df.dropna(subset=["cuenta_finkargo"])
            df["cuenta_finkargo"] = df["cuenta_finkargo"].astype(str).str.strip()
            df["cuenta_homologacion"] = df["cuenta_homologacion"].astype(str).str.strip()
            df["nombre_homologacion"] = df["nombre_homologacion"].astype(str).str.strip()

            # Convert to list of dicts
            entries = df[["cuenta_finkargo", "cuenta_homologacion", "nombre_homologacion"]].to_dict("records")

            if replace_existing:
                await self.repository.clear_catalog()

            # Upload entries
            uploaded, updated, skipped, errors = await self.repository.upsert_catalog_entries(
                entries, created_by
            )

            return PAAccountCatalogUploadResponse(
                success=True,
                entries_uploaded=uploaded,
                entries_updated=updated,
                entries_skipped=skipped,
                errors=errors,
                message=f"Catálogo actualizado: {uploaded} nuevas, {updated} actualizadas, {skipped} omitidas"
            )

        except Exception as e:
            logger.error(f"Error uploading account catalog: {e}")
            return PAAccountCatalogUploadResponse(
                success=False,
                message=f"Error al procesar archivo: {str(e)}",
                errors=[str(e)]
            )

    def _get_catalog_column_mapping(self, columns: List[str]) -> Optional[Dict[str, str]]:
        """
        Get column mapping for account catalog.

        Handles various column name variations.
        """
        mapping = {}

        # Cuenta Finkargo variations
        for col in columns:
            col_lower = col.lower()
            if "cuenta" in col_lower and ("finkargo" in col_lower or "netsuite" in col_lower or "linea" in col_lower):
                mapping[col] = "cuenta_finkargo"
                break
            if col_lower in ["cuenta_finkargo", "cuenta finkargo", "cuenta"]:
                mapping[col] = "cuenta_finkargo"
                break

        # Cuenta Homologación variations
        for col in columns:
            col_lower = col.lower()
            if "cuenta" in col_lower and "homolog" in col_lower:
                mapping[col] = "cuenta_homologacion"
                break
            if col_lower in ["cuenta_homologacion", "cuenta homologación", "homologacion"]:
                mapping[col] = "cuenta_homologacion"
                break

        # Nombre Homologación variations
        for col in columns:
            col_lower = col.lower()
            if "nombre" in col_lower and "homolog" in col_lower:
                mapping[col] = "nombre_homologacion"
                break
            if col_lower in ["nombre_homologacion", "nombre homologación", "nombre"]:
                mapping[col] = "nombre_homologacion"
                break

        # Check if we have all required columns
        if len(mapping) == 3:
            return mapping
        return None

    async def get_account_catalog(self, limit: int = 1000, offset: int = 0) -> Tuple[List[Dict], int]:
        """
        Get account catalog entries.

        Args:
            limit: Maximum entries.
            offset: Entries to skip.

        Returns:
            Tuple of (entries, total_count).
        """
        return await self.repository.get_account_catalog(limit, offset)

    # =========================================================================
    # Classification Rules Operations
    # =========================================================================

    async def upload_classification_rules(
        self,
        file_content: bytes,
        filename: str,
        created_by: Optional[str] = None,
        replace_existing: bool = True
    ) -> PAClassificationRulesUploadResponse:
        """
        Upload and parse classification rules Excel file.

        Expected columns:
        - Tipo Transacción
        - Tipo Comprobante
        - Patrón Documento (optional)
        - Categoría
        - Subcategoría Base (optional)
        - Clasificación Default (optional)
        - Prioridad (optional)

        Args:
            file_content: Excel file bytes.
            filename: Original filename.
            created_by: User ID.
            replace_existing: If True, clear existing rules first.

        Returns:
            Upload response with stats.
        """
        try:
            df = pd.read_excel(BytesIO(file_content))
            df.columns = df.columns.str.strip().str.lower()

            column_mapping = self._get_classification_column_mapping(df.columns.tolist())

            if not column_mapping:
                return PAClassificationRulesUploadResponse(
                    success=False,
                    message="No se encontraron las columnas requeridas. Se esperan: Tipo Transacción, Tipo Comprobante, Categoría",
                    errors=["Columnas no válidas"]
                )

            df = df.rename(columns=column_mapping)

            # Clean data
            df = df.dropna(subset=["tipo_transaccion", "tipo_comprobante", "categoria"])
            for col in ["tipo_transaccion", "tipo_comprobante", "categoria"]:
                df[col] = df[col].astype(str).str.strip()

            # Handle optional columns
            if "numero_documento_patron" not in df.columns:
                df["numero_documento_patron"] = None
            if "subcategoria_base" not in df.columns:
                df["subcategoria_base"] = None
            if "clasificacion_default" not in df.columns:
                df["clasificacion_default"] = None
            if "prioridad" not in df.columns:
                df["prioridad"] = 100

            # Convert to list of dicts
            rules = df[[
                "tipo_transaccion", "tipo_comprobante", "numero_documento_patron",
                "categoria", "subcategoria_base", "clasificacion_default", "prioridad"
            ]].to_dict("records")

            if replace_existing:
                await self.repository.clear_classification_rules()

            uploaded, updated, skipped, errors = await self.repository.upsert_classification_rules(
                rules, created_by
            )

            return PAClassificationRulesUploadResponse(
                success=True,
                rules_uploaded=uploaded,
                rules_updated=updated,
                rules_skipped=skipped,
                errors=errors,
                message=f"Reglas actualizadas: {uploaded} nuevas, {updated} actualizadas, {skipped} omitidas"
            )

        except Exception as e:
            logger.error(f"Error uploading classification rules: {e}")
            return PAClassificationRulesUploadResponse(
                success=False,
                message=f"Error al procesar archivo: {str(e)}",
                errors=[str(e)]
            )

    def _get_classification_column_mapping(self, columns: List[str]) -> Optional[Dict[str, str]]:
        """Get column mapping for classification rules."""
        mapping = {}
        required_found = 0

        for col in columns:
            col_lower = col.lower()

            if "tipo" in col_lower and "transac" in col_lower:
                mapping[col] = "tipo_transaccion"
                required_found += 1
            elif "tipo" in col_lower and "comprob" in col_lower:
                mapping[col] = "tipo_comprobante"
                required_found += 1
            elif col_lower in ["categoria", "categoría"]:
                mapping[col] = "categoria"
                required_found += 1
            elif "patron" in col_lower or "patrón" in col_lower:
                mapping[col] = "numero_documento_patron"
            elif "subcateg" in col_lower:
                mapping[col] = "subcategoria_base"
            elif "clasific" in col_lower and "default" in col_lower:
                mapping[col] = "clasificacion_default"
            elif col_lower == "prioridad":
                mapping[col] = "prioridad"

        if required_found >= 3:
            return mapping
        return None

    async def get_classification_rules(self, active_only: bool = True) -> List[Dict]:
        """Get classification rules."""
        return await self.repository.get_classification_rules(active_only)

    # =========================================================================
    # Clasificación Cuenta Rules Operations
    # =========================================================================

    async def upload_clasificacion_cuenta_rules(
        self,
        file_content: bytes,
        filename: str,
        created_by: Optional[str] = None,
        replace_existing: bool = True
    ) -> PAClasificacionCuentaRulesUploadResponse:
        """
        Upload and parse clasificación cuenta rules Excel file.

        Expected columns:
        - Cuenta Nombre Patrón
        - Clasificación
        - Categoría Aplicable (optional)
        - Prioridad (optional)

        Args:
            file_content: Excel file bytes.
            filename: Original filename.
            created_by: User ID.
            replace_existing: If True, clear existing rules first.

        Returns:
            Upload response with stats.
        """
        try:
            df = pd.read_excel(BytesIO(file_content))
            df.columns = df.columns.str.strip().str.lower()

            column_mapping = self._get_clasificacion_cuenta_column_mapping(df.columns.tolist())

            if not column_mapping:
                return PAClasificacionCuentaRulesUploadResponse(
                    success=False,
                    message="No se encontraron las columnas requeridas. Se esperan: Cuenta Nombre Patrón, Clasificación",
                    errors=["Columnas no válidas"]
                )

            df = df.rename(columns=column_mapping)

            df = df.dropna(subset=["cuenta_nombre_patron", "clasificacion"])
            df["cuenta_nombre_patron"] = df["cuenta_nombre_patron"].astype(str).str.strip()
            df["clasificacion"] = df["clasificacion"].astype(str).str.strip()

            if "categoria_aplicable" not in df.columns:
                df["categoria_aplicable"] = None
            if "prioridad" not in df.columns:
                df["prioridad"] = 100

            rules = df[[
                "cuenta_nombre_patron", "clasificacion", "categoria_aplicable", "prioridad"
            ]].to_dict("records")

            if replace_existing:
                await self.repository.clear_clasificacion_cuenta_rules()

            uploaded, updated, skipped, errors = await self.repository.upsert_clasificacion_cuenta_rules(
                rules, created_by
            )

            return PAClasificacionCuentaRulesUploadResponse(
                success=True,
                rules_uploaded=uploaded,
                rules_updated=updated,
                rules_skipped=skipped,
                errors=errors,
                message=f"Reglas actualizadas: {uploaded} nuevas, {updated} actualizadas, {skipped} omitidas"
            )

        except Exception as e:
            logger.error(f"Error uploading clasificacion cuenta rules: {e}")
            return PAClasificacionCuentaRulesUploadResponse(
                success=False,
                message=f"Error al procesar archivo: {str(e)}",
                errors=[str(e)]
            )

    def _get_clasificacion_cuenta_column_mapping(self, columns: List[str]) -> Optional[Dict[str, str]]:
        """Get column mapping for clasificación cuenta rules."""
        mapping = {}
        required_found = 0

        for col in columns:
            col_lower = col.lower()

            if ("cuenta" in col_lower and "patron" in col_lower) or col_lower == "cuenta_nombre_patron":
                mapping[col] = "cuenta_nombre_patron"
                required_found += 1
            elif col_lower in ["clasificacion", "clasificación"]:
                mapping[col] = "clasificacion"
                required_found += 1
            elif "categoria" in col_lower and "aplicable" in col_lower:
                mapping[col] = "categoria_aplicable"
            elif col_lower == "prioridad":
                mapping[col] = "prioridad"

        if required_found >= 2:
            return mapping
        return None

    async def get_clasificacion_cuenta_rules(self, active_only: bool = True) -> List[Dict]:
        """Get clasificación cuenta rules."""
        return await self.repository.get_clasificacion_cuenta_rules(active_only)

    # =========================================================================
    # Nexo Rules Operations
    # =========================================================================

    async def upload_nexo_rules(
        self,
        file_content: bytes,
        filename: str,
        created_by: Optional[str] = None,
        replace_existing: bool = True
    ) -> PANexoRulesUploadResponse:
        """
        Upload and parse nexo rules Excel file.

        Expected columns:
        - Cuenta Nombre Patrón
        - Nexo
        - Prioridad (optional)

        Args:
            file_content: Excel file bytes.
            filename: Original filename.
            created_by: User ID.
            replace_existing: If True, clear existing rules first.

        Returns:
            Upload response with stats.
        """
        try:
            df = pd.read_excel(BytesIO(file_content))
            df.columns = df.columns.str.strip().str.lower()

            column_mapping = self._get_nexo_column_mapping(df.columns.tolist())

            if not column_mapping:
                return PANexoRulesUploadResponse(
                    success=False,
                    message="No se encontraron las columnas requeridas. Se esperan: Cuenta Nombre Patrón, Nexo",
                    errors=["Columnas no válidas"]
                )

            df = df.rename(columns=column_mapping)

            df = df.dropna(subset=["cuenta_nombre_patron", "nexo"])
            df["cuenta_nombre_patron"] = df["cuenta_nombre_patron"].astype(str).str.strip()
            df["nexo"] = df["nexo"].astype(str).str.strip()

            if "prioridad" not in df.columns:
                df["prioridad"] = 100

            rules = df[[
                "cuenta_nombre_patron", "nexo", "prioridad"
            ]].to_dict("records")

            if replace_existing:
                await self.repository.clear_nexo_rules()

            uploaded, updated, skipped, errors = await self.repository.upsert_nexo_rules(
                rules, created_by
            )

            return PANexoRulesUploadResponse(
                success=True,
                rules_uploaded=uploaded,
                rules_updated=updated,
                rules_skipped=skipped,
                errors=errors,
                message=f"Reglas actualizadas: {uploaded} nuevas, {updated} actualizadas, {skipped} omitidas"
            )

        except Exception as e:
            logger.error(f"Error uploading nexo rules: {e}")
            return PANexoRulesUploadResponse(
                success=False,
                message=f"Error al procesar archivo: {str(e)}",
                errors=[str(e)]
            )

    def _get_nexo_column_mapping(self, columns: List[str]) -> Optional[Dict[str, str]]:
        """Get column mapping for nexo rules."""
        mapping = {}
        required_found = 0

        for col in columns:
            col_lower = col.lower()

            if ("cuenta" in col_lower and "patron" in col_lower) or col_lower == "cuenta_nombre_patron":
                mapping[col] = "cuenta_nombre_patron"
                required_found += 1
            elif col_lower == "nexo":
                mapping[col] = "nexo"
                required_found += 1
            elif col_lower == "prioridad":
                mapping[col] = "prioridad"

        if required_found >= 2:
            return mapping
        return None

    async def get_nexo_rules(self, active_only: bool = True) -> List[Dict]:
        """Get nexo rules."""
        return await self.repository.get_nexo_rules(active_only)

    # =========================================================================
    # Summary Operations
    # =========================================================================

    async def get_rules_summary(self) -> PARulesSummary:
        """
        Get summary of all loaded rules.

        Returns:
            Rules summary object.
        """
        summary_data = await self.repository.get_rules_summary()
        return PARulesSummary(**summary_data)


# Factory function
def get_pa_rules_service(repository: PARulesRepository) -> PARulesService:
    """
    Create PA rules service instance.

    Args:
        repository: PA rules repository.

    Returns:
        PARulesService instance.
    """
    return PARulesService(repository)
