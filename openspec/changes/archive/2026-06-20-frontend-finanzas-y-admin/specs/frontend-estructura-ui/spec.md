## ADDED Requirements

### Requirement: ABM real de cohortes

El sistema SHALL reemplazar el stub de cohortes (que retornaba `[]` en C-23) por un ABM real (permiso `estructura:gestionar`) consumiendo los endpoints de cohortes del backend con la instancia Axios centralizada. El formulario (React Hook Form + Zod) SHALL capturar al menos `etiqueta`, `carrera_id` y las fechas de la cohorte. La tabla SHALL listar las cohortes del tenant. Los DTOs SHALL estar tipados sin `any`, en `snake_case`.

#### Scenario: Listado de cohortes reemplaza el estado vacío stub
- **WHEN** se abre la página de cohortes y el backend devuelve cohortes
- **THEN** la tabla las muestra (ya no el mensaje "funcionalidad en implementación")

#### Scenario: Crear cohorte exitosamente
- **WHEN** el usuario completa el formulario de cohorte con datos válidos y envía
- **THEN** la mutación crea la cohorte e invalida la lista al responder éxito

#### Scenario: Sin cohortes muestra estado vacío informativo
- **WHEN** el backend devuelve lista vacía
- **THEN** la UI muestra "No hay cohortes registradas" en lugar de tabla vacía

### Requirement: ABM real de materias con clave de Plus obligatoria

El sistema SHALL reemplazar el stub de materias por un ABM real (permiso `estructura:gestionar`). El formulario (React Hook Form + Zod) SHALL capturar `nombre` y `clave_plus` (PROG|BD|ARQ|MAT|MET) como campo OBLIGATORIO — no SHALL permitir crear ni guardar una materia sin clave asignada. La tabla SHALL mostrar la clave de Plus por materia.

#### Scenario: Crear materia con clave de Plus
- **WHEN** el usuario completa `nombre` y selecciona una `clave_plus` válida y envía
- **THEN** la mutación crea la materia e invalida la lista al responder éxito

#### Scenario: Materia sin clave de Plus es rechazada en validación
- **WHEN** el usuario intenta enviar el formulario sin seleccionar `clave_plus`
- **THEN** la validación Zod bloquea el submit y muestra el error "la clave de Plus es obligatoria"

#### Scenario: Tabla muestra la clave de Plus por materia
- **WHEN** se renderiza el listado de materias
- **THEN** cada fila muestra su clave de Plus (PROG/BD/ARQ/MAT/MET)

### Requirement: Fetch de cohortes y materias vía hooks de TanStack Query

El sistema SHALL realizar el acceso de datos de cohortes y materias mediante hooks de TanStack Query, integrados al patrón query key factory de la feature estructura. Cada mutación SHALL invalidar la lista correspondiente.

#### Scenario: Crear materia invalida solo la lista de materias
- **WHEN** se crea una materia
- **THEN** se invalida la query de materias (no la de cohortes ni carreras)
