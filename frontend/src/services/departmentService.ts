/**
 * Department service - handles department-related API calls
 */
import apiClient from '../api/clients/apiClient';
import type { Department } from '../types';

export const departmentService = {
  /**
   * Get all departments
   */
  getDepartments: async (): Promise<Department[]> => {
    const response = await apiClient.get<{ departments: Department[] }>('/departments');
    return response.data.departments;
  },
};
