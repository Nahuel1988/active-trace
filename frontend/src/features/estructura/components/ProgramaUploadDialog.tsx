// ── ProgramaUploadDialog ──────────────────────────────────────────────────────
// Modal para subir un programa de materia (PDF).

import { useState, useRef } from 'react';
import { useCrearPrograma } from '@/features/estructura/hooks/useEstructura';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export function ProgramaUploadDialog({ isOpen, onClose }: Props) {
  const crearPrograma = useCrearPrograma();
  const fileRef = useRef<HTMLInputElement>(null);
  const [titulo, setTitulo] = useState('');
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const file = fileRef.current?.files?.[0];
    if (!file) {
      setError('Debe seleccionar un archivo PDF.');
      return;
    }
    if (file.type !== 'application/pdf') {
      setError('Solo se permiten archivos PDF.');
      return;
    }
    if (!titulo.trim()) {
      setError('El título es requerido.');
      return;
    }

    const formData = new FormData();
    formData.append('archivo', file);
    formData.append('titulo', titulo.trim());

    crearPrograma.mutate(formData, {
      onSuccess: () => {
        setTitulo('');
        if (fileRef.current) fileRef.current.value = '';
        onClose();
      },
      onError: (err) => {
        setError((err as Error).message);
      },
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          Subir programa
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Título
            </label>
            <input
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="Programa 2025"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Archivo PDF
            </label>
            <input
              ref={fileRef}
              type="file"
              accept="application/pdf"
              className="mt-1 block w-full text-sm text-gray-500 file:mr-3 file:rounded-md file:border-0 file:bg-indigo-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-indigo-700 hover:file:bg-indigo-100"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
          {crearPrograma.isError && (
            <p className="text-sm text-red-600">
              {(crearPrograma.error as Error).message}
            </p>
          )}

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={crearPrograma.isPending}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {crearPrograma.isPending ? 'Subiendo...' : 'Subir'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
