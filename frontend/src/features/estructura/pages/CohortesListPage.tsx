// ── CohortesListPage ──────────────────────────────────────────────────────────
// Página de listado de cohortes con creación y eliminación.

import { useState } from 'react';
import { Spinner } from '@/shared/components/Spinner';
import { CohorteTable } from '@/features/estructura/components/CohorteTable';
import { CohorteFormDialog } from '@/features/estructura/components/CohorteFormDialog';
import {
  useCohortes,
  useCrearCohorte,
  useEliminarCohorte,
} from '@/features/estructura/hooks/useEstructura';
import type { CohorteFormData } from '@/features/estructura/types';

export default function CohortesListPage() {
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: cohortes, isLoading } = useCohortes();
  const crearCohorte = useCrearCohorte();
  const eliminarCohorte = useEliminarCohorte();

  const handleSubmit = (data: CohorteFormData) => {
    crearCohorte.mutate(data, {
      onSuccess: () => setDialogOpen(false),
    });
  };

  const handleEliminar = (id: string) => {
    eliminarCohorte.mutate(id);
  };

  const errorMessage = crearCohorte.isError
    ? (crearCohorte.error as Error).message
    : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cohortes</h1>
          <p className="mt-1 text-sm text-gray-500">
            Gestión de cohortes académicas de la institución.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setDialogOpen(true)}
          className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Nueva cohorte
        </button>
      </div>

      {isLoading ? (
        <Spinner className="py-8" />
      ) : (
        <CohorteTable
          cohortes={cohortes ?? []}
          onEliminar={handleEliminar}
        />
      )}

      <CohorteFormDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleSubmit}
        isPending={crearCohorte.isPending}
        error={errorMessage}
      />
    </div>
  );
}
