## ADDED Requirements

### Requirement: Listado paginado de usuarios del tenant sin PII

El sistema SHALL renderizar el listado de usuarios del tenant (permiso `usuarios:gestionar`) consumiendo `GET /api/v1/admin/usuarios?regional=&facturador=` con la instancia Axios centralizada. La tabla SHALL mostrar únicamente `nombre`, `apellidos`, `legajo`, `regional`, `facturador` e `is_active` — NUNCA `dni`, `cuil`, `cbu` ni `alias_cbu` en el listado. SHALL soportar paginación (cursor/total) y filtros por `regional` y `facturador`. Los DTOs SHALL estar tipados sin `any`, en `snake_case`.

#### Scenario: Listado sin PII sensible
- **WHEN** se renderiza la tabla de usuarios
- **THEN** ninguna columna muestra `dni`, `cuil`, `cbu` ni `alias_cbu`

#### Scenario: Filtros combinados
- **WHEN** el usuario aplica `regional=Mendoza` y `facturador=true`
- **THEN** la query se invalida y recarga, mostrando solo los usuarios que cumplen ambos filtros

#### Scenario: Paginación por defecto
- **WHEN** se abre el listado sin filtros
- **THEN** la tabla muestra la primera página (hasta el límite del backend) con control para paginar

#### Scenario: Usuarios soft-deleted no aparecen
- **WHEN** existen usuarios dados de baja (soft delete)
- **THEN** no aparecen en el listado por defecto

### Requirement: Detalle de usuario con PII descifrada aislada

El sistema SHALL renderizar el detalle de un usuario consumiendo `GET /api/v1/admin/usuarios/{id}`, que devuelve `dni`, `cuil`, `cbu` y `alias_cbu` en claro. Esta PII SHALL mostrarse SOLO en el componente de detalle (campos enmascarables), NUNCA en estado global, en el listado ni en `console.log`.

#### Scenario: Detalle muestra PII descifrada
- **WHEN** un usuario con `usuarios:gestionar` abre el detalle de un usuario
- **THEN** se muestran `dni`, `cuil`, `cbu` y `alias_cbu` en claro en el detalle

#### Scenario: PII no se loguea ni propaga
- **WHEN** se inspecciona el flujo del detalle
- **THEN** la PII vive solo en el componente de detalle y no se escribe en logs, estado global ni se pasa a otras features

### Requirement: Alta y edición de usuarios

El sistema SHALL ofrecer un formulario (React Hook Form + Zod) para alta (`POST /api/v1/admin/usuarios`) y edición (`PUT /api/v1/admin/usuarios/{id}`). El formulario SHALL rechazar campos no declarados (consistente con `extra='forbid'` del backend: un 422 por campo extra se muestra como error). La edición parcial SHALL preservar los campos no enviados.

#### Scenario: Alta exitosa invalida el listado
- **WHEN** el usuario completa el formulario con datos válidos y envía
- **THEN** la mutación llama `POST /api/v1/admin/usuarios`, y al responder 201 invalida la lista

#### Scenario: Edición parcial preserva campos
- **WHEN** el usuario edita solo `regional` y `facturador` y guarda
- **THEN** la mutación llama `PUT /api/v1/admin/usuarios/{id}` con solo esos campos y el resto se preserva

#### Scenario: Campo no permitido devuelve error visible
- **WHEN** el backend responde 422 por un campo no declarado
- **THEN** el formulario muestra el error inline sin crash

### Requirement: Baja de usuario (soft delete) con confirmación

El sistema SHALL ofrecer una acción de baja (`DELETE /api/v1/admin/usuarios/{id}`) con confirmación previa. La baja es soft delete; tras ejecutarla la UI SHALL invalidar el listado y el usuario dejará de aparecer.

#### Scenario: Baja con confirmación
- **WHEN** el usuario pulsa "Dar de baja"
- **THEN** se muestra un diálogo de confirmación antes de enviar la request

#### Scenario: Baja exitosa actualiza el listado
- **WHEN** el backend responde 204 a la baja
- **THEN** la UI invalida el listado y el usuario desaparece de la tabla

### Requirement: Guard de permiso fail-closed

El sistema SHALL renderizar todas las vistas y acciones de usuarios solo si el usuario tiene el permiso `usuarios:gestionar`. Sin el permiso, la ruta SHALL redirigir a la pantalla 403 (fail-closed), consistente con el `ProtectedRoute` existente.

#### Scenario: Usuario sin permiso es redirigido a 403
- **WHEN** un usuario sin `usuarios:gestionar` navega a `/admin/usuarios`
- **THEN** la UI lo redirige a la pantalla 403 sin renderizar la tabla

### Requirement: Fetch de usuarios vía hooks de TanStack Query

El sistema SHALL realizar todo acceso de datos de usuarios mediante hooks de TanStack Query con query keys keyed por los filtros (lista) y por `id` (detalle). Cada mutación SHALL invalidar el listado afectado.

#### Scenario: Baja invalida el listado filtrado
- **WHEN** se da de baja un usuario con filtros aplicados
- **THEN** la query del listado con esos filtros se invalida y recarga
