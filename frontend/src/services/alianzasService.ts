/**
 * Alianzas (Partnerships) Service - API calls for broker management
 */
import apiClient from '../api/clients/apiClient';
import type {
  Broker,
  BrokerCreateRequest,
  BrokerUpdateRequest,
  BrokerSearchParams,
  BrokerWithSubBrokers,
  MasterBrokerOption,
  BrokerContractData,
  TipoCambioResponse,
  ComisionInput,
  ComisionCalculada,
  ComisionBatchInput,
  ComisionBatchResponse,
  ComisionListResponse,
  ComisionResumenBroker,
  ComisionAprobacionRequest,
  ComisionAprobacionResponse,
  EstadoComision,
  Pago,
  PagoListResponse,
  PagoEstadoUpdate,
  EstadoPago,
} from '../types/alianzas';

export const alianzasService = {
  // ==================== Broker Operations ====================

  /**
   * Get all brokers with optional filters
   */
  getBrokers: async (params?: {
    active_only?: boolean;
    tipo_broker?: string;
    estado?: string;
  }): Promise<Broker[]> => {
    const response = await apiClient.get<Broker[]>('/alianzas/brokers', { params });
    return response.data;
  },

  /**
   * Search brokers by various criteria
   */
  searchBrokers: async (params: BrokerSearchParams): Promise<Broker[]> => {
    const response = await apiClient.get<Broker[]>('/alianzas/brokers/search', { params });
    return response.data;
  },

  /**
   * Get a broker by ID
   */
  getBrokerById: async (id: string): Promise<Broker> => {
    const response = await apiClient.get<Broker>(`/alianzas/brokers/${id}`);
    return response.data;
  },

  /**
   * Create a new broker
   */
  createBroker: async (data: BrokerCreateRequest): Promise<Broker> => {
    const response = await apiClient.post<Broker>('/alianzas/brokers', data);
    return response.data;
  },

  /**
   * Update an existing broker
   */
  updateBroker: async (id: string, data: BrokerUpdateRequest): Promise<Broker> => {
    const response = await apiClient.put<Broker>(`/alianzas/brokers/${id}`, data);
    return response.data;
  },

  /**
   * Delete a broker (soft delete)
   */
  deleteBroker: async (id: string): Promise<void> => {
    await apiClient.delete(`/alianzas/brokers/${id}`);
  },

  /**
   * Get a broker with its sub-brokers
   */
  getBrokerWithSubBrokers: async (id: string): Promise<BrokerWithSubBrokers> => {
    const response = await apiClient.get<BrokerWithSubBrokers>(
      `/alianzas/brokers/${id}/sub-brokers`
    );
    return response.data;
  },

  /**
   * Get master brokers for dropdown selection
   */
  getMasterBrokers: async (): Promise<MasterBrokerOption[]> => {
    const response = await apiClient.get<MasterBrokerOption[]>('/alianzas/brokers/master-brokers');
    return response.data;
  },

  // ==================== Contract Extraction Operations ====================

  /**
   * Extract contract data from an uploaded file (PDF or DOCX)
   */
  extractContract: async (file: File): Promise<BrokerContractData> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<BrokerContractData>(
      '/alianzas/brokers/extract-contract',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Extract contract data from a scanned PDF using AI (LandingAI ADE)
   * This method is slower (30-60 seconds) but works with scanned documents.
   */
  extractContractAI: async (file: File): Promise<BrokerContractData> => {
    const formData = new FormData();
    formData.append('contract_file', file);

    const response = await apiClient.post<BrokerContractData>(
      '/alianzas/brokers/extract-contract-ai',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minutes for AI processing
      }
    );
    return response.data;
  },

  // ==================== Exchange Rate Operations ====================

  /**
   * Get current USD/MXN exchange rate from Banxico
   * Falls back to previous business day if today's rate is not available
   */
  getTipoCambioActual: async (): Promise<TipoCambioResponse> => {
    const response = await apiClient.get<TipoCambioResponse>('/alianzas/tipo-cambio');
    return response.data;
  },

  /**
   * Get USD/MXN exchange rate for a specific date
   * @param fecha - Date in ISO format (YYYY-MM-DD)
   */
  getTipoCambioFecha: async (fecha: string): Promise<TipoCambioResponse> => {
    const response = await apiClient.get<TipoCambioResponse>(`/alianzas/tipo-cambio/${fecha}`);
    return response.data;
  },

  // ==================== Commission Operations ====================

  /**
   * Calculate a single commission (preview, not saved)
   */
  calcularComision: async (input: ComisionInput): Promise<ComisionCalculada> => {
    const response = await apiClient.post<ComisionCalculada>(
      '/alianzas/comisiones/calcular',
      input
    );
    return response.data;
  },

  /**
   * Calculate commissions in batch with optional save
   */
  calcularComisionesLote: async (
    data: ComisionBatchInput
  ): Promise<ComisionBatchResponse> => {
    const response = await apiClient.post<ComisionBatchResponse>(
      '/alianzas/comisiones/calcular-lote',
      data
    );
    return response.data;
  },

  /**
   * List commissions by period
   */
  listarComisionesPorPeriodo: async (
    periodoMes: number,
    periodoAnio: number,
    tipoComision?: string
  ): Promise<ComisionListResponse> => {
    const response = await apiClient.get<ComisionListResponse>(
      `/alianzas/comisiones/${periodoAnio}/${periodoMes}`,
      { params: tipoComision ? { tipo_comision: tipoComision } : undefined }
    );
    return response.data;
  },

  /**
   * Get commission summary by broker for a period
   */
  obtenerResumenComisiones: async (
    periodoMes: number,
    periodoAnio: number
  ): Promise<ComisionResumenBroker[]> => {
    const response = await apiClient.get<ComisionResumenBroker[]>(
      `/alianzas/comisiones/resumen/${periodoAnio}/${periodoMes}`
    );
    return response.data;
  },

  /**
   * List commissions by broker
   */
  listarComisionesPorBroker: async (
    brokerId: string,
    periodoMes?: number,
    periodoAnio?: number
  ): Promise<ComisionCalculada[]> => {
    const response = await apiClient.get<ComisionCalculada[]>(
      `/alianzas/comisiones/broker/${brokerId}`,
      {
        params: {
          ...(periodoMes && { periodo_mes: periodoMes }),
          ...(periodoAnio && { periodo_anio: periodoAnio }),
        },
      }
    );
    return response.data;
  },

  /**
   * Update commission status
   */
  actualizarEstadoComision: async (
    comisionId: string,
    estado: EstadoComision
  ): Promise<ComisionCalculada> => {
    const response = await apiClient.patch<ComisionCalculada>(
      `/alianzas/comisiones/${comisionId}/estado`,
      { estado }
    );
    return response.data;
  },

  // ==================== Export Operations ====================

  /**
   * Export commissions to Excel file
   * Returns a Blob containing the Excel file
   */
  exportarComisionesExcel: async (
    periodoMes: number,
    periodoAnio: number
  ): Promise<Blob> => {
    const response = await apiClient.get(
      `/alianzas/comisiones/export/${periodoAnio}/${periodoMes}`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },

  // ==================== Approval Operations ====================

  /**
   * Approve all calculated commissions for a period
   * Creates payment records per broker
   */
  aprobarComisiones: async (
    data: ComisionAprobacionRequest
  ): Promise<ComisionAprobacionResponse> => {
    const response = await apiClient.post<ComisionAprobacionResponse>(
      '/alianzas/comisiones/aprobar',
      data
    );
    return response.data;
  },

  // ==================== Payment Operations ====================

  /**
   * List payment history with optional filters
   */
  listarPagos: async (params?: {
    broker_id?: string;
    estado?: EstadoPago;
    limit?: number;
    offset?: number;
  }): Promise<PagoListResponse> => {
    const response = await apiClient.get<PagoListResponse>('/alianzas/pagos', {
      params,
    });
    return response.data;
  },

  /**
   * List payments by period
   */
  listarPagosPorPeriodo: async (
    periodoMes: number,
    periodoAnio: number,
    brokerId?: string
  ): Promise<Pago[]> => {
    const response = await apiClient.get<Pago[]>(
      `/alianzas/pagos/${periodoAnio}/${periodoMes}`,
      { params: brokerId ? { broker_id: brokerId } : undefined }
    );
    return response.data;
  },

  /**
   * Get a payment by ID
   */
  obtenerPago: async (pagoId: string): Promise<Pago> => {
    const response = await apiClient.get<Pago>(`/alianzas/pagos/${pagoId}`);
    return response.data;
  },

  /**
   * Update payment status
   */
  actualizarEstadoPago: async (
    pagoId: string,
    data: PagoEstadoUpdate
  ): Promise<Pago> => {
    const response = await apiClient.patch<Pago>(
      `/alianzas/pagos/${pagoId}/estado`,
      data
    );
    return response.data;
  },
};
