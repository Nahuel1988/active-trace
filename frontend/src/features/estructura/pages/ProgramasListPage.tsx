// ── ProgramasListPage ─────────────────────────────────────────────────────────
// Página de listado de programas con tabla y diálogo de subida.

import { useState } from 'react';
import { ProgramaTable } from '@/features/estructura/components/ProgramaTable';
import { ProgramaUploadDialog } from '@/features/estructura/components/ProgramaUploadDialog';

export default function ProgramasListPage() {
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Programas</h1>
          <p className="mt-1 text-sm text-gray-500">
            Programas de materia por carrera y cohorte.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setUploadOpen(true)}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Subir programa
        </button>
      </div>

      <ProgramaTable />
      <ProgramaUploadDialog
        isOpen={uploadOpen}
        onClose={() => setUploadOpen(false)}
      />
    </div>
  );
}
