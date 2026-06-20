export const tareasKeys = {
  all: ['tareas'] as const,
  lists: () => [...tareasKeys.all, 'list'] as const,
  list: (filters?: Record<string, string | undefined>) =>
    [...tareasKeys.lists(), filters] as const,
  details: () => [...tareasKeys.all, 'detail'] as const,
  detail: (id: string) => [...tareasKeys.details(), id] as const,
  comentarios: (tareaId: string) =>
    [...tareasKeys.all, tareaId, 'comentarios'] as const,
};
