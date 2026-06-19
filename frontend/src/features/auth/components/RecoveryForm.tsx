// ── RecoveryForm ─────────────────────────────────────────────────────────────
// Formulario de solicitud de recuperación de contraseña.
// Validación Zod del email. Llama a authApi.requestRecovery().
// Muestra confirmación genérica "revisá tu email" sin exponer usuarios.

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import * as authApi from '@/features/auth/services/authApi';

const recoverySchema = z.object({
  email: z
    .string()
    .min(1, 'El email es requerido')
    .email('Ingresá un email válido'),
});

type RecoveryFormData = z.infer<typeof recoverySchema>;

export function RecoveryForm() {
  const [isSent, setIsSent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RecoveryFormData>({
    resolver: zodResolver(recoverySchema),
  });

  const onSubmit = async (data: RecoveryFormData) => {
    setIsLoading(true);
    setServerError(null);

    try {
      await authApi.requestRecovery(data.email);
      setIsSent(true);
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

  if (isSent) {
    return (
      <div className="rounded-md bg-green-50 p-4 text-center">
        <p className="text-sm text-green-700">
          Revisá tu email. Si la cuenta existe, vas a recibir un enlace para
          restablecer tu contraseña.
        </p>
        <a
          href="/login"
          className="mt-3 inline-block text-sm font-medium text-indigo-600 hover:text-indigo-500"
        >
          Volver al inicio de sesión
        </a>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <p className="text-sm text-gray-500">
        Ingresá tu email y te enviaremos un enlace para restablecer tu
        contraseña.
      </p>

      <div>
        <label
          htmlFor="recovery-email"
          className="block text-sm font-medium text-gray-700"
        >
          Email
        </label>
        <input
          id="recovery-email"
          type="email"
          autoComplete="email"
          {...register('email')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          placeholder="tu@email.com"
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
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
        {isLoading ? 'Enviando...' : 'Enviar enlace'}
      </button>

      <p className="text-center text-sm text-gray-500">
        <a
          href="/login"
          className="font-medium text-indigo-600 hover:text-indigo-500"
        >
          Volver al inicio de sesión
        </a>
      </p>
    </form>
  );
}
