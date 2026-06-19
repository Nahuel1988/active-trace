## Context

El backend (C-01→C-05) está operativo: auth JWT + refresh rotation, 2FA TOTP, RBAC con permisos `modulo:accion` y audit log. No existe todavía ningún frontend. C-21 crea la SPA base sobre la que se montarán todas las features (C-22/23/24). La lógica de auth del frontend debe respetar la misma "regla de oro" del backend: identidad exclusivamente desde el JWT verificado, nunca desde parámetros de URL ni localStorage accesible a JS externo.

## Goals / Non-Goals

**Goals:**
- Proyecto React 18 + TypeScript + Vite funcional bajo `frontend/` con estructura feature-based (`features/{name}/{components,hooks,services,types,pages}`, `shared/`).
- Cliente HTTP Axios centralizado en `shared/services/api.ts` con interceptor de auth y refresh transparente.
- Pantallas completas: login, gate 2FA, solicitar recuperación, reset de contraseña.
- Guard de rutas que verifica sesión y permiso declarado; redirige a login si no hay sesión activa.
- Layout shell con menú lateral/superior cuya visibilidad de ítems se deriva de los permisos de la sesión.
- Logout que revoca sesión en backend.
- Servicio `frontend` en `docker-compose.yml` para desarrollo local.

**Non-Goals:**
- Ninguna feature de dominio (alumnos, calificaciones, equipos, etc.) — esas son C-22/23/24.
- SSR / Next.js — la SPA pura es suficiente para este dominio.
- Internacionalización (i18n) — fuera de scope en esta fase.

## Decisions

### D-01 — Almacenamiento de tokens: memoria + cookie httpOnly para refresh

El access token (15 min) se mantiene en **memoria de React** (`useRef` o estado en `AuthContext`), nunca en `localStorage` ni `sessionStorage`. El refresh token se almacena en una **cookie httpOnly** configurada por el backend (`Set-Cookie` desde `POST /api/auth/login`), inaccesible a JavaScript.

*Alternativa descartada*: `localStorage` para ambos tokens — expone al usuario a ataques XSS que extraigan tokens de larga vida.

### D-02 — AuthContext para estado de sesión

Un `AuthContext` (React Context) expone: `user` (claims del JWT decodificado: `user_id`, `tenant_id`, `roles`, `permissions`), `isAuthenticated`, `login()`, `logout()`, `hasPermission(perm)`. Se inicializa con un intento de refresh silencioso al cargar la SPA para recuperar sesión existente.

El `TanStack Query` gestiona server state de features de dominio, NO la sesión de auth (que es estado de app, no server state).

### D-03 — Refresh transparente en Axios: cola de requests fallidos

El interceptor de respuesta de Axios detecta 401. Pausa todas las requests en vuelo con una cola (Promise array), intenta un único `POST /api/auth/refresh`, y reintenta la cola con el nuevo access token. Si el refresh falla, limpia sesión y redirige a `/login`.

*Alternativa descartada*: refresh por temporizador (setTimeout antes de expiración) — complejo con múltiples tabs y no cubre el caso de token expirado con app en background.

### D-04 — Route guard como Higher-Order Component / wrapper de ruta

`<ProtectedRoute permission="modulo:accion">` envuelve cada `<Route>`. Si no hay sesión → redirige a `/login` (guardando `returnTo` en state). Si hay sesión pero sin el permiso → redirige a `/403`. El permiso es opcional: si se omite solo verifica sesión activa.

### D-05 — Menú dinámico derivado de permisos

El shell layout renderiza un menú lateral donde cada ítem se muestra condicionado a `hasPermission(...)`. El filtrado es puramente declarativo en el arreglo de definición de rutas/menú — no hay lógica de roles hardcodeada en el JSX.

### D-06 — Estructura feature-based desde el inicio

```
frontend/src/
├── features/
│   └── auth/
│       ├── components/   # LoginForm, TwoFAGate, RecoveryForm, ResetForm
│       ├── hooks/        # useLogin, use2FA, useRecovery
│       ├── services/     # authApi.ts (wraps shared/services/api)
│       ├── types/        # LoginRequest, AuthUser, etc.
│       └── pages/        # LoginPage, RecoveryPage, ResetPage
└── shared/
    ├── services/api.ts   # Axios instance + interceptors
    ├── context/AuthContext.tsx
    ├── components/       # ProtectedRoute, AppLayout, Sidebar, Spinner
    └── hooks/            # useAuth, usePermission
```

## Risks / Trade-offs

- **[Race condition en refresh con múltiples tabs]** → El refresh en memoria no se coordina entre tabs. Mitigación: la cookie httpOnly garantiza que el backend siempre recibe el token válido más reciente; si dos tabs llaman refresh simultáneamente, la rotación del backend invalida el anterior y la segunda tab recibirá 401 → redirige a login (comportamiento correcto).
- **[SPA bundle inicial grande a medida que crecen C-22/23/24]** → Route-based code splitting desde el inicio (`React.lazy` + `Suspense` en cada `<Page>`).
- **[Refresh token en cookie httpOnly requiere `credentials: 'include'` en Axios]** → El backend debe configurar `Access-Control-Allow-Credentials: true` y `SameSite=Strict`/`Lax` en la cookie. Coordinar con C-01/C-03 en el CORS config.
- **[2FA gate: estado intermedio entre login y sesión activa]** → El flujo es: login OK → token provisional de 2FA pendiente (sin permisos reales) → verify 2FA → sesión completa. El AuthContext distingue `pendingTwoFactor` de `isAuthenticated`.

## Migration Plan

1. Crear `frontend/` con `npm create vite@latest` + TypeScript template.
2. Instalar deps: Tailwind, TanStack Query, React Hook Form, Zod, Axios, React Router v6.
3. Agregar servicio `frontend` a `docker-compose.yml` (Node 20, puerto 5173, volumen de src).
4. Implementar en orden: `shared/services/api.ts` → `AuthContext` → pantallas auth → `ProtectedRoute` → `AppLayout`.
5. Tests con Vitest + React Testing Library (ya incluido en el template Vite).

**Rollback**: el servicio `frontend` es independiente — el backend no se toca en este change. Revertir es simplemente no levantar el contenedor frontend.

## Open Questions

- ¿El backend configura `SameSite=Strict` o `Lax` en la cookie de refresh? (impacta si el frontend está en subdominio distinto al API en producción).
- ¿Se usa `HashRouter` (ideal para Easypanel sin config de server) o `BrowserRouter` (URLs limpias, requiere rewrite rule en el proxy)? → Preferir `BrowserRouter` con config Nginx en el contenedor.
