## ADDED Requirements

### Requirement: Modelo Comunicacion con cifrado y máquina de estados
El sistema SHALL definir un modelo `Comunicacion` que herede de `TenantScopedMixin` y `Base`, con los campos: `id` (UUID PK), `tenant_id` (FK → tenant), `enviado_por` (FK → user), `materia_id` (FK → materia, nullable), `destinatario` (texto cifrado AES-256), `destinatario_hash` (texto, SHA-256 determinístico del email en lowercase para búsqueda), `asunto` (texto), `cuerpo` (texto enriquecido), `estado` (enum: Pendiente, Enviando, Enviado, Error, Cancelado), `lote_id` (UUID nullable, agrupa envíos masivos), `requiere_aprobacion` (booleano, default true), `enviado_at` (datetime nullable). SHALL aplicar soft delete (`deleted_at`) y tenant-scoping obligatorio.

#### Scenario: Creación de comunicación válida
- **WHEN** se crea un `Comunicacion` con datos completos y el destinatario se cifra automáticamente
- **THEN** el registro se persiste con estado `Pendiente`, `deleted_at = NULL`, y el campo `destinatario` contiene el email cifrado

#### Scenario: Destinatario se almacena cifrado
- **WHEN** se persiste un `Comunicacion` con email `alumno@example.com`
- **THEN** el valor en DB de `destinatario` NO es texto plano, es un string base64 cifrado con AES-256

#### Scenario: Soft delete no elimina físicamente
- **WHEN** se ejecuta `soft_delete` sobre una comunicación
- **THEN** el registro persiste en DB con `deleted_at` no nulo

#### Scenario: Máquina de estados rechaza transición inválida
- **WHEN** se intenta cambiar una comunicación de `Enviado` a `Pendiente`
- **THEN** el sistema rechaza la operación con error 400

#### Scenario: Transición Pendiente → Enviando
- **WHEN** se aprueba una comunicación en estado `Pendiente`
- **THEN** el estado cambia a `Enviando`

#### Scenario: Transición Enviando → Enviado
- **WHEN** el worker completa el despacho de una comunicación en estado `Enviando`
- **THEN** el estado cambia a `Enviado` y `enviado_at` se actualiza

#### Scenario: Transición Pendiente → Cancelado
- **WHEN** se cancela una comunicación en estado `Pendiente`
- **THEN** el estado cambia a `Cancelado`

#### Scenario: Comunicación siempre scoped por tenant
- **WHEN** se consulta una comunicación por ID
- **THEN** la query siempre filtra por `tenant_id`

### Requirement: Repositorio ComunicacionRepository con filtros
El sistema SHALL proveer `ComunicacionRepository(BaseRepository[Comunicacion])` con métodos: `get`, `list`, `create`, `soft_delete` (heredados) y métodos adicionales `list_by_lote(tenant_id, lote_id)` y `list_pendientes_para_worker(tenant_id, limit, session)` que retorna registros con `estado = 'Pendiente'` y `requiere_aprobacion = false` usando `FOR UPDATE SKIP LOCKED`.

#### Scenario: Listar por lote_id
- **WHEN** se llama a `list_by_lote` con un `lote_id` válido
- **THEN** retorna todas las comunicaciones activas de ese lote en el tenant

#### Scenario: Worker obtiene pendientes sin aprobación
- **WHEN** el worker llama a `list_pendientes_para_worker`
- **THEN** retorna comunicaciones con `estado = 'Pendiente'` y `requiere_aprobacion = false`, bloqueando las filas con `FOR UPDATE SKIP LOCKED`

### Requirement: Preview obligatorio antes del envío
El sistema SHALL exponer una operación de preview que recibe una plantilla de asunto, una plantilla de cuerpo y una lista de destinatarios con datos de sustitución, y retorna el asunto y cuerpo renderizados para cada destinatario. NO SHALL persistir ningún registro. SHALL requerir permiso `comunicacion:enviar`.

#### Scenario: Preview renderiza correctamente
- **WHEN** se envía un preview con asunto `"Alerta: {nombre_alumno}"` y datos `{"nombre_alumno": "Juan"}`
- **THEN** el asunto renderizado es `"Alerta: Juan"`

#### Scenario: Preview no persiste datos
- **WHEN** se completa una operación de preview exitosamente
- **THEN** no existe ningún registro nuevo en la tabla `comunicacion`

### Requirement: Envío masivo con cola y lote_id
El sistema SHALL exponer un endpoint que recibe una lista de destinatarios con datos de sustitución, una plantilla de asunto y cuerpo, y el `lote_id` (UUID generado por el cliente o por el server). SHALL crear un registro `Comunicacion` por cada destinatario en una sola transacción, todos con el mismo `lote_id`. SHALL requerir permiso `comunicacion:enviar`. SHALL auditar con `COMUNICACION_ENVIAR`.

#### Scenario: Envío masivo crea N registros
- **WHEN** se envían 5 destinatarios en un mismo lote
- **THEN** se crean 5 registros `Comunicacion` con el mismo `lote_id`, cada uno con estado `Pendiente`

#### Scenario: Envío atómico
- **WHEN** falla el envío masivo para el destinatario 3 de 5
- **THEN** no se persiste ningún registro (rollback de la transacción)

#### Scenario: Envío sin aprobación
- **WHEN** el usuario tiene permiso `comunicacion:enviar` con scope `propio`
- **THEN** los registros se crean con `requiere_aprobacion = false`

#### Scenario: Envío con aprobación requerida
- **WHEN** el usuario tiene permiso `comunicacion:enviar` con scope `global` (COORDINADOR/ADMIN) pero la configuración del tenant requiere aprobación
- **THEN** los registros se crean con `requiere_aprobacion = true`

### Requirement: Worker async de despacho
El sistema SHALL proveer un worker asíncrono en `workers/comunicacion_worker.py` que ejecuta un loop: pollea comunicaciones `Pendiente` con `requiere_aprobacion = false` (o `Enviando`), las envía, y actualiza el estado a `Enviado` o `Error`. SHALL usar `FOR UPDATE SKIP LOCKED` para evitar contención. SHALL respetar el intervalo de polling configurable. SHALL registrar cada resultado en el log de aplicación.

#### Scenario: Worker procesa lote exitosamente
- **WHEN** el worker encuentra 3 comunicaciones `Enviando`
- **THEN** las 3 pasan a `Enviado` y `enviado_at` se actualiza

#### Scenario: Worker marca error si falla el envío
- **WHEN** el worker falla al enviar una comunicación
- **THEN** la comunicación pasa a estado `Error`

#### Scenario: Worker no procesa Pendientes con requiere_aprobacion = true
- **WHEN** el worker ejecuta su ciclo de polling
- **THEN** solo considera registros con `estado = 'Enviando'`, o `estado = 'Pendiente'` con `requiere_aprobacion = false`

### Requirement: Plantillas con variables de sustitución
El sistema SHALL soportar las siguientes variables de sustitución en asunto y cuerpo: `{nombre_alumno}`, `{apellido_alumno}`, `{email_alumno}`, `{materia}`, `{comision}`, `{nombre_institucion}`. SHALL usar reemplazo exacto (`str.replace`) sin motor de templates externo. SHALL rechazar preview con variables desconocidas en la plantilla si no hay valor correspondiente (fail-fast).

#### Scenario: Sustitución de variable conocida
- **WHEN** el cuerpo contiene `"Hola {nombre_alumno}, tu materia es {materia}"` con datos `{nombre_alumno: "María", materia: "Matemáticas"}`
- **THEN** el cuerpo renderizado es `"Hola María, tu materia es Matemáticas"`

#### Scenario: Variable sin valor no se reemplaza
- **WHEN** la plantilla contiene `{variable_desconocida}` y no hay valor para ella
- **THEN** el sistema lanza error indicando variable no soportada

### Requirement: Listado de comunicaciones con filtros
El sistema SHALL exponer `GET /api/comunicaciones` con filtros opcionales: `estado`, `lote_id`, `materia_id`, `enviado_por`, `desde`, `hasta`. SHALL requerir `comunicacion:enviar` y respetar scope (propio → solo comunicaciones del usuario; global → todas del tenant). SHALL aplicar paginación (limit/offset).

#### Scenario: Filtro por estado
- **WHEN** se filtra por `estado = Error`
- **THEN** solo se retornan comunicaciones con estado `Error`

#### Scenario: Scope propio filtra por enviado_por
- **WHEN** un PROFESOR (scope propio) lista comunicaciones
- **THEN** solo ve comunicaciones donde `enviado_por = current_user.id`
