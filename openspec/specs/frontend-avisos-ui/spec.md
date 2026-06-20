## ADDED Requirements

### Requirement: Listado de avisos para gestión (coordinación)

El sistema SHALL mostrar una página de listado de todos los avisos del tenant (`GET /api/v1/avisos/`) para gestión, incluyendo activos e inactivos. Cada fila SHALL mostrar título, alcance (badge), severidad (badge colorido), vigencia y acciones (editar, toggle activo/inactivo, eliminar).

#### Scenario: Coordinador ve todos los avisos
- **WHEN** un usuario con `avisos:publicar` navega a `/avisos`
- **THEN** el sistema ejecuta `useQuery` con key `['avisos', 'list']` y muestra tabla con todos los avisos no soft-deleted

#### Scenario: Sin avisos en el tenant
- **WHEN** no existen avisos en el tenant
- **THEN** el sistema muestra "No hay avisos publicados" y botón "Crear primer aviso"

#### Scenario: Error de carga
- **WHEN** la request falla
- **THEN** el sistema muestra mensaje de error con botón de reintento

### Requirement: Creación de aviso con formulario tipado

El sistema SHALL exponer un formulario de creación/edición de aviso (modal o página) con React Hook Form + Zod. Campos: título, cuerpo (textarea), alcance (select: Global/PorMateria/PorCohorte/PorRol), severidad (select: Info/Advertencia/Crítico), materia_id (condicional a alcance PorMateria), cohorte_id (condicional a PorCohorte), rol_destino (condicional a PorRol), inicio_en, fin_en (datetime), orden (number), requiere_ack (checkbox).

#### Scenario: Creación exitosa de aviso
- **WHEN** un usuario con `avisos:publicar` completa y envía el formulario
- **THEN** el sistema ejecuta `useMutation` a `POST /api/v1/avisos/`, invalida `['avisos']`, muestra toast de éxito, cierra el modal

#### Scenario: Validación condicional de alcance
- **WHEN** el usuario selecciona alcance PorMateria y no completa materia_id
- **THEN** Zod muestra "Debe seleccionar una materia para este alcance"

#### Scenario: Validación de rango de fechas
- **WHEN** el usuario ingresa `inicio_en` posterior a `fin_en`
- **THEN** Zod muestra error de validación correspondiente

### Requirement: Edición de aviso existente

El sistema SHALL permitir editar un aviso existente (`PUT /api/v1/avisos/{id}`) con el mismo formulario de creación pre-poblado.

#### Scenario: Edición exitosa
- **WHEN** un usuario con `avisos:publicar` edita un aviso
- **THEN** el sistema ejecuta `PUT /api/v1/avisos/{id}`, invalida `['avisos']`, muestra toast

#### Scenario: Edición de aviso soft-deleted
- **WHEN** un usuario intenta editar un aviso que fue eliminado
- **THEN** el sistema muestra "El aviso no existe o fue eliminado"

### Requirement: Toggle activo/inactivo de aviso

El sistema SHALL permitir activar/desactivar un aviso sin abrir el formulario de edición, mediante un toggle switch en la tabla que actualiza el campo `activo` vía `PUT /api/v1/avisos/{id}`.

#### Scenario: Desactivar aviso
- **WHEN** un usuario hace clic en el toggle de un aviso activo
- **THEN** el sistema ejecuta mutación, invalida `['avisos']`, muestra toast "Aviso desactivado"

#### Scenario: Activar aviso
- **WHEN** un usuario hace clic en el toggle de un aviso inactivo
- **THEN** el sistema ejecuta mutación, invalida `['avisos']`, muestra toast "Aviso activado"

### Requirement: Eliminación de aviso (soft-delete)

El sistema SHALL permitir eliminar un aviso con confirmación previa (`DELETE /api/v1/avisos/{id}`).

#### Scenario: Eliminación exitosa
- **WHEN** un usuario confirma la eliminación de un aviso
- **THEN** el sistema ejecuta `DELETE /api/v1/avisos/{id}`, invalida `['avisos']`, muestra toast
