## Why

El rol PROFESOR (y de forma acotada el TUTOR) ejecuta el flujo de mayor valor de la plataforma: importar datos del LMS → detectar alumnos atrasados → comunicar con aprobación (FL-02, FL-04). Hoy ese flujo no tiene UI: el shell de `C-21 frontend-shell-y-auth` ya está archivado (AuthContext, cliente HTTP con refresh transparente, guard de rutas por permiso, sidebar filtrado por permisos, layout base), pero no hay ninguna página de dominio montada sobre él. `C-22` construye las pantallas docentes que convierten ese shell en una herramienta usable, consumiendo los endpoints de `C-09…C-12` que el backend expondrá.

## What Changes

- **Feature `padron`**: pantalla de importación de padrón de alumnos por materia/cohorte. Upload de archivo (xlsx/csv), preview de alumnos detectados, confirmación de upsert destructivo (RN-05), feedback del resultado. Reemplaza el padrón anterior de la materia.
- **Feature `calificaciones`**: pantalla de importación de calificaciones con preview de actividades detectadas, selección de cuáles incluir en el análisis (RN-01, RN-02), y configuración del umbral de aprobación por materia (RN-03, default 60%).
- **Feature `atrasados`**: dashboard de alumnos atrasados (RN-06), ranking de actividades aprobadas (RN-09), reportes rápidos por comisión, notas finales agrupadas y detección/export de entregas sin corregir (RN-07, RN-08). Selección de alumnos para disparar comunicación.
- **Feature `comunicaciones`**: cola de comunicaciones salientes con preview por destinatario (F3.1), envío a la cola, y tracking de estado en tiempo real (Pendiente → Enviando → OK/Fallido/Cancelado, RN-15). Aprobación/cancelación por lote o por destinatario para quien tenga `comunicacion:aprobar` (FL-04).
- **Feature `comisiones` (shared docente)**: selector de comisión (materia + cohorte) reutilizado por las features anteriores como contexto de trabajo.
- **Contratos de API documentados**: como el backend (`C-09…C-12`) aún no existe, esta propuesta fija los contratos esperados (endpoints REST, DTOs request/response, códigos de estado) que el frontend consumirá. Los servicios se construyen contra esos contratos y se testean con mocks.
- **Integración con el shell**: nuevos ítems de `Sidebar` filtrados por permiso (`calificaciones:importar`, `atrasados:ver`, `comunicacion:enviar`), nuevas rutas lazy en `App.tsx` envueltas en `<ProtectedRoute>` con el permiso requerido.

No hay breaking changes: todo es aditivo sobre el shell ya archivado.

## Capabilities

### New Capabilities
- `frontend-padron-ui`: pantalla de importación de padrón (upload, preview, confirmación de upsert destructivo, resultado) y su servicio TanStack Query.
- `frontend-calificaciones-ui`: importación de calificaciones con preview/selección de actividades y configuración de umbral por materia.
- `frontend-atrasados-ui`: dashboard de atrasados, ranking, reportes rápidos, notas finales y export de entregas sin corregir.
- `frontend-comunicaciones-ui`: cola de comunicaciones con preview, envío, aprobación/cancelación y tracking de estado en tiempo real.
- `frontend-comision-context`: selector de comisión (materia + cohorte) compartido como contexto de trabajo docente, y contratos de API esperados de `C-06`/`C-07` para poblarlo.

### Modified Capabilities
<!-- Ninguna. El shell de C-21 (frontend-shell, frontend-auth-ui, frontend-http-client) expone los puntos de extensión (Sidebar items, rutas en App.tsx, ProtectedRoute) sin cambio de requisitos; C-22 los usa tal como están especificados. -->

## Impact

- **Código frontend nuevo**: `frontend/src/features/{comisiones,padron,calificaciones,atrasados,comunicaciones}/` con `{components,hooks,services,types,pages}` cada uno.
- **Código frontend tocado (aditivo)**: `frontend/src/shared/components/Sidebar.tsx` (nuevos ítems), `frontend/src/App.tsx` (nuevas rutas lazy protegidas).
- **Contratos de backend (aún no implementados)**: endpoints de `C-09 padron-ingesta-moodle`, `C-10 calificaciones-y-umbral`, `C-11 analisis-atrasados-reportes`, `C-12 comunicaciones-cola-worker`, y los catálogos de `C-06 estructura-academica` / `C-07 usuarios-y-asignaciones`. Esta propuesta documenta los contratos esperados; cualquier divergencia al implementar el backend se reconcilia ajustando solo la capa `services/` + `types/`.
- **Dependencias npm**: ninguna nueva esperada (el stack de `C-21` ya cubre React Hook Form + Zod, TanStack Query, Axios, Tailwind). Si se requiere parsing de xlsx en cliente para preview, se evalúa en design; el preview canónico lo provee el backend.
- **Tests**: Vitest + React Testing Library con mocks de API (sin tocar el backend). Cobertura ≥80% líneas en la capa de UI/servicios de estas features.
