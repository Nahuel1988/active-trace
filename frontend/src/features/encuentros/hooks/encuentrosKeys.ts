export const encuentrosKeys = {
  all: ['encuentros'] as const,
  slots: {
    all: () => [...encuentrosKeys.all, 'slots'] as const,
    lists: () => [...encuentrosKeys.slots.all(), 'list'] as const,
    list: (filters?: { materia_id?: string }) =>
      [...encuentrosKeys.slots.lists(), filters] as const,
    details: () => [...encuentrosKeys.slots.all(), 'detail'] as const,
    detail: (id: string) => [...encuentrosKeys.slots.details(), id] as const,
  },
  instancias: {
    all: () => [...encuentrosKeys.all, 'instancias'] as const,
    lists: () => [...encuentrosKeys.instancias.all(), 'list'] as const,
    list: (filters?: Record<string, unknown>) =>
      [...encuentrosKeys.instancias.lists(), filters] as const,
    details: () => [...encuentrosKeys.instancias.all(), 'detail'] as const,
    detail: (id: string) => [...encuentrosKeys.instancias.details(), id] as const,
  },
};
