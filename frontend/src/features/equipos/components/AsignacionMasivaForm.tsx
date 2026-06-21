import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery } from '@tanstack/react-query';
import { useAsignacionMasiva } from '@/features/equipos/hooks/useEquipoMutations';
import { useCarreras, useMaterias, useCohortes } from '@/features/estructura/hooks/useEstructura';
import { fetchRoles } from '@/features/admin/services/usuariosApi';
import type { AsignacionMasivaResult } from '@/features/equipos/types';

const schema = z.object({
  materia_id: z.string().min(1, 'Seleccioná una materia'),
  carrera_id: z.string().min(1, 'Seleccioná una carrera'),
  cohorte_id: z.string().min(1, 'Seleccioná un cohorte'),
  role_id: z.string().min(1, 'Seleccioná un rol'),
  comisiones: z.string().min(1, 'Ingresá al menos una comisión'),
  desde: z.string().min(1, 'Requerido'),
  hasta: z.string().optional(),
  usuario_ids: z.string().min(1, 'Ingresá al menos un usuario (separados por coma)'),
  responsable_id: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export function AsignacionMasivaForm() {
  const [step, setStep] = useState(1);
  const [result, setResult] = useState<AsignacionMasivaResult | null>(null);
  const mutation = useAsignacionMasiva();

  const { data: carreras = [], isLoading: loadingCarreras } = useCarreras();
  const { data: materias = [], isLoading: loadingMaterias } = useMaterias();
  const { data: cohortes = [], isLoading: loadingCohortes } = useCohortes();
  const { data: roles = [], isLoading: loadingRoles } = useQuery({
    queryKey: ['rbac', 'roles'],
    queryFn: fetchRoles,
  });

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
        usuario_ids: data.usuario_ids.split(',').map((u) => u.trim()).filter(Boolean),
        role_id: data.role_id,
        materia_id: data.materia_id,
        carrera_id: data.carrera_id,
        cohorte_id: data.cohorte_id,
        comisiones: data.comisiones.split(',').map((c) => c.trim()).filter(Boolean),
        desde: data.desde,
        hasta: data.hasta || undefined,
        responsable_id: data.responsable_id || undefined,
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
          <p className="text-green-700">Asignaciones creadas: {result.creadas}</p>
          {result.rechazadas.length > 0 && (
            <div>
              <p className="font-medium text-red-600">Rechazadas: {result.rechazadas.length}</p>
              <ul className="list-inside list-disc text-red-600">
                {result.rechazadas.map((r, i) => (
                  <li key={i}>{r.usuario_id}: {r.motivo}</li>
                ))}
              </ul>
            </div>
          )}
          {result.omitidas.length > 0 && (
            <div>
              <p className="font-medium text-yellow-600">Omitidas: {result.omitidas.length}</p>
              <ul className="list-inside list-disc text-yellow-600">
                {result.omitidas.map((o, i) => (
                  <li key={i}>{o.usuario_id}: {o.motivo}</li>
                ))}
              </ul>
            </div>
          )}
          <button
            type="button"
            onClick={() => { setResult(null); setStep(1); }}
            className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Nueva asignación
          </button>
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
          <h2 className="text-lg font-semibold text-gray-900">Paso 1: Datos del equipo</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700">Materia</label>
            <select
              {...register('materia_id')}
              disabled={loadingMaterias}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50"
            >
              <option value="">{loadingMaterias ? 'Cargando...' : 'Seleccionar...'}</option>
              {(materias as Array<{ id: string; nombre: string; codigo?: string }>).map((m) => (
                <option key={m.id} value={m.id}>
                  {m.codigo ? `${m.codigo} — ` : ''}{m.nombre}
                </option>
              ))}
            </select>
            {errors.materia_id && <p className="mt-1 text-xs text-red-500">{errors.materia_id.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Carrera</label>
            <select
              {...register('carrera_id')}
              disabled={loadingCarreras}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50"
            >
              <option value="">{loadingCarreras ? 'Cargando...' : 'Seleccionar...'}</option>
              {carreras.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
            {errors.carrera_id && <p className="mt-1 text-xs text-red-500">{errors.carrera_id.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Cohorte</label>
            <select
              {...register('cohorte_id')}
              disabled={loadingCohortes}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50"
            >
              <option value="">{loadingCohortes ? 'Cargando...' : 'Seleccionar...'}</option>
              {(cohortes as Array<{ id: string; nombre?: string; etiqueta?: string }>).map((c) => (
                <option key={c.id} value={c.id}>{c.nombre ?? c.etiqueta}</option>
              ))}
            </select>
            {errors.cohorte_id && <p className="mt-1 text-xs text-red-500">{errors.cohorte_id.message}</p>}
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
          <h2 className="text-lg font-semibold text-gray-900">Paso 2: Asignación</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700">Rol</label>
            <select
              {...register('role_id')}
              disabled={loadingRoles}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50"
            >
              <option value="">{loadingRoles ? 'Cargando...' : 'Seleccionar...'}</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>{r.nombre}</option>
              ))}
            </select>
            {errors.role_id && <p className="mt-1 text-xs text-red-500">{errors.role_id.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Usuarios (UUIDs separados por coma)
            </label>
            <input
              type="text"
              {...register('usuario_ids')}
              placeholder="uuid-1, uuid-2, uuid-3"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.usuario_ids && <p className="mt-1 text-xs text-red-500">{errors.usuario_ids.message}</p>}
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
            {errors.comisiones && <p className="mt-1 text-xs text-red-500">{errors.comisiones.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Responsable (UUID opcional)
            </label>
            <input
              type="text"
              {...register('responsable_id')}
              placeholder="UUID del responsable"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Desde</label>
            <input
              type="date"
              {...register('desde')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.desde && <p className="mt-1 text-xs text-red-500">{errors.desde.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Hasta (opcional)</label>
            <input
              type="date"
              {...register('hasta')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
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
