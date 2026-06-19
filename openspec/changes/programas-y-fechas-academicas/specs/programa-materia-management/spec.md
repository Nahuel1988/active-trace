## ADDED Requirements

### Requirement: Asociar un programa a materia × carrera × cohorte
El sistema SHALL permitir registrar un `ProgramaMateria` que asocia el programa oficial de una materia a una combinación específica de carrera y cohorte, con un título descriptivo y una `referencia_archivo` (string opaco al servicio de almacenamiento). La combinación `(tenant_id, materia_id, carrera_id, cohorte_id)` SHALL ser única; el sistema SHALL rechazar un segundo registro para la misma combinación.

#### Scenario: Crear programa con combinación nueva
- **WHEN** un usuario con `estructura:gestionar` envía `POST /api/programas` con `materia_id`, `carrera_id`, `cohorte_id`, `titulo` y `referencia_archivo` válidos y la combinación no existe en el tenant
- **THEN** el sistema crea el programa, persiste `cargado_at` y retorna 201 con el recurso creado

#### Scenario: Rechazar combinación duplicada
- **WHEN** un usuario envía `POST /api/programas` con una combinación `(materia_id, carrera_id, cohorte_id)` que ya existe en el mismo tenant
- **THEN** el sistema retorna 409 (o 400) con mensaje de conflicto de unicidad y no crea un segundo registro

#### Scenario: Rechazar materia/carrera/cohorte inexistente o borrada
- **WHEN** un usuario envía `POST /api/programas` con un `materia_id`, `carrera_id` o `cohorte_id` que no existe en el tenant o está soft-deleted
- **THEN** el sistema retorna 404 (o 422) y no crea el programa

---

### Requirement: La referencia de archivo es opaca
El sistema SHALL persistir y devolver `referencia_archivo` como un string sin interpretarlo, sin validar la existencia física del archivo ni su formato. El sistema NO SHALL recibir ni almacenar el binario del documento en este módulo.

#### Scenario: Persistir referencia tal cual
- **WHEN** un usuario crea un programa con `referencia_archivo = "storage://tenant-a/programas/prog-i-2026.pdf"`
- **THEN** el sistema guarda exactamente ese string y lo devuelve sin modificarlo en `GET /api/programas/{id}`

#### Scenario: No se valida existencia del archivo
- **WHEN** un usuario crea un programa con una `referencia_archivo` que apunta a un archivo inexistente en storage
- **THEN** el sistema acepta el registro (la validación de existencia es responsabilidad del servicio de almacenamiento)

---

### Requirement: Actualizar la referencia/título del programa vigente
El sistema SHALL permitir actualizar `titulo` y `referencia_archivo` de un programa existente vía `PUT /api/programas/{id}`, manteniendo la combinación materia × carrera × cohorte. Subir una nueva versión del programa reemplaza la referencia sin crear un duplicado.

#### Scenario: Reemplazar referencia con nueva versión
- **WHEN** un usuario con `estructura:gestionar` envía `PUT /api/programas/{id}` con una nueva `referencia_archivo`
- **THEN** el sistema actualiza el registro existente y retorna 200 con la referencia nueva

---

### Requirement: Listar y obtener programas (lectura)
El sistema SHALL permitir listar programas del tenant filtrando opcionalmente por `materia_id`, `carrera_id` o `cohorte_id`, y obtener un programa por su `id`. La lectura SHALL requerir el permiso `estructura:ver`.

#### Scenario: Listar programas filtrados por cohorte
- **WHEN** un usuario con `estructura:ver` envía `GET /api/programas?cohorte_id={id}`
- **THEN** el sistema retorna 200 con solo los programas de esa cohorte en el tenant del usuario

#### Scenario: Obtener programa por id
- **WHEN** un usuario con `estructura:ver` envía `GET /api/programas/{id}` de un programa existente del tenant
- **THEN** el sistema retorna 200 con el recurso

---

### Requirement: Soft delete de programas
El sistema SHALL implementar borrado lógico vía `deleted_at`. Un programa borrado no aparece en los listados ni se recupera por id.

#### Scenario: Borrar programa
- **WHEN** un usuario con `estructura:gestionar` envía `DELETE /api/programas/{id}`
- **THEN** el sistema establece `deleted_at`, retorna 204 y el programa deja de aparecer en `GET /api/programas`

#### Scenario: Programa borrado no se recupera por id
- **WHEN** un usuario envía `GET /api/programas/{id}` de un programa con `deleted_at` poblado
- **THEN** el sistema retorna 404

---

### Requirement: RBAC fail-closed en programas
El sistema SHALL verificar `estructura:gestionar` en escritura (POST/PUT/DELETE) y `estructura:ver` en lectura (GET). Sin el permiso correspondiente → 403.

#### Scenario: Escritura sin permiso de gestión
- **WHEN** un usuario sin `estructura:gestionar` envía `POST /api/programas`
- **THEN** el sistema retorna 403 y no crea el programa

#### Scenario: Lectura sin permiso de ver
- **WHEN** un usuario sin `estructura:ver` envía `GET /api/programas`
- **THEN** el sistema retorna 403

---

### Requirement: Aislamiento multi-tenant en programas
El sistema SHALL operar únicamente sobre programas del tenant del usuario autenticado, derivado de la sesión JWT. Un usuario NO SHALL listar, obtener, actualizar ni borrar programas de otro tenant.

#### Scenario: Listado aislado por tenant
- **WHEN** un usuario del tenant A consulta `GET /api/programas`
- **THEN** el sistema retorna solo los programas del tenant A, ninguno del tenant B

#### Scenario: Acceso cruzado a programa de otro tenant
- **WHEN** un usuario del tenant A envía `GET /api/programas/{id}` de un programa que pertenece al tenant B
- **THEN** el sistema retorna 404 (no revela existencia cross-tenant)
