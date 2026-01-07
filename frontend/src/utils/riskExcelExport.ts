/**
 * Risk Excel Export Utility
 * Exports document extraction data from fraud risk evaluations to Excel
 */
import * as XLSX from 'xlsx';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import type {
  DocumentType,
  DocumentExtraction,
  DocumentExtractionList,
} from '../types/risk';
import { DOCUMENT_TYPE_CONFIG } from '../types/risk';

/**
 * Document type to Spanish sheet name mapping
 */
const DOCUMENT_TYPE_SHEET_NAMES: Record<DocumentType, string> = {
  financial_statement_current: 'EEFF Año Actual',
  financial_statement_prior: 'EEFF Año Anterior',
  cedula: 'Cédula',
  composicion_accionaria: 'Composición Accionaria',
  rut: 'RUT',
  certificado_existencia: 'Certificado Existencia',
};

/**
 * Spanish labels for common extracted field names
 */
const FIELD_LABELS: Record<string, string> = {
  // Financial statements
  company_name: 'Nombre de Empresa',
  nit: 'NIT',
  fiscal_year: 'Año Fiscal',
  period_end_date: 'Fecha Cierre Período',
  auditor_name: 'Nombre del Auditor',
  total_assets: 'Total Activos',
  total_liabilities: 'Total Pasivos',
  total_equity: 'Total Patrimonio',
  net_income: 'Utilidad Neta',
  revenue: 'Ingresos',
  signatory_name: 'Nombre del Firmante',
  signatory_id: 'Cédula del Firmante',
  // Cédula
  full_name: 'Nombre Completo',
  first_names: 'Nombres',
  last_names: 'Apellidos',
  document_number: 'Número de Documento',
  document_type: 'Tipo de Documento',
  birth_date: 'Fecha de Nacimiento',
  birth_place: 'Lugar de Nacimiento',
  issue_date: 'Fecha de Expedición',
  issue_place: 'Lugar de Expedición',
  gender: 'Género',
  blood_type: 'Tipo de Sangre',
  // Composición accionaria
  document_date: 'Fecha del Documento',
  total_shares: 'Total de Acciones',
  share_value: 'Valor por Acción',
  shareholders: 'Accionistas',
  majority_shareholder: 'Accionista Mayoritario',
  // RUT
  city: 'Ciudad',
  address: 'Dirección',
  email: 'Correo Electrónico',
  phone: 'Teléfono',
  economic_activity: 'Actividad Económica',
  legal_representative: 'Representante Legal',
  registration_date: 'Fecha de Registro',
  // Certificado existencia
  entity_type: 'Tipo de Entidad',
  registered_capital: 'Capital Registrado',
  // Contador (Accountant) fields
  contador_name: 'Nombre del Contador',
  contador_cedula: 'Cédula del Contador',
  contador_license: 'Tarjeta Profesional Contador',
  // Revisor Fiscal fields (Certificado de Existencia)
  revisor_fiscal_name: 'Nombre del Revisor Fiscal',
  revisor_fiscal_cedula: 'Cédula del Revisor Fiscal',
  revisor_fiscal_license: 'Tarjeta Profesional Revisor Fiscal',
  // Revisor Fiscal fields (RUT - principal and suplente)
  revisor_fiscal_principal_name: 'Nombre del Revisor Fiscal Principal',
  revisor_fiscal_principal_cedula: 'Cédula del Revisor Fiscal Principal',
  revisor_fiscal_suplente_name: 'Nombre del Revisor Fiscal Suplente',
  revisor_fiscal_suplente_cedula: 'Cédula del Revisor Fiscal Suplente',
  // Signatories (Financial Statements)
  signatories: 'Firmantes',
};

/**
 * Format date for Excel display (DD/MM/YYYY HH:mm)
 */
const formatDateForExcel = (dateString: string | undefined | null): string => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'N/A';
    return format(date, 'dd/MM/yyyy HH:mm', { locale: es });
  } catch {
    return 'N/A';
  }
};

/**
 * Format currency for Excel display (COP format with thousands separator)
 */
const formatCurrencyForExcel = (amount: number | undefined | null): string => {
  if (amount === undefined || amount === null) return '$0';
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

/**
 * Format percentage for Excel display
 */
const formatPercentageForExcel = (value: number | undefined | null): string => {
  if (value === undefined || value === null) return 'N/A';
  return `${(value * 100).toFixed(2)}%`;
};

/**
 * Format a value for Excel based on its type and field name
 */
const formatValueForExcel = (value: unknown, fieldName?: string): string => {
  if (value === null || value === undefined) {
    return 'N/A';
  }

  // Handle arrays (like shareholders)
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return 'N/A';
    }
    // For arrays, return count - detailed data goes in separate rows
    if (typeof value[0] === 'object') {
      return `${value.length} registros`;
    }
    return value.join(', ');
  }

  // Handle objects (like legal_representative)
  if (typeof value === 'object') {
    const obj = value as Record<string, unknown>;
    // Try to get a meaningful name from the object
    const name = obj.name || obj.nombre || obj.razon_social;
    if (name) {
      return String(name);
    }
    // For complex objects, stringify key-value pairs
    const entries = Object.entries(obj);
    if (entries.length > 0) {
      return entries
        .slice(0, 3)
        .map(([k, v]) => `${k}: ${v}`)
        .join('; ');
    }
    return 'N/A';
  }

  // Handle numbers - check for currency/percentage fields
  if (typeof value === 'number') {
    if (fieldName) {
      const lowerField = fieldName.toLowerCase();
      if (
        lowerField.includes('total') ||
        lowerField.includes('capital') ||
        lowerField.includes('income') ||
        lowerField.includes('revenue') ||
        lowerField.includes('value') ||
        lowerField.includes('assets') ||
        lowerField.includes('liabilities') ||
        lowerField.includes('equity')
      ) {
        return formatCurrencyForExcel(value);
      }
      if (lowerField.includes('percentage') || lowerField.includes('porcentaje')) {
        return `${value}%`;
      }
    }
    // Format with thousands separator for large numbers
    if (value >= 1000) {
      return new Intl.NumberFormat('es-CO').format(value);
    }
    return String(value);
  }

  // Handle boolean
  if (typeof value === 'boolean') {
    return value ? 'Sí' : 'No';
  }

  // Handle date strings
  if (typeof value === 'string') {
    // Check if it looks like an ISO date
    if (/^\d{4}-\d{2}-\d{2}/.test(value)) {
      return formatDateForExcel(value);
    }
    return value;
  }

  return String(value);
};

/**
 * Get Spanish label for a field name
 */
const getFieldLabel = (fieldName: string): string => {
  if (FIELD_LABELS[fieldName]) {
    return FIELD_LABELS[fieldName];
  }
  // Convert snake_case to Title Case
  return fieldName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
};

/**
 * Create summary sheet data
 */
const createSummarySheet = (
  assessmentId: string,
  clientNit: string | undefined,
  extractions: DocumentExtractionList
): XLSX.WorkSheet => {
  const completedDocs = extractions.extractions.filter(
    (e) => e.extraction_status === 'completed'
  );

  const summaryData = [
    ['Campo', 'Valor'],
    ['ID Evaluación', assessmentId],
    ['NIT Cliente', clientNit || 'N/A'],
    ['Fecha Exportación', formatDateForExcel(new Date().toISOString())],
    ['Documentos Procesados', completedDocs.length],
    ['Documentos Totales', extractions.total_documents],
    [''],
    ['Documentos Incluidos:'],
  ];

  // Add list of included documents
  completedDocs.forEach((doc) => {
    const docLabel = DOCUMENT_TYPE_CONFIG[doc.document_type]?.label || doc.document_type;
    summaryData.push(['', `- ${docLabel}`]);
  });

  const worksheet = XLSX.utils.aoa_to_sheet(summaryData);

  // Set column widths
  worksheet['!cols'] = [{ wch: 25 }, { wch: 40 }];

  return worksheet;
};

/**
 * Create a sheet for a document extraction
 */
const createDocumentSheet = (extraction: DocumentExtraction): XLSX.WorkSheet | null => {
  if (!extraction.extracted_data) {
    return null;
  }

  const data: (string | number)[][] = [];

  // Add header with extraction info
  data.push(['Campo', 'Valor']);
  data.push(['Archivo', extraction.document_filename || 'N/A']);
  data.push(['Confianza', extraction.extraction_confidence
    ? formatPercentageForExcel(extraction.extraction_confidence)
    : 'N/A']);
  data.push(['Fecha Extracción', formatDateForExcel(extraction.created_at)]);
  data.push(['']); // Empty row

  // Add extracted data
  const extractedData = extraction.extracted_data;

  Object.entries(extractedData).forEach(([key, value]) => {
    // Skip arrays (handled separately)
    if (Array.isArray(value)) {
      return;
    }
    data.push([getFieldLabel(key), formatValueForExcel(value, key)]);
  });

  // Handle shareholders array separately (expand to multiple rows)
  const shareholders = extractedData.shareholders as Array<Record<string, unknown>> | undefined;
  if (shareholders && Array.isArray(shareholders) && shareholders.length > 0) {
    data.push(['']); // Empty row
    data.push(['--- Accionistas ---', '']);

    shareholders.forEach((shareholder, idx) => {
      data.push([`Accionista ${idx + 1}`, '']);
      Object.entries(shareholder).forEach(([key, value]) => {
        data.push([`  ${getFieldLabel(key)}`, formatValueForExcel(value, key)]);
      });
    });
  }

  // Handle signatories array separately (expand to multiple rows) - Financial Statements
  const signatories = extractedData.signatories as Array<Record<string, unknown>> | undefined;
  if (signatories && Array.isArray(signatories) && signatories.length > 0) {
    data.push(['']); // Empty row
    data.push(['--- Firmantes ---', '']);

    signatories.forEach((signatory, idx) => {
      data.push([`Firmante ${idx + 1}`, '']);
      Object.entries(signatory).forEach(([key, value]) => {
        data.push([`  ${getFieldLabel(key)}`, formatValueForExcel(value, key)]);
      });
    });
  }

  const worksheet = XLSX.utils.aoa_to_sheet(data);

  // Set column widths
  worksheet['!cols'] = [{ wch: 30 }, { wch: 50 }];

  return worksheet;
};

/**
 * Export document extractions to Excel file
 * @param extractions - Document extraction list from risk service
 * @param assessmentId - Assessment ID for filename and metadata
 * @param clientNit - Optional client NIT for metadata
 * @returns true if export was successful, false if no data to export
 */
export const exportDocumentExtractionsToExcel = (
  extractions: DocumentExtractionList,
  assessmentId: string,
  clientNit?: string
): boolean => {
  // Filter to only completed extractions with data
  const completedExtractions = extractions.extractions.filter(
    (e) => e.extraction_status === 'completed' && e.extracted_data
  );

  if (completedExtractions.length === 0) {
    return false;
  }

  // Create workbook
  const workbook = XLSX.utils.book_new();

  // Add summary sheet
  const summarySheet = createSummarySheet(assessmentId, clientNit, extractions);
  XLSX.utils.book_append_sheet(workbook, summarySheet, 'Resumen');

  // Add sheet for each completed extraction
  completedExtractions.forEach((extraction) => {
    const sheet = createDocumentSheet(extraction);
    if (sheet) {
      const sheetName = DOCUMENT_TYPE_SHEET_NAMES[extraction.document_type] || extraction.document_type;
      // Excel sheet names have 31 char limit
      const truncatedName = sheetName.substring(0, 31);
      XLSX.utils.book_append_sheet(workbook, sheet, truncatedName);
    }
  });

  // Generate filename with assessment ID and current date
  const dateStr = format(new Date(), 'yyyy-MM-dd_HHmm');
  const filename = `documentos_extraidos_${assessmentId}_${dateStr}.xlsx`;

  // Download the file
  XLSX.writeFile(workbook, filename);

  return true;
};

/**
 * Check if there are completed extractions to export
 */
export const hasExportableExtractions = (extractions: DocumentExtractionList | null): boolean => {
  if (!extractions) return false;
  return extractions.extractions.some(
    (e) => e.extraction_status === 'completed' && e.extracted_data
  );
};
