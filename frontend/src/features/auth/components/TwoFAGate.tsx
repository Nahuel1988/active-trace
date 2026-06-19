// ── TwoFAGate ────────────────────────────────────────────────────────────────
// Gate de verificación 2FA. Aparece tras login exitoso con 2FA activo.
// Input de 6 dígitos TOTP, validación Zod.
// Al verify exitoso → setSession + redirige.

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import * as authApi from '@/features/auth/services/authApi';

export function TwoFAGate() {
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { setSession } = useAuth();
  const navigate = useNavigate();

  const isValidCode = /^\d{6}$/.test(code);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isValidCode) {
      setError('El código debe tener exactamente 6 dígitos');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await authApi.verify2FA(code);
      setSession(response.user, response.access_token);
      navigate('/', { replace: true });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Error de conexión');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label
          htmlFor="totp-code"
          className="block text-sm font-medium text-gray-700"
        >
          Código de verificación
        </label>
        <p className="mt-1 text-sm text-gray-500">
          Ingresá el código de 6 dígitos generado por tu aplicación de
          autenticación.
        </p>
        <input
          id="totp-code"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          value={code}
          onChange={(e) => {
            const digits = e.target.value.replace(/\D/g, '').slice(0, 6);
            setCode(digits);
          }}
          placeholder="000000"
          className="mt-2 block w-full rounded-md border border-gray-300 px-3 py-2 text-center text-2xl tracking-widest shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading || !isValidCode}
        className="flex w-full justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isLoading ? 'Verificando...' : 'Verificar'}
      </button>
    </form>
  );
}
