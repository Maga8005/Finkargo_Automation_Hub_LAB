/**
 * Operations Service - API calls for Operations department
 */
import apiClient from '../api/clients/apiClient';
import type {
  ContractGenerationRequest,
  ContractGeneration,
  OperationsFilterParams,
  CotizacionData,
  SolicitudDesembolsoRequest,
  BankCertificateData,
  InstruccionMandatoRequest,
  DIANMandatoRequest,
} from '../types/legal';

const BASE_URL = '/operations';

export const operationsService = {
  /**
   * Request contract generation (Operations initiates)
   */
  async requestContractGeneration(
    request: ContractGenerationRequest
  ): Promise<ContractGeneration> {
    // Create FormData for multipart/form-data (backend expects Form parameters)
    const formData = new FormData();
    formData.append('client_nit', request.client_nit);
    formData.append('contract_type', request.contract_type || 'activos');

    const response = await apiClient.post<ContractGeneration>(
      `${BASE_URL}/contracts/generate`,
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
   * Get all approved contracts with optional filters
   * @param filters - Optional filter parameters
   * @param sortBy - Optional field to sort by
   * @param sortOrder - Optional sort order ('asc' or 'desc')
   */
  async getApprovedContracts(
    filters?: OperationsFilterParams,
    sortBy?: string,
    sortOrder?: string
  ): Promise<ContractGeneration[]> {
    const params: Record<string, string | number> = {};

    // Add filter parameters
    if (filters) {
      // Handle contract_types array - send as single contract_type for now
      // Backend expects single contract_type, frontend will handle multi-select UI
      if (filters.contract_types && filters.contract_types.length > 0) {
        // For now, if multiple types selected, don't filter by type (show all)
        // If single type, filter by that type
        if (filters.contract_types.length === 1) {
          params.contract_type = filters.contract_types[0];
        }
      }

      if (filters.client_name) {
        params.client_name = filters.client_name;
      }
      if (filters.client_nit) {
        params.client_nit = filters.client_nit;
      }
      if (filters.date_from) {
        params.date_from = filters.date_from;
      }
      if (filters.date_to) {
        params.date_to = filters.date_to;
      }
      if (filters.cupo_min !== undefined) {
        params.cupo_min = filters.cupo_min;
      }
      if (filters.cupo_max !== undefined) {
        params.cupo_max = filters.cupo_max;
      }
    }

    // Add sorting parameters
    if (sortBy) {
      params.sort_by = sortBy;
    }
    if (sortOrder) {
      params.sort_order = sortOrder;
    }

    const response = await apiClient.get<ContractGeneration[]>(
      `${BASE_URL}/contracts/approved`,
      { params }
    );
    return response.data;
  },

  /**
   * Request Otrosí contract generation (Operations initiates)
   */
  async requestOtrosiGeneration(
    clientNit: string
  ): Promise<ContractGeneration> {
    // Create FormData for multipart/form-data (backend expects Form parameters)
    const formData = new FormData();
    formData.append('client_nit', clientNit);
    formData.append('contract_type', 'otrosi');

    const response = await apiClient.post<ContractGeneration>(
      `${BASE_URL}/contracts/generate`,
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
   * Get all approved Otrosí contracts
   */
  async getApprovedOtrosis(): Promise<ContractGeneration[]> {
    return this.getApprovedContracts({ contract_types: ['otrosi'] });
  },

  /**
   * Request Inventario Bodega contract generation with RUT upload (Operations initiates)
   *
   * @param clientNit - Client NIT
   * @param rutFile - RUT PDF document for custodian operator
   * @param useAiExtraction - Use LandingAI for AI-powered extraction (for scanned PDFs)
   */
  async requestInventarioBodegaGeneration(
    clientNit: string,
    rutFile: File,
    useAiExtraction: boolean = false
  ): Promise<ContractGeneration> {
    // Create FormData for multipart/form-data upload
    const formData = new FormData();
    formData.append('client_nit', clientNit);
    formData.append('contract_type', 'inventario_bodega');
    formData.append('rut_file', rutFile);
    formData.append('use_ai_extraction', useAiExtraction.toString());

    const response = await apiClient.post<ContractGeneration>(
      `${BASE_URL}/contracts/generate`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        // Increase timeout for AI extraction (can take 30-60 seconds)
        timeout: useAiExtraction ? 120000 : 30000,
      }
    );
    return response.data;
  },

  /**
   * Get contract details by ID
   */
  async getContractDetails(contractId: string): Promise<ContractGeneration> {
    const response = await apiClient.get<ContractGeneration>(
      `${BASE_URL}/contracts/${contractId}`
    );
    return response.data;
  },

  /**
   * Download approved contract PDF
   */
  async downloadApprovedContractPdf(contractId: string): Promise<Blob> {
    const response = await apiClient.get(
      `${BASE_URL}/contracts/${contractId}/download/pdf`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },

  /**
   * Get all approved Paga Local Colombia contracts
   * Filters by all Paga Local CO contract types
   */
  async getApprovedPagaLocalCOContracts(
    filters?: OperationsFilterParams,
    sortBy?: string,
    sortOrder?: string
  ): Promise<ContractGeneration[]> {
    const pagaLocalCOTypes = [
      'pl_co_credito_aval_pj',
      'pl_co_mandato_pj',
      'pl_co_credito_aval_pn',
      'pl_co_mandato_pn',
      'pl_co_credito_no_aval',
      'pl_co_mandato_no_aval',
      'pl_co_mandato_im',
      'pl_co_solicitud_desembolso',
      'pl_co_dian_mandato_im',
    ];
    return this.getApprovedContracts(
      { ...filters, contract_types: pagaLocalCOTypes },
      sortBy,
      sortOrder
    );
  },

  /**
   * Parse Cotización PDF and extract data for Solicitud de Desembolso
   */
  async parseCotizacionPdf(file: File): Promise<CotizacionData> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<CotizacionData>(
      `${BASE_URL}/contracts/solicitud-desembolso/parse-cotizacion`,
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
   * Generate Solicitud de Desembolso contract
   */
  async generateSolicitudDesembolso(
    request: SolicitudDesembolsoRequest
  ): Promise<ContractGeneration> {
    const response = await apiClient.post<ContractGeneration>(
      `${BASE_URL}/contracts/solicitud-desembolso/generate`,
      request
    );
    return response.data;
  },

  /**
   * Parse Cotización PDF and extract data for Instrucción de Mandato
   */
  async parseCotizacionForMandato(file: File): Promise<CotizacionData> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<CotizacionData>(
      `${BASE_URL}/contracts/instruccion-mandato/parse-cotizacion`,
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
   * Parse Bank Certificate PDF and extract creditor bank account information
   */
  async parseBankCertificate(file: File): Promise<BankCertificateData> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<BankCertificateData>(
      `${BASE_URL}/contracts/instruccion-mandato/parse-bank-certificate`,
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
   * Generate Instrucción de Mandato contract
   */
  async generateInstruccionMandato(
    request: InstruccionMandatoRequest
  ): Promise<ContractGeneration> {
    const response = await apiClient.post<ContractGeneration>(
      `${BASE_URL}/contracts/instruccion-mandato/generate`,
      request
    );
    return response.data;
  },

  /**
   * Parse Cotización PDF and extract data for DIAN Mandato (IM)
   */
  async parseCotizacionForDIANMandato(file: File): Promise<CotizacionData> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<CotizacionData>(
      `${BASE_URL}/contracts/dian-mandato/parse-cotizacion`,
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
   * Generate DIAN Mandato (IM) contract - simplified, no creditors
   */
  async generateDIANMandato(
    request: DIANMandatoRequest
  ): Promise<ContractGeneration> {
    const response = await apiClient.post<ContractGeneration>(
      `${BASE_URL}/contracts/dian-mandato/generate`,
      request
    );
    return response.data;
  },
};
