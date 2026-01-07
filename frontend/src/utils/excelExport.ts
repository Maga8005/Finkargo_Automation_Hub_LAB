/**
 * Excel Export Utility
 * Provides reusable functions for exporting data to Excel files
 */
import * as XLSX from 'xlsx';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import type { ContractGeneration } from '../types/legal';

/**
 * Contract type labels for Excel export (standard contracts)
 */
const STANDARD_CONTRACT_TYPE_LABELS: Record<string, string> = {
  activos: 'Activos',
  otrosi: 'Otrosí No. 1',
  inventario_bodega: 'Inventario Bodega 3ro',
};

/**
 * Contract type labels for Excel export (Paga Local CO contracts)
 */
const PAGA_LOCAL_CONTRACT_TYPE_LABELS: Record<string, string> = {
  pl_co_credito_aval_pj: 'Crédito Aval PJ',
  pl_co_mandato_pj: 'Mandato PJ',
  pl_co_credito_aval_pn: 'Crédito Aval PN',
  pl_co_mandato_pn: 'Mandato PN',
  pl_co_credito_no_aval: 'Crédito No Aval',
  pl_co_mandato_no_aval: 'Mandato No Aval',
  pl_co_mandato_im: 'Mandato (IM)',
  pl_co_solicitud_desembolso: 'Solicitud Desembolso',
  pl_co_dian_mandato_im: 'DIAN Mandato (IM)',
};

/**
 * Get human-readable contract type label
 */
const getContractTypeLabel = (contractType: string): string => {
  return (
    STANDARD_CONTRACT_TYPE_LABELS[contractType] ||
    PAGA_LOCAL_CONTRACT_TYPE_LABELS[contractType] ||
    contractType
  );
};

/**
 * Format date for Excel display (DD/MM/YYYY HH:mm)
 */
const formatDateForExcel = (dateString: string | undefined | null): string => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    return format(date, 'dd/MM/yyyy HH:mm', { locale: es });
  } catch {
    return 'N/A';
  }
};

/**
 * Format currency for Excel display (COP format)
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
 * Export contract data to an Excel file
 * @param contracts - Array of contract generations to export
 * @param filenamePrefix - Prefix for the filename (e.g., 'contratos_aprobados')
 * @param includesCupo - Whether to include the Cupo Aprobado column (default: true)
 */
export const exportContractsToExcel = (
  contracts: ContractGeneration[],
  filenamePrefix: string = 'contratos_aprobados',
  includesCupo: boolean = true
): void => {
  // Define headers based on whether cupo is included
  const headers = includesCupo
    ? [
        'ID Contrato',
        'Tipo',
        'Cliente',
        'NIT',
        'Cupo Aprobado',
        'Fecha Aprobación',
        'Estado',
      ]
    : ['ID Contrato', 'Tipo', 'Cliente', 'NIT', 'Fecha Aprobación', 'Estado'];

  // Transform contracts to Excel-friendly format
  const data = contracts.map((contract) => {
    const baseData = {
      'ID Contrato': contract.contract_id || 'N/A',
      Tipo: getContractTypeLabel(contract.contract_type || 'activos'),
      Cliente: contract.data_snapshot?.nombre_importador || 'N/A',
      NIT: contract.client_nit || 'N/A',
    };

    if (includesCupo) {
      return {
        ...baseData,
        'Cupo Aprobado': formatCurrencyForExcel(
          contract.data_snapshot?.cupo_plataforma
        ),
        'Fecha Aprobación': formatDateForExcel(contract.reviewed_at),
        Estado: 'Aprobado',
      };
    }

    return {
      ...baseData,
      'Fecha Aprobación': formatDateForExcel(contract.reviewed_at),
      Estado: 'Aprobado',
    };
  });

  // Create workbook and worksheet
  const workbook = XLSX.utils.book_new();
  const worksheet = XLSX.utils.json_to_sheet(data, { header: headers });

  // Set column widths for better readability
  const columnWidths = includesCupo
    ? [
        { wch: 20 }, // ID Contrato
        { wch: 22 }, // Tipo
        { wch: 35 }, // Cliente
        { wch: 15 }, // NIT
        { wch: 18 }, // Cupo Aprobado
        { wch: 20 }, // Fecha Aprobación
        { wch: 12 }, // Estado
      ]
    : [
        { wch: 20 }, // ID Contrato
        { wch: 22 }, // Tipo
        { wch: 35 }, // Cliente
        { wch: 15 }, // NIT
        { wch: 20 }, // Fecha Aprobación
        { wch: 12 }, // Estado
      ];

  worksheet['!cols'] = columnWidths;

  // Add worksheet to workbook
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Contratos Aprobados');

  // Generate filename with current date
  const currentDate = format(new Date(), 'yyyy-MM-dd');
  const filename = `${filenamePrefix}_${currentDate}.xlsx`;

  // Download the file
  XLSX.writeFile(workbook, filename);
};

/**
 * Export Paga Local CO contracts to Excel
 * Uses specific configuration for Paga Local documents (no cupo column)
 */
export const exportPagaLocalContractsToExcel = (
  contracts: ContractGeneration[]
): void => {
  exportContractsToExcel(contracts, 'paga_local_co_contratos_aprobados', false);
};
