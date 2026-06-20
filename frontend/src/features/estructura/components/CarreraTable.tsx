// ── CarreraTable ─────────────────────────────────────────────────────────────
// Tabla de carreras con indicador de estado y soporte para crear.

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Spinner } from '@/shared/components/Spinner';
import { useCarreras, useCrearCarrera } from '@/features/estructura/hooks/useEstructura';
import type { CarreraFormData } from '@/features/estructura/types';

const carreraSchema = z.object({
  codigo: z.string().min(1, 'El código es requerido'),
  nombre: z.string().min(1, 'El nombre es requerido'),
});

export function CarreraTable() {
  const { data: carreras, isLoading } = useCarreras();
  const crearCarrera = useCrearCarrera();
  const [showForm, setShowForm] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CarreraFormData>({
    resolver: zodResolver(carreraSchema),
  });

  const onSubmit = (data: CarreraFormData) => {
    crearCarrera.mutate(data, {
      onSuccess: () => {
        reset();
        setShowForm(false);
      },
    });
  };

  if (isLoading) return <Spinner className="py-8" />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Carreras</h2>
        <button
          type="button"
          onClick={() => setShowForm(!showForm)}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500"
        >
          {showForm ? 'Cancelar' : 'Nueva carrera'}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-3"
        >
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Código
              </label>
              <input
                {...register('codigo')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              {errors.codigo && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.codigo.message}
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Nombre
              </label>
              <input
                {...register('nombre')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              {errors.nombre && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.nombre.message}
                </p>
              )}
            </div>
          </div>
          {crearCarrera.isError && (
            <p className="text-sm text-red-600">
              {(crearCarrera.error as Error).message}
            </p>
          )}
          <button
            type="submit"
            disabled={crearCarrera.isPending}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {crearCarrera.isPending ? 'Guardando...' : 'Guardar'}
          </button>
        </form>
      )}

      {carreras && carreras.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Código
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Nombre
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Estado
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {carreras.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-900">{c.codigo}</td>
                  <td className="px-4 py-3 text-gray-900">{c.nombre}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        c.estado === 'activa'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {c.estado}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="py-8 text-center text-sm text-gray-500">
          No hay carreras registradas.
        </p>
      )}
    </div>
  );
}
