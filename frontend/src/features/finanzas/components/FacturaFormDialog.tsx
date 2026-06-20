import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { FacturaFormData } from '@/features/finanzas/types';

const facturaSchema = z.object({
  usuario_id: z.string().min(1, 'El usuario es requerido'),
  periodo: z.string().min(1, 'El período es requerido'),
  detalle: z.string().min(1, 'El detalle es requerido'),
  referencia_archivo: z.string().min(1, 'La referencia del archivo es requerida'),
  tamano_kb: z.string().min(1, 'El tamaño es requerido'),
});

type FacturaFormSchema = z.infer<typeof facturaSchema>;

interface Facturador {
  id: string;
  nombre: string;
  apellidos: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: FacturaFormData) => void;
  isPending: boolean;
  error: string | null;
  facturadores: Facturador[];
}

export function FacturaFormDialog({
  open,
  onClose,
  onSubmit,
  isPending,
  error,
  facturadores,
}: Props) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FacturaFormSchema>({
    resolver: zodResolver(facturaSchema),
    defaultValues: {
      usuario_id: '',
      periodo: '',
      detalle: '',
      referencia_archivo: '',
      tamano_kb: '',
    },
  });

  useEffect(() => {
    if (!open) {
      reset();
    }
  }, [open, reset]);

  const handleFormSubmit = (data: FacturaFormSchema) => {
    onSubmit(data);
  };

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
    >
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Nueva factura</h2>

        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          <div>
            <label htmlFor="usuario_id" className="block text-sm font-medium text-gray-700">
              Facturador
            </label>
            <select
              id="usuario_id"
              {...register('usuario_id')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">Seleccioná un facturador</option>
              {facturadores.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.apellidos}, {f.nombre}
                </option>
              ))}
            </select>
            {errors.usuario_id && (
              <p className="mt-1 text-sm text-red-600">{errors.usuario_id.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="periodo" className="block text-sm font-medium text-gray-700">
              Período
            </label>
            <input
              id="periodo"
              type="text"
              placeholder="ej. 2025-06"
              {...register('periodo')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.periodo && (
              <p className="mt-1 text-sm text-red-600">{errors.periodo.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="detalle" className="block text-sm font-medium text-gray-700">
              Detalle
            </label>
            <textarea
              id="detalle"
              rows={3}
              {...register('detalle')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.detalle && (
              <p className="mt-1 text-sm text-red-600">{errors.detalle.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="referencia_archivo" className="block text-sm font-medium text-gray-700">
              Referencia de archivo
            </label>
            <input
              id="referencia_archivo"
              type="text"
              {...register('referencia_archivo')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.referencia_archivo && (
              <p className="mt-1 text-sm text-red-600">{errors.referencia_archivo.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="tamano_kb" className="block text-sm font-medium text-gray-700">
              Tamaño (KB)
            </label>
            <input
              id="tamano_kb"
              type="text"
              {...register('tamano_kb')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.tamano_kb && (
              <p className="mt-1 text-sm text-red-600">{errors.tamano_kb.message}</p>
            )}
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isPending ? 'Guardando...' : 'Crear factura'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
