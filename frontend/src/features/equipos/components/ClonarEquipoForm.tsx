import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useClonarEquipo } from '@/features/equipos/hooks/useEquipoMutations';
import type { ClonarResult } from '@/features/equipos/types';

const schema = z.object({
  origen_equipo_id: z.string().min(1, 'Seleccioná el equipo origen'),
  destino_carrera_id: z.string().min(1, 'Seleccioná la carrera destino'),
  destino_cohorte_id: z.string().min(1, 'Seleccioná el cohorte destino'),
  nueva_vigencia_desde: z.string().optional(),
  nueva_vigencia_hasta: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export function ClonarEquipoForm() {
  const [result, setResult] = useState<ClonarResult | null>(null);
  const mutation = useClonarEquipo();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = (data: FormData) => {
    mutation.mutate(
      {
        origen_equipo_id: data.origen_equipo_id,
        destino_carrera_id: data.destino_carrera_id,
        destino_cohorte_id: data.destino_cohorte_id,
        nueva_vigencia_desde: data.nueva_vigencia_desde || undefined,
        nueva_vigencia_hasta: data.nueva_vigencia_hasta || undefined,
      },
      {
        onSuccess: (res) => {
          setResult(res);
        },
      },
    );
  };

  if (result) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-gray-900">Resultado</h2>
        <div className="mt-4 space-y-2 text-sm">
          <p className="text-green-700">Clonadas: {result.clonadas}</p>
          {result.omitidas > 0 && (
            <p className="text-yellow-600">Omitidas: {result.omitidas}</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="rounded-lg border border-gray-200 bg-white p-6"
    >
      <h2 className="mb-4 text-lg font-semibold text-gray-900">
        Clonar equipo
      </h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Equipo origen
          </label>
          <select
            {...register('origen_equipo_id')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">Seleccionar...</option>
            <option value="1">Matemática — 2025</option>
            <option value="2">Lengua — 2025</option>
          </select>
          {errors.origen_equipo_id && (
            <p className="mt-1 text-xs text-red-500">
              {errors.origen_equipo_id.message}
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Carrera destino
          </label>
          <select
            {...register('destino_carrera_id')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">Seleccionar...</option>
            <option value="1">Ingeniería</option>
            <option value="2">Licenciatura</option>
          </select>
          {errors.destino_carrera_id && (
            <p className="mt-1 text-xs text-red-500">
              {errors.destino_carrera_id.message}
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Cohorte destino
          </label>
          <select
            {...register('destino_cohorte_id')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">Seleccionar...</option>
            <option value="1">2025</option>
            <option value="2">2026</option>
          </select>
          {errors.destino_cohorte_id && (
            <p className="mt-1 text-xs text-red-500">
              {errors.destino_cohorte_id.message}
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Nueva vigencia desde (opcional)
          </label>
          <input
            type="date"
            {...register('nueva_vigencia_desde')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Nueva vigencia hasta (opcional)
          </label>
          <input
            type="date"
            {...register('nueva_vigencia_hasta')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <button
          type="submit"
          disabled={mutation.isPending}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {mutation.isPending ? 'Clonando...' : 'Clonar equipo'}
        </button>

        {mutation.isError && (
          <p className="text-sm text-red-600">
            Error al clonar el equipo. Intentá de nuevo.
          </p>
        )}
      </div>
    </form>
  );
}
