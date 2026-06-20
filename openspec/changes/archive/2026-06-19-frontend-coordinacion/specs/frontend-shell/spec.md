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
