## ADDED Requirements

### Requirement: Listado de slots de encuentro (vista coordinación/admin)

El sistema SHALL mostrar una página de listado de todos los slots de encuentro del tenant (`GET /api/encuentros/slots`) para administración. Cada fila SHALL mostrar materia, título, día de semana, hora, tipo (recurrente/único), cantidad de instancias generadas y acciones (ver detalle, eliminar, exportar HTML para LMS).

#### Scenario: Coordinador ve todos los slots
- **WHEN** un usuario con `encuentros:gestionar` navega a `/encuentros`
- **THEN** el sistema ejecuta `useQuery` con key `['encuentros', 'slots', 'list']` y muestra tabla con todos los slots del tenant

#### Scenario: Sin slots registrados
- **WHEN** no existen slots en el tenant
- **THEN** el sistema muestra "No hay encuentros programados" y botón "Crear primer slot"

#### Scenario: Filtrar slots por materia
- **WHEN** un usuario selecciona una materia en el filtro
- **THEN** el sistema pasa `?materia_id=` a `GET /api/encuentros/slots` y refresca la tabla

### Requirement: Creación de slot (recurrente o único)

El sistema SHALL exponer un formulario (modal) para crear un slot de encuentro con React Hook Form + Zod. Campos: modo (toggle recurrente/único), materia_id (select), título, hora, día_semana (select), fecha_inicio, cant_semanas (visible solo si modo=recurrente), fecha_unica (visible solo si modo=único), meet_url (opcional), vig_desde, vig_hasta.

#### Scenario: Creación exitosa de slot recurrente
- **WHEN** un usuario completa el formulario en modo recurrente y envía
- **THEN** el sistema ejecuta `useMutation` a `POST /api/encuentros/slots` con `modo: "recurrente"`, invalida `['encuentros']`, muestra toast "Slot creado con N instancias"

#### Scenario: Validación de campos condicionales
- **WHEN** el usuario selecciona modo recurrente y no completa `cant_semanas`
- **THEN** Zod muestra "Debe indicar la cantidad de semanas"

#### Scenario: Validación fecha_inicio vs día_semana (recurrente)
- **WHEN** el usuario selecciona modo recurrente con fecha_inicio que no coincide con día_semana
- **THEN** el sistema muestra error "La fecha de inicio debe ser {día_semana}"

### Requirement: Detalle de slot con instancias editables

El sistema SHALL mostrar el detalle de un slot (`GET /api/encuentros/slots/{slot_id}`) con su lista de instancias generadas. Cada instancia SHALL mostrar fecha, hora, estado (programado/realizado/cancelado), meet_url, video_url y comentario. El usuario SHALL poder editar cada instancia inline.

#### Scenario: Ver detalle de slot
- **WHEN** un usuario hace clic en un slot de la tabla
- **THEN** navega a `/encuentros/slots/{id}` y ve el detalle con todas las instancias

#### Scenario: Editar instancia inline
- **WHEN** un usuario cambia el estado de una instancia a "realizado" y agrega video_url
- **THEN** el sistema ejecuta `PATCH /api/encuentros/instancias/{instancia_id}`, invalida `['encuentros']`, muestra toast

#### Scenario: Exportar HTML para LMS
- **WHEN** un usuario hace clic en "Exportar HTML" en un slot
- **THEN** el sistema ejecuta `GET /api/encuentros/slots/{slot_id}/html` y muestra el HTML generado en un modal para copiar

### Requirement: Eliminación de slot (soft-delete)

El sistema SHALL permitir eliminar un slot con confirmación previa (`DELETE /api/encuentros/slots/{slot_id}`).

#### Scenario: Eliminación exitosa
- **WHEN** un usuario confirma la eliminación de un slot
- **THEN** el sistema ejecuta `DELETE /api/encuentros/slots/{slot_id}`, invalida `['encuentros']`, muestra toast "Slot eliminado"
