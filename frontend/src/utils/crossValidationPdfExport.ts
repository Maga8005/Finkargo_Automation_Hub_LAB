/**
 * Cross-Validation PDF Export Utility
 * Generates PDF reports for cross-validation findings in the Risk module
 */
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import type {
  CrossValidationResponse,
  DiscrepancySeverity,
  ValidationType,
  ClientInfo,
} from '../types/risk';
import {
  DISCREPANCY_SEVERITY_CONFIG,
  VALIDATION_TYPE_LABELS,
  DOCUMENT_TYPE_CONFIG,
} from '../types/risk';

// Finkargo brand colors (consistent with pdfExport.ts)
const FINKARGO_COLORS = {
  primaryDark: '#0C147B',
  primaryMain: '#3C47D3',
  coral: '#EB8774',
  success: '#2CA14D',
  warning: '#B86E00',
  error: '#CC071E',
  grey50: '#F9FAFB',
  grey100: '#F3F4F6',
  grey900: '#111827',
  white: '#FFFFFF',
};

// Severity colors for PDF (RGB values for jsPDF)
const SEVERITY_PDF_COLORS: Record<DiscrepancySeverity, { bg: [number, number, number]; text: [number, number, number] }> = {
  critical: { bg: [204, 7, 30], text: [255, 255, 255] },
  high: { bg: [255, 228, 228], text: [204, 7, 30] },
  medium: { bg: [255, 244, 229], text: [184, 110, 0] },
  low: { bg: [224, 247, 230], text: [44, 161, 77] },
};

/**
 * Format validation type to Spanish label
 */
const formatValidationType = (type: ValidationType): string => {
  return VALIDATION_TYPE_LABELS[type] || type;
};

/**
 * Format severity to Spanish label with color info
 */
const formatSeverity = (severity?: DiscrepancySeverity): { label: string; color: string } => {
  if (!severity) {
    return { label: 'N/A', color: FINKARGO_COLORS.grey900 };
  }
  const config = DISCREPANCY_SEVERITY_CONFIG[severity];
  return { label: config.label, color: config.textColor };
};

/**
 * Get document label from document type string
 */
const getDocumentLabel = (docType: string): string => {
  const config = DOCUMENT_TYPE_CONFIG[docType as keyof typeof DOCUMENT_TYPE_CONFIG];
  return config?.label || docType;
};

/**
 * Format documents compared list
 */
const formatDocumentsCompared = (docs: string[]): string => {
  return docs.map(getDocumentLabel).join(', ');
};

interface AssessmentContext {
  assessment_id: string;
  client_nit: string;
  client_info?: ClientInfo;
}

/**
 * Export cross-validation results to PDF
 */
export const exportCrossValidationToPDF = (
  results: CrossValidationResponse,
  assessment: AssessmentContext
): void => {
  try {
    // Create PDF document (A4, portrait)
    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    });

    // Set document properties
    doc.setProperties({
      title: `Reporte de Validación Cruzada - ${assessment.assessment_id}`,
      subject: 'Análisis de discrepancias en documentos',
      author: 'Finkargo Automation Hub - Módulo de Riesgos',
      creator: 'Finkargo Automation Hub',
    });

    const pageWidth = doc.internal.pageSize.width;
    let yPosition = 15;

    // ==================== HEADER ====================
    // Title
    doc.setFontSize(18);
    doc.setTextColor(FINKARGO_COLORS.primaryDark);
    doc.setFont('helvetica', 'bold');
    doc.text('Reporte de Validación Cruzada', 14, yPosition);
    yPosition += 7;

    // Subtitle
    doc.setFontSize(12);
    doc.setTextColor(FINKARGO_COLORS.coral);
    doc.text('Finkargo - Módulo de Gestión de Riesgos', 14, yPosition);
    yPosition += 10;

    // ==================== ASSESSMENT INFO ====================
    doc.setFontSize(10);
    doc.setTextColor(FINKARGO_COLORS.grey900);
    doc.setFont('helvetica', 'normal');

    // Assessment ID
    doc.setFont('helvetica', 'bold');
    doc.text('ID Evaluación:', 14, yPosition);
    doc.setFont('courier', 'normal');
    doc.text(assessment.assessment_id, 50, yPosition);
    yPosition += 5;

    // Client NIT
    doc.setFont('helvetica', 'bold');
    doc.text('NIT Cliente:', 14, yPosition);
    doc.setFont('helvetica', 'normal');
    doc.text(assessment.client_nit, 50, yPosition);
    yPosition += 5;

    // Company name
    if (assessment.client_info?.nombre_importador) {
      doc.setFont('helvetica', 'bold');
      doc.text('Empresa:', 14, yPosition);
      doc.setFont('helvetica', 'normal');
      doc.text(assessment.client_info.nombre_importador, 50, yPosition);
      yPosition += 5;
    }

    // Export date
    const exportDate = format(new Date(), "dd 'de' MMMM 'de' yyyy, HH:mm", { locale: es });
    doc.setFont('helvetica', 'bold');
    doc.text('Fecha de reporte:', 14, yPosition);
    doc.setFont('helvetica', 'normal');
    doc.text(exportDate, 50, yPosition);
    yPosition += 5;

    // Validation date
    if (results.validated_at) {
      const validatedDate = format(new Date(results.validated_at), "dd/MM/yyyy HH:mm", { locale: es });
      doc.setFont('helvetica', 'bold');
      doc.text('Validación ejecutada:', 14, yPosition);
      doc.setFont('helvetica', 'normal');
      doc.text(validatedDate, 50, yPosition);
      yPosition += 5;
    }

    yPosition += 5;

    // ==================== SUMMARY SECTION ====================
    doc.setFillColor(FINKARGO_COLORS.grey100);
    doc.rect(14, yPosition, pageWidth - 28, 30, 'F');

    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(FINKARGO_COLORS.primaryDark);
    doc.text('Resumen de Validación', 18, yPosition + 7);

    // Summary statistics in a row
    const summaryY = yPosition + 14;
    const colWidth = (pageWidth - 36) / 5;

    // Total validations
    doc.setFontSize(14);
    doc.setTextColor(FINKARGO_COLORS.primaryMain);
    doc.text(String(results.results.length), 18, summaryY);
    doc.setFontSize(8);
    doc.setTextColor(FINKARGO_COLORS.grey900);
    doc.text('Total', 18, summaryY + 5);

    // Total discrepancies
    doc.setFontSize(14);
    doc.setTextColor(results.total_discrepancies > 0 ? FINKARGO_COLORS.error : FINKARGO_COLORS.success);
    doc.text(String(results.total_discrepancies), 18 + colWidth, summaryY);
    doc.setFontSize(8);
    doc.setTextColor(FINKARGO_COLORS.grey900);
    doc.text('Discrepancias', 18 + colWidth, summaryY + 5);

    // Critical
    doc.setFontSize(14);
    doc.setTextColor('#CC071E');
    doc.text(String(results.critical_count), 18 + colWidth * 2, summaryY);
    doc.setFontSize(8);
    doc.setTextColor(FINKARGO_COLORS.grey900);
    doc.text('Críticas', 18 + colWidth * 2, summaryY + 5);

    // High
    doc.setFontSize(14);
    doc.setTextColor(FINKARGO_COLORS.error);
    doc.text(String(results.high_count), 18 + colWidth * 3, summaryY);
    doc.setFontSize(8);
    doc.setTextColor(FINKARGO_COLORS.grey900);
    doc.text('Altas', 18 + colWidth * 3, summaryY + 5);

    // Medium + Low
    doc.setFontSize(14);
    doc.setTextColor(FINKARGO_COLORS.warning);
    doc.text(String(results.medium_count + results.low_count), 18 + colWidth * 4, summaryY);
    doc.setFontSize(8);
    doc.setTextColor(FINKARGO_COLORS.grey900);
    doc.text('Medias/Bajas', 18 + colWidth * 4, summaryY + 5);

    yPosition += 35;

    // Score impact alert
    if (Number(results.total_score_impact) > 0) {
      doc.setFillColor(255, 244, 229);
      doc.rect(14, yPosition, pageWidth - 28, 10, 'F');
      doc.setFontSize(9);
      doc.setTextColor(FINKARGO_COLORS.warning);
      doc.setFont('helvetica', 'bold');
      doc.text(`Impacto total en puntuación de riesgo: +${Number(results.total_score_impact).toFixed(0)} puntos`, 18, yPosition + 6);
      yPosition += 15;
    }

    yPosition += 5;

    // ==================== DISCREPANCIES TABLE ====================
    const discrepancies = results.results
      .filter(r => r.is_discrepancy)
      .sort((a, b) => {
        const severityOrder: Record<DiscrepancySeverity, number> = { critical: 0, high: 1, medium: 2, low: 3 };
        return (severityOrder[a.severity || 'low'] || 4) - (severityOrder[b.severity || 'low'] || 4);
      });

    if (discrepancies.length > 0) {
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(FINKARGO_COLORS.error);
      doc.text(`Discrepancias Encontradas (${discrepancies.length})`, 14, yPosition);
      yPosition += 5;

      const discrepancyData = discrepancies.map((r) => [
        formatValidationType(r.validation_type),
        r.field_compared || '-',
        formatSeverity(r.severity).label,
        `+${Number(r.score_impact).toFixed(0)}`,
        r.description || '-',
      ]);

      autoTable(doc, {
        head: [['Tipo de Validación', 'Campo', 'Severidad', 'Impacto', 'Descripción']],
        body: discrepancyData,
        startY: yPosition,
        theme: 'grid',
        styles: {
          fontSize: 8,
          cellPadding: 2,
          overflow: 'linebreak',
          halign: 'left',
          valign: 'middle',
        },
        headStyles: {
          fillColor: FINKARGO_COLORS.primaryDark,
          textColor: FINKARGO_COLORS.white,
          fontStyle: 'bold',
          fontSize: 8,
          halign: 'center',
        },
        alternateRowStyles: {
          fillColor: FINKARGO_COLORS.grey50,
        },
        columnStyles: {
          0: { cellWidth: 35 },
          1: { cellWidth: 25 },
          2: { cellWidth: 20, halign: 'center' },
          3: { cellWidth: 18, halign: 'center', textColor: FINKARGO_COLORS.error },
          4: { cellWidth: 'auto' },
        },
        margin: { left: 14, right: 14 },
        didParseCell: (data) => {
          // Color-code severity column
          if (data.section === 'body' && data.column.index === 2) {
            const severityLabel = data.cell.raw as string;
            if (severityLabel === 'Crítico') {
              data.cell.styles.fillColor = SEVERITY_PDF_COLORS.critical.bg;
              data.cell.styles.textColor = SEVERITY_PDF_COLORS.critical.text;
              data.cell.styles.fontStyle = 'bold';
            } else if (severityLabel === 'Alto') {
              data.cell.styles.fillColor = SEVERITY_PDF_COLORS.high.bg;
              data.cell.styles.textColor = SEVERITY_PDF_COLORS.high.text;
            } else if (severityLabel === 'Medio') {
              data.cell.styles.fillColor = SEVERITY_PDF_COLORS.medium.bg;
              data.cell.styles.textColor = SEVERITY_PDF_COLORS.medium.text;
            } else if (severityLabel === 'Bajo') {
              data.cell.styles.fillColor = SEVERITY_PDF_COLORS.low.bg;
              data.cell.styles.textColor = SEVERITY_PDF_COLORS.low.text;
            }
          }
        },
        didDrawPage: (data) => {
          addPageFooter(doc, data.pageNumber);
        },
      });

      // Get final Y position after table
      yPosition = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 10;
    } else {
      // No discrepancies message
      doc.setFillColor(224, 247, 230);
      doc.rect(14, yPosition, pageWidth - 28, 12, 'F');
      doc.setFontSize(10);
      doc.setTextColor(FINKARGO_COLORS.success);
      doc.setFont('helvetica', 'bold');
      doc.text('Sin discrepancias encontradas - Todos los documentos son consistentes', 18, yPosition + 8);
      yPosition += 20;
    }

    // ==================== PASSED VALIDATIONS TABLE ====================
    const passedValidations = results.results.filter(r => !r.is_discrepancy);

    if (passedValidations.length > 0) {
      // Check if we need a new page
      if (yPosition > 230) {
        doc.addPage();
        yPosition = 20;
      }

      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(FINKARGO_COLORS.success);
      doc.text(`Validaciones Exitosas (${passedValidations.length})`, 14, yPosition);
      yPosition += 5;

      const passedData = passedValidations.map((r) => [
        formatValidationType(r.validation_type),
        r.field_compared || '-',
        formatDocumentsCompared(r.documents_compared),
        'Consistente',
      ]);

      autoTable(doc, {
        head: [['Tipo de Validación', 'Campo', 'Documentos Comparados', 'Resultado']],
        body: passedData,
        startY: yPosition,
        theme: 'grid',
        styles: {
          fontSize: 8,
          cellPadding: 2,
          overflow: 'linebreak',
          halign: 'left',
          valign: 'middle',
        },
        headStyles: {
          fillColor: FINKARGO_COLORS.success,
          textColor: FINKARGO_COLORS.white,
          fontStyle: 'bold',
          fontSize: 8,
          halign: 'center',
        },
        alternateRowStyles: {
          fillColor: FINKARGO_COLORS.grey50,
        },
        columnStyles: {
          0: { cellWidth: 35 },
          1: { cellWidth: 25 },
          2: { cellWidth: 'auto' },
          3: { cellWidth: 25, halign: 'center', textColor: FINKARGO_COLORS.success },
        },
        margin: { left: 14, right: 14 },
        didDrawPage: (data) => {
          addPageFooter(doc, data.pageNumber);
        },
      });
    }

    // Add footer to all pages
    const totalPages = doc.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      addPageFooter(doc, i, totalPages);
    }

    // Generate filename with assessment ID and date
    const dateStr = format(new Date(), 'yyyy-MM-dd');
    const filename = `validacion_cruzada_${assessment.assessment_id}_${dateStr}.pdf`;

    // Save PDF
    doc.save(filename);
  } catch (error) {
    console.error('Error generating cross-validation PDF:', error);
    throw new Error('Error al generar el PDF de validación cruzada');
  }
};

/**
 * Add page footer with page numbers and timestamp
 */
const addPageFooter = (doc: jsPDF, pageNumber: number, totalPages?: number): void => {
  const pageHeight = doc.internal.pageSize.height;
  const pageWidth = doc.internal.pageSize.width;

  doc.setFontSize(8);
  doc.setTextColor(FINKARGO_COLORS.grey900);
  doc.setFont('helvetica', 'normal');

  // Page number
  const pageText = totalPages
    ? `Página ${pageNumber} de ${totalPages}`
    : `Página ${pageNumber}`;
  doc.text(pageText, pageWidth / 2, pageHeight - 10, { align: 'center' });

  // Footer line
  doc.setDrawColor(FINKARGO_COLORS.grey100);
  doc.line(14, pageHeight - 15, pageWidth - 14, pageHeight - 15);

  // Generation info
  doc.setFontSize(7);
  doc.setTextColor(150, 150, 150);
  doc.text('Generado por Finkargo Automation Hub - Módulo de Gestión de Riesgos', 14, pageHeight - 7);
};
