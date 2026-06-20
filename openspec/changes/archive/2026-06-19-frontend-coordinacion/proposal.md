## Why

La SPA base (C-21) tiene solo auth y shell vacío. El backend ya expone endpoints completos para equipos docentes (C-07/C-08), avisos (C-15), tareas (C-16), coloquios (C-14) y estructura académica (C-06/C-17). Sin este change, los perfiles COORDINADOR y ADMIN no tienen interfaz para gestionar asignaciones, comunicaciones, tareas internas, coloquios ni la estructura académica del tenant.

## What Changes

- Nuevo módulo `features/equipos/` con vistas de mis equipos (docente), consulta de asignaciones, asignación masiva, clonar equipo, modificar vigencia y exportar CSV.
- Nuevo módulo `features/avisos/` con ABM de avisos (tablón de coordinación), visibilidad de acks y toggle activo/inactivo.
- Nuevo módulo `features/tareas/` con vista mis tareas, admin de tareas del equipo, asignación delegación y comentarios por tarea.
- Nuevo módulo `features/coloquios/` con panel de métricas, listado de convocatorias CRUD, agenda consolidada y registro académico.
- Nuevo módulo `features/estructura/` con listado de carreras, gestión de programas (upload + list), fechas académicas CRUD y calendario.
- Nuevo módulo `features/encuentros/` con vista admin de slots e instancias, edición de instancias (estado, URLs, comentarios) y exportación HTML para LMS.
- Nuevo módulo `features/guardias/` con listado, registro y cambio de estado de guardias, y exportación CSV.
- Sidebar actualizada: fix del hooks violation en `.filter()` actual, items de navegación para cada módulo con permisos.
- `App.tsx`: routes protegidas con lazy loading para cada feature.
- Introducción de TanStack Query (`useQuery`/`useMutation`) para server state de features de dominio.
- Tests: al menos un test por hook/page crítico en cada módulo.

## Capabilities

### New Capabilities

- `frontend-equipos-ui`: Vistas de mis equipos (propio docente), consulta y gestión de asignaciones individuales, asignación masiva, clonar, modificar vigencia, exportar CSV. Consume `GET /api/v1/equipos/mis-equipos`, `GET /api/v1/equipos`, `POST /api/v1/equipos/asignacion-masiva`, `POST /api/v1/equipos/clonar`, `PATCH /api/v1/equipos/vigencia`, `GET /api/v1/equipos/export`, `GET /api/v1/asignaciones`, `POST /api/v1/asignaciones`, `DELETE /api/v1/asignaciones/{id}`.
- `frontend-avisos-ui`: Tablón de avisos para coordinación — listado de gestión, creación/edición con alcance y severidad, toggle activo/inactivo, vista de acks, soft-delete. Consume `GET /api/v1/avisos/`, `POST /api/v1/avisos/`, `PUT /api/v1/avisos/{id}`, `DELETE /api/v1/avisos/{id}`.
- `frontend-tareas-ui`: Tareas internas — vista "mis tareas" (docente), admin de todas las tareas (coordinación), creación/asignación, cambio de estado, comentarios por tarea. Consume `GET /api/tareas/mias`, `GET /api/tareas`, `POST /api/tareas`, `DELETE /api/tareas/{id}`, `POST /api/tareas/{id}/asignar`, `PATCH /api/tareas/{id}/estado`, `GET /api/tareas/{id}/comentarios`, `POST /api/tareas/{id}/comentarios`.
- `frontend-coloquios-ui`: Panel de métricas globales, CRUD de convocatorias de coloquio, agenda consolidada de reservas, registro académico. Consume `GET /api/v1/coloquios`, `POST /api/v1/coloquios`, `GET /api/v1/coloquios/metricas`, `GET /api/v1/coloquios/agenda`, `GET /api/v1/coloquios/registro-academico`.
- `frontend-estructura-ui`: Listado de carreras (admin), gestión de programas (upload PDF + listado), fechas académicas CRUD + calendario. Consume `GET /api/v1/estructura/carreras`, `POST /api/v1/estructura/carreras`, `GET /api/v1/programas`, `POST /api/v1/programas`, `GET /api/v1/programas/{id}`, `GET /api/v1/fechas-academicas`, `POST /api/v1/fechas-academicas`, `PUT /api/v1/fechas-academicas/{id}`, `GET /api/v1/fechas-academicas/calendario`.
- `frontend-encuentros-ui`: Vista admin de slots e instancias — listado de slots, detalle con instancias, edición de instancia (estado, meet_url, video_url, comentario), exportación HTML para LMS. Consume `POST /api/encuentros/slots`, `GET /api/encuentros/slots`, `GET /api/encuentros/slots/{slot_id}`, `DELETE /api/encuentros/slots/{slot_id}`, `GET /api/encuentros/instancias`, `GET /api/encuentros/instancias/{instancia_id}`, `PATCH /api/encuentros/instancias/{instancia_id}`, `GET /api/encuentros/slots/{slot_id}/html`.
- `frontend-guardias-ui`: Registro y gestión de guardias — listado con filtros, cambio de estado, exportación CSV. Consume `POST /api/guardias`, `GET /api/guardias`, `GET /api/guardias/{guardia_id}`, `PATCH /api/guardias/{guardia_id}/estado`, `GET /api/guardias/export`.
- `frontend-query-client`: Introducción de TanStack Query provider y hooks `useQuery`/`useMutation` para server state de dominio. Wrappers de queries por módulo. Patrón query key factory.

### Modified Capabilities

- `frontend-shell`: Agregar nuevas rutas protegidas con lazy loading en App.tsx. Sidebar con items de dominio y permisos. Fix del hooks violation en Sidebar.tsx (usePermission dentro de .filter()).
- `frontend-auth-ui`: No se modifica — la sesión y permisos existentes se reutilizan.

## Impact

- Nuevos directorios: `frontend/src/features/{equipos,avisos,tareas,coloquios,estructura}/` con estructura `{types,services,hooks,components,pages}/`.
- Modificaciones en: `frontend/src/App.tsx` (routes), `frontend/src/shared/components/Sidebar.tsx` (items + fix hooks), `frontend/src/shared/components/AppLayout.tsx` (QueryClientProvider).
- Dependencias npm: `@tanstack/react-query` ya instalado en C-21, no se requieren nuevas librerías.
- No toca backend ni base de datos.
- Known gaps: Estructura GET /cohortes y /materias son stubs que retornan [] — se muestran con mensaje "Sin datos".
