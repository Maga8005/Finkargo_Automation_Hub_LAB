/**
 * Department service - handles department-related API calls
 */
import apiClient from '../api/clients/apiClient';
import type { Department } from '../types';

/**
 * Type guard to validate Department objects
 */
function isValidDepartment(dept: unknown): dept is Department {
  return (
    typeof dept === 'object' &&
    dept !== null &&
    'id' in dept &&
    typeof (dept as { id: unknown }).id === 'string' &&
    (dept as { id: string }).id.length > 0 &&
    'name' in dept &&
    typeof (dept as { name: unknown }).name === 'string' &&
    (dept as { name: string }).name.length > 0 &&
    'icon' in dept &&
    typeof (dept as { icon: unknown }).icon === 'string' &&
    (dept as { icon: string }).icon.length > 0
  );
}

export const departmentService = {
  /**
   * Get all departments with comprehensive validation
   * @throws {Error} If API response is invalid or no valid departments found
   */
  getDepartments: async (): Promise<Department[]> => {
    try {
      console.log('[departmentService] Fetching departments from API...');
      const response = await apiClient.get<{ departments: Department[] }>('/departments');

      console.log('[departmentService] Received response:', {
        status: response.status,
        hasData: !!response.data,
        hasDepartments: !!response.data?.departments,
      });

      // Validate response structure
      if (!response.data) {
        console.error('[departmentService] Response has no data property');
        throw new Error('Respuesta de API inválida: sin datos');
      }

      if (!response.data.departments) {
        console.error('[departmentService] Response data has no departments property', response.data);
        throw new Error('Respuesta de API inválida: sin propiedad departments');
      }

      if (!Array.isArray(response.data.departments)) {
        console.error('[departmentService] departments is not an array', {
          type: typeof response.data.departments,
          value: response.data.departments,
        });
        throw new Error('Respuesta de API inválida: departments no es un array');
      }

      // Filter and validate departments
      const allDepartments = response.data.departments;
      const validDepartments = allDepartments.filter((dept, index) => {
        const isValid = isValidDepartment(dept);
        if (!isValid) {
          console.warn(`[departmentService] Invalid department at index ${index}:`, dept);
        }
        return isValid;
      });

      console.log('[departmentService] Validation results:', {
        total: allDepartments.length,
        valid: validDepartments.length,
        invalid: allDepartments.length - validDepartments.length,
      });

      if (validDepartments.length === 0) {
        console.error('[departmentService] No valid departments found in response');
        throw new Error('No se encontraron departamentos válidos');
      }

      return validDepartments;
    } catch (error) {
      // Enhanced error logging
      if (error instanceof Error) {
        console.error('[departmentService] Error fetching departments:', {
          message: error.message,
          stack: error.stack,
        });
      } else {
        console.error('[departmentService] Unknown error fetching departments:', error);
      }

      // Re-throw with context
      throw error;
    }
  },
};
