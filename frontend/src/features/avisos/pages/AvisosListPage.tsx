// ── AvisosListPage ────────────────────────────────────────────────────────────
// Lista de avisos con tabla y botón para crear nuevo aviso en modal.

import { useState } from 'react';
import { useAvisos } from '@/features/avisos/hooks/useAvisos';
import { AvisoTable } from '@/features/avisos/components/AvisoTable';
import { AvisoFormDialog } from '@/features/avisos/components/AvisoFormDialog';
import { Spinner } from '@/shared/components/Spinner';
import type { Aviso } from '@/features/avisos/types';

export default function AvisosListPage() {
  const { data: avisos, isLoading, isError, error } = useAvisos();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedAviso, setSelectedAviso] = useState<Aviso | null>(null);

  const handleNew = () => {
    setSelectedAviso(null);
    setDialogOpen(true);
  };

  const handleEdit = (aviso: Aviso) => {
    setSelectedAviso(aviso);
    setDialogOpen(true);
  };

  const handleClose = () => {
    setDialogOpen(false);
    setSelectedAviso(null);
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
        {error instanceof Error ? error.message : 'Error al cargar los avisos'}
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Avisos</h1>
        <button
          onClick={handleNew}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
        >
          Nuevo aviso
        </button>
      </div>

      <AvisoTable avisos={avisos ?? []} onEdit={handleEdit} />

      <AvisoFormDialog
        open={dialogOpen}
        onClose={handleClose}
        aviso={selectedAviso}
      />
    </div>
  );
}
