## ADDED Requirements

### Requirement: Extensión PII cifrada del modelo Usuario
El sistema SHALL extender el modelo `User` con los atributos institucionales `nombre`, `apellidos`, `banco`, `regional`, `legajo_profesional` y `facturador` (booleano, default `false`), y con las columnas de PII cifrada `dni_encrypted`, `cuil_encrypted`, `cbu_encrypted` y `alias_cbu_encrypted`. Las columnas `_encrypted` MUST almacenar el ciphertext producido por `EncryptionService.encrypt()` (AES-256-GCM) y NUNCA el valor en claro. El sistema MUST conservar el campo `legajo` existente como atributo de negocio nullable, sin promoverlo a credencial.

#### Scenario: Persistencia de DNI en columna cifrada
- **WHEN** se crea un usuario con `dni = "30123456"`
- **THEN** la columna `dni_encrypted` contiene un ciphertext base64 distinto de `"30123456"`, y el valor en claro NO aparece en ninguna columna de la tabla `user`

#### Scenario: Persistencia de CBU en columna cifrada
- **WHEN** se crea un usuario con `cbu = "0140123456789012345678"`
- **THEN** la columna `cbu_encrypted` contiene ciphertext base64 y el valor en claro NO aparece en ninguna columna

#### Scenario: Atributos no sensibles persistidos en claro
- **WHEN** se crea un usuario con `banco = "Banco Provincia"` y `regional = "Mendoza"`
- **THEN** las columnas `banco` y `regional` contienen los valores en claro tal como fueron provistos

#### Scenario: Round-trip de cifrado y descifrado
- **WHEN** se persiste un usuario con `cuil = "20301234564"` y se lee posteriormente vía el repository
- **THEN** el repository devuelve `cuil = "20301234564"` (descifrado correctamente)

#### Scenario: Flag facturador default false
- **WHEN** se crea un usuario sin especificar `facturador`
- **THEN** el registro persiste con `facturador = false`

#### Scenario: Legajo profesional opcional
- **WHEN** se crea un usuario sin `legajo_profesional`
- **THEN** el registro se persiste con `legajo_profesional = NULL` y es válido

### Requirement: PII jamás emitida en logs ni texto plano
El sistema SHALL garantizar que los valores en claro de `dni`, `cuil`, `cbu`, `alias_cbu` y `email` NUNCA aparezcan en logs estructurados, traces de OpenTelemetry, mensajes de error de la API ni stack traces. La representación de los schemas Pydantic (`__repr__` / `__str__`) MUST enmascarar estos campos.

#### Scenario: Logger no emite PII
- **WHEN** el service de usuarios crea un usuario y emite un log estructurado con el objeto request
- **THEN** los campos `dni`, `cuil`, `cbu`, `alias_cbu` y `email` aparecen enmascarados (ej: `"***"`) o ausentes en el log resultante

#### Scenario: Error de validación no expone PII en el detalle
- **WHEN** la API rechaza una request con un DNI inválido y devuelve un error 422
- **THEN** el detalle del error NO contiene el valor en claro del DNI

#### Scenario: Repr de schema Pydantic enmascara PII
- **WHEN** se evalúa `repr(usuario_create)` o `str(usuario_create)` para un schema cargado con PII
- **THEN** los campos `dni`, `cuil`, `cbu`, `alias_cbu` NO aparecen con su valor en claro

### Requirement: Unicidad por tenant preservada
El sistema SHALL preservar la unicidad `(tenant_id, email_lookup)` previamente establecida. NO MUST introducirse unicidad por `dni` ni por `cuil` en esta capacidad; si se requiere en el futuro, se agregará vía un change posterior con su correspondiente columna `_lookup` HMAC.

#### Scenario: Email único por tenant sigue vigente
- **WHEN** se intenta crear un segundo usuario con el mismo email en el mismo tenant
- **THEN** la base de datos rechaza la inserción por violación de la constraint `uq_user_tenant_email`

#### Scenario: DNI repetido en el mismo tenant es aceptado
- **WHEN** se crean dos usuarios distintos en el mismo tenant con el mismo `dni`
- **THEN** ambos registros coexisten sin error (no hay constraint de unicidad por DNI en esta capacidad)
