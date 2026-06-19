## ADDED Requirements

### Requirement: Modelo de hilos y mensajes internos

El sistema SHALL modelar la mensajería interna con dos entidades multi-tenant: `HiloMensaje` (la conversación) y `MensajeInterno` (cada mensaje del hilo). `HiloMensaje` SHALL tener `tenant_id`, `asunto`, `iniciado_por` (FK Usuario) y un conjunto de participantes (al menos remitente y destinatario). `MensajeInterno` SHALL tener `tenant_id`, `hilo_id` (FK), `autor_id` (FK Usuario), `cuerpo`, `creado_at` y el estado de lectura por destinatario (`leido_at` nullable). Ambas entidades SHALL usar soft delete (nunca hard delete).

#### Scenario: Un hilo agrupa sus mensajes
- **WHEN** se crea un hilo con un primer mensaje y luego se agrega una respuesta
- **THEN** ambos `MensajeInterno` comparten el mismo `hilo_id` y se ordenan por `creado_at`

#### Scenario: Las entidades llevan tenant_id
- **WHEN** se persiste un hilo o un mensaje
- **THEN** ambos registros llevan el `tenant_id` del autor de la sesión

### Requirement: Listado de hilos recibidos (inbox)

El sistema SHALL exponer `GET /api/inbox` que lista los hilos en los que el usuario del JWT es participante, dentro de su tenant, ordenados por actividad reciente. La respuesta SHALL incluir asunto, contraparte, fecha del último mensaje y un indicador de no leídos. El usuario SHALL ver solo hilos donde participa; nunca hilos ajenos.

#### Scenario: El usuario ve sus hilos recibidos
- **WHEN** un usuario participante de 3 hilos hace `GET /api/inbox`
- **THEN** el sistema responde 200 con esos 3 hilos y su estado de no leídos

#### Scenario: No se ven hilos donde no se participa
- **WHEN** existe un hilo entre otros dos usuarios y un tercero hace `GET /api/inbox`
- **THEN** ese hilo NO aparece en la respuesta del tercero

### Requirement: Apertura de un hilo y marcado de leído

El sistema SHALL exponer `GET /api/inbox/{hilo_id}` que devuelve los mensajes del hilo en orden cronológico, SOLO si el usuario del JWT es participante. Al abrir el hilo, los mensajes dirigidos al usuario SHALL marcarse como leídos (`leido_at`). Si el usuario no participa del hilo, el sistema SHALL responder 403 (fail-closed), nunca 404 que filtre existencia.

#### Scenario: Participante abre su hilo y se marca leído
- **WHEN** un participante hace `GET /api/inbox/{hilo_id}` con mensajes no leídos dirigidos a él
- **THEN** el sistema responde 200 con los mensajes y marca como leídos los que le corresponden

#### Scenario: No participante no puede abrir el hilo
- **WHEN** un usuario que no participa del hilo hace `GET /api/inbox/{hilo_id}`
- **THEN** el sistema responde 403 y no expone el contenido

### Requirement: Inicio de un hilo hacia otro usuario

El sistema SHALL exponer `POST /api/inbox` que crea un hilo nuevo con su primer mensaje hacia otro usuario registrado del MISMO tenant. El remitente SHALL ser SIEMPRE el usuario del JWT (no un valor del body). El destinatario SHALL validarse como usuario existente y activo del tenant. El body SHALL declarar `destinatario_id`, `asunto` y `cuerpo`, validados con Pydantic `extra='forbid'`.

#### Scenario: Inicio exitoso de un hilo
- **WHEN** un usuario hace `POST /api/inbox` con `{ "destinatario_id": "<uuid>", "asunto": "Reunión", "cuerpo": "..." }` hacia un usuario válido de su tenant
- **THEN** el sistema responde 201, crea el `HiloMensaje` y su primer `MensajeInterno` con `autor_id` = usuario de la sesión

#### Scenario: El remitente no puede falsificarse
- **WHEN** el body incluye un `autor_id` o `remitente_id` distinto del usuario de la sesión
- **THEN** el sistema rechaza el campo (422 por `extra='forbid'`) o lo ignora, y usa siempre el `sub` del JWT

#### Scenario: Destinatario de otro tenant es rechazado
- **WHEN** un usuario del tenant A intenta iniciar un hilo con un `destinatario_id` del tenant B
- **THEN** el sistema responde 404/422 (destinatario no encontrado en el tenant) y no crea el hilo

### Requirement: Respuesta dentro de un hilo

El sistema SHALL exponer `POST /api/inbox/{hilo_id}/responder` que agrega un `MensajeInterno` al hilo existente, SOLO si el usuario del JWT es participante. El `autor_id` del mensaje SHALL ser el usuario de la sesión. El body SHALL declarar `cuerpo` validado con `extra='forbid'`.

#### Scenario: Respuesta exitosa dentro del hilo
- **WHEN** un participante hace `POST /api/inbox/{hilo_id}/responder` con `{ "cuerpo": "De acuerdo" }`
- **THEN** el sistema responde 201 y agrega el mensaje al hilo con `autor_id` = usuario de la sesión

#### Scenario: No participante no puede responder
- **WHEN** un usuario que no participa del hilo intenta responder
- **THEN** el sistema responde 403 y no agrega el mensaje

### Requirement: Aislamiento por participante y por tenant

El sistema SHALL acotar toda operación de inbox al `tenant_id` del JWT y al conjunto de participantes del hilo. Ningún usuario SHALL leer, abrir ni responder hilos de otro tenant ni hilos donde no participa.

#### Scenario: Aislamiento entre tenants
- **WHEN** un usuario del tenant A consulta cualquier endpoint de `/api/inbox`
- **THEN** el repositorio filtra por `tenant_id` del tenant A y nunca alcanza hilos ni mensajes de otro tenant

#### Scenario: La mensajería interna es independiente de las comunicaciones a alumnos
- **WHEN** se listan los hilos del inbox interno
- **THEN** no se incluyen las comunicaciones salientes a alumnos (C-12); son dominios separados
