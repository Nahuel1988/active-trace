## ADDED Requirements

### Requirement: SPA scaffolding con Vite + React 18 + TypeScript
El sistema SHALL proveer un proyecto frontend bajo `frontend/` construido con Vite, React 18 y TypeScript strict. El bundler SHALL producir un bundle optimizado y soportar HMR en desarrollo. No SHALL existir el tipo `any` en el código de la aplicación.

#### Scenario: App arranca sin errores
- **WHEN** se ejecuta `npm run dev` en `frontend/`
- **THEN** el servidor de desarrollo levanta en el puerto 5173 y la ruta `/` renderiza la shell de la aplicación sin errores en consola

#### Scenario: Build de producción exitoso
- **WHEN** se ejecuta `npm run build`
- **THEN** se genera un bundle en `frontend/dist/` sin errores de TypeScript ni de build

#### Scenario: TypeScript strict sin `any`
- **WHEN** se ejecuta `tsc --noEmit`
- **THEN** no hay errores de tipos y ningún archivo de la aplicación contiene el tipo `any` explícito

### Requirement: Estructura feature-based
El código SHALL organizarse en `src/features/{dominio}/{components,hooks,services,types,pages}` y `src/shared/`. Ningún módulo de dominio SHALL importar directamente desde otro módulo de dominio (solo desde `shared/`).

#### Scenario: Feature auth contiene sus propios módulos
- **WHEN** se inspecciona `src/features/auth/`
- **THEN** existen los directorios `components/`, `hooks/`, `services/`, `types/` y `pages/`

#### Scenario: Sin cross-feature imports
- **WHEN** se analiza estáticamente el código
- **THEN** no hay imports de `features/X` dentro de `features/Y` (solo desde `shared/`)

### Requirement: Tailwind CSS configurado
El sistema SHALL tener Tailwind CSS configurado y operativo. Todos los estilos SHALL aplicarse mediante clases de Tailwind. No SHALL usarse CSS modules ni estilos inline salvo para valores dinámicos no expresables en clases.

#### Scenario: Clases Tailwind aplicadas en runtime
- **WHEN** se renderiza cualquier componente con clases Tailwind
- **THEN** los estilos se aplican correctamente en el navegador

### Requirement: TanStack Query configurado
El sistema SHALL proveer un `QueryClient` configurado y un `QueryClientProvider` en la raíz de la app. Todos los fetches de datos de dominio SHALL usar hooks de TanStack Query (no `useEffect` + fetch manual).

#### Scenario: QueryClient disponible en toda la app
- **WHEN** cualquier componente dentro del árbol de la app llama a `useQuery` o `useMutation`
- **THEN** puede acceder al QueryClient sin errores de contexto

### Requirement: Layout shell con menú dinámico por permisos
El sistema SHALL renderizar un layout shell (barra lateral o superior + área de contenido) que muestre solo los ítems de navegación para los que el usuario autenticado tiene permiso. La visibilidad de cada ítem SHALL derivarse de `hasPermission(...)` del AuthContext, sin hardcodear roles en el JSX.

#### Scenario: Usuario sin permiso no ve el ítem de menú
- **WHEN** el usuario autenticado no tiene el permiso `liquidaciones:ver`
- **THEN** el ítem "Liquidaciones" no aparece en el menú de navegación

#### Scenario: Usuario con permiso ve el ítem de menú
- **WHEN** el usuario autenticado tiene el permiso `estructura:gestionar`
- **THEN** el ítem "Estructura académica" aparece en el menú de navegación

### Requirement: Code splitting por ruta
Cada página (componente de nivel ruta) SHALL cargarse de forma lazy (`React.lazy` + `Suspense`) para que el bundle inicial no incluya código de features no visitadas.

#### Scenario: Página de dominio no está en el bundle inicial
- **WHEN** se analiza el bundle de producción
- **THEN** el código de páginas de features de dominio está en chunks separados del entry bundle

### Requirement: Servicio frontend en docker-compose
El sistema SHALL incluir un servicio `frontend` en `docker-compose.yml` basado en Node 20, que levante el servidor de desarrollo Vite con hot-reload y monte el directorio `frontend/src` como volumen.

#### Scenario: Servicio frontend levanta con docker-compose up
- **WHEN** se ejecuta `docker-compose up frontend`
- **THEN** el servidor de desarrollo queda disponible en `http://localhost:5173`
