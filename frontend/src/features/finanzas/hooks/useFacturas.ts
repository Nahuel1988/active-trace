import { useQuery } from '@tanstack/react-query';
import { fetchFacturas, fetchFactura } from '@/features/finanzas/services/facturasApi';
import { facturasKeys } from '@/features/finanzas/services/facturasKeys';
import type { FacturaFilters } from '@/features/finanzas/types';

export function useFacturas(filters: FacturaFilters) {
  return useQuery({
    queryKey: facturasKeys.list(filters),
    queryFn: () => fetchFacturas(filters),
  });
}

export function useFactura(id: string) {
  return useQuery({
    queryKey: facturasKeys.detail(id),
    queryFn: () => fetchFactura(id),
    enabled: !!id,
  });
}
