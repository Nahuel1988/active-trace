export const coloquiosKeys = {
  all: ['coloquios'] as const,
  lists: () => [...coloquiosKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) =>
    [...coloquiosKeys.lists(), filters] as const,
  metricas: () => [...coloquiosKeys.all, 'metricas'] as const,
  agenda: (filters?: Record<string, unknown>) =>
    [...coloquiosKeys.all, 'agenda', filters] as const,
  registroAcademico: (filters?: Record<string, unknown>) =>
    [...coloquiosKeys.all, 'registro-academico', filters] as const,
};
