import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  previewCalificaciones,
  commitCalificaciones,
  getUmbral,
  putUmbral,
} from '@/features/calificaciones/services/calificacionesApi';

export function useCalificacionesPreview() {
  return useMutation({
    mutationFn: ({ materia_id, file }: { materia_id: string; file: File }) =>
      previewCalificaciones(materia_id, file),
  });
}

export function useCalificacionesCommit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      materia_id,
      import_id,
      actividades_seleccionadas,
    }: {
      materia_id: string;
      import_id: string;
      actividades_seleccionadas: string[];
    }) => commitCalificaciones(materia_id, import_id, actividades_seleccionadas),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['atrasados'] });
      queryClient.invalidateQueries({ queryKey: ['ranking'] });
    },
  });
}

export function useUmbral(materia_id: string) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['umbral', materia_id],
    queryFn: () => getUmbral(materia_id),
    enabled: !!materia_id,
  });

  const mutation = useMutation({
    mutationFn: (umbral_porcentaje: number) => putUmbral(materia_id, umbral_porcentaje),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['umbral', materia_id] });
      queryClient.invalidateQueries({ queryKey: ['atrasados'] });
      queryClient.invalidateQueries({ queryKey: ['ranking'] });
    },
  });

  return { ...query, mutation };
}
