## Context

C-12 es el último change del camino crítico del roadmap. Construye sobre:
- **C-04 (RBAC)**: permisos `comunicacion:enviar` (seed: PROFESOR propio, COORDINADOR/ADMIN global) y `comunicacion:aprobar` (seed: COORDINADOR/ADMIN global) ya existen en `rbac_seed.py`.
- **C-05 (Audit log)**: el código `COMUNICACION_ENVIAR` ya existe en `AuditCodes`.
- **C-06 (Estructura académica)**: FK a `Materia` disponible.
- **C-07 (Usuarios y asignaciones)**: FK a `Usuario` disponible.
- **C-11 (Análisis atrasados)**: flujo que dispara comunicaciones existe.
- `workers/main.py`: placeholder no-op. Se reemplaza con el worker real.

El worker debe ser un proceso async independiente que comparte la misma base de datos y configuración que la API. No hay infraestructura de cola externa (Redis/RabbitMQ) disponible; la cola es la tabla `comunicacion` misma.

## Goals / Non-Goals

**Goals:**
- Modelo `Comunicacion` con cifrado AES-256 del destinatario, máquina de estados, lote_id, soft delete.
- Worker async en `workers/` que consume Pendiente → despacha → Enviado/Error.
- Preview obligatorio server-side antes de encolar (POST /api/comunicaciones/preview).
- Envío masivo vía POST /api/comunicaciones que crea N registros Pendiente en una tx.
- Aprobación: POST /api/comunicaciones/{id}/aprobar (individual) y POST /api/comunicaciones/lote/{lote_id}/aprobar (lote).
- Cancelación: POST /api/comunicaciones/{id}/cancelar y lote/{lote_id}/cancelar.
- Listado con filtros: GET /api/comunicaciones (estado, lote_id, materia_id, enviado_por).
- Plantillas con variables de sustitución: `{nombre_alumno}`, `{materia}`, `{comision}`.
- Auditoría vía `@audited` decorator con `AuditCodes.COMUNICACION_ENVIAR`.
- Tests de máquina de estados, preview, aprobación, cancelación, cifrado, worker.

**Non-Goals:**
- Infraestructura de cola externa (Redis, RabbitMQ, SQS). La cola es la DB.
- Mensajería interna (F3.4 — es otro change, C-14/C-15).
- Tablón de avisos (F3.5 — C-17).
- Reintentos automáticos (el worker marca Error; reintento es manual o en change futuro).
- Webhooks o callbacks de entrega.
- Frontend de comunicaciones (es parte del frontend shell).

## Decisions

### D-01: Cola sobre PostgreSQL sin middleware externo
**Contexto**: no hay Redis/RabbitMQ en la infraestructura actual. Agregarlos sería otro change.
**Decisión**: la tabla `comunicacion` es la cola. El worker hace polling periódico (`SELECT ... WHERE estado = 'Pendiente' LIMIT N FOR UPDATE SKIP LOCKED`).
**Por qué**: cero dependencias nuevas. El volumen esperado es bajo (decenas de mensajes por lote, no miles por segundo). FOR UPDATE SKIP LOCKED evita contención entre réplicas del worker.
**Alternativa**: Celery/ARQ — sobreingeniería para este volumen.

### D-02: Worker como proceso async independiente con asyncio loop
**Contexto**: `workers/main.py` es un placeholder.
**Decisión**: el worker corre en un proceso Python separado con `asyncio.run()`, comparte `Settings`, engine, y repositorios.
**Por qué**: reutiliza toda la capa de datos. El patrón `while True → poll → process → sleep` es simple y testeable extrayendo la lógica de polling a una función pura.

### D-03: Destinatario cifrado AES-256 con el servicio existente
**Contexto**: `app/core/security.py` ya tiene `EncryptionService` con AES-256.
**Decisión**: el campo `destinatario` se almacena cifrado. El service descifra al enviar. El valor cifrado es un string base64.
**Por qué**: el email del alumno es PII según RN-25. Reutilizamos el cifrado existente.
**Impacto**: las queries no pueden filtrar por email destino (el cifrado es probabilístico). Si se necesita búsqueda, se agrega una columna hash determinística (SHA-256 del email en lowercase).

### D-04: Máquina de estados en Enum con tabla de transiciones
**Contexto**: patrón usado en `Tarea` (C-16).
**Decisión**: `EstadoComunicacion(str, Enum)` con `_TRANSICIONES: dict[Estado, set[Estado]]` en el Service.
**Transiciones**:
- `Pendiente` → `Enviando` | `Cancelado`
- `Enviando` → `Enviado` | `Error`
- `Enviado` → (terminal)
- `Error` → (terminal, reintento manual es change futuro)
- `Cancelado` → (terminal)

### D-05: Lote como columna UUID, no entidad separada
**Contexto**: los mensajes masivos se agrupan.
**Decisión**: `lote_id` es un UUID en la misma tabla. No hay entidad `Lote`. El frontend agrupa por este campo.
**Por qué**: evita tabla extra, tx atómica. El lote es un concepto de agrupación, no de dominio.

### D-06: Plantillas con reemplazo string, sin motor de templates
**Contexto**: las variables son `{nombre_alumno}`, `{materia}`, `{comision}`.
**Decisión**: `str.replace()` simple. No se necesita Jinja2 ni renderizado HTML.
**Por qué**: evita dependencia. Las variables son fijas y controladas.

### D-07: Preview retorna asunto y cuerpo renderizados sin persistir
**Contexto**: RN-16 exige preview antes de encolar.
**Decisión**: `POST /api/comunicaciones/preview` recibe `PreviewRequest(asunto_template, cuerpo_template, destinatarios[])` y retorna `PreviewResponse(items[])` con asunto y cuerpo renderizados por destinatario. No persiste nada.
**Por qué**: separa claramente preview de envío. El frontend puede mostrar la preview y pedir confirmación antes de llamar a POST /api/comunicaciones.

### D-08: Aprobación como acción explícita, no estado automático
**Contexto**: RN-17 exige aprobación antes de pasar a Enviando.
**Decisión**: el endpoint `POST /api/comunicaciones/{id}/aprobar` transiciona `Pendiente → Enviando`. Sin aprobación explícita, el worker NO toca Pendientes (solo procesa los marcados como Enviando). Alternativamente, el worker podría procesar Pendientes que NO requieren aprobación (flujo profesor→alumno atrasado directo) y esperar aprobación para los demás. Esta distinción se modela con un flag `requiere_aprobacion` en cada registro.
**Por qué**: flexibilidad. Los mensajes de FL-02 paso 7 (profesor→alumno atrasado) no necesitan aprobación. FL-04 sí. El flag permite ambos flujos sin duplicar endpoints.

## Risks / Trade-offs

- **[R01] Polling sobre DB**: si el volumen crece, el polling satura la DB. → **Mitigación**: intervalo configurable, batch limit configurable, FOR UPDATE SKIP LOCKED.
- **[R02] Sin cola externa**: no hay persistencia fuera de DB. Si la DB cae, los mensajes en tránsito se pierden. → **Mitigación**: el estado Enviando permite detectar mensajes huérfanos (timeout en worker). Aceptable para el dominio.
- **[R03] Cifrado probabilístico impide búsqueda por email**: no se puede filtrar comunicaciones por destinatario exacto. → **Mitigación**: agregar columna `destinatario_hash` (SHA-256 determinístico) si el negocio lo exige. No se implementa en este change por PA-10 no resuelta.
- **[R04] Worker sin supervisión**: si el worker muere, los Pendientes no se procesan. → **Mitigación**: Docker restart policy. En producción, healthcheck + supervisor.
