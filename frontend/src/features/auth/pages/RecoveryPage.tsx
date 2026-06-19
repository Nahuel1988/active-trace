// ── RecoveryPage ─────────────────────────────────────────────────────────────
// Página de solicitud de recuperación de contraseña (/auth/recovery).
// Monta RecoveryForm.

import { RecoveryForm } from '@/features/auth/components/RecoveryForm';

export default function RecoveryPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900">trace</h1>
          <p className="mt-1 text-sm text-gray-500">
            Recuperar contraseña
          </p>
        </div>

        <div className="rounded-lg bg-white p-8 shadow-md">
          <h2 className="mb-6 text-center text-lg font-semibold text-gray-900">
            Restablecer contraseña
          </h2>
          <RecoveryForm />
        </div>
      </div>
    </div>
  );
}
