## ADDED Requirements

### Requirement: Listado de carreras del tenant

El sistema SHALL mostrar un listado de carreras del tenant (`GET /api/v1/estructura/carreras`) con opción de crear nueva carrera (`POST /api/v1/estructura/carreras`).

#### Scenario: Coordinador ve carreras
- **WHEN** un usuario con `estructura:gestionar` navega a `/estructura/carreras`
- **THEN** el sistema ejecuta `useQuery` con key `['estructura', 'carreras']` y muestra tabla

#### Scenario: Crear carrera
- **WHEN** un usuario completa el formulario de nueva carrera
- **THEN** el sistema ejecuta `useMutation`, invalida `['estructura', 'carreras']`, muestra toast

#### Scenario: Sin carreras en el tenant
- **WHEN** no existen carreras
- **THEN** el sistema muestra "No hay carreras registradas"

### Requirement: Gestión de programas (upload + listado)

El sistema SHALL mostrar un listado de programas del tenant (`GET /api/v1/programas`) con opción de subir nuevo programa (PDF) y ver detalle de programa existente (`GET /api/v1/programas/{id}`). Consume `POST /api/v1/programas` con FormData (multipart).

#### Scenario: Listado de programas
- **WHEN** un usuario con `estructura:ver` navega a `/estructura/programas`
- **THEN** el sistema ejecuta `useQuery` con key `['estructura', 'programas']` y muestra tabla

#### Scenario: Subir nuevo programa
- **WHEN** un usuario con `estructura:gestionar` selecciona un archivo PDF y envía
- **THEN** el sistema ejecuta `useMutation` con FormData, invalida `['estructura', 'programas']`, muestra toast

#### Scenario: Validación de tipo de archivo
- **WHEN** el usuario selecciona un archivo que no es PDF
- **THEN** Zod muestra "El programa debe ser un archivo PDF"

### Requirement: CRUD de fechas académicas

El sistema SHALL mostrar un listado de fechas académicas (`GET /api/v1/fechas-academicas`) con opciones de crear (`POST /api/v1/fechas-academicas`) y editar (`PUT /api/v1/fechas-academicas/{id}`). Incluye una vista de calendario (`GET /api/v1/fechas-academicas/calendario`).

#### Scenario: Listado de fechas académicas
- **WHEN** un usuario con `estructura:ver` navega a `/estructura/fechas`
- **THEN** el sistema ejecuta `useQuery` con key `['estructura', 'fechas']` y muestra tabla

#### Scenario: Crear fecha académica
- **WHEN** un usuario con `estructura:gestionar` completa el formulario
- **THEN** el sistema ejecuta `useMutation`, invalida `['estructura', 'fechas']`, muestra toast

#### Scenario: Editar fecha académica
- **WHEN** un usuario con `estructura:gestionar` edita una fecha existente
- **THEN** el sistema ejecuta `useMutation`, invalida `['estructura', 'fechas']`, muestra toast

#### Scenario: Vista calendario
- **WHEN** un usuario con `estructura:ver` hace clic en "Vista Calendario"
- **THEN** el sistema ejecuta `useQuery` con key `['estructura', 'calendario']` y muestra eventos en formato lista mensual
