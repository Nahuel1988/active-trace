## Why

El sistema necesita una cola asíncrona de comunicaciones con alumnos para soportar envíos masivos trazables desde la detección de atrasados (C-11) y garantizar preview obligatorio (RN-16), aprobación administrativa (RN-17) y ciclo de vida completo del mensaje (RN-15) sin bloquear al usuario.

## What Changes

- Nuevo modelo `Comunicacion` con destinatario cifrado AES-256, `lote_id` para agrupar envíos, y máquina de estados `Pendiente → Enviando → Enviado/Error/Cancelado`
- Worker asíncrono en `workers/` que consume mensajes `Pendiente`, los despacha y transiciona a `Enviado`/`Error`
- Preview obligatorio en `POST /api/comunicaciones/preview` antes de encolar
- Endpoints CRUD + acciones: listar, crear cola, aprobar (lote/individual), cancelar (lote/individual)
- Nuevos permisos `comunicacion:enviar` y `comunicacion:aprobar` en el catálogo RBAC
- Nuevo código de auditoría `COMUNICACION_ENVIAR`
- Plantillas de mensajes con variables de sustitución (`nombre_alumno`, `materia`, etc.)
- Filtro multi-tenant obligatorio en todas las queries via `BaseRepository`

## Capabilities

### New Capabilities
- `modelo-worker-comunicacion`: Modelo `Comunicacion` (cifrado, estados, lote_id), worker async en `workers/`, preview, envío masivo con cola, plantillas con sustitución, tracking de estado en tiempo real
- `aprobacion-comunicacion`: Aprobación de envíos masivos (lote completo o individual), cancelación, cola de aprobación visible para rol con `comunicacion:aprobar`

### Modified Capabilities
- `audit-log`: Agregar código `COMUNICACION_ENVIAR` al catálogo `AuditCodes`
- `rbac-permission-catalog`: Agregar permisos `comunicacion:enviar` y `comunicacion:aprobar` al seed de matriz base

## Impact

- **Backend**: nuevo modelo SQLAlchemy `Comunicacion`, nuevo repositorio `ComunicacionRepository`, nuevo service `ComunicacionService`, nuevo router `/api/comunicaciones/*`, nuevo worker `workers/comunicacion_worker.py`
- **Auth/RBAC**: dos nuevos permisos seedeados, guard `require_permission` existente se reutiliza
- **Audit**: un nuevo código en `AuditCodes`
- **Seguridad**: cifrado AES-256 del campo `destinatario` (email del alumno — PII)
- **No breaking**: todos los endpoints nuevos, sin modificar existentes
