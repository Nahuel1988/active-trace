// ── App ──────────────────────────────────────────────────────────────────────
// Root component de la aplicación. Define las rutas con React Router v6.
// Code splitting con React.lazy + Suspense.
//
// Rutas públicas: /login, /auth/recovery, /auth/reset, /403
// Rutas protegidas: / (AppLayout + Outlet) con features de dominio.

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

// ── Domain feature pages ────────────────────────────────────────────────────
const ImportPage = lazy(() => import('@/features/importacion/pages/ImportPage'));
const AtrasadosDashboardPage = lazy(() => import('@/features/atrasados/pages/AtrasadosDashboardPage'));
const ComunicacionesQueuePage = lazy(() => import('@/features/comunicaciones/pages/ComunicacionesQueuePage'));

const EquiposListPage = lazy(() => import('@/features/equipos/pages/EquiposListPage'));
const MisEquiposPage = lazy(() => import('@/features/equipos/pages/MisEquiposPage'));
const AsignacionMasivaPage = lazy(() => import('@/features/equipos/pages/AsignacionMasivaPage'));
const ClonarEquipoPage = lazy(() => import('@/features/equipos/pages/ClonarEquipoPage'));

const AvisosListPage = lazy(() => import('@/features/avisos/pages/AvisosListPage'));
const AvisoFormPage = lazy(() => import('@/features/avisos/pages/AvisoFormPage'));

const TareasListPage = lazy(() => import('@/features/tareas/pages/TareasListPage'));
const MisTareasPage = lazy(() => import('@/features/tareas/pages/MisTareasPage'));
const TareaFormPage = lazy(() => import('@/features/tareas/pages/TareaFormPage'));
const TareaDetailPage = lazy(() => import('@/features/tareas/pages/TareaDetailPage'));

const ColoquiosListPage = lazy(() => import('@/features/coloquios/pages/ColoquiosListPage'));
const ColoquioFormPage = lazy(() => import('@/features/coloquios/pages/ColoquioFormPage'));
const ColoquiosAgendaPage = lazy(() => import('@/features/coloquios/pages/ColoquiosAgendaPage'));
const RegistroAcademicoPage = lazy(() => import('@/features/coloquios/pages/RegistroAcademicoPage'));

const EstructuraHomePage = lazy(() => import('@/features/estructura/pages/EstructuraHomePage'));
const CarrerasListPage = lazy(() => import('@/features/estructura/pages/CarrerasListPage'));
const ProgramasListPage = lazy(() => import('@/features/estructura/pages/ProgramasListPage'));
const FechasAcademicasPage = lazy(() => import('@/features/estructura/pages/FechasAcademicasPage'));

const EncuentrosSlotsPage = lazy(() => import('@/features/encuentros/pages/EncuentrosSlotsPage'));
const SlotDetailPage = lazy(() => import('@/features/encuentros/pages/SlotDetailPage'));

const GuardiasListPage = lazy(() => import('@/features/guardias/pages/GuardiasListPage'));

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

            {/* Equipos docentes */}
            <Route
              path="equipos"
              element={<ProtectedRoute permission="equipos:asignar" />}
            >
              <Route index element={<EquiposListPage />} />
              <Route path="mis-equipos" element={<MisEquiposPage />} />
              <Route
                path="asignacion-masiva"
                element={<AsignacionMasivaPage />}
              />
              <Route path="clonar" element={<ClonarEquipoPage />} />
            </Route>

            {/* Avisos */}
            <Route
              path="avisos"
              element={<ProtectedRoute permission="avisos:publicar" />}
            >
              <Route index element={<AvisosListPage />} />
              <Route path="nuevo" element={<AvisoFormPage />} />
              <Route path=":id/editar" element={<AvisoFormPage />} />
            </Route>

            {/* Tareas */}
            <Route
              path="tareas"
              element={<ProtectedRoute permission="tareas:gestionar" />}
            >
              <Route index element={<TareasListPage />} />
              <Route path="mias" element={<MisTareasPage />} />
              <Route path="nueva" element={<TareaFormPage />} />
              <Route path=":id" element={<TareaDetailPage />} />
            </Route>

            {/* Coloquios */}
            <Route
              path="coloquios"
              element={<ProtectedRoute permission="coloquios:gestionar" />}
            >
              <Route index element={<ColoquiosListPage />} />
              <Route path="nuevo" element={<ColoquioFormPage />} />
              <Route path="agenda" element={<ColoquiosAgendaPage />} />
              <Route
                path="registro-academico"
                element={<RegistroAcademicoPage />}
              />
            </Route>

            {/* Estructura académica */}
            <Route
              path="estructura"
              element={<ProtectedRoute permission="estructura:gestionar" />}
            >
              <Route index element={<EstructuraHomePage />} />
              <Route path="carreras" element={<CarrerasListPage />} />
              <Route path="programas" element={<ProgramasListPage />} />
              <Route path="fechas" element={<FechasAcademicasPage />} />
            </Route>

            {/* Encuentros */}
            <Route
              path="encuentros"
              element={<ProtectedRoute permission="encuentros:gestionar" />}
            >
              <Route index element={<EncuentrosSlotsPage />} />
              <Route path="slots/:id" element={<SlotDetailPage />} />
            </Route>

            {/* Guardias */}
            <Route
              path="guardias"
              element={<ProtectedRoute permission="guardias:registrar" />}
            >
              <Route index element={<GuardiasListPage />} />
            </Route>

            {/* Importar padrón/calificaciones */}
            <Route
              path="importar"
              element={<ProtectedRoute permission="calificaciones:importar" />}
            >
              <Route index element={<ImportPage />} />
            </Route>

            {/* Atrasados */}
            <Route
              path="atrasados"
              element={<ProtectedRoute permission="atrasados:ver" />}
            >
              <Route index element={<AtrasadosDashboardPage />} />
            </Route>

            {/* Comunicaciones */}
            <Route
              path="comunicaciones"
              element={<ProtectedRoute permission="comunicacion:enviar" />}
            >
              <Route index element={<ComunicacionesQueuePage />} />
            </Route>
          </Route>
        </Route>

        {/* Catch-all: redirigir a inicio */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </PageSuspense>
  );
}

export default App;
