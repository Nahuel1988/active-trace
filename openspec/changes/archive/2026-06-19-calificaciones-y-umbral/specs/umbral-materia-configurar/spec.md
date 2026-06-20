## ADDED Requirements

### Requirement: Leer umbral de aprobación por asignación

El sistema SHALL exponer un endpoint para que un docente lea su `UmbralMateria` configurado para una materia. Si no existe configuración, SHALL devolver los valores por defecto (umbral_pct = 60, valores_aprobatorios = catálogo del tenant) sin crearlos en DB.

#### Scenario: Leer umbral existente

- **WHEN** un docente consulta su umbral para materia M
- **AND** existe `UmbralMateria` para su `asignacion_id`
- **THEN** el sistema devuelve `umbral_pct` y `valores_aprobatorios` configurados

#### Scenario: Leer umbral sin configuración previa

- **WHEN** un docente consulta su umbral para materia M
- **AND** no existe `UmbralMateria` para su `asignacion_id`
- **THEN** el sistema devuelve los valores por defecto (`umbral_pct = 60`, `valores_aprobatorios` del catálogo)
- **AND** no crea ningún registro en DB

### Requirement: Configurar umbral de aprobación (F2.1, RN-03)

El sistema SHALL permitir que un docente configure su umbral de aprobación por materia. SHALL aceptar `umbral_pct` (entero 0-100) y `valores_aprobatorios` (lista de texto opcional). SHALL crear o actualizar el `UmbralMateria` para la `asignacion_id` del usuario autenticado. SHALL auditar la operación con código `CALIFICACIONES_IMPORTAR`.

#### Scenario: Configurar umbral numérico

- **WHEN** un docente configura `umbral_pct = 75` para su asignación
- **THEN** el sistema crea o actualiza `UmbralMateria` con `umbral_pct = 75`
- **AND** `valores_aprobatorios` mantiene los valores por defecto si no se especifican

#### Scenario: Configurar valores aprobatorios textuales

- **WHEN** un docente configura `valores_aprobatorios = ["Aprobado", "Muy bueno"]` para su asignación
- **THEN** el sistema crea o actualiza `UmbralMateria` con esos valores
- **AND** `umbral_pct` mantiene el valor existente o default si no se especifica

#### Scenario: Configurar umbral fuera de rango

- **WHEN** un docente intenta configurar `umbral_pct = 150`
- **THEN** el sistema responde `422` con error de validación (rango permitido: 0-100)

#### Scenario: Configuración de umbral solo para asignaciones vigentes

- **WHEN** un docente intenta configurar umbral para una materia donde su asignación está vencida
- **THEN** el sistema responde `403 Forbidden`

### Requirement: Cálculo de aprobado usa el umbral configurado

El sistema SHALL computar `aprobado` en read-time usando el `UmbralMateria` del docente autenticado. Para notas numéricas: `nota_numerica >= umbral_pct`. Para notas textuales: `nota_textual in valores_aprobatorios`. Si no existe umbral configurado, usa los valores por defecto.

#### Scenario: Nota numérica aprueba con umbral 60

- **WHEN** `umbral_pct = 60`, `nota_numerica = 65`
- **THEN** `aprobado = true`

#### Scenario: Nota numérica no aprueba con umbral 60

- **WHEN** `umbral_pct = 60`, `nota_numerica = 55`
- **THEN** `aprobado = false`

#### Scenario: Nota textual aprueba según valores aprobatorios

- **WHEN** `valores_aprobatorios = ["Satisfactorio"]`, `nota_textual = "Satisfactorio"`
- **THEN** `aprobado = true`

#### Scenario: Nota textual no aprueba según valores aprobatorios

- **WHEN** `valores_aprobatorios = ["Satisfactorio"]`, `nota_textual = "No satisfactorio"`
- **THEN** `aprobado = false`

#### Scenario: Cambio de umbral afecta retrospectivamente

- **WHEN** un docente cambia `umbral_pct` de 60 a 40
- **AND** existía una calificación con `nota_numerica = 50` que antes no aprobaba
- **THEN** al consultar nuevamente, esa calificación aparece como `aprobado = true`

### Requirement: Auditoría de configuración de umbral

Toda configuración de umbral SHALL generar un registro de auditoría con código `CALIFICACIONES_IMPORTAR`.

#### Scenario: Auditoría al configurar umbral

- **WHEN** un docente configura el umbral para su asignación
- **THEN** se crea un `AuditLog` con `accion = "CALIFICACIONES_IMPORTAR"`, detalle incluyendo `umbral_pct` y `valores_aprobatorios` configurados
