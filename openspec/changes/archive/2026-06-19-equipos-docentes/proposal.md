## Why

C-07 entregó el modelo `Asignacion` (usuario × rol × contexto académico) con su CRUD individual. Pero la operación real de coordinación no es asignar de a uno: al iniciar cada período lectivo, un COORDINADOR necesita ver "su" equipo, asignar docentes en bloque, **clonar** el equipo de la cohorte anterior (RN-12), correr las fechas de vigencia de todo el equipo de una sola vez y exportar el resultado. Hacer eso con el CRUD individual de C-07 es inviable (decenas de llamadas manuales, sin atomicidad, sin trazabilidad de la operación de bloque). C-08 agrega la capa de **operaciones a nivel equipo** sobre el modelo ya existente.

## What Changes

- **Vista "mis equipos" del docente (F4.2)**: endpoint que lista las asignaciones vigentes del usuario autenticado (derivado del JWT), agrupadas por materia/carrera/cohorte/rol, con estado de vigencia. Lectura propia, sin requerir `equipos:asignar`.
- **Gestión de asignaciones del equipo (F4.3)**: vista de coordinación de todas las asignaciones del tenant con filtros (materia, carrera, cohorte, usuario, rol, responsable). Reutiliza el listado de C-07; C-08 agrega la noción de "equipo" como agrupación por la tupla (materia, carrera, cohorte).
- **Asignación masiva (F4.4, RN-30)**: dado un bloque `docentes[] × materia × carrera × cohorte × rol × vigencia`, crea N asignaciones en una sola transacción atómica, aplicando las validaciones rol×contexto de C-07 a cada una. Devuelve el resumen (creadas, rechazadas con motivo).
- **Clonar equipo entre períodos (F4.5, RN-12)**: dado un equipo origen (materia × carrera × cohorte) y un destino (carrera × cohorte destino + nueva vigencia), duplica todas las asignaciones **vigentes** del origen al destino, reescribiendo `cohorte_id`/`carrera_id` y las fechas `desde`/`hasta`. Resuelve solapamientos por idempotencia (no duplica una asignación ya existente en el destino).
- **Modificar vigencia general del equipo (F4.6)**: actualiza `desde`/`hasta` de todas las asignaciones de un equipo en una sola operación de bloque.
- **Exportar equipo (F4.7)**: genera un archivo CSV con el detalle de las asignaciones del equipo (docente, rol, materia, carrera, cohorte, comisiones, vigencia, estado).
- **Endpoints nuevos** bajo `/api/v1/equipos/*`, todos los de escritura/coordinación con guard `equipos:asignar` (fail-closed; COORDINADOR, NEXO, ADMIN según matriz RBAC). La vista "mis equipos" se resuelve por identidad de sesión, no por permiso de coordinación.
- **Auditoría**: las operaciones de bloque emiten `ASIGNACION_MODIFICAR` (más `ASIGNACION_CREAR` por cada alta en masiva/clonado) vía el repositorio de audit de C-05, registrando `filas_afectadas` real de la operación de bloque.

## Capabilities

### New Capabilities
- `equipo-mis-asignaciones`: vista de solo-lectura del equipo propio del docente (F4.2), resuelta por identidad de sesión; agrupa las asignaciones vigentes del usuario por contexto académico.
- `equipo-operaciones-bloque`: operaciones de coordinación a nivel equipo sobre `Asignacion` — asignación masiva (F4.4), clonado entre períodos (F4.5, RN-12) y modificación de vigencia en bloque (F4.6), todas atómicas, auditadas y guardadas por `equipos:asignar`.
- `equipo-export`: exportación del detalle de un equipo a CSV (F4.7).

### Modified Capabilities
<!-- C-08 NO modifica el contrato del modelo Asignacion ni su CRUD individual.
     Las capabilities asignacion-modelo y asignacion-crud (C-07) quedan intactas;
     C-08 las consume sin cambiar sus requisitos. -->

## Impact

- **Código nuevo**: `app/api/v1/routers/equipos.py`, `app/services/equipo_service.py`, métodos nuevos en `AsignacionRepository` (consultas por tupla de equipo, alta en lote), `app/schemas/equipo.py`.
- **Reutiliza sin modificar**: `Asignacion` (modelo), `AsignacionService` (validaciones rol×contexto), `AuditLogRepository` (C-05), `require_permission("equipos:asignar")` (C-04), `get_current_user` (C-03).
- **Sin migración de schema**: opera sobre tablas existentes (`asignacion`, `audit_log`). No agrega columnas.
- **RBAC**: `equipos:asignar` ya existe en el catálogo y la matriz base (rbac_seed); no requiere nuevo permiso.
- **Multi-tenancy**: todas las consultas y altas de bloque filtran por `tenant_id` del JWT por defecto.
