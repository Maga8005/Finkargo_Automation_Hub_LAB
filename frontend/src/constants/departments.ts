/**
 * Static departments data - eliminates API call for instant sidebar rendering
 *
 * This data is intentionally hardcoded because:
 * 1. Departments rarely change (organizational structure)
 * 2. Changes require code deployment anyway (backend also hardcodes this)
 * 3. Eliminates 2-5 second loading delay on login/refresh
 */
import type { Department } from '../types';

/**
 * Complete list of Finkargo departments
 * Keep in sync with backend/main.py /api/departments endpoint
 */
export const DEPARTMENTS: Department[] = [
  { id: 'operations', name: 'Operaciones', icon: 'Settings' },
  { id: 'sales', name: 'Ventas', icon: 'TrendingUp' },
  { id: 'finance', name: 'Finanzas', icon: 'AttachMoney' },
  { id: 'tesoreria', name: 'Tesorería', icon: 'AccountBalance' },
  { id: 'alianzas', name: 'Alianzas', icon: 'Handshake' },
  { id: 'hr', name: 'Recursos Humanos', icon: 'People' },
  { id: 'tech', name: 'Tecnología', icon: 'Code' },
  { id: 'support', name: 'Atención al Cliente', icon: 'Support' },
  { id: 'legal', name: 'Legal', icon: 'Gavel' },
  { id: 'collections', name: 'Collections', icon: 'Settings' },
];

/**
 * Get a department by ID
 * @param id - Department ID to look up
 * @returns Department object or undefined if not found
 */
export function getDepartmentById(id: string): Department | undefined {
  return DEPARTMENTS.find((dept) => dept.id === id);
}

/**
 * Get department name by ID (convenience helper)
 * @param id - Department ID to look up
 * @returns Department name or empty string if not found
 */
export function getDepartmentName(id: string): string {
  return getDepartmentById(id)?.name ?? '';
}
