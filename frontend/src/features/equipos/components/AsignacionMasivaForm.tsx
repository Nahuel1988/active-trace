import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAsignacionMasiva } from '@/features/equipos/hooks/useEquipoMutations';
import type { AsignacionMasivaResult } from '@/features/equipos/types';

const schema = z.object({
  materia_id: z.string().min(1, 'Seleccioná una materia'),
  carrera_id: z.string().min(1, 'Seleccioná una carrera'),
  cohorte_id: z.string().min(1, 'Seleccioná un cohorte'),
  rol: z.string().min(1, 'Seleccioná un rol'),
  comisiones: z.string().min(1, 'Ingresá al menos una comisión'),
  vigencia_desde: z.string().min(1, 'Requerido'),
  vigencia_hasta: z.string().min(1, 'Requerido'),
  responsables: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export function AsignacionMasivaForm() {
  const [step, setStep] = useState(1);
  const [result, setResult] = useState<AsignacionMasivaResult | null>(null);
  const mutation = useAsignacionMasiva();

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
        materia_id: data.materia_id,
        carrera_id: data.carrera_id,
        cohorte_id: data.cohorte_id,
        rol: data.rol,
        comisiones: data.comisiones.split(',').map((c) => c.trim()),
        vigencia_desde: data.vigencia_desde,
        vigencia_hasta: data.vigencia_hasta,
        user_ids: [],
        responsable: data.responsables ? data.responsables.length > 0 : false,
      },
      {
        onSuccess: (res) => {
          setResult(res);
          setStep(3);
        },
      },
    );
  };

  if (result) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-gray-900">Resultado</h2>
        <div className="mt-4 space-y-2 text-sm">
          <p className="text-green-700">
            Asignaciones creadas: {result.creadas}
          </p>
          {result.rechazadas > 0 && (
            <p className="text-red-600">
              Rechazadas: {result.rechazadas}
            </p>
          )}
          {result.errores && result.errores.length > 0 && (
            <ul className="list-inside list-disc text-red-600">
              {result.errores.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
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
      {step === 1 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Paso 1: Datos del equipo
          </h2>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Materia
            </label>
            <select
              {...register('materia_id')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">Seleccionar...</option>
              <option value="1">Matemática</option>
              <option value="2">Lengua</option>
            </select>
            {errors.materia_id && (
              <p className="mt-1 text-xs text-red-500">
                {errors.materia_id.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Carrera
            </label>
            <select
              {...register('carrera_id')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">Seleccionar...</option>
              <option value="1">Ingeniería</option>
              <option value="2">Licenciatura</option>
            </select>
            {errors.carrera_id && (
              <p className="mt-1 text-xs text-red-500">
                {errors.carrera_id.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Cohorte
            </label>
            <select
              {...register('cohorte_id')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">Seleccionar...</option>
              <option value="1">2025</option>
              <option value="2">2026</option>
            </select>
            {errors.cohorte_id && (
              <p className="mt-1 text-xs text-red-500">
                {errors.cohorte_id.message}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={() => setStep(2)}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Siguiente
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Paso 2: Asignación
          </h2>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Rol
            </label>
            <select
              {...register('rol')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">Seleccionar...</option>
              <option value="profesor">Profesor</option>
              <option value="tutor">Tutor</option>
              <option value="auxiliar">Auxiliar</option>
            </select>
            {errors.rol && (
              <p className="mt-1 text-xs text-red-500">
                {errors.rol.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Comisiones (separadas por coma)
            </label>
            <input
              type="text"
              {...register('comisiones')}
              placeholder="A, B, C"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.comisiones && (
              <p className="mt-1 text-xs text-red-500">
                {errors.comisiones.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Vigencia desde
            </label>
            <input
              type="date"
              {...register('vigencia_desde')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.vigencia_desde && (
              <p className="mt-1 text-xs text-red-500">
                {errors.vigencia_desde.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Vigencia hasta
            </label>
            <input
              type="date"
              {...register('vigencia_hasta')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.vigencia_hasta && (
              <p className="mt-1 text-xs text-red-500">
                {errors.vigencia_hasta.message}
              </p>
            )}
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Anterior
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {mutation.isPending ? 'Asignando...' : 'Asignar docentes'}
            </button>
          </div>
          {mutation.isError && (
            <p className="text-sm text-red-600">
              Error al crear asignaciones. Intentá de nuevo.
            </p>
          )}
        </div>
      )}
    </form>
  );
}
