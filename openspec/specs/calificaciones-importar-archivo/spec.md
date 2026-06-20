## ADDED Requirements

### Requirement: Import de calificaciones en dos pasos (preview → confirm)

El sistema SHALL soportar la importación de calificaciones desde un archivo `.xlsx` o `.csv` exportado del LMS en dos pasos: (1) preview que parsea y detecta columnas, (2) confirm que ejecuta la importación con selección de actividades por el usuario. El flujo es stateless: el preview no guarda estado en el servidor.

#### Scenario: Preview de archivo válido

- **WHEN** un usuario sube un archivo `.csv` de calificaciones del LMS
- **THEN** el sistema devuelve un preview con: columnas detectadas clasificadas (numéricas, textuales, ignoradas), cantidad de filas, primeras 3 filas como muestra
- **AND** no se persiste ningún dato en DB

#### Scenario: Preview de archivo sin columnas reconocibles

- **WHEN** un usuario sube un archivo sin columnas que terminen en `(Real)` ni valores textuales reconocibles
- **THEN** el sistema responde `422` con detalle de columnas encontradas y sugerencia de formato esperado

#### Scenario: Confirmar importación con actividades seleccionadas

- **WHEN** un usuario envía `actividades_seleccionadas = ["TP1 (Real)", "TP2 (Real)"]` después del preview
- **THEN** el sistema importa solo las actividades seleccionadas
- **AND** crea una `Calificacion` por cada alumno × actividad seleccionada
- **AND** las calificaciones tienen `origen = Importado`
- **AND** `creado_por = usuario_id` del JWT

#### Scenario: Confirmar con actividad inexistente en preview

- **WHEN** un usuario envía `actividades_seleccionadas` que incluyen un nombre de columna no detectado en el preview
- **THEN** el sistema responde `422` indicando qué actividades no existen en el archivo original

#### Scenario: Importación excede límite máximo de filas

- **WHEN** la cantidad de calificaciones a importar (alumnos × actividades seleccionadas) supera `MAX_CALIFICACIONES_IMPORT` (5000)
- **THEN** el sistema responde `413` con instrucción de reducir la selección

### Requirement: Detección de columnas numéricas (RN-01)

El sistema SHALL detectar como columnas de nota numérica aquellas cuyo encabezado termina en `(Real)`. Cualquier otra columna no se procesa como nota numérica.

#### Scenario: Detección de columna numérica por cabecera (Real)

- **WHEN** el archivo contiene una columna con cabecera `TP1 (Real)`
- **THEN** el sistema clasifica esa columna como numérica
- **AND** los valores de esa columna se parsean como `nota_numerica`

#### Scenario: Columna sin sufijo (Real) no es numérica

- **WHEN** el archivo contiene una columna con cabecera `TP1` (sin `(Real)`)
- **THEN** el sistema NO clasifica esa columna como numérica
- **AND** intenta clasificarla como textual

### Requirement: Detección de columnas textuales (RN-02)

El sistema SHALL detectar como columnas de nota textual aquellas cuyos valores coinciden con el catálogo de escala textual configurado.

#### Scenario: Detección de columna textual

- **WHEN** el archivo contiene una columna con valores como "Satisfactorio", "No satisfactorio"
- **THEN** el sistema clasifica esa columna como textual
- **AND** los valores se almacenan como `nota_textual`

#### Scenario: Columna con valores mixtos

- **WHEN** una columna contiene una mezcla de valores numéricos y textuales
- **THEN** el sistema clasifica según la mayoría de valores detectados
- **AND** los valores que no coinciden con el tipo detectado se almacenan como nulos en el campo correspondiente

### Requirement: Aislamiento por usuario (RN-04)

Las calificaciones importadas SHALL estar scoped al `(usuario_id, materia_id)` del usuario autenticado. Una importación solo crea calificaciones con `creado_por = usuario_id` del JWT.

#### Scenario: Importación scoped al usuario autenticado

- **WHEN** el usuario A importa calificaciones para materia M
- **THEN** las calificaciones tienen `creado_por = usuario_id` de A
- **AND** el usuario B (misma materia) no ve estas calificaciones en su consulta por defecto

### Requirement: Auditoría de importación

Cada importación de calificaciones SHALL generar un registro de auditoría con código `CALIFICACIONES_IMPORTAR`, `filas_afectadas = cantidad de calificaciones creadas` y referencia a `materia_id`.

#### Scenario: Auditoría al confirmar importación

- **WHEN** se confirma una importación de 50 calificaciones
- **THEN** se crea un `AuditLog` con `accion = "CALIFICACIONES_IMPORTAR"`, `filas_afectadas = 50`, `materia_id = materia_id`, `actor_id = usuario_id` del JWT, `ip` y `user_agent` de la request

#### Scenario: Auditoría NO registra PII

- **WHEN** se genera el log de auditoría de una importación
- **THEN** el campo `detalle` NO contiene `nota_numerica`, `nota_textual` ni identificadores de alumnos
- **AND** solo contiene metadatos de la operación (actividades seleccionadas, cantidad de filas, materia_id)
