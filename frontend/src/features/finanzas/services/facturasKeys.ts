import type { FacturaFilters } from '@/features/finanzas/types';

export const facturasKeys = {
  all: ['facturas'] as const,
  list: (filters: FacturaFilters) => ['facturas', 'list', filters] as const,
  detail: (id: string) => ['facturas', 'detail', id] as const,
};
