// ── LoginPage ────────────────────────────────────────────────────────────────
// Página completa de login. Monta LoginForm o TwoFAGate según el estado.
// Lee returnTo de location.state para redirigir post-login.

import { useLocation } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { LoginForm } from '@/features/auth/components/LoginForm';
import { TwoFAGate } from '@/features/auth/components/TwoFAGate';

export default function LoginPage() {
  const { pendingTwoFactor } = useAuth();
  const location = useLocation();

  const returnTo =
    (location.state as { returnTo?: string })?.returnTo ?? '/';

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        {/* Logo / Brand */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900">trace</h1>
          <p className="mt-1 text-sm text-gray-500">
            Plataforma de gestión académica
          </p>
        </div>

        {/* Card */}
        <div className="rounded-lg bg-white p-8 shadow-md">
          {pendingTwoFactor ? (
            <>
              <h2 className="mb-6 text-center text-lg font-semibold text-gray-900">
                Verificación en dos pasos
              </h2>
              <TwoFAGate />
            </>
          ) : (
            <>
              <h2 className="mb-6 text-center text-lg font-semibold text-gray-900">
                Iniciar sesión
              </h2>
              <LoginForm />
            </>
          )}
        </div>

        {/* returnTo oculto pero accesible */}
        {returnTo !== '/' && (
          <p className="mt-4 text-center text-xs text-gray-400">
            Serás redirigido a la página solicitada luego del ingreso.
          </p>
        )}
      </div>
    </div>
  );
}
