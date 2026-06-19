## Why

El backend ya tiene auth (C-03), RBAC (C-04) y audit-log (C-05) completos. Para que cualquier usuario pueda interactuar con el sistema se necesita una SPA con scaffolding base, cliente HTTP que maneje tokens de forma transparente y las pantallas de autenticación. Sin este change, todos los módulos de frontend (C-22/23/24) no tienen dónde montarse.

## What Changes

- Nuevo proyecto frontend React 18 + TypeScript + Vite bajo `frontend/` con estructura feature-based.
- Cliente HTTP centralizado (Axios) con interceptor de auth, refresh transparente de access tokens y manejo de 401/403.
- Pantallas: login (email + password), gate de 2FA TOTP, recuperación de contraseña (solicitud + reset).
- Guard de rutas que verifica sesión activa y permiso requerido; redirige a login si no hay sesión.
- Layout/menú shell adaptado dinámicamente a los permisos de la sesión activa.
- Logout explícito que revoca la sesión en el backend (consume `POST /api/auth/logout`).
- Setup de Tailwind CSS, TanStack Query (server state), React Hook Form + Zod (formularios validados).
- Tests: render de pantallas de auth, flujo login con mock de API, guard sin sesión redirige, refresh transparente activa correctamente.

## Capabilities

### New Capabilities

- `frontend-shell`: Scaffolding SPA (React 18 + TypeScript + Vite), estructura feature-based, layout compartido, menú dinámico por permisos, configuración de Tailwind + TanStack Query.
- `frontend-http-client`: Cliente HTTP centralizado (Axios), interceptor de auth que adjunta access token, refresh transparente cuando el servidor retorna 401, propagación de 403 a la capa de UI.
- `frontend-auth-ui`: Pantallas de login, gate 2FA, recuperación de contraseña y reset; guard de rutas por permiso; logout con revocación de sesión.

### Modified Capabilities

(ninguna — solo se crean capabilities nuevas)

## Impact

- Directorio nuevo: `frontend/` (fuera del alcance de `backend/`; no toca la API).
- Consume endpoints ya existentes: `POST /api/auth/login`, `POST /api/auth/2fa/verify`, `POST /api/auth/forgot`, `POST /api/auth/reset`, `POST /api/auth/refresh`, `POST /api/auth/logout`.
- Dependencia de build: Node.js 20 LTS + npm; se agrega servicio `frontend` al `docker-compose.yml` de desarrollo.
- C-22, C-23 y C-24 dependen de este shell como punto de montaje.
