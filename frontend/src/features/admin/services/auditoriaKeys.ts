import type { AuditFilters, AuditLogFilters } from '../types';

export const auditoriaKeys = {
  all: ['auditoria'] as const,
  metricas: (filters: AuditFilters) =>
    [...auditoriaKeys.all, 'metricas', filters] as const,
  log: (filters: AuditLogFilters) =>
    [...auditoriaKeys.all, 'log', filters] as const,
};
