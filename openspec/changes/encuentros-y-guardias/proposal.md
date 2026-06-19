## Why

Los docentes y tutores necesitan planificar, registrar y publicar sus encuentros sincrónicos con alumnos, y los tutores deben registrar las guardias de atención que cubren. Hoy ambas capacidades son manuales o inexistentes: el docente anota sus encuentros fuera del sistema, copia links de videoconferencia a mano y no existe trazabilidad de guardias para coordinación. C-13 cierra ese gap (Épica 6 F6.1–F6.6 y FL-06) habilitando la planificación recurrente automatizada, el seguimiento por instancia y el export al LMS. Es un módulo de **uso frecuente**: cada docente opera con él al inicio y al cierre de cada encuentro semanal.

## What Changes

- Nuevo modelo `SlotEncuentro` (plantilla recurrente o fecha única de un encuentro): `asignacion_id` → FK a `Asignacion` (quién crea), `materia_id`, `titulo`, `hora`, `dia_semana` (enum), `fecha_inicio`, `cant_semanas` (0 si es encuentro único), `fecha_unica` (nullable, alternativa a recurrencia), `meet_url`, `vig_desde`, `vig_hasta`.
- Nuevo modelo `InstanciaEncuentro` (encuentro concreto derivado de un slot o independiente): `slot_id` (nullable si es independiente), `materia_id`, `fecha`, `hora`, `titulo`, `estado` (enum: Programado / Realizado / Cancelado), `meet_url`, `video_url` (nullable), `comentario` (nullable).
- Nuevo modelo `Guardia`: `asignacion_id` → FK a `Asignacion` (quién cubre), `materia_id`, `carrera_id`, `cohorte_id`, `dia` (enum día semana), `horario` (texto rango, ej. "14:00–14:45"), `estado` (enum: Pendiente / Realizada / Cancelada), `comentarios`, `creada_at`.
- Creación de encuentro recurrente (F6.1, RN-13): el sistema genera automáticamente todas las instancias del slot a partir de `fecha_inicio` + `cant_semanas`.
- Creación de encuentro único (F6.2, RN-13): slot con `fecha_unica` → genera exactamente 1 instancia.
- Edición de instancia individual (F6.3, RN-14): `estado`, `meet_url`, `video_url`, `comentario` editables por instancia sin afectar el slot ni otras instancias.
- Generación de bloque HTML para el aula virtual (F6.4): endpoint que retorna un fragmento HTML con la lista de instancias ordenadas cronológicamente, con links de videoconferencia y grabación.
- Vista admin de encuentros del tenant (F6.5): COORDINADOR/ADMIN ven todos los encuentros del tenant con filtros por materia y estado.
- Registro de guardias (F6.6): TUTOR registra sus propias guardias; COORDINADOR/ADMIN consultan el registro global con filtros y pueden exportar.
- Endpoints REST: `/api/encuentros/*` y `/api/guardias/*` protegidos con `encuentros:gestionar`.
- Migración Alembic `008_encuentros_y_guardias`: crea `slot_encuentro`, `instancia_encuentro`, `guardia`.
- Todos los modelos llevan `tenant_id` y soft delete; aislamiento row-level via `BaseRepository`.

## Capabilities

### New Capabilities

- `slot-encuentro-lifecycle`: Creación de slots recurrentes y únicos con generación automática de instancias (RN-13). Un slot recurrente genera N instancias; un slot único genera 1.
- `instancia-encuentro-edit`: Edición por instancia de estado, meet_url, video_url y comentario (RN-14). Independiente del slot padre.
- `encuentro-html-export`: Generación de bloque HTML con el calendario de encuentros y grabaciones para embeber en el aula virtual del LMS (F6.4, FL-06 paso 7).
- `encuentros-admin-view`: Vista transversal de todos los encuentros del tenant para COORDINADOR/ADMIN (F6.5).
- `guardia-lifecycle`: Registro de guardias por tutor con ciclo de estados (Pendiente / Realizada / Cancelada) y consulta/export global para coordinación (F6.6).

### Modified Capabilities

*(ninguna — no existen specs previas de encuentros ni guardias)*

## Impact

- **Nuevas tablas**: `slot_encuentro`, `instancia_encuentro`, `guardia` (una migración Alembic `008_encuentros_y_guardias`).
- **Nuevos endpoints**:
  - `POST /api/encuentros/slots` — crear slot (recurrente o único; genera instancias automáticamente).
  - `GET /api/encuentros/slots` — listar slots del usuario autenticado (o todos si COORDINADOR/ADMIN).
  - `GET /api/encuentros/slots/{slot_id}` — detalle del slot con sus instancias.
  - `DELETE /api/encuentros/slots/{slot_id}` — soft delete del slot (no borra instancias individuales).
  - `GET /api/encuentros/instancias` — listado de instancias con filtros (materia, estado, rango de fechas).
  - `GET /api/encuentros/instancias/{id}` — detalle de una instancia.
  - `PATCH /api/encuentros/instancias/{id}` — editar estado / meet_url / video_url / comentario.
  - `GET /api/encuentros/instancias/{slot_id}/html` — bloque HTML del slot para el LMS.
  - `POST /api/guardias` — registrar guardia (TUTOR registra la propia).
  - `GET /api/guardias` — listar guardias con filtros (materia, carrera, cohorte, estado, usuario).
  - `GET /api/guardias/{id}` — detalle.
  - `PATCH /api/guardias/{id}/estado` — cambiar estado de una guardia.
  - `GET /api/guardias/export` — export CSV/JSON del registro de guardias (COORDINADOR/ADMIN).
- **Permiso nuevo**: `encuentros:gestionar` — seed en `rbac_seed.py`, asignar a PROFESOR, TUTOR, COORDINADOR y ADMIN. El alcance "propio" vs "global" se resuelve en el service según el rol efectivo.
- **Dependencias hacia atrás**: C-07 (`Asignacion`, `Usuario`) y C-06 (`Materia`, `Carrera`, `Cohorte`) proveen las FK. Las tablas deben existir en el `head` antes de ejecutar la migración de C-13.
- **Dependencia hacia adelante**: C-23 (`frontend-coordinacion`) y C-21 (`frontend-shell`) consumirán estos endpoints para los paneles de encuentros y guardias.
- **Auditoría**: creación de slot, edición de estado de instancia y registro de guardia generan registro en `AuditLog` (C-05) con códigos `ENCUENTRO_SLOT_CREAR`, `ENCUENTRO_INSTANCIA_EDITAR`, `GUARDIA_REGISTRAR`.
- **Sin breaking changes**: primera definición de estas entidades en el sistema.
