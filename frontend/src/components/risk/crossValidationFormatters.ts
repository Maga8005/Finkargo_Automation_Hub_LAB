/**
 * Cross-validation formatting utilities
 * Shared by FKCrossValidationResults and FKDiscrepancyValidationItem
 */

import { DOCUMENT_TYPE_CONFIG } from '../../types/risk';

// Field label mapping for signatory data - maps technical field names to Spanish labels
export const SIGNATORY_FIELD_LABELS: Record<string, string> = {
  signatory_name: 'Firmante',
  signatory_id: 'Cédula Firmante',
  auditor_name: 'Auditor',
  auditor_license: 'Licencia Auditor',
  all_signatories: 'Todos los Firmantes',
  contador_name: 'Contador',
  contador_cedula: 'Cédula Contador',
  revisor_fiscal_name: 'Revisor Fiscal',
  revisor_fiscal_cedula: 'Cédula Revisor Fiscal',
  revisor_fiscal_principal_name: 'Revisor Fiscal Principal',
  revisor_fiscal_principal_cedula: 'Cédula Revisor Fiscal Principal',
  revisor_fiscal_suplente_name: 'Revisor Fiscal Suplente',
  revisor_fiscal_suplente_cedula: 'Cédula Revisor Fiscal Suplente',
  name: 'Nombre',
  id: 'Cédula',
  role: 'Rol',
};

// Check if object contains signatory-related fields
export const isSignatoryObject = (obj: Record<string, unknown>): boolean => {
  const signatoryFields = [
    'signatory_name',
    'contador_name',
    'revisor_fiscal_name',
    'revisor_fiscal_principal_name',
    'all_signatories',
    'auditor_name',
  ];
  return signatoryFields.some((field) => field in obj);
};

// Format a single signatory from all_signatories array
export const formatSignatory = (sig: Record<string, unknown>): string => {
  const name = sig.name || sig.nombre || 'Sin nombre';
  const role = sig.role || sig.rol || '';
  const id = sig.id || sig.cedula || '';

  if (role && id) {
    return `${name} (${role}) - Cédula: ${id}`;
  } else if (role) {
    return `${name} (${role})`;
  } else if (id) {
    return `${name} - Cédula: ${id}`;
  }
  return String(name);
};

// Format signatory object with readable labels
export const formatSignatoryObject = (obj: Record<string, unknown>): string => {
  const lines: string[] = [];

  // Handle all_signatories array first
  if (Array.isArray(obj.all_signatories) && obj.all_signatories.length > 0) {
    lines.push(`${SIGNATORY_FIELD_LABELS.all_signatories}:`);
    obj.all_signatories.forEach((sig: Record<string, unknown>) => {
      lines.push(`  • ${formatSignatory(sig)}`);
    });
  }

  // Handle other signatory fields
  for (const [key, value] of Object.entries(obj)) {
    if (key === 'all_signatories') continue; // Already handled
    if (value === null || value === undefined || value === '') continue;

    const label = SIGNATORY_FIELD_LABELS[key] || key;
    lines.push(`${label}: ${value}`);
  }

  return lines.join('\n');
};

// Get document label from document type string
export const getDocumentLabel = (docType: string): string => {
  const config = DOCUMENT_TYPE_CONFIG[docType as keyof typeof DOCUMENT_TYPE_CONFIG];
  return config?.label || docType;
};

// Format value for display based on type
export const formatValueForDisplay = (value: unknown): string => {
  if (value === null || value === undefined) {
    return 'N/A';
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return 'N/A';
    }
    // Check if array of objects (like shareholders or signatories)
    if (typeof value[0] === 'object' && value[0] !== null) {
      // Check if it's an array of signatories
      const firstItem = value[0] as Record<string, unknown>;
      if ('role' in firstItem || 'rol' in firstItem) {
        // Format as signatories list
        return value
          .map((sig) => formatSignatory(sig as Record<string, unknown>))
          .join('\n');
      }

      const formatted = value.map((item, idx) => {
        // Try to get a meaningful name/identifier from the object
        const name = item.name || item.nombre || item.razon_social || `Item ${idx + 1}`;
        const percentage = item.percentage || item.porcentaje;
        if (percentage !== undefined && percentage !== null) {
          return `${name} (${percentage}%)`;
        }
        return name;
      });
      // Truncate if too many items
      if (formatted.length > 5) {
        return `${formatted.slice(0, 5).join(', ')} ... y ${formatted.length - 5} más`;
      }
      return formatted.join(', ');
    }
    // Array of primitives
    return value.join(', ');
  }

  if (typeof value === 'object') {
    // Single object - extract key info
    const obj = value as Record<string, unknown>;

    // Check if this is a signatory-related object
    if (isSignatoryObject(obj)) {
      return formatSignatoryObject(obj);
    }

    const name = obj.name || obj.nombre || obj.razon_social;
    if (name) {
      return String(name);
    }
    return JSON.stringify(value);
  }

  return String(value);
};
