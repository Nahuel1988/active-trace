// ── UsuarioFormPage ────────────────────────────────────────────────────────
// Create and edit page for Usuarios ABM.
// Doubles as /admin/usuarios/nuevo (isEdit=false) and
// /admin/usuarios/:id/editar (isEdit=true).

import { useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useUsuario } from '@/features/admin/hooks/useUsuarios';
import {
  useCrearUsuario,
  useActualizarUsuario,
} from '@/features/admin/hooks/useUsuarioMutations';
import { UsuarioFormDialog } from '@/features/admin/components/UsuarioFormDialog';
import type { UsuarioFormData } from '@/features/admin/types';

export function UsuarioFormPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;

  const [formError, setFormError] = useState<string | null>(null);

  // Only load detail when editing. PII is needed here to pre-fill the form.
  const { data: usuario, isLoading } = useUsuario(id ?? '');

  const { mutate: crear, isPending: isCreating } = useCrearUsuario();
  const { mutate: actualizar, isPending: isUpdating } = useActualizarUsuario();

  const isPending = isCreating || isUpdating;

  const handleSubmit = useCallback(
    (data: UsuarioFormData) => {
      setFormError(null);

      const onError = (err: unknown) => {
        const axiosErr = err as {
          response?: { status?: number; data?: { detail?: string } };
        };
        const status = axiosErr.response?.status;
        const detail = axiosErr.response?.data?.detail;
        if (status === 422) {
          setFormError(detail ?? 'Error de validación. Revisá los campos ingresados.');
        } else {
          setFormError(detail ?? 'Error al guardar el usuario.');
        }
      };

      if (isEdit && id) {
        actualizar(
          { id, data },
          {
            onSuccess: () => navigate('/admin/usuarios'),
            onError,
          },
        );
      } else {
        crear(data, {
          onSuccess: () => navigate('/admin/usuarios'),
          onError,
        });
      }
    },
    [isEdit, id, crear, actualizar, navigate],
  );

  if (isEdit && isLoading) {
    return (
      <div className="p-6">
        <p className="text-sm text-gray-400">Cargando usuario…</p>
      </div>
    );
  }

  const defaultValues: Partial<UsuarioFormData> | undefined = isEdit && usuario
    ? {
        legajo: usuario.legajo,
        nombre: usuario.nombre,
        apellidos: usuario.apellidos,
        email: usuario.email,
        regional: usuario.regional,
        facturador: usuario.facturador,
        dni: usuario.dni,
        cuil: usuario.cuil,
        cbu: usuario.cbu ?? undefined,
        alias_cbu: usuario.alias_cbu ?? undefined,
      }
    : undefined;

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center gap-4">
        <button
          type="button"
          onClick={() => navigate('/admin/usuarios')}
          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
        >
          ← Volver
        </button>
        <h1 className="text-2xl font-bold text-gray-900">
          {isEdit ? 'Editar usuario' : 'Nuevo usuario'}
        </h1>
      </div>

      <UsuarioFormDialog
        open
        onClose={() => navigate('/admin/usuarios')}
        onSubmit={handleSubmit}
        isPending={isPending}
        error={formError}
        defaultValues={defaultValues}
        isEdit={isEdit}
      />
    </div>
  );
}
