import { useMutation, useQueryClient } from '@tanstack/react-query';
import { previewPadron, commitPadron } from '@/features/padron/services/padronApi';

export interface PreviewInput {
  materia_id: string;
  file: File;
}

export interface CommitInput {
  materia_id: string;
  import_id: string;
}

export function usePadronPreview() {
  return useMutation({
    mutationFn: ({ materia_id, file }: PreviewInput) => previewPadron(materia_id, file),
  });
}

export function usePadronCommit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ materia_id, import_id }: CommitInput) => commitPadron(materia_id, import_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['padron'] });
    },
  });
}
