/**
 * Error Utilities - Format API errors for user display
 */

/**
 * Pydantic validation error structure from FastAPI
 */
interface ValidationError {
  type: string;
  loc: (string | number)[];
  msg: string;
  input?: unknown;
}

/**
 * Translation map for common error messages to Spanish
 */
const ERROR_TRANSLATIONS: Record<string, string> = {
  'Field required': 'Campo requerido',
  'field required': 'Campo requerido',
  'Invalid value': 'Valor inválido',
  'invalid value': 'Valor inválido',
  'Client not found': 'Cliente no encontrado',
  'client not found': 'Cliente no encontrado',
  'Invalid contract type': 'Tipo de contrato inválido',
  'invalid contract type': 'Tipo de contrato inválido',
  'value is not a valid enumeration member': 'Tipo de contrato inválido',
  'NIT must be at least 5 characters': 'El NIT debe tener al menos 5 caracteres',
};

/**
 * Format field name from validation error location
 */
function formatFieldName(loc: (string | number)[]): string {
  const fieldMap: Record<string, string> = {
    'client_nit': 'NIT del cliente',
    'contract_type': 'Tipo de contrato',
    'rut_file': 'Archivo RUT',
  };

  // Get the last item in the location array (usually the field name)
  const field = loc[loc.length - 1];
  return fieldMap[String(field)] || String(field);
}

/**
 * Format a single Pydantic validation error
 */
function formatValidationError(error: ValidationError): string {
  const fieldName = formatFieldName(error.loc);

  // Try to find a translation for the error message
  const translatedMsg = ERROR_TRANSLATIONS[error.msg] || error.msg;

  return `${fieldName}: ${translatedMsg}`;
}

/**
 * Format API error for user display
 *
 * Handles various error formats from the backend:
 * - Pydantic validation errors (array of ValidationError objects)
 * - Simple string error messages
 * - Error objects with detail property
 * - Unknown error formats
 *
 * @param error - The error object from axios or other source
 * @returns User-friendly error message in Spanish
 */
export function formatApiError(error: unknown): string {
  // Default fallback message
  const defaultMessage = 'Error al procesar la solicitud. Por favor intente nuevamente.';

  try {
    // Type assertion for axios error structure
    const axiosError = error as { response?: { data?: { detail?: unknown } }; message?: string };

    // Handle axios error structure
    if (axiosError?.response?.data) {
      const { detail } = axiosError.response.data;

      // Case 1: Pydantic validation errors (array of error objects)
      if (Array.isArray(detail)) {
        const validationErrors = detail as ValidationError[];
        if (validationErrors.length > 0) {
          // Format all validation errors
          const messages = validationErrors.map(formatValidationError);
          return messages.join('; ');
        }
      }

      // Case 2: Simple string error message
      if (typeof detail === 'string') {
        // Check if we have a translation
        return ERROR_TRANSLATIONS[detail] || detail;
      }

      // Case 3: Object with message property
      if (typeof detail === 'object' && detail !== null && 'message' in detail) {
        const detailWithMessage = detail as { message: string };
        return ERROR_TRANSLATIONS[detailWithMessage.message] || detailWithMessage.message;
      }
    }

    // Handle direct error message
    if (axiosError?.message) {
      // Check for network errors
      if (axiosError.message.includes('Network Error') || axiosError.message.includes('ERR_NETWORK')) {
        return 'Error de conexión. Verifique su conexión a internet e intente nuevamente.';
      }

      return ERROR_TRANSLATIONS[axiosError.message] || axiosError.message;
    }

    // Handle string errors
    if (typeof error === 'string') {
      return ERROR_TRANSLATIONS[error] || error;
    }

  } catch (e) {
    // If anything goes wrong during error formatting, return default message
    console.error('Error formatting API error:', e);
  }

  return defaultMessage;
}

/**
 * Check if an error is a validation error (422)
 */
export function isValidationError(error: unknown): boolean {
  const axiosError = error as { response?: { status?: number } };
  return axiosError?.response?.status === 422;
}

/**
 * Check if an error is an authentication error (401)
 */
export function isAuthError(error: unknown): boolean {
  const axiosError = error as { response?: { status?: number } };
  return axiosError?.response?.status === 401;
}

/**
 * Check if an error is a forbidden error (403)
 */
export function isForbiddenError(error: unknown): boolean {
  const axiosError = error as { response?: { status?: number } };
  return axiosError?.response?.status === 403;
}

/**
 * Check if an error is a not found error (404)
 */
export function isNotFoundError(error: unknown): boolean {
  const axiosError = error as { response?: { status?: number } };
  return axiosError?.response?.status === 404;
}

/**
 * Check if an error is a timeout error
 */
export function isTimeoutError(error: unknown): boolean {
  const axiosError = error as { code?: string; message?: string };
  return axiosError?.code === 'ECONNABORTED' ||
         (axiosError?.message?.toLowerCase().includes('timeout') ?? false);
}

/**
 * Extract error message from various error types
 *
 * This is a comprehensive error extractor that handles:
 * - String errors directly
 * - Error instances with message property
 * - Axios errors with response.data.detail
 * - FastAPI validation errors (arrays)
 * - Timeout errors
 * - Network errors
 * - Objects with msg/message properties
 * - Fallback JSON stringification with circular reference protection
 *
 * @param error - Any error type
 * @param fallbackMessage - Optional fallback message (default: Spanish generic error)
 * @returns Human-readable error message string
 */
export function extractErrorMessage(
  error: unknown,
  fallbackMessage: string = 'Error al procesar la solicitud. Por favor intente nuevamente.'
): string {
  // Handle null/undefined
  if (error === null || error === undefined) {
    return fallbackMessage;
  }

  // Handle string errors directly
  if (typeof error === 'string') {
    return error || fallbackMessage;
  }

  // Type assertion for various error structures
  const errorObj = error as {
    response?: { data?: { detail?: unknown }; status?: number };
    message?: string;
    code?: string;
    msg?: string;
  };

  // Handle timeout errors specifically
  if (isTimeoutError(error)) {
    return 'La operación tardó demasiado tiempo. Por favor intente nuevamente.';
  }

  // Handle axios error structure
  if (errorObj?.response?.data) {
    const { detail } = errorObj.response.data;

    // Case 1: Pydantic validation errors (array of error objects)
    if (Array.isArray(detail)) {
      const validationErrors = detail as ValidationError[];
      if (validationErrors.length > 0) {
        const messages = validationErrors.map(formatValidationError);
        return messages.join('; ');
      }
    }

    // Case 2: Simple string error message
    if (typeof detail === 'string') {
      return ERROR_TRANSLATIONS[detail] || detail;
    }

    // Case 3: Object with message or msg property
    if (typeof detail === 'object' && detail !== null) {
      const detailObj = detail as { message?: string; msg?: string };
      if (detailObj.message) {
        return ERROR_TRANSLATIONS[detailObj.message] || detailObj.message;
      }
      if (detailObj.msg) {
        return ERROR_TRANSLATIONS[detailObj.msg] || detailObj.msg;
      }

      // Try to stringify the detail object safely
      try {
        const stringified = JSON.stringify(detail);
        if (stringified && stringified !== '{}') {
          return stringified;
        }
      } catch {
        // Circular reference or other JSON error - ignore
      }
    }
  }

  // Handle Error instances
  if (error instanceof Error) {
    // Check for network errors
    if (error.message.includes('Network Error') || error.message.includes('ERR_NETWORK')) {
      return 'Error de conexión. Verifique su conexión a internet e intente nuevamente.';
    }
    return ERROR_TRANSLATIONS[error.message] || error.message || fallbackMessage;
  }

  // Handle objects with message property
  if (errorObj?.message) {
    if (errorObj.message.includes('Network Error') || errorObj.message.includes('ERR_NETWORK')) {
      return 'Error de conexión. Verifique su conexión a internet e intente nuevamente.';
    }
    return ERROR_TRANSLATIONS[errorObj.message] || errorObj.message;
  }

  // Handle objects with msg property
  if (errorObj?.msg) {
    return ERROR_TRANSLATIONS[errorObj.msg] || errorObj.msg;
  }

  // Last resort: try to stringify the error object
  if (typeof error === 'object') {
    try {
      const stringified = JSON.stringify(error);
      if (stringified && stringified !== '{}' && stringified !== '[]') {
        return stringified;
      }
    } catch {
      // Circular reference or other JSON error - use fallback
    }
  }

  return fallbackMessage;
}
