// ── AvisoFormDialog ───────────────────────────────────────────────────────────
// Modal con formulario RHF + Zod para crear/editar avisos.
// Soporta dos variantes: 'dialog' (modal con backdrop) y 'page' (inline).

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCrearAviso, useActualizarAviso } from '@/features/avisos/hooks/useAvisos';
import type { Aviso, AvisoFormData, Alcance } from '@/features/avisos/types';

const avisoSchema = z
  .object({
    titulo: z.string().min(1, 'El título es requerido'),
    cuerpo: z.string().min(1, 'El cuerpo es requerido'),
    alcance: z.enum(['Global', 'PorMateria', 'PorCohorte', 'PorRol']),
    severidad: z.enum(['Informativo', 'Advertencia', 'Critico']),
    materia_id: z.string().nullable().optional(),
    cohorte_id: z.string().nullable().optional(),
    rol_destino: z.string().nullable().optional(),
    inicio_en: z.string().min(1, 'La fecha de inicio es requerida'),
    fin_en: z.string().min(1, 'La fecha de fin es requerida'),
    orden: z.number().int().nullable().optional(),
    requiere_ack: z.boolean(),
  })
  .refine(
    (data) => {
      if (!data.inicio_en || !data.fin_en) return true;
      return new Date(data.fin_en) > new Date(data.inicio_en);
    },
    { message: 'La fecha de fin debe ser posterior a la de inicio', path: ['fin_en'] },
  );

export type AvisoFormSchema = z.infer<typeof avisoSchema>;
export { avisoSchema };

interface AvisoFormDialogProps {
  open: boolean;
  onClose: () => void;
  aviso?: Aviso | null;
}

export function AvisoFormDialog({ open, onClose, aviso }: AvisoFormDialogProps) {
  const isEdit = !!aviso;
  const crearAviso = useCrearAviso();
  const actualizarAviso = useActualizarAviso();

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<AvisoFormSchema>({
    resolver: zodResolver(avisoSchema),
    defaultValues: {
      titulo: '',
      cuerpo: '',
      alcance: 'Global',
      severidad: 'Informativo',
      materia_id: null,
      cohorte_id: null,
      rol_destino: null,
      inicio_en: '',
      fin_en: '',
      orden: null,
      requiere_ack: false,
    },
  });

  const alcance = watch('alcance');

  useEffect(() => {
    if (aviso) {
      reset({
        titulo: aviso.titulo,
        cuerpo: aviso.cuerpo,
        alcance: aviso.alcance as Alcance,
        severidad: aviso.severidad,
        materia_id: aviso.materia_id,
        cohorte_id: aviso.cohorte_id,
        rol_destino: aviso.rol_destino,
        inicio_en: aviso.inicio_en.slice(0, 16),
        fin_en: aviso.fin_en.slice(0, 16),
        orden: aviso.orden,
        requiere_ack: aviso.requiere_ack,
      });
    } else {
      reset({
        titulo: '',
        cuerpo: '',
        alcance: 'Global',
        severidad: 'Informativo',
        materia_id: null,
        cohorte_id: null,
        rol_destino: null,
        inicio_en: '',
        fin_en: '',
        orden: null,
        requiere_ack: false,
      });
    }
  }, [aviso, reset]);

  const onSubmit = async (data: AvisoFormSchema) => {
    const payload: AvisoFormData = {
      ...data,
      materia_id: data.alcance === 'PorMateria' ? data.materia_id ?? null : null,
      cohorte_id: data.alcance === 'PorCohorte' ? data.cohorte_id ?? null : null,
      rol_destino: data.alcance === 'PorRol' ? data.rol_destino ?? null : null,
      orden: data.orden ?? null,
    };

    if (isEdit) {
      await actualizarAviso.mutateAsync({ id: aviso!.id, data: payload });
    } else {
      await crearAviso.mutateAsync(payload);
    }

    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          {isEdit ? 'Editar aviso' : 'Nuevo aviso'}
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Titulo */}
          <div>
            <label htmlFor="titulo" className="block text-sm font-medium text-gray-700">Título</label>
            <input id="titulo" type="text" {...register('titulo')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
            {errors.titulo && <p className="mt-1 text-sm text-red-600">{errors.titulo.message}</p>}
          </div>

          {/* Cuerpo */}
          <div>
            <label htmlFor="cuerpo" className="block text-sm font-medium text-gray-700">Cuerpo</label>
            <textarea id="cuerpo" rows={4} {...register('cuerpo')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
            {errors.cuerpo && <p className="mt-1 text-sm text-red-600">{errors.cuerpo.message}</p>}
          </div>

          {/* Alcance + Severidad row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="alcance" className="block text-sm font-medium text-gray-700">Alcance</label>
              <select id="alcance" {...register('alcance')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500">
                <option value="Global">Global</option>
                <option value="PorMateria">Por Materia</option>
                <option value="PorCohorte">Por Cohorte</option>
                <option value="PorRol">Por Rol</option>
              </select>
            </div>
            <div>
              <label htmlFor="severidad" className="block text-sm font-medium text-gray-700">Severidad</label>
              <select id="severidad" {...register('severidad')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500">
                <option value="Informativo">Informativo</option>
                <option value="Advertencia">Advertencia</option>
                <option value="Critico">Crítico</option>
              </select>
            </div>
          </div>

          {/* Conditional fields */}
          {alcance === 'PorMateria' && (
            <div>
              <label htmlFor="materia_id" className="block text-sm font-medium text-gray-700">Materia</label>
              <input id="materia_id" type="text" {...register('materia_id')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
            </div>
          )}

          {alcance === 'PorCohorte' && (
            <div>
              <label htmlFor="cohorte_id" className="block text-sm font-medium text-gray-700">Cohorte</label>
              <input id="cohorte_id" type="text" {...register('cohorte_id')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
            </div>
          )}

          {alcance === 'PorRol' && (
            <div>
              <label htmlFor="rol_destino" className="block text-sm font-medium text-gray-700">Rol destino</label>
              <input id="rol_destino" type="text" {...register('rol_destino')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
            </div>
          )}

          {/* Fechas row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="inicio_en" className="block text-sm font-medium text-gray-700">Inicio</label>
              <input id="inicio_en" type="datetime-local" {...register('inicio_en')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
              {errors.inicio_en && <p className="mt-1 text-sm text-red-600">{errors.inicio_en.message}</p>}
            </div>
            <div>
              <label htmlFor="fin_en" className="block text-sm font-medium text-gray-700">Fin</label>
              <input id="fin_en" type="datetime-local" {...register('fin_en')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
              {errors.fin_en && <p className="mt-1 text-sm text-red-600">{errors.fin_en.message}</p>}
            </div>
          </div>

          {/* Orden */}
          <div>
            <label htmlFor="orden" className="block text-sm font-medium text-gray-700">Orden</label>
            <input id="orden" type="number" {...register('orden', { valueAsNumber: true })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
          </div>

          {/* Requiere ack */}
          <div className="flex items-center gap-2">
            <input id="requiere_ack" type="checkbox" {...register('requiere_ack')}
              className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
            <label htmlFor="requiere_ack" className="text-sm font-medium text-gray-700">Requiere acknowledgment</label>
          </div>

          {/* Error de submit */}
          {(crearAviso.error || actualizarAviso.error) && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
              {(crearAviso.error ?? actualizarAviso.error) instanceof Error
                ? (crearAviso.error ?? actualizarAviso.error)!.message
                : 'Error al guardar el aviso'}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
              Cancelar
            </button>
            <button type="submit" disabled={isSubmitting}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50">
              {isSubmitting ? 'Guardando...' : isEdit ? 'Actualizar' : 'Crear'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
