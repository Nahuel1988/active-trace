import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { SlotCreateRequest } from '../types';

const encuentroFormSchema = z
  .object({
    modo: z.union([z.literal('recurrente'), z.literal('unico')]),
    materia_id: z.string().min(1, 'La materia es requerida'),
    titulo: z.string().min(1, 'El título es requerido'),
    dia_semana: z.string().min(1, 'El día es requerido'),
    hora: z.string().min(1, 'La hora es requerida'),
    fecha_inicio: z.string().min(1, 'La fecha de inicio es requerida'),
    cant_semanas: z.coerce.number().int().min(1).optional().nullable(),
    fecha_unica: z.string().optional().nullable(),
    meet_url: z
      .string()
      .url('Ingresá una URL válida')
      .optional()
      .or(z.literal('')),
    vig_desde: z.string().min(1, 'La vigencia desde es requerida'),
    vig_hasta: z.string().optional().nullable(),
  })
  .superRefine((data, ctx) => {
    if (data.modo === 'recurrente') {
      if (!data.cant_semanas || data.cant_semanas < 1) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Debe indicar la cantidad de semanas',
          path: ['cant_semanas'],
        });
      }
    } else {
      if (!data.fecha_unica) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Debe indicar la fecha única',
          path: ['fecha_unica'],
        });
      }
    }
  });

type EncuentroFormValues = z.infer<typeof encuentroFormSchema>;

const DIAS_SEMANA = [
  { value: 'lunes', label: 'Lunes' },
  { value: 'martes', label: 'Martes' },
  { value: 'miércoles', label: 'Miércoles' },
  { value: 'jueves', label: 'Jueves' },
  { value: 'viernes', label: 'Viernes' },
  { value: 'sábado', label: 'Sábado' },
  { value: 'domingo', label: 'Domingo' },
];

const defaultValues: EncuentroFormValues = {
  modo: 'recurrente',
  materia_id: '',
  titulo: '',
  dia_semana: '',
  hora: '',
  fecha_inicio: '',
  cant_semanas: null,
  fecha_unica: null,
  meet_url: '',
  vig_desde: '',
  vig_hasta: null,
};

interface EncuentroFormDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: SlotCreateRequest) => void;
  isSubmitting?: boolean;
}

export function EncuentroFormDialog({ open, onClose, onSubmit, isSubmitting }: EncuentroFormDialogProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<EncuentroFormValues>({
    resolver: zodResolver(encuentroFormSchema),
    defaultValues,
  });

  const modo = watch('modo');

  if (!open) return null;

  const onFormSubmit = (data: EncuentroFormValues) => {
    onSubmit({
      ...data,
      cant_semanas: data.modo === 'recurrente' ? data.cant_semanas : null,
      fecha_unica: data.modo === 'unico' ? data.fecha_unica : null,
      meet_url: data.meet_url || null,
      vig_hasta: data.vig_hasta || null,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Nuevo slot de encuentro</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 hover:text-gray-600"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
          {/* Modo toggle */}
          <fieldset>
            <legend className="text-sm font-medium text-gray-700">Tipo</legend>
            <div className="mt-1 flex rounded-md border border-gray-300 overflow-hidden">
              <label
                className={`flex-1 cursor-pointer px-4 py-2 text-center text-sm font-medium ${
                  modo === 'recurrente'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <input
                  type="radio"
                  value="recurrente"
                  {...register('modo')}
                  className="sr-only"
                />
                Recurrente
              </label>
              <label
                className={`flex-1 cursor-pointer px-4 py-2 text-center text-sm font-medium ${
                  modo === 'unico'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <input
                  type="radio"
                  value="unico"
                  {...register('modo')}
                  className="sr-only"
                />
                Único
              </label>
            </div>
          </fieldset>

          {/* Materia */}
          <div>
            <label htmlFor="materia_id" className="block text-sm font-medium text-gray-700">ID de Materia</label>
            <input
              id="materia_id"
              type="text"
              {...register('materia_id')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="UUID de la materia"
            />
            {errors.materia_id && <p className="mt-1 text-xs text-red-600">{errors.materia_id.message}</p>}
          </div>

          {/* Título */}
          <div>
            <label htmlFor="titulo" className="block text-sm font-medium text-gray-700">Título</label>
            <input
              id="titulo"
              type="text"
              {...register('titulo')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.titulo && <p className="mt-1 text-xs text-red-600">{errors.titulo.message}</p>}
          </div>

          {/* Día de semana */}
          <div>
            <label htmlFor="dia_semana" className="block text-sm font-medium text-gray-700">Día de semana</label>
            <select
              id="dia_semana"
              {...register('dia_semana')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">Seleccioná un día</option>
              {DIAS_SEMANA.map((d) => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
            {errors.dia_semana && <p className="mt-1 text-xs text-red-600">{errors.dia_semana.message}</p>}
          </div>

          {/* Hora */}
          <div>
            <label htmlFor="hora" className="block text-sm font-medium text-gray-700">Hora</label>
            <input
              id="hora"
              type="time"
              {...register('hora')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.hora && <p className="mt-1 text-xs text-red-600">{errors.hora.message}</p>}
          </div>

          {/* Fecha inicio */}
          <div>
            <label htmlFor="fecha_inicio" className="block text-sm font-medium text-gray-700">Fecha de inicio</label>
            <input
              id="fecha_inicio"
              type="date"
              {...register('fecha_inicio')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.fecha_inicio && <p className="mt-1 text-xs text-red-600">{errors.fecha_inicio.message}</p>}
          </div>

          {/* Condicional: cant_semanas (recurrente) */}
          {modo === 'recurrente' && (
            <div>
              <label htmlFor="cant_semanas" className="block text-sm font-medium text-gray-700">Cantidad de semanas</label>
              <input
                id="cant_semanas"
                type="number"
                min={1}
                {...register('cant_semanas')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              {errors.cant_semanas && <p className="mt-1 text-xs text-red-600">{errors.cant_semanas.message}</p>}
            </div>
          )}

          {/* Condicional: fecha_unica (único) */}
          {modo === 'unico' && (
            <div>
              <label htmlFor="fecha_unica" className="block text-sm font-medium text-gray-700">Fecha única</label>
              <input
                id="fecha_unica"
                type="date"
                {...register('fecha_unica')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              {errors.fecha_unica && <p className="mt-1 text-xs text-red-600">{errors.fecha_unica.message}</p>}
            </div>
          )}

          {/* Meet URL (opcional) */}
          <div>
            <label htmlFor="meet_url" className="block text-sm font-medium text-gray-700">
              Meet URL <span className="text-gray-400">(opcional)</span>
            </label>
            <input
              id="meet_url"
              type="url"
              {...register('meet_url')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="https://meet.google.com/..."
            />
            {errors.meet_url && <p className="mt-1 text-xs text-red-600">{errors.meet_url.message}</p>}
          </div>

          {/* Vigencia desde */}
          <div>
            <label htmlFor="vig_desde" className="block text-sm font-medium text-gray-700">Vigencia desde</label>
            <input
              id="vig_desde"
              type="date"
              {...register('vig_desde')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.vig_desde && <p className="mt-1 text-xs text-red-600">{errors.vig_desde.message}</p>}
          </div>

          {/* Vigencia hasta (opcional) */}
          <div>
            <label htmlFor="vig_hasta" className="block text-sm font-medium text-gray-700">
              Vigencia hasta <span className="text-gray-400">(opcional)</span>
            </label>
            <input
              id="vig_hasta"
              type="date"
              {...register('vig_hasta')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.vig_hasta && <p className="mt-1 text-xs text-red-600">{errors.vig_hasta.message}</p>}
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting ? 'Creando...' : 'Crear slot'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
