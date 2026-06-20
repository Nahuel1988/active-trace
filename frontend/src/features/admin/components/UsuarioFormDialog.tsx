// ── UsuarioFormDialog ──────────────────────────────────────────────────────
// Modal form for creating / editing a Usuario.
// PII fields (dni, cuil, cbu) are togglable password → text via MaskedInput.
// Schema + field sub-components live in UsuarioFormFields.tsx.

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import type { UsuarioFormData } from '@/features/admin/types';
import {
  usuarioSchema,
  MaskedInput,
  UsuarioBaseFields,
} from '@/features/admin/components/UsuarioFormFields';

interface UsuarioFormDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: UsuarioFormData) => void;
  isPending: boolean;
  error: string | null;
  defaultValues?: Partial<UsuarioFormData>;
  isEdit?: boolean;
}

export function UsuarioFormDialog({
  open,
  onClose,
  onSubmit,
  isPending,
  error,
  defaultValues,
  isEdit = false,
}: UsuarioFormDialogProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UsuarioFormData>({
    resolver: zodResolver(usuarioSchema),
    defaultValues: { facturador: false, ...defaultValues },
  });

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={isEdit ? 'Editar usuario' : 'Nuevo usuario'}
    >
      <div className="w-full max-w-lg rounded-lg bg-white shadow-xl overflow-y-auto max-h-[90vh]">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            {isEdit ? 'Editar usuario' : 'Nuevo usuario'}
          </h2>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="px-6 py-4 space-y-4">
          <UsuarioBaseFields register={register} errors={errors} />

          <hr className="border-gray-200" />
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Datos sensibles (PII)
          </p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <MaskedInput
              label="DNI"
              fieldName="dni"
              register={register}
              error={errors.dni?.message}
            />
            <MaskedInput
              label="CUIL"
              fieldName="cuil"
              register={register}
              error={errors.cuil?.message}
            />
            <MaskedInput
              label="CBU (opcional)"
              fieldName="cbu"
              register={register}
              error={errors.cbu?.message}
            />
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Alias CBU (opcional)
              </label>
              <input
                {...register('alias_cbu')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          {!isEdit && (
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Contraseña (opcional)
              </label>
              <input
                {...register('password')}
                type="password"
                autoComplete="new-password"
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          )}

          {error && (
            <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              Error: {error}
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
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isPending ? 'Guardando…' : isEdit ? 'Guardar cambios' : 'Crear usuario'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
