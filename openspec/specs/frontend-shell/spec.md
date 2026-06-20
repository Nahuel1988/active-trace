## MODIFIED Requirements

### Requirement: Layout shell con menú dinámico por permisos

El sistema SHALL renderizar un layout shell (barra lateral o superior + área de contenido) que muestre solo los ítems de navegación para los que el usuario autenticado tiene permiso. La visibilidad de cada ítem SHALL derivarse de `usePermission(...)` invocado desde un custom hook dedicado (`useMenuItems`), sin violar las Rules of Hooks de React (no llamar hooks dentro de `.filter()` u otros callbacks). Los ítems de dominio se definen en un array declarativo con su permiso asociado.

#### Scenario: Usuario sin permiso no ve el ítem de menú (sin hooks violation)
- **WHEN** el usuario autenticado no tiene el permiso `estructura:gestionar`
- **THEN** el ítem "Estructura académica" no aparece en el menú, y el código no llama `usePermission` dentro de un callback de array

#### Scenario: Coordinador ve items de equipos, avisos, tareas, coloquios y estructura
- **WHEN** el usuario autenticado tiene los permisos `equipos:asignar`, `avisos:publicar`, `tareas:gestionar`, `coloquios:gestionar` y `estructura:gestionar`
- **THEN** los items aparecen en el menú: Equipos docentes, Avisos, Tareas internas, Coloquios, Estructura académica

#### Scenario: Docente ve solo mis equipos y mis tareas
- **WHEN** el usuario autenticado tiene rol TUTOR/PROFESOR sin permisos de coordinación
- **THEN** el menú muestra solo Inicio y items sin permiso requerido

### Requirement: Code splitting por ruta (incluye rutas de dominio)

Cada página (componente de nivel ruta) SHALL cargarse de forma lazy (`React.lazy` + `Suspense`) para que el bundle inicial no incluya código de features no visitadas. Las rutas protegidas del dominio se agregan dentro del `<ProtectedRoute>` con sus permisos correspondientes.

#### Scenario: Páginas de coordinación no están en el bundle inicial
- **WHEN** se analiza el bundle de producción
- **THEN** el código de `features/equipos/`, `features/avisos/`, `features/tareas/`, `features/coloquios/` y `features/estructura/` está en chunks separados

#### Scenario: Ruta de equipos requiere permiso
- **WHEN** un usuario sin `equipos:asignar` navega a `/equipos`
- **THEN** el sistema redirige a `/403`

## ADDED Requirements (C-24)

### Requirement: Items de sidebar para Finanzas, Usuarios y Auditoría

El sistema SHALL agregar items de navegación al sidebar, filtrados por permiso mediante el hook `useMenuItems` existente (D-02 de C-23, `usePermission` en posición fija, sin hooks violation): `Finanzas` (`liquidaciones:ver`), `Usuarios` (`usuarios:gestionar`) y `Auditoría` (`auditoria:ver`). El item `Estructura` existente SHALL ganar acceso a las sub-rutas de cohortes y materias.

#### Scenario: Item Finanzas visible solo con permiso
- **WHEN** un usuario con `liquidaciones:ver` abre la app
- **THEN** el sidebar muestra el item "Finanzas"; un usuario sin ese permiso no lo ve

#### Scenario: Items Usuarios y Auditoría filtrados por permiso
- **WHEN** un usuario con `usuarios:gestionar` y `auditoria:ver` abre la app
- **THEN** el sidebar muestra "Usuarios" y "Auditoría"; sin esos permisos no se muestran

#### Scenario: Sin hooks violation
- **WHEN** se evalúa el filtrado de los nuevos items
- **THEN** `usePermission` se llama en posición fija dentro de `useMenuItems`, no dentro de un `.filter()` callback

### Requirement: Rutas protegidas con lazy loading para finanzas y admin

El sistema SHALL agregar rutas protegidas con lazy loading (React.lazy) en `App.tsx` para los nuevos features, cada una declarando su permiso requerido vía `ProtectedRoute` (fail-closed → redirige a 403): `/finanzas`, `/finanzas/historial`, `/finanzas/grilla`, `/finanzas/facturas`, `/admin/usuarios`, `/admin/usuarios/nuevo`, `/admin/usuarios/:id`, `/admin/usuarios/:id/editar`, `/admin/auditoria`, `/admin/auditoria/log`, `/estructura/cohortes`, `/estructura/materias`.

#### Scenario: Ruta protegida redirige sin permiso
- **WHEN** un usuario sin el permiso requerido navega a una ruta de finanzas o admin
- **THEN** el `ProtectedRoute` lo redirige a la pantalla 403

#### Scenario: Lazy loading de las páginas
- **WHEN** se navega por primera vez a una ruta de finanzas o admin
- **THEN** la página se carga vía code splitting (React.lazy + Suspense), consistente con las rutas existentes

#### Scenario: Sub-rutas de estructura accesibles
- **WHEN** un usuario con `estructura:gestionar` navega a `/estructura/cohortes` o `/estructura/materias`
- **THEN** las páginas de ABM real de cohortes y materias se renderizan
