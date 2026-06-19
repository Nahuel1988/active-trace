// ── ResetForm ────────────────────────────────────────────────────────────────
// Formulario de restablecimiento de contraseña.
// Lee el token de query param. Valida nueva contraseña + confirmación con Zod.
// Llama a authApi.resetPassword(). Redirige a /login en éxito.

import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import * as authApi from '@/features/auth/services/authApi';

const resetSchema = z
  .object({
    password: z
      .string()
      .min(6, 'La contraseña debe tener al menos 6 caracteres'),
    confirm_password: z
      .string()
      .min(1, 'Confirmá tu nueva contraseña'),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: 'Las contraseñas no coinciden',
    path: ['confirm_password'],
  });

type ResetFormData = z.infer<typeof resetSchema>;

export function ResetForm() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();

  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetFormData>({
    resolver: zodResolver(resetSchema),
  });

  const onSubmit = async (data: ResetFormData) => {
    if (!token) {
      setServerError('Token de restablecimiento no encontrado en la URL.');
      return;
    }

    setIsLoading(true);
    setServerError(null);

    try {
      await authApi.resetPassword({
        token,
        password: data.password,
        confirm_password: data.confirm_password,
      });
      navigate('/login', { replace: true });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setServerError(err.message);
      } else {
        setServerError('Error de conexión');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-center">
        <p className="text-sm text-red-700">
          Enlace inválido o expirado. Solicitá un nuevo restablecimiento de
          contraseña.
        </p>
        <a
          href="/auth/recovery"
          className="mt-3 inline-block text-sm font-medium text-indigo-600 hover:text-indigo-500"
        >
          Solicitar nuevo enlace
        </a>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <div>
        <label
          htmlFor="reset-password"
          className="block text-sm font-medium text-gray-700"
        >
          Nueva contraseña
        </label>
        <input
          id="reset-password"
          type="password"
          autoComplete="new-password"
          {...register('password')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">
            {errors.password.message}
          </p>
        )}
      </div>

      <div>
        <label
          htmlFor="reset-confirm"
          className="block text-sm font-medium text-gray-700"
        >
          Confirmar contraseña
        </label>
        <input
          id="reset-confirm"
          type="password"
          autoComplete="new-password"
          {...register('confirm_password')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {errors.confirm_password && (
          <p className="mt-1 text-sm text-red-600">
            {errors.confirm_password.message}
          </p>
        )}
      </div>

      {serverError && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
          {serverError}
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="flex w-full justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isLoading ? 'Restableciendo...' : 'Restablecer contraseña'}
      </button>
    </form>
  );
}
