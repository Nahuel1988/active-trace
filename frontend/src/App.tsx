// ── App ──────────────────────────────────────────────────────────────────────
// Root component de la aplicación. Define las rutas con React Router v6.
// Code splitting con React.lazy + Suspense.
//
// Rutas públicas: /login, /auth/recovery, /auth/reset, /403
// Rutas protegidas: / (AppLayout + Outlet)

import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/shared/components/ProtectedRoute';
import { Spinner } from '@/shared/components/Spinner';
import { useAuth } from '@/shared/hooks/useAuth';

// ── Lazy imports (code splitting) ──────────────────────────────────────────
const LoginPage = lazy(() => import('@/features/auth/pages/LoginPage'));
const RecoveryPage = lazy(() => import('@/features/auth/pages/RecoveryPage'));
const ResetPage = lazy(() => import('@/features/auth/pages/ResetPage'));
const ForbiddenPage = lazy(
  () => import('@/shared/components/ForbiddenPage'),
);
const AppLayout = lazy(() => import('@/shared/components/AppLayout'));

// ── Fallback global ─────────────────────────────────────────────────────────
function PageSuspense({ children }: { children: React.ReactNode }) {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
          <Spinner />
        </div>
      }
    >
      {children}
    </Suspense>
  );
}

// ── Home placeholder ────────────────────────────────────────────────────────
function HomePage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Bienvenido a trace</h1>
      <p className="mt-2 text-gray-600">
        Seleccioná una sección del menú lateral para comenzar.
      </p>
    </div>
  );
}

// ── Componente principal ────────────────────────────────────────────────────
function App() {
  const { isLoading } = useAuth();

  // Mostrar pantalla de carga mientras se resuelve el refresh silencioso
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <Spinner />
      </div>
    );
  }

  return (
    <PageSuspense>
      <Routes>
        {/* Rutas públicas */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/recovery" element={<RecoveryPage />} />
        <Route path="/auth/reset" element={<ResetPage />} />
        <Route path="/403" element={<ForbiddenPage />} />

        {/* Ruta protegida con layout shell */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomePage />} />
            {/* Acá se agregarán rutas de features de dominio (C-22, C-23, C-24) */}
          </Route>
        </Route>

        {/* Catch-all: redirigir a inicio */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </PageSuspense>
  );
}

export default App;
