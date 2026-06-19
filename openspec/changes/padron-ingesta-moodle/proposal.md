## Why

El modelo de datos base (`Materia`, `Cohorte`, `Usuario`, `Asignacion`) está disponible desde C-06 y C-07. Sin un padrón de alumnos vinculado a cada combinación materia × cohorte, los módulos de análisis (C-10), comunicaciones (C-11) y seguimiento no tienen sobre qué operar: no hay a quiénes detectar como atrasados, ni destinatarios de mensajes salientes. C-09 cierra esta brecha introduciendo el **padrón versionado de alumnos** y la **integración con Moodle Web Services** para sync on-demand, con fallback de carga manual por archivo.

## What Changes

- **Modelos `VersionPadron` + `EntradaPadron` (E6)**: modelo versionado donde cada carga genera una nueva versión activa; activar una nueva versión desactiva la anterior para esa combinación `(materia_id, cohorte_id)`. `EntradaPadron.email` es PII → AES-256. `EntradaPadron.usuario_id` es nullable (alumno sin cuenta en el sistema).
- **Migración 008**: tablas `version_padron` y `entrada_padron` con índices y constraint de unicidad de versión activa por `(tenant_id, materia_id, cohorte_id)`.
- **Import de padrón por archivo (F1.3, F1.4)**: sube `.xlsx` o `.csv` con vista previa de alumnos detectados antes de confirmar la carga. Lógica de upsert destructivo que activa la nueva versión y desactiva la anterior.
- **Integración Moodle Web Services (§5.1)**: cliente `integrations/moodle_ws.py` que ejecuta sync on-demand del padrón desde el LMS; errores de la API de Moodle → `502` con mecanismo de reintento en el worker.
- **Vaciar datos de materia (F1.5, RN-04)**: endpoint que elimina (soft delete sobre la versión activa) los datos de padrón de la materia scoped al usuario que ejecuta la operación, sin afectar otras materias ni otros docentes.
- **Auditoría**: toda carga de padrón emite `PADRON_CARGAR` en el audit log con `filas_afectadas` real y referencia a la versión creada.
- **Endpoints nuevos** bajo `/api/v1/padron/*`: carga, vista previa, confirmación, sync Moodle y vaciado, todos guardados por `padron:cargar` / `padron:vaciar` (fail-closed).

## Capabilities

### New Capabilities

- `padron-version`: modelo versionado de padrón por `(materia, cohorte)` — `VersionPadron` + `EntradaPadron` (E6); invariante de una sola versión activa por tupla; `email` cifrado AES-256; `usuario_id` nullable.
- `padron-ingesta-archivo`: import de padrón desde `.xlsx`/`.csv` con vista previa y confirmación en dos pasos; activa nueva versión y desactiva la anterior; audita `PADRON_CARGAR`.
- `padron-moodle-sync`: integración con Moodle Web Services para sync on-demand del padrón; fallback a carga manual; errores → `502` con reintento.
- `padron-vaciar`: vaciado de datos de padrón de una materia scoped al usuario (RN-04); audita la operación.

### Modified Capabilities

<!-- C-09 NO modifica los contratos de Materia, Cohorte, Usuario ni Asignacion.
     Las capabilities de C-06 y C-07 quedan intactas; C-09 las referencia sin alterar sus requisitos. -->

## Impact

- **Código nuevo**: `app/models/padron.py` (`VersionPadron`, `EntradaPadron`), `app/repositories/padron_repository.py`, `app/services/padron_service.py`, `app/api/v1/routers/padron.py`, `app/schemas/padron.py`, `app/integrations/moodle_ws.py`.
- **Reutiliza sin modificar**: `AuditLogRepository` (C-05), `require_permission("padron:cargar")` (C-04), `get_current_user` / JWT (C-03), `Materia` y `Cohorte` (C-06), `cifrado AES-256` util (C-02).
- **Migración**: `migrations/versions/008_version_padron_entrada_padron.py` — tablas nuevas, índices, constraint `UNIQUE (tenant_id, materia_id, cohorte_id, activa) WHERE activa = true`.
- **RBAC**: permisos `padron:cargar` y `padron:vaciar` se agregan al catálogo; asignados a PROFESOR (scope propio) y COORDINADOR (scope global).
- **PII**: `EntradaPadron.email` cifrado en reposo con AES-256; no aparece en logs ni en respuestas sin desencriptar.
- **Multi-tenancy**: `tenant_id` en ambas tablas; todos los queries filtran por tenant del JWT.
