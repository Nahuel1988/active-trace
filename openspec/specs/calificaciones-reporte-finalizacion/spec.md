## ADDED Requirements

### Requirement: Importar reporte de finalización del LMS

El sistema SHALL aceptar un archivo `.xlsx` o `.csv` con el reporte de finalización de actividades exportado desde el LMS. SHALL parsear el archivo y cruzar los datos contra las calificaciones importadas existentes para detectar entregas finalizadas por el alumno que aún no tienen calificación registrada (RN-07). Esta operación NO crea registros en la base de datos — solo genera una vista derivada.

#### Scenario: Reporte de finalización con entregas sin calificar

- **WHEN** un usuario sube un reporte de finalización
- **AND** existen entradas en el reporte marcadas como "finalizadas" para alumno × actividad
- **AND** no existe `Calificacion` correspondiente para ese `(entrada_padron_id, actividad)`
- **THEN** el sistema incluye esa entrega en el listado de "posibles entregas sin corregir"
- **AND** muestra: nombre del alumno, actividad, fecha de finalización

#### Scenario: Todas las entregas ya están calificadas

- **WHEN** un usuario sube un reporte de finalización
- **AND** todas las actividades finalizadas ya tienen `Calificacion` registrada
- **THEN** el sistema devuelve un listado vacío de "posibles entregas sin corregir"

### Requirement: Filtro solo actividades textuales (RN-08)

El reporte de entregas sin corregir SHALL incluir únicamente actividades de escala textual (cualitativa). Las actividades numéricas NO se incluyen porque en esa escala la ausencia de nota equivale a "no entregado", no a "pendiente de corrección" (RN-08).

#### Scenario: Actividad textual sin calificar se reporta

- **WHEN** la actividad `TP_Cualitativo` es de tipo textual
- **AND** el alumno la finalizó pero no tiene calificación
- **THEN** aparece en el reporte de entregas sin corregir

#### Scenario: Actividad numérica sin calificar NO se reporta

- **WHEN** la actividad `TP_1 (Real)` es de tipo numérico
- **AND** el alumno la finalizó pero no tiene calificación
- **THEN** NO aparece en el reporte de entregas sin corregir

### Requirement: Sin persistencia en DB

El reporte de entregas sin corregir SHALL ser una vista derivada calculada en memoria al momento de la consulta. NO se crean registros en `Calificacion` ni en ninguna otra tabla como resultado de este reporte.

#### Scenario: Reporte no modifica datos existentes

- **WHEN** se genera el reporte de finalización
- **THEN** no se insertan, actualizan ni eliminan registros en ninguna tabla del sistema

### Requirement: Aislamiento por usuario

El cruce del reporte de finalización SHALL considerar solo las calificaciones del usuario autenticado (`creado_por = usuario_id` del JWT). No cruza contra calificaciones de otros docentes.

#### Scenario: Cruce scoped al usuario autenticado

- **WHEN** el usuario A genera el reporte de finalización para materia M
- **THEN** el cruce solo considera calificaciones donde `creado_por = usuario_id` de A
- **AND** si el usuario B tiene calificaciones del mismo alumno, no afectan el reporte de A
