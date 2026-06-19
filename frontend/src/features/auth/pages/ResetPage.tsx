// ── ResetPage ────────────────────────────────────────────────────────────────
// Página de restablecimiento de contraseña (/auth/reset?token=...).
// Monta ResetForm.

import { ResetForm } from '@/features/auth/components/ResetForm';

export default function ResetPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900">trace</h1>
          <p className="mt-1 text-sm text-gray-500">
            Nueva contraseña
          </p>
        </div>

        <div className="rounded-lg bg-white p-8 shadow-md">
          <h2 className="mb-6 text-center text-lg font-semibold text-gray-900">
            Establecer nueva contraseña
          </h2>
          <ResetForm />
        </div>
      </div>
    </div>
  );
}
