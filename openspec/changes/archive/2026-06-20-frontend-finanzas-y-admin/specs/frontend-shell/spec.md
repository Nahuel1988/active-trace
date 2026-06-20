## ADDED Requirements

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
