/**
 * PDF Export Utility - Export approved contracts to PDF
 * Uses jsPDF with jspdf-autotable for professional table formatting
 */
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import type { ContractGeneration } from '../types/legal';

// Finkargo brand colors (from theme.ts)
const FINKARGO_COLORS = {
  primaryDark: '#0C147B',
  primaryMain: '#3C47D3',
  coral: '#EB8774',
  success: '#2CA14D',
  grey50: '#F9FAFB',
  grey100: '#F3F4F6',
  grey900: '#111827',
  white: '#FFFFFF',
};

/**
 * Format contract type to Spanish label
 */
const formatContractTypeLabel = (type: string): string => {
  const typeMap: Record<string, string> = {
    'activos': 'Activos',
    'otrosi': 'Otrosí No. 1',
    'inventario_bodega': 'Inventario Bodega 3ro',
    'pl_co_credito_aval_pj': 'PL CO - Crédito Aval PJ',
    'pl_co_mandato_pj': 'PL CO - Mandato PJ',
    'pl_co_credito_aval_pn': 'PL CO - Crédito Aval PN',
    'pl_co_mandato_pn': 'PL CO - Mandato PN',
    'pl_co_credito_no_aval': 'PL CO - Crédito Sin Aval',
    'pl_co_mandato_no_aval': 'PL CO - Mandato Sin Aval',
    'pl_co_mandato_im': 'PL CO - Mandato IM',
    'pl_co_solicitud_desembolso': 'PL CO - Solicitud Desembolso',
    'pl_co_dian_mandato_im': 'PL CO - DIAN Mandato IM',
  };
  return typeMap[type] || type;
};

/**
 * Format currency amount to COP format
 */
const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
  }).format(amount);
};

/**
 * Format date to DD/MM/YYYY HH:mm format
 */
const formatDate = (dateString: string): string => {
  try {
    return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: es });
  } catch {
    return 'N/A';
  }
};

/**
 * Export standard contracts (Activos, Otrosí, Inventario) to PDF
 */
export const exportContractsToPDF = (contracts: ContractGeneration[]): void => {
  try {
    // Create PDF document (A4, portrait)
    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    });

    // Set document properties
    doc.setProperties({
      title: 'Contratos Aprobados - Finkargo',
      subject: 'Lista de contratos aprobados',
      author: 'Finkargo Automation Hub',
      creator: 'Finkargo Automation Hub',
    });

    // Add title
    doc.setFontSize(18);
    doc.setTextColor(FINKARGO_COLORS.primaryDark);
    doc.setFont('helvetica', 'bold');
    doc.text('Contratos Aprobados - Finkargo', 14, 20);

    // Add export metadata
    doc.setFontSize(10);
    doc.setTextColor(FINKARGO_COLORS.grey900);
    doc.setFont('helvetica', 'normal');
    const exportDate = format(new Date(), "dd 'de' MMMM 'de' yyyy, HH:mm", { locale: es });
    doc.text(`Fecha de exportación: ${exportDate}`, 14, 28);
    doc.text(`Total de contratos: ${contracts.length}`, 14, 33);

    // Prepare table data
    const tableData = contracts.map((contract) => [
      contract.contract_id,
      formatContractTypeLabel(contract.contract_type || 'activos'),
      contract.data_snapshot?.nombre_importador || 'N/A',
      contract.client_nit,
      formatCurrency(contract.data_snapshot?.cupo_plataforma || 0),
      contract.reviewed_at ? formatDate(contract.reviewed_at) : 'N/A',
      'Aprobado',
    ]);

    // Generate table with autoTable
    autoTable(doc, {
      head: [['ID Contrato', 'Tipo', 'Cliente', 'NIT', 'Cupo Aprobado', 'Fecha Aprobación', 'Estado']],
      body: tableData,
      startY: 40,
      theme: 'grid',
      styles: {
        fontSize: 9,
        cellPadding: 3,
        overflow: 'linebreak',
        halign: 'left',
        valign: 'middle',
      },
      headStyles: {
        fillColor: FINKARGO_COLORS.primaryDark,
        textColor: FINKARGO_COLORS.white,
        fontStyle: 'bold',
        fontSize: 9,
        halign: 'center',
      },
      alternateRowStyles: {
        fillColor: FINKARGO_COLORS.grey50,
      },
      columnStyles: {
        0: { cellWidth: 30, fontStyle: 'bold', font: 'courier' }, // ID Contrato (monospace)
        1: { cellWidth: 30 }, // Tipo
        2: { cellWidth: 40 }, // Cliente
        3: { cellWidth: 25 }, // NIT
        4: { cellWidth: 28, halign: 'right', textColor: FINKARGO_COLORS.success }, // Cupo
        5: { cellWidth: 30 }, // Fecha
        6: { cellWidth: 22, halign: 'center', textColor: FINKARGO_COLORS.success }, // Estado
      },
      margin: { left: 14, right: 14 },
      didDrawPage: (data) => {
        // Add page numbers in footer
        const pageCount = doc.getNumberOfPages();
        doc.setFontSize(8);
        doc.setTextColor(FINKARGO_COLORS.grey900);
        doc.setFont('helvetica', 'normal');
        const pageText = `Página ${data.pageNumber} de ${pageCount}`;
        doc.text(pageText, doc.internal.pageSize.width / 2, doc.internal.pageSize.height - 10, {
          align: 'center',
        });
      },
    });

    // Generate filename with current date
    const filename = `contratos_aprobados_${format(new Date(), 'yyyy-MM-dd')}.pdf`;

    // Save PDF
    doc.save(filename);
  } catch (error) {
    console.error('Error generating PDF:', error);
    throw new Error('Error al generar el PDF');
  }
};

/**
 * Export Paga Local CO contracts to PDF
 */
export const exportPagaLocalContractsToPDF = (contracts: ContractGeneration[]): void => {
  try {
    // Create PDF document (A4, portrait)
    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    });

    // Set document properties
    doc.setProperties({
      title: 'Paga Local CO - Contratos Aprobados - Finkargo',
      subject: 'Lista de contratos Paga Local Colombia aprobados',
      author: 'Finkargo Automation Hub',
      creator: 'Finkargo Automation Hub',
    });

    // Add title
    doc.setFontSize(18);
    doc.setTextColor(FINKARGO_COLORS.primaryDark);
    doc.setFont('helvetica', 'bold');
    doc.text('Paga Local CO - Contratos Aprobados', 14, 20);

    // Add subtitle
    doc.setFontSize(12);
    doc.setTextColor(FINKARGO_COLORS.coral);
    doc.text('Finkargo', 14, 26);

    // Add export metadata
    doc.setFontSize(10);
    doc.setTextColor(FINKARGO_COLORS.grey900);
    doc.setFont('helvetica', 'normal');
    const exportDate = format(new Date(), "dd 'de' MMMM 'de' yyyy, HH:mm", { locale: es });
    doc.text(`Fecha de exportación: ${exportDate}`, 14, 33);
    doc.text(`Total de contratos: ${contracts.length}`, 14, 38);

    // Prepare table data
    const tableData = contracts.map((contract) => [
      contract.contract_id,
      formatContractTypeLabel(contract.contract_type || 'activos'),
      contract.data_snapshot?.nombre_importador || 'N/A',
      contract.client_nit,
      formatCurrency(contract.data_snapshot?.cupo_plataforma || 0),
      contract.reviewed_at ? formatDate(contract.reviewed_at) : 'N/A',
      'Aprobado',
    ]);

    // Generate table with autoTable
    autoTable(doc, {
      head: [['ID Contrato', 'Tipo', 'Cliente', 'NIT', 'Cupo Aprobado', 'Fecha Aprobación', 'Estado']],
      body: tableData,
      startY: 45,
      theme: 'grid',
      styles: {
        fontSize: 9,
        cellPadding: 3,
        overflow: 'linebreak',
        halign: 'left',
        valign: 'middle',
      },
      headStyles: {
        fillColor: FINKARGO_COLORS.primaryDark,
        textColor: FINKARGO_COLORS.white,
        fontStyle: 'bold',
        fontSize: 9,
        halign: 'center',
      },
      alternateRowStyles: {
        fillColor: FINKARGO_COLORS.grey50,
      },
      columnStyles: {
        0: { cellWidth: 30, fontStyle: 'bold', font: 'courier' }, // ID Contrato (monospace)
        1: { cellWidth: 30 }, // Tipo
        2: { cellWidth: 40 }, // Cliente
        3: { cellWidth: 25 }, // NIT
        4: { cellWidth: 28, halign: 'right', textColor: FINKARGO_COLORS.success }, // Cupo
        5: { cellWidth: 30 }, // Fecha
        6: { cellWidth: 22, halign: 'center', textColor: FINKARGO_COLORS.success }, // Estado
      },
      margin: { left: 14, right: 14 },
      didDrawPage: (data) => {
        // Add page numbers in footer
        const pageCount = doc.getNumberOfPages();
        doc.setFontSize(8);
        doc.setTextColor(FINKARGO_COLORS.grey900);
        doc.setFont('helvetica', 'normal');
        const pageText = `Página ${data.pageNumber} de ${pageCount}`;
        doc.text(pageText, doc.internal.pageSize.width / 2, doc.internal.pageSize.height - 10, {
          align: 'center',
        });
      },
    });

    // Generate filename with current date
    const filename = `paga_local_co_contratos_aprobados_${format(new Date(), 'yyyy-MM-dd')}.pdf`;

    // Save PDF
    doc.save(filename);
  } catch (error) {
    console.error('Error generating PDF:', error);
    throw new Error('Error al generar el PDF');
  }
};
