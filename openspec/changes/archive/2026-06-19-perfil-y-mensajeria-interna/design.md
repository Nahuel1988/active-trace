## Context

activia-trace ya tiene el modelo `User` (auth-mínimo: `email_encrypted`, `email_lookup`, `password_hash`, `legajo`, `is_active`, `totp_enabled`) en `backend/app/models/user.py`, el `encryption_service` AES-256-GCM en `backend/app/core/security.py`, `get_current_user` que resuelve identidad desde el JWT (`backend/app/core/dependencies.py`) y el logout en `POST /api/auth/logout` (C-03). El roadmap (CHANGES.md, C-20) coloca este change en GATE 6, dependiente de **C-07 usuarios-y-asignaciones**, que entrega el modelo `Usuario` completo con la PII de perfil cifrada (`dni`, `cuil`, `cbu`, `alias_cbu`, etc.).

Este change implementa F11.1 (perfil propio editable), F3.4/F11.2/FL-10 (mensajería interna) y reutiliza F11.3 (logout de C-03). Governance: BAJO.

**Restricciones del proyecto** (reglas duras): identidad SIEMPRE desde el JWT; multi-tenancy row-level (`tenant_id` en cada tabla, repos filtran por tenant por defecto); PII cifrada AES-256; Pydantic `extra='forbid'`; Routers → Services → Repositories → Models; soft delete siempre; snake_case; TDD estricto (≥80% líneas, ≥90% reglas de negocio); sin mocks de DB (usar DB efímera de test); ≤500 LOC por archivo backend; una migración Alembic por cambio de schema.

## Goals / Non-Goals

**Goals:**
- `GET /api/perfil` y `PATCH /api/perfil` operando SIEMPRE sobre el usuario del JWT, con CUIL de solo lectura y PII bancaria cifrada.
- Modelos `HiloMensaje` y `MensajeInterno` + endpoints `/api/inbox/*` para listar, abrir, iniciar y responder hilos, con aislamiento por participante y por tenant.
- Una migración Alembic (`006_perfil_y_mensajeria`).
- Cobertura TDD de los campos editables, el rechazo de CUIL, el ciclo leer/responder de hilos y el aislamiento.

**Non-Goals:**
- NO reimplementar logout (se reutiliza `POST /api/auth/logout` de C-03).
- NO implementar el ABM de usuarios ni la edición de CUIL por ADMIN (es C-07).
- NO frontend (es C-21+).
- NO notificaciones push, adjuntos, ni búsqueda full-text en el inbox (fuera de alcance; el inbox solo recibe y responde hilos según FL-10).
- NO integrar con la cola de comunicaciones a alumnos (C-12): es un dominio paralelo e independiente.

## Decisions

### D1 — Los campos de perfil viven en `User`/`Usuario`, no en una entidad separada
La KB (§E4) modela todos los datos de perfil como atributos del propio `Usuario`. Este change extiende el modelo `User` existente con los campos de perfil. **Acoplamiento con C-07**: C-07 es el dueño canónico de estos campos. Para no bloquear, la migración de este change agrega los campos que aún no existan (idempotencia a nivel de schema: si C-07 ya los creó, este change solo agrega lo propio de mensajería + `modalidad_cobro`). En apply, lo primero es verificar el estado real de `user.py` y la migración de C-07.
- _Alternativa descartada_: una tabla `Perfil` 1-1 con `Usuario` → duplica identidad, contradice §E4 y complica el join. Rechazada.

### D2 — CUIL read-only se enforce por schema, no por lógica condicional
El `PerfilUpdate` Pydantic NO declara el campo `cuil`; con `extra='forbid'`, cualquier intento de enviarlo devuelve 422 automáticamente. Es la barrera más fuerte y más simple: el campo no existe en el contrato de escritura del dueño.
- _Alternativa descartada_: aceptar `cuil` y descartarlo en el service → permite que un cliente crea que lo editó y oculta el error. Rechazada por claridad de contrato.

### D3 — PII descifrada solo en la respuesta al propio dueño
`GET /api/perfil` descifra `dni`, `cbu`, `alias_cbu`, `cuil` para mostrárselos al dueño (es su propio dato). El cifrado/descifrado pasa por `encryption_service` (AES-256-GCM existente). Los logs nunca registran estos valores; los schemas de response los exponen solo en este endpoint del dueño, no en listados ni en el inbox.

### D4 — Identidad de participantes del hilo: remitente desde JWT, destinatario validado
El `autor_id`/remitente SIEMPRE es `current_user.id` (regla dura 8). El `destinatario_id` viene del body pero se valida que sea un usuario existente, activo y del MISMO tenant antes de crear el hilo. La autorización de abrir/responder se hace por pertenencia a participantes (fail-closed → 403 si no participa, no 404, para no filtrar contenido pero sí negar acceso).

### D5 — Modelo de participantes del hilo
`HiloMensaje` lleva `iniciado_por` y, para 1-a-1 (alcance de FL-10), un `destinatario_id`. La pertenencia de un usuario al hilo se evalúa como `user.id in {iniciado_por, destinatario_id}`. Esto cubre la conversación bidireccional de FL-10 sin sobre-diseñar una tabla N-N de participantes (que se podría agregar después si surge multi-destinatario).
- _Alternativa considerada_: tabla `participante_hilo` N-N desde el inicio → over-engineering para el alcance actual (FL-10 es 1-a-1). Se deja como evolución futura.

### D6 — Marcado de leído al abrir
Al hacer `GET /api/inbox/{hilo_id}`, el service marca `leido_at` en los `MensajeInterno` dirigidos al usuario actual que aún no estaban leídos. El indicador de no-leídos del listado se deriva de `leido_at IS NULL` (no se denormaliza un contador).

### D7 — Estructura por capas y archivos
- Models: `hilo_mensaje.py`, `mensaje_interno.py` (usan `TenantScopedMixin` + soft delete del `base.py` existente).
- Repositories: extender `user_repository` con `update_perfil`; nuevos `hilo_mensaje_repository`, `mensaje_interno_repository` (filtran por tenant por defecto).
- Services: `perfil_service` (lee/actualiza, cifra PII), `mensajeria_service` (lista/abre/inicia/responde, valida participación y tenant).
- Routers: `perfil.py`, `inbox.py` (sin lógica de negocio; delegan a services; identidad vía `get_current_user`).
- Schemas: `perfil.py` (`PerfilRead`, `PerfilUpdate` sin `cuil`), `inbox.py` (`HiloRead`, `HiloListItem`, `MensajeRead`, `IniciarHilo`, `ResponderMensaje`) — todos con `extra='forbid'`.

## Risks / Trade-offs

- **[C-07 aún en progreso entrega los campos de PII de `Usuario`]** → El apply debe primero inspeccionar el estado real de `user.py` y de la migración de C-07. Mitigación: migración aditiva y condicional; coordinar con el compañero de C-07 para no duplicar columnas ni migraciones. Si C-07 ya mergeó, este change solo agrega `modalidad_cobro` + tablas de mensajería.
- **[Filtrado de existencia de hilos]** → Responder 404 vs 403 puede filtrar si un hilo existe. Mitigación: 403 fail-closed para no-participantes; los endpoints nunca revelan contenido de hilos ajenos.
- **[Crecimiento del inbox]** → Sin paginación, `GET /api/inbox` podría devolver muchos hilos. Mitigación: paginar el listado (limit/offset) desde el inicio; ordenar por actividad reciente con índice `(tenant_id, destinatario_id)` y `(tenant_id, hilo_id)`.
- **[PII en logs]** → Descifrar PII para la respuesta del dueño abre riesgo de log accidental. Mitigación: nunca loguear el objeto perfil completo; tests que verifican que la PII no aparece en logs/respuestas de otros endpoints.

## Migration Plan

1. Verificar en apply el estado real de `backend/app/models/user.py` y de la migración de C-07 (¿ya existen `nombre`, `cuil`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo_profesional`?).
2. Crear migración `006_perfil_y_mensajeria`: agrega columnas de perfil faltantes sobre `user` (mínimo `modalidad_cobro`) + tablas `hilo_mensaje` y `mensaje_interno` con `tenant_id`, soft delete e índices de aislamiento.
3. Implementar models → repositories → services → schemas → routers con TDD.
4. Rollback: `downgrade` revierte las tablas nuevas y las columnas agregadas por ESTA migración (no las de C-07).

## Open Questions

- ¿C-07 ya está mergeado al momento del apply? Define cuántas columnas agrega la migración 006. **Resolver al iniciar el apply, coordinando con el compañero de C-07.**
- ¿La numeración de migración será `006` o la siguiente libre? Verificar el último `versions/*` antes de generar (actualmente el último es `005_estructura_academica`).
