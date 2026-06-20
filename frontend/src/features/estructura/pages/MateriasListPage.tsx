// ── MateriasListPage ──────────────────────────────────────────────────────────
// Página de listado de materias con creación (clave_plus obligatoria).

import { useState } from 'react';
import { Spinner } from '@/shared/components/Spinner';
import { MateriaTable } from '@/features/estructura/components/MateriaTable';
import { MateriaFormDialog } from '@/features/estructura/components/MateriaFormDialog';
import {
  useMaterias,
  useCrearMateria,
} from '@/features/estructura/hooks/useEstructura';
import type { MateriaFormData } from '@/features/estructura/types';

export default function MateriasListPage() {
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: materias, isLoading } = useMaterias();
  const crearMateria = useCrearMateria();

  const handleSubmit = (data: MateriaFormData) => {
    crearMateria.mutate(data, {
      onSuccess: () => setDialogOpen(false),
    });
  };

  const errorMessage = crearMateria.isError
    ? (crearMateria.error as Error).message
    : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Materias</h1>
          <p className="mt-1 text-sm text-gray-500">
            Gestión de materias de la institución.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setDialogOpen(true)}
          className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Nueva materia
        </button>
      </div>

      {isLoading ? (
        <Spinner className="py-8" />
      ) : (
        <MateriaTable materias={materias ?? []} />
      )}

      <MateriaFormDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleSubmit}
        isPending={crearMateria.isPending}
        error={errorMessage}
      />
    </div>
  );
}
