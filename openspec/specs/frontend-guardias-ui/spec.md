## ADDED Requirements

### Requirement: Listado de guardias con filtros

El sistema SHALL mostrar una página de listado de todas las guardias del tenant (`GET /api/guardias`) para coordinación. Cada fila SHALL mostrar materia, tutor (docente), día, horario, estado (badge colorido) y acciones (cambiar estado, ver detalle). La página SHALL incluir una barra de filtros por materia, carrera, cohorte y estado.

#### Scenario: Coordinador ve todas las guardias
- **WHEN** un usuario con `guardias:registrar` navega a `/guardias`
- **THEN** el sistema ejecuta `useQuery` con key `['guardias', 'list']` y muestra tabla con filtros

#### Scenario: Sin guardias registradas
- **WHEN** no existen guardias en el tenant
- **THEN** el sistema muestra "No hay guardias registradas" y botón "Registrar guardia"

#### Scenario: Filtrar por estado
- **WHEN** un usuario selecciona estado "pendiente" en el filtro
- **THEN** el sistema pasa `?estado=pendiente` a `GET /api/guardias` y refresca

### Requirement: Registro de guardia

El sistema SHALL exponer un formulario (modal) para registrar una nueva guardia con React Hook Form + Zod. Campos: materia_id (select), carrera_id (select), cohorte_id (select), día (select lunes-domingo), horario (texto, ej. "14:00–15:00"), comentarios (textarea opcional).

#### Scenario: Registro exitoso
- **WHEN** un usuario completa y envía el formulario
- **THEN** el sistema ejecuta `useMutation` a `POST /api/guardias`, invalida `['guardias']`, muestra toast "Guardia registrada"

#### Scenario: Validación de campos requeridos
- **WHEN** el usuario intenta enviar sin completar materia u horario
- **THEN** Zod muestra errores de validación en los campos vacíos

### Requirement: Cambio de estado de guardia

El sistema SHALL permitir cambiar el estado de una guardia (pendiente → realizada, pendiente → cancelada) mediante un badge interactivo con dropdown inline.

#### Scenario: Marcar guardia como realizada
- **WHEN** un usuario selecciona "Realizada" en el dropdown de estado de una guardia pendiente
- **THEN** el sistema ejecuta `PATCH /api/guardias/{guardia_id}/estado` con `{ "estado": "realizada" }`, invalida `['guardias']`, muestra toast

### Requirement: Exportación CSV de guardias

El sistema SHALL exponer un botón "Exportar CSV" que descarga el listado completo de guardias filtradas (`GET /api/guardias/export`) como archivo CSV.

#### Scenario: Exportar guardias filtradas
- **WHEN** un usuario tiene filtros activos y hace clic en "Exportar CSV"
- **THEN** el sistema ejecuta `GET /api/guardias/export` con los mismos filtros, descarga el archivo
