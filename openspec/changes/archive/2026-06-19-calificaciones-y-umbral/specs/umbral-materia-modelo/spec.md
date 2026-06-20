## ADDED Requirements

### Requirement: Modelo UmbralMateria por asignación docente

El sistema SHALL mantener un modelo `UmbralMateria` que defina el criterio de aprobación de una materia, scoped por asignación docente (FK a `Asignacion`). SHALL contener `umbral_pct` (entero, default 60) y `valores_aprobatorios` (lista de texto). SHALL tener FK a `Materia`. Cada docente tiene su propio umbral para la misma materia, sin afectar a otros docentes (RN-03, RN-04).

#### Scenario: Crear umbral con valores por defecto

- **WHEN** se crea un `UmbralMateria` para una `asignacion_id` sin especificar umbral
- **THEN** `umbral_pct` es 60 (default)
- **AND** `valores_aprobatorios` es la lista por defecto del tenant (`["Satisfactorio", "Supera lo esperado"]`)

#### Scenario: Configurar umbral personalizado

- **WHEN** un docente configura `umbral_pct = 75` para su asignación
- **THEN** el umbral se almacena con ese valor
- **AND** no afecta el umbral de otros docentes de la misma materia

#### Scenario: Umbral por asignación es independiente

- **WHEN** el docente A configura `umbral_pct = 70` y el docente B configura `umbral_pct = 50` para la misma materia
- **THEN** cada uno ve sus calificaciones evaluadas con su propio umbral
- **AND** cambiar el umbral de A no afecta las calificaciones de B

### Requirement: valores_aprobatorios como lista textual

`UmbralMateria.valores_aprobatorios` SHALL ser una lista de cadenas de texto que definen qué valores textuales cuentan como aprobado. SHALL almacenarse como JSONB en PostgreSQL. SHALL ser configurable por el docente.

#### Scenario: Valores aprobatorios textuales

- **WHEN** `valores_aprobatorios = ["Satisfactorio", "Supera lo esperado"]`
- **AND** una calificación tiene `nota_textual = "Satisfactorio"`
- **THEN** la calificación se considera aprobada

#### Scenario: Valor textual no aprobatorio

- **WHEN** `valores_aprobatorios = ["Satisfactorio", "Supera lo esperado"]`
- **AND** una calificación tiene `nota_textual = "No satisfactorio"`
- **THEN** la calificación NO se considera aprobada

### Requirement: Aislamiento multi-tenant de UmbralMateria

Toda operación sobre `UmbralMateria` SHALL estar scoped al `tenant_id` del JWT.

#### Scenario: Consulta de umbral scoped al tenant

- **WHEN** un usuario consulta su umbral de una materia
- **THEN** solo se devuelve el `UmbralMateria` cuyo `tenant_id` coincide con el del JWT

#### Scenario: Intento de modificar umbral de otro tenant

- **WHEN** se intenta modificar un `UmbralMateria` de otro tenant
- **THEN** el sistema responde `404 Not Found`
