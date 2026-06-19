## ADDED Requirements

### Requirement: Lectura del perfil propio

El sistema SHALL exponer `GET /api/perfil` que devuelve el perfil del usuario autenticado tomando la identidad EXCLUSIVAMENTE del JWT verificado (claim `sub`), nunca de un parámetro de URL, body ni header. La respuesta SHALL incluir los campos de perfil con la PII sensible (`dni`, `cbu`, `alias_cbu`, `cuil`) descifrada para mostrarse al propio dueño, y SHALL excluir campos internos de auth (`password_hash`, `email_lookup`).

#### Scenario: Usuario autenticado lee su propio perfil
- **WHEN** un usuario con JWT válido hace `GET /api/perfil`
- **THEN** el sistema responde 200 con sus datos de perfil (nombre, apellidos, email, dni, cuil, cbu, alias_cbu, banco, regional, legajo, legajo_profesional, modalidad_cobro, estado)

#### Scenario: La identidad proviene del token, no de la petición
- **WHEN** un usuario hace `GET /api/perfil` enviando en el body o query un `usuario_id` distinto al suyo
- **THEN** el sistema ignora ese valor y responde con el perfil del `sub` del JWT

#### Scenario: Sin token la lectura es rechazada
- **WHEN** se hace `GET /api/perfil` sin Authorization válido
- **THEN** el sistema responde 401

### Requirement: Edición de campos editables del perfil propio

El sistema SHALL exponer `PATCH /api/perfil` que actualiza ÚNICAMENTE el perfil del usuario del JWT. Los campos editables SHALL ser: `nombre`, `apellidos`, `dni`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo_profesional` y `modalidad_cobro` (valores permitidos: `factura`, `liquidacion`). La PII sensible editada (`dni`, `cbu`, `alias_cbu`) SHALL persistirse cifrada AES-256 mediante el `encryption_service` existente y NO SHALL aparecer en texto plano en logs.

#### Scenario: Edición exitosa de campos editables
- **WHEN** el usuario hace `PATCH /api/perfil` con `{ "banco": "Banco Nación", "cbu": "0110599520000001234567", "regional": "Córdoba" }`
- **THEN** el sistema responde 200, persiste los cambios y devuelve el perfil actualizado

#### Scenario: La PII bancaria se guarda cifrada
- **WHEN** el usuario actualiza su `cbu`
- **THEN** el valor se almacena cifrado AES-256 en la columna correspondiente y nunca en texto plano

#### Scenario: Actualización parcial respeta los campos no enviados
- **WHEN** el usuario hace `PATCH /api/perfil` enviando solo `{ "regional": "Mendoza" }`
- **THEN** el sistema actualiza solo `regional` y conserva el resto de los campos sin cambios

### Requirement: CUIL es de solo lectura para el dueño del perfil

El sistema SHALL tratar el `cuil` como campo de solo lectura desde `/api/perfil`. El schema de actualización de perfil (`extra='forbid'`) SHALL rechazar cualquier intento de enviar `cuil`. El `cuil` solo puede ser modificado por un ADMIN a través del ABM de usuarios (C-07), nunca por el propio usuario.

#### Scenario: Intento de modificar el CUIL es rechazado
- **WHEN** el usuario hace `PATCH /api/perfil` con un body que incluye `cuil`
- **THEN** el sistema responde 422 (campo no permitido por `extra='forbid'`) y NO modifica el `cuil`

#### Scenario: El CUIL se muestra pero no se altera
- **WHEN** el usuario lee su perfil y luego edita otros campos
- **THEN** el `cuil` se devuelve en la lectura pero permanece inalterado tras cualquier `PATCH /api/perfil`

### Requirement: Validación de campos del perfil

El sistema SHALL validar los campos del perfil con Pydantic v2 y `model_config = ConfigDict(extra='forbid')`. Campos desconocidos SHALL ser rechazados con 422. `modalidad_cobro` SHALL aceptar únicamente `factura` o `liquidacion`.

#### Scenario: Campo desconocido rechazado
- **WHEN** el usuario hace `PATCH /api/perfil` con un campo no declarado (p. ej. `is_admin: true`)
- **THEN** el sistema responde 422 sin aplicar ningún cambio

#### Scenario: modalidad_cobro inválida rechazada
- **WHEN** el usuario envía `modalidad_cobro: "efectivo"`
- **THEN** el sistema responde 422

### Requirement: Aislamiento por tenant del perfil

El sistema SHALL resolver el perfil dentro del `tenant_id` del JWT. Ningún usuario SHALL poder leer ni modificar un perfil de otro tenant bajo ninguna circunstancia.

#### Scenario: El perfil resuelto pertenece al tenant de la sesión
- **WHEN** un usuario del tenant A opera sobre `/api/perfil`
- **THEN** el repositorio filtra por `tenant_id` del tenant A y nunca alcanza usuarios de otro tenant

### Requirement: Cierre de sesión reutiliza el logout de C-03

El cierre de sesión explícito (F11.3) SHALL reutilizar el endpoint existente `POST /api/auth/logout` implementado en C-03. Este change NO SHALL reimplementar logout ni emitir un endpoint de logout propio bajo `/api/perfil`.

#### Scenario: La UI de perfil invoca el logout existente
- **WHEN** el usuario solicita cerrar sesión desde la pantalla de perfil
- **THEN** la aplicación invoca `POST /api/auth/logout` (contrato de C-03) y no un endpoint nuevo de este change
