## Why

El backend ya expone los dominios FINANZAS (liquidaciones, grilla salarial, facturas — C-18) y ADMIN/auditoría (usuarios del tenant — C-07, panel de auditoría y métricas — C-19, estructura académica — C-06). Sin este change, los perfiles FINANZAS y ADMIN no tienen interfaz para liquidar honorarios del período, administrar la grilla salarial, gestionar facturas de docentes facturantes, ni para administrar usuarios del tenant, completar la estructura académica (cohortes y materias quedaron como stubs en C-23) ni consultar el panel de auditoría con sus filtros. C-24 cierra el roadmap frontend conectando estos dominios de respaldo administrativo y financiero a la SPA existente.

## What Changes

- Nuevo módulo `features/finanzas/` con:
  - Vista de liquidaciones del período segmentada (general / NEXO / facturantes) + KPIs de cabecera (`total_sin_factura`, `total_con_factura`), filtrada por cohorte + período (consume `ComisionContext`).
  - Cierre de liquidación (transición a `Cerrada`, inmutable) con confirmación.
  - Historial de liquidaciones cerradas con filtros (cohorte, período, docente).
  - ABM de grilla salarial: `SalarioBase` y `SalarioPlus` con vigencia temporal y validación de solapamiento.
  - Gestión de facturas: listado con filtros, alta (solo docentes facturantes), edición de pendientes, transición a abonada.
- Nuevo módulo `features/admin/` con:
  - ABM de usuarios del tenant: listado paginado con filtros, detalle con PII descifrada, alta/edición/baja (soft delete).
  - Panel de auditoría y métricas (consume C-19): acciones por día, estado de comunicaciones por docente, interacciones docente × materia, log de últimas acciones.
  - Log completo de auditoría con filtros combinados (rango de fechas, materia, usuario, código de acción).
- Extensión del módulo `features/estructura/` existente (C-23): ABM de cohortes y materias (los stubs `[]` de C-23 pasan a CRUD real), incluyendo el mapeo materia → clave de Plus (PROG|BD|ARQ|MAT|MET) que consume el cálculo de liquidaciones.
- Sidebar: nuevos items `Finanzas` (`liquidaciones:ver`), `Usuarios` (`usuarios:gestionar`) y `Auditoría` (`auditoria:ver`); el item `Estructura` existente gana sub-rutas de cohortes y materias.
- `App.tsx`: rutas protegidas con lazy loading para `/finanzas/*`, `/admin/usuarios/*`, `/admin/auditoria/*` y las nuevas sub-rutas de `/estructura/*`.
- Reutilización de TanStack Query (query key factory por módulo), React Hook Form + Zod, `useComisionContext` para el scope cohorte/materia, todo sin nuevas dependencias npm.
- Tests: vista de liquidación segmentada con KPIs, cierre de liquidación, ABM de grilla salarial (incl. solapamiento), gestión de facturas (alta/abonar), panel de auditoría con filtros, ABM de usuarios, ABM de cohortes/materias.

## Capabilities

### New Capabilities

- `frontend-finanzas-liquidaciones`: Vista de liquidaciones del período segmentada (general/NEXO/facturantes) + KPIs, cierre inmutable e historial de cerradas. Consume `GET /api/v1/liquidaciones`, `POST /api/v1/liquidaciones/{id}/cerrar`, `GET /api/v1/liquidaciones/historial`.
- `frontend-finanzas-grilla`: ABM de `SalarioBase` y `SalarioPlus` con vigencia temporal y feedback de solapamiento. Consume `GET/POST/PUT/DELETE /api/v1/grilla/salarios-base` y `.../salarios-plus`.
- `frontend-finanzas-facturas`: Gestión de facturas de docentes facturantes — listado con filtros, alta (solo facturadores), edición de pendientes, transición a abonada. Consume `GET/POST/PUT /api/v1/facturas`, `GET /api/v1/facturas/{id}`, `POST /api/v1/facturas/{id}/abonar`.
- `frontend-admin-usuarios`: ABM de usuarios del tenant — listado paginado con filtros, detalle con PII descifrada, alta/edición/baja soft delete. Consume `GET/POST /api/v1/admin/usuarios`, `GET/PUT/DELETE /api/v1/admin/usuarios/{id}`.
- `frontend-admin-auditoria`: Panel de métricas (acciones por día, comunicaciones por docente, interacciones docente×materia, últimas acciones) + log completo filtrable. Consume `GET /api/v1/auditoria/*` (panel y query).

### Modified Capabilities

- `frontend-estructura-ui`: ABM real de cohortes y materias (reemplaza los stubs `[]` de C-23) + mapeo materia → clave de Plus. Consume los endpoints de estructura/materias/cohortes.
- `frontend-shell`: Nuevos items de sidebar (Finanzas, Usuarios, Auditoría) y sub-rutas de estructura; nuevas rutas protegidas con lazy loading en `App.tsx`.

## Impact

- Nuevos directorios: `frontend/src/features/finanzas/` y `frontend/src/features/admin/`, cada uno con estructura `{types,services,hooks,components,pages}/`.
- Extensión de `frontend/src/features/estructura/` (nuevos types, services, hooks, components y pages para cohortes y materias).
- Modificaciones en: `frontend/src/App.tsx` (rutas), `frontend/src/shared/hooks/useMenuItems.ts` (items + permisos), posibles sub-rutas en el menú de estructura.
- Reutiliza `useComisionContext` de `shared/comision/` para el scope cohorte/período de liquidaciones.
- Dependencias npm: `@tanstack/react-query`, `react-hook-form`, `zod`, `axios` ya instalados — no se requieren nuevas librerías.
- No toca backend ni base de datos.
- Governance: BAJO (consume backend ya implementado; sin lógica crítica nueva en el cliente). La PII descifrada (DNI/CUIL/CBU) solo se muestra en el detalle admin y nunca se loguea.
