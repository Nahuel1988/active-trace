import { useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { SlotDetail } from '@/features/encuentros/components/SlotDetail';
import { useSlot } from '@/features/encuentros/hooks/useEncuentros';
import { useEditarInstancia } from '@/features/encuentros/hooks/useEncuentroMutations';
import type { EstadoInstancia } from '@/features/encuentros/types';
import { Spinner } from '@/shared/components/Spinner';

export default function SlotDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: slot, isLoading, isError } = useSlot(id!);
  const editarInstancia = useEditarInstancia();

  const handleSaveInstancia = useCallback(
    (
      instancia_id: string,
      data: {
        estado?: EstadoInstancia;
        meet_url?: string | null;
        video_url?: string | null;
        comentario?: string | null;
      },
    ) => {
      editarInstancia.mutate({ instancia_id, data });
    },
    [editarInstancia],
  );

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    );
  }

  if (isError || !slot) {
    return (
      <div className="p-6">
        <p className="text-red-600">No se pudo cargar el slot</p>
        <button
          type="button"
          onClick={() => navigate('/encuentros')}
          className="mt-4 text-sm text-indigo-600 hover:text-indigo-800"
        >
          Volver a encuentros
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Back navigation */}
      <button
        type="button"
        onClick={() => navigate('/encuentros')}
        className="inline-flex items-center text-sm text-indigo-600 hover:text-indigo-800"
      >
        <svg className="mr-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Volver a encuentros
      </button>

      <SlotDetail
        slot={slot}
        onSaveInstancia={handleSaveInstancia}
        isSaving={editarInstancia.isPending}
      />
    </div>
  );
}
