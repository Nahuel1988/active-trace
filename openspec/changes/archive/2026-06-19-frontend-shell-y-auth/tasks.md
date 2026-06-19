## 1. Scaffolding y configuración base

- [x] 1.1 Crear proyecto Vite + React 18 + TypeScript en `frontend/` (`npm create vite@latest frontend -- --template react-ts`)
- [x] 1.2 Configurar TypeScript strict (`strict: true`, `noImplicitAny: true`) en `tsconfig.app.json`
- [x] 1.3 Instalar dependencias: `tailwindcss`, `@tanstack/react-query`, `react-hook-form`, `zod`, `@hookform/resolvers`, `axios`, `react-router-dom`
- [x] 1.4 Instalar dependencias de testing: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`, `jsdom`, configurar `vitest.config.ts`
- [x] 1.5 Configurar Tailwind CSS v4 (`@tailwindcss/vite` plugin + `@import "tailwindcss"` en `src/index.css`)
- [x] 1.6 Crear estructura de directorios: `src/features/auth/{components,hooks,services,types,pages}`, `src/shared/{services,context,components,hooks}`, `src/test/`
- [x] 1.7 Configurar alias `@/` → `src/` en `vite.config.ts` y `tsconfig.app.json`
- [x] 1.8 Agregar servicio `frontend` a `docker-compose.yml` (imagen Node 20, puerto 5173, volumen `./frontend`)
- [x] 1.9 Verificar `npm run build` sin errores; `tsc --noEmit` sin errores

## 2. Cliente HTTP centralizado

- [x] 2.1 Crear `src/shared/services/api.ts` con instancia Axios (`baseURL: import.meta.env.VITE_API_URL`, `withCredentials: true`)
- [x] 2.2 Implementar `AuthContext` en `src/shared/context/AuthContext.tsx` con estado: `{ user, accessToken, isAuthenticated, pendingTwoFactor }` y métodos `setSession()`, `clearSession()`
- [x] 2.3 Implementar cola de requests fallidos para refresh: variable `isRefreshing` + array `failedQueue` con resolve/reject
- [x] 2.4 Agregar request interceptor que adjunta `Authorization: Bearer <token>` si hay token en AuthContext
- [x] 2.5 Agregar response interceptor que detecta 401 → activa cola → llama `POST /api/auth/refresh` → reintenta cola o redirige a `/login`
- [x] 2.6 Agregar response interceptor para 403 → lanza `ForbiddenError` tipado (clase custom que extiende `Error`)
- [x] 2.7 Exponer hook `useAuth()` en `src/shared/hooks/useAuth.ts` que consume `AuthContext`
- [x] 2.8 Exponer hook `usePermission(perm: string)` que verifica si el usuario tiene el permiso dado

## 3. Pantallas de autenticación

- [x] 3.1 Crear tipos en `src/features/auth/types/`: `LoginRequest`, `LoginResponse`, `TwoFARequest`, `RecoveryRequest`, `ResetRequest`, `AuthUser`
- [x] 3.2 Crear `src/features/auth/services/authApi.ts` con funciones: `login()`, `verify2FA()`, `requestRecovery()`, `resetPassword()`, `refresh()`, `logout()`
- [x] 3.3 Crear hook `useLogin` en `src/features/auth/hooks/useLogin.ts` que llama a `authApi.login()` y maneja el flujo login/2FA
- [x] 3.4 Crear `LoginForm` en `src/features/auth/components/LoginForm.tsx` con React Hook Form + Zod (email requerido y válido, password requerido)
- [x] 3.5 Crear `LoginPage` en `src/features/auth/pages/LoginPage.tsx` que monta `LoginForm`, maneja redirección a `/` o `returnTo`, avanza a gate 2FA si corresponde
- [x] 3.6 Crear `TwoFAGate` en `src/features/auth/components/TwoFAGate.tsx` con input de 6 dígitos TOTP, validación Zod y llamada a `verify2FA()`
- [x] 3.7 Crear `RecoveryForm` y `RecoveryPage` (`/auth/recovery`): formulario de email, llama a `requestRecovery()`, muestra confirmación genérica
- [x] 3.8 Crear `ResetForm` y `ResetPage` (`/auth/reset`): lee token de query param, formulario nueva contraseña + confirmación (Zod), llama a `resetPassword()`, redirige a `/login`
- [x] 3.9 Configurar `react-router-dom` en `src/App.tsx` con rutas: `/login`, `/auth/recovery`, `/auth/reset`

## 4. Guard de rutas y layout shell

- [x] 4.1 Crear `ProtectedRoute` en `src/shared/components/ProtectedRoute.tsx`: verifica `isAuthenticated`; si no hay sesión redirige a `/login` con `state: { returnTo: location.pathname }`; si falta permiso redirige a `/403`
- [x] 4.2 Crear `AppLayout` en `src/shared/components/AppLayout.tsx`: sidebar/header + `<Outlet />` para el contenido
- [x] 4.3 Implementar lógica de refresh silencioso al cargar la app: en `AuthContext`, al montar, llama a `authApi.refresh()` para recuperar sesión desde cookie httpOnly; actualiza estado antes de renderizar rutas
- [x] 4.4 Crear menú de navegación declarativo en `src/shared/components/Sidebar.tsx`: array de ítems con `{ label, path, icon, permission? }`, filtrados con `usePermission()`
- [x] 4.5 Crear página `/403` en `src/shared/components/ForbiddenPage.tsx`
- [x] 4.6 Agregar acción de logout en la UI (botón en el layout): llama a `authApi.logout()`, limpia `AuthContext`, redirige a `/login`; maneja error de red limpiando sesión igualmente
- [x] 4.7 Configurar code splitting: envolver cada `<Page>` con `React.lazy` + `<Suspense fallback={<Spinner />}>`
- [x] 4.8 Integrar `QueryClientProvider` en la raíz de la app (`src/main.tsx`) con `QueryClient` configurado

## 5. Tests

- [x] 5.1 Test: `LoginPage` renderiza el formulario sin errores (`render(<LoginPage />)` con providers mockeados)
- [x] 5.2 Test: login exitoso sin 2FA actualiza AuthContext y redirige (mock de `authApi.login()`)
- [x] 5.3 Test: login con credenciales inválidas muestra mensaje de error sin redirigir
- [x] 5.4 Test: `ProtectedRoute` sin sesión redirige a `/login` con `returnTo` en state
- [x] 5.5 Test: `ProtectedRoute` con sesión pero sin permiso redirige a `/403`
- [x] 5.6 Test: refresh transparente — mock de 401 seguido de refresh exitoso reintenta la request original
- [x] 5.7 Test: múltiples 401 simultáneos producen exactamente un `POST /api/auth/refresh`
- [x] 5.8 Test: logout limpia AuthContext y redirige a `/login` incluso si la request al backend falla
- [x] 5.9 Verificar cobertura de líneas ≥80% en los módulos de `features/auth/` y `shared/`
