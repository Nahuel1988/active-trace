// ── useAuditoria ──────────────────────────────────────────────────────────────
// Hooks de TanStack Query para métricas y log de auditoría.

import { useQuery } from '@tanstack/react-query';
import { fetchMetricas, fetchAuditLog } from '../services/auditoriaApi';
import { auditoriaKeys } from '../services/auditoriaKeys';
import type { AuditFilters, AuditLogFilters } from '../types';

export function useMetricasAuditoria(filters: AuditFilters) {
  return useQuery({
    queryKey: auditoriaKeys.metricas(filters),
    queryFn: () => fetchMetricas(filters),
  });
}

export function useAuditLog(filters: AuditLogFilters) {
  return useQuery({
    queryKey: auditoriaKeys.log(filters),
    queryFn: () => fetchAuditLog(filters),
  });
}
