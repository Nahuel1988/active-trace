## ADDED Requirements

### Requirement: Vista "Mis Equipos" para el docente autenticado

El sistema SHALL mostrar una página "Mis Equipos" que lista las asignaciones del docente autenticado, obtenidas de `GET /api/v1/equipos/mis-equipos`. Cada asignación SHALL mostrar materia, carrera, cohorte, rol y vigencia.

#### Scenario: Docente ve sus equipos
- **WHEN** un usuario autenticado navega a `/equipos/mis-equipos`
- **THEN** el sistema ejecuta `useQuery` con key `['equipos', 'mis-equipos']` y muestra un grid de tarjetas con los datos de cada asignación

#### Scenario: Docente sin asignaciones ve estado vacío
- **WHEN** un usuario autenticado sin asignaciones navega a `/equipos/mis-equipos`
- **THEN** el sistema muestra "No tenés equipos asignados" con un icono ilustrativo

#### Scenario: Error de red muestra mensaje de error
- **WHEN** la request a `GET /api/v1/equipos/mis-equipos` falla por error de red
- **THEN** el sistema muestra "Error al cargar tus equipos" con botón de reintento

### Requirement: Listado de equipos del tenant para coordinación

El sistema SHALL mostrar una página de listado de equipos del tenant (`GET /api/v1/equipos`) con filtros por materia, carrera, cohorte y rol. Cada fila SHALL mostrar materia, comisiones, cantidad de docentes asignados y acciones (asignación masiva, clonar, exportar).

#### Scenario: Coordinador ve todos los equipos del tenant
- **WHEN** un usuario con `equipos:asignar` navega a `/equipos`
- **THEN** el sistema ejecuta `useQuery` con key `['equipos', 'list', filters]` y muestra una tabla paginada

#### Scenario: Coordinador filtra equipos
- **WHEN** un usuario selecciona un filtro de materia
- **THEN** el sistema refresca la query con los nuevos filtros y la tabla se actualiza

#### Scenario: Sin equipos en el tenant
- **WHEN** no existen equipos en el tenant
- **THEN** el sistema muestra "No hay equipos cargados" y botón "Ir a asignación masiva"

### Requirement: Formulario de asignación masiva de docentes

El sistema SHALL exponer un formulario paso a paso para asignación masiva que consume `POST /api/v1/equipos/asignacion-masiva`. El formulario SHALL incluir: selección de materia, carrera, cohorte, rol, responsable opcional, comisiones, vigencia y selección múltiple de usuarios. SHALL mostrar resultado con creadas/rechazadas.

#### Scenario: Asignación masiva exitosa
- **WHEN** un usuario con `equipos:asignar` completa el formulario y envía
- **THEN** el sistema ejecuta `useMutation` con invalidation de `['equipos']` y `['asignaciones']`, muestra toast de éxito con detalle de creadas y rechazadas

#### Scenario: Error de validación en el formulario
- **WHEN** el formulario se envía sin datos requeridos (ej. sin materia)
- **THEN** Zod valida y muestra error en el campo correspondiente, no se envía la request

#### Scenario: Error 422 del backend
- **WHEN** el backend responde 422 con errores de validación
- **THEN** el sistema muestra los errores en el formulario o un mensaje genérico "Error en los datos enviados"

### Requirement: Formulario de clonación de equipo

El sistema SHALL exponer un formulario de clonación de equipo entre períodos (`POST /api/v1/equipos/clonar`) con selección de equipo origen y destino (carrera, cohorte, vigencia nueva).

#### Scenario: Clonación exitosa
- **WHEN** un usuario con `equipos:asignar` completa el formulario de clonación
- **THEN** el sistema ejecuta `useMutation`, invalida `['equipos']`, muestra toast con resultado (clonadas/omitidas)

#### Scenario: Equipo origen sin asignaciones vigentes
- **WHEN** el equipo origen seleccionado no tiene asignaciones vigentes para clonar
- **THEN** el sistema muestra toast informativo "El equipo origen no tiene asignaciones vigentes para clonar"

### Requirement: Modificación de vigencia de equipo

El sistema SHALL exponer un formulario inline para modificar la vigencia de un equipo completo (`PATCH /api/v1/equipos/vigencia`), con campos desde/hasta.

#### Scenario: Actualización de vigencia exitosa
- **WHEN** un usuario con `equipos:asignar` envía nueva vigencia
- **THEN** el sistema ejecuta `useMutation`, invalida `['equipos']`, muestra toast con cantidad de filas afectadas

#### Scenario: Rango de fechas inválido
- **WHEN** el usuario ingresa `desde` posterior a `hasta`
- **THEN** Zod muestra error de validación "La fecha de inicio debe ser anterior a la fecha de fin"

### Requirement: Exportación de equipo a CSV

El sistema SHALL exponer un botón de exportación que descarga un archivo CSV consumiendo `GET /api/v1/equipos/export`. La descarga SHALL usar `responseType: 'blob'` y disparar la descarga del navegador.

#### Scenario: Exportación exitosa
- **WHEN** un usuario con `equipos:asignar` hace clic en "Exportar"
- **THEN** el sistema descarga un archivo CSV con los datos del equipo filtrado

#### Scenario: Error en exportación
- **WHEN** la request de exportación falla
- **THEN** el sistema muestra toast de error "Error al exportar"

### Requirement: CRUD de asignaciones individuales

El sistema SHALL permitir crear y eliminar asignaciones individuales dentro del contexto de un equipo (`POST /api/v1/asignaciones`, `DELETE /api/v1/asignaciones/{id}`).

#### Scenario: Crear asignación individual
- **WHEN** un usuario con `equipos:asignar` crea una asignación
- **THEN** el sistema ejecuta `useMutation`, invalida `['asignaciones']`, muestra toast de éxito

#### Scenario: Eliminar asignación (soft-delete)
- **WHEN** un usuario con `equipos:asignar` elimina una asignación
- **THEN** el sistema solicita confirmación, ejecuta `useMutation`, invalida `['asignaciones']`, muestra toast
