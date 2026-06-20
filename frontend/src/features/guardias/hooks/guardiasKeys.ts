import type { GuardiaFiltros } from '../types';

export const guardiasKeys = {
  all: ['guardias'] as const,
  lists: () => [...guardiasKeys.all, 'list'] as const,
  list: (filters?: GuardiaFiltros) =>
    [...guardiasKeys.lists(), filters ?? 'all'] as const,
  details: () => [...guardiasKeys.all, 'detail'] as const,
  detail: (id: string) => [...guardiasKeys.details(), id] as const,
};
