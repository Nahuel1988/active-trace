## Why

Todo usuario autenticado necesita mantener sus propios datos de perfil (nombre, identificación fiscal, datos bancarios para liquidación, regional, modalidad de cobro) sin depender de un ADMIN, y comunicarse con otros usuarios registrados del sistema a través de una bandeja interna paralela a los emails que el sistema envía a alumnos. Hoy el modelo `Usuario` solo cubre identidad de auth; faltan la edición de perfil propio (F11.1), la mensajería interna entre usuarios (F3.4 / F11.2 / FL-10) y un canal de hilos que recoja notificaciones de coordinación y respuestas de actores. Sin los datos bancarios en perfil, un docente no puede ser liquidado (RN-26).

## What Changes

- **Perfil propio editable (F11.1)**: endpoints `GET /api/perfil` y `PATCH /api/perfil` que leen/actualizan SIEMPRE el usuario de la sesión (JWT), nunca un id de URL. Campos editables: `nombre`, `apellidos`, `dni`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo_profesional`, `modalidad_cobro` (factura | liquidacion). El CUIL es **solo lectura** para el dueño del perfil: nunca editable vía `/api/perfil`; solo un ADMIN puede modificarlo (vía el ABM de C-07). La PII sensible (`dni`, `cbu`, `alias_cbu`, `cuil`) se almacena cifrada AES-256 y nunca aparece en logs ni en texto plano.
- **Bandeja de mensajería interna (F3.4 / F11.2 / FL-10)**: nuevos modelos `HiloMensaje` (conversación) y `MensajeInterno` (cada mensaje del hilo, con autor, asunto, cuerpo, leído). Endpoints `/api/inbox/*` para listar hilos recibidos, abrir un hilo (marca leído), iniciar un hilo hacia otro usuario del tenant, y responder dentro del hilo. Mensajería **entre usuarios registrados** del sistema, paralela e independiente de las comunicaciones salientes a alumnos (C-12).
- **Cierre de sesión explícito (F11.3)**: se **reutiliza** el endpoint `POST /api/auth/logout` ya implementado en C-03. NO se reimplementa logout en este change; solo se documenta que la UI de perfil lo invoca.
- **Migración Alembic**: agrega las tablas `hilo_mensaje` y `mensaje_interno`, y las columnas de perfil faltantes sobre `user` que C-07 no haya provisto aún (`modalidad_cobro` como mínimo). Si C-07 ya entregó los campos de PII de `Usuario`, la migración de este change NO los duplica.

## Capabilities

### New Capabilities
- `perfil-usuario`: edición del perfil propio del usuario de la sesión, con campos editables vs. solo lectura por dominio, PII cifrada, e identidad tomada exclusivamente del JWT.
- `mensajeria-interna`: hilos y mensajes entre usuarios registrados del tenant (inbox), con lectura, inicio de hilo, respuesta dentro del hilo y aislamiento por participante y por tenant.

### Modified Capabilities
<!-- Ninguna capability existente cambia sus requisitos a nivel spec. El logout de C-03 se reutiliza sin modificar su contrato. -->

## Impact

- **Modelos nuevos**: `backend/app/models/hilo_mensaje.py`, `backend/app/models/mensaje_interno.py`.
- **Modelo modificado (acoplado a C-07)**: `backend/app/models/user.py` gana los atributos de perfil (`nombre`, `apellidos`, `dni`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo_profesional`, `cuil`, `modalidad_cobro`). Estos campos son provistos por **C-07 (usuarios-y-asignaciones)**, dependencia directa de este change. Si C-07 aún no los agregó, este change los introduce respetando el cifrado AES-256 existente.
- **Repositories nuevos**: `user_repository` extendido con update de perfil; `hilo_mensaje_repository`, `mensaje_interno_repository`.
- **Services nuevos**: `perfil_service`, `mensajeria_service`.
- **Routers nuevos**: `backend/app/api/v1/routers/perfil.py`, `backend/app/api/v1/routers/inbox.py`.
- **Schemas nuevos**: Pydantic v2 con `extra='forbid'` para request/response de perfil e inbox; el schema de actualización de perfil **excluye** CUIL.
- **Reutiliza**: `app.core.security.encryption_service` (AES-256), `get_current_user` (identidad desde JWT), `POST /api/auth/logout` de C-03.
- **Migración**: una migración Alembic (`006_perfil_y_mensajeria`).
- **Governance**: BAJO. Autonomía total si pasan los tests (no toca auth/RBAC/liquidaciones, aunque consume PII cifrada ya existente).
- **Dependencia**: C-07 (en progreso) provee el modelo `Usuario` con PII cifrada. El inbox no bloquea por C-07 (solo necesita `user.id`), pero la edición de perfil sí necesita los campos.
