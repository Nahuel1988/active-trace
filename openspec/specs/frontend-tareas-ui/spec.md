## ADDED Requirements

### Requirement: Vista "Mis Tareas" para el usuario autenticado

El sistema SHALL mostrar una página "Mis Tareas" que lista las tareas asignadas al usuario (`GET /api/tareas/mias`). Cada tarea SHALL mostrar título, descripción, estado (badge), prioridad, creador, fecha de vencimiento y acciones (ver detalle, cambiar estado).

#### Scenario: Usuario ve sus tareas
- **WHEN** un usuario autenticado navega a `/tareas/mias`
- **THEN** el sistema ejecuta `useQuery` con key `['tareas', 'mias']` y muestra tabla de tareas

#### Scenario: Sin tareas asignadas
- **WHEN** el usuario no tiene tareas asignadas
- **THEN** el sistema muestra "No tenés tareas pendientes"

### Requirement: Listado admin de todas las tareas del tenant

El sistema SHALL mostrar un listado admin de todas las tareas del tenant (`GET /api/tareas`) con filtros por estado, asignado, prioridad y rango de fechas. Vista toggleable entre tabla y kanban.

#### Scenario: Admin ve todas las tareas
- **WHEN** un usuario con `tareas:gestionar` navega a `/tareas`
- **THEN** el sistema ejecuta `useQuery` con key `['tareas', 'list', filters]` y muestra tabla

#### Scenario: Filtro por estado
- **WHEN** el usuario selecciona un estado en el filtro
- **THEN** el sistema refresca la query y muestra solo tareas en ese estado

#### Scenario: Vista kanban
- **WHEN** el usuario hace clic en "Vista Kanban"
- **THEN** el sistema muestra columnas por estado (Pendiente, En Progreso, Completada)

### Requirement: Creación de tarea con asignación

El sistema SHALL exponer un formulario de creación de tarea (modal) con campos: título, descripción, prioridad (select), asignado_a (select de usuarios del tenant), fecha_vencimiento (date), estado inicial. Consume `POST /api/tareas`.

#### Scenario: Creación exitosa
- **WHEN** un usuario con `tareas:gestionar` completa el formulario
- **THEN** el sistema ejecuta `useMutation`, invalida `['tareas']`, muestra toast de éxito

#### Scenario: Validación de campos requeridos
- **WHEN** el formulario se envía sin título
- **THEN** Zod muestra "El título es requerido"

### Requirement: Detalle de tarea con comentarios

El sistema SHALL mostrar una página de detalle de tarea (`GET /api/tareas/{id}`) con información completa y timeline de comentarios (`GET /api/tareas/{id}/comentarios`). El usuario SHALL poder agregar comentarios inline (`POST /api/tareas/{id}/comentarios`).

#### Scenario: Ver detalle de tarea
- **WHEN** un usuario navega a `/tareas/:id`
- **THEN** el sistema ejecuta `useQuery` para la tarea y sus comentarios, muestra detalle + timeline

#### Scenario: Agregar comentario
- **WHEN** un usuario escribe y envía un comentario
- **THEN** el sistema ejecuta `useMutation`, invalida `['comentarios']`, muestra el nuevo comentario en la timeline

### Requirement: Cambio de estado de tarea

El sistema SHALL permitir cambiar el estado de una tarea (`PATCH /api/tareas/{id}/estado`) desde la tabla, detalle o vista kanban. Los estados SHALL ser: Pendiente, En Progreso, Completada, Cancelada.

#### Scenario: Cambio de estado exitoso
- **WHEN** un usuario cambia el estado de una tarea
- **THEN** el sistema ejecuta `useMutation`, invalida `['tareas']`, muestra toast

### Requirement: Reasignación de tarea

El sistema SHALL permitir reasignar una tarea a otro usuario (`POST /api/tareas/{id}/asignar`) mediante un select de usuarios.

#### Scenario: Reasignación exitosa
- **WHEN** un usuario selecciona un nuevo asignado
- **THEN** el sistema ejecuta mutación, invalida `['tareas']`, muestra toast "Tarea reasignada"
