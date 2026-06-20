## ADDED Requirements

### Requirement: Contrato de API de análisis de atrasados y reportes
El sistema SHALL definir el contrato esperado del backend (`C-11 analisis-atrasados-reportes`) para el dashboard docente, y consumirlo con la instancia Axios centralizada. Los DTOs SHALL estar tipados sin `any`. El acceso requiere el permiso `atrasados:ver` (la UI recibe `403` como `ForbiddenError` si no lo tiene).

El contrato esperado SHALL incluir, todos acotados por `?materia_id=&cohorte_id=` y con base `/api/v1/analisis/`:
- `GET /api/v1/analisis/atrasados` → `200` con `{ items: Array<{ entrada_padron_id: string; alumno_nombre: string; alumno_apellido: string; email: string | null; materia_id: string; materia_nombre: string; clasificacion: 'missing' | 'below_threshold'; actividad: string | null }>; total: number }` (RN-06).
- `GET /api/v1/analisis/ranking` → `200` con `{ items: Array<{ entrada_padron_id: string; alumno_nombre: string; alumno_apellido: string; actividades_aprobadas: number; total_actividades: number; porcentaje_aprobacion: number }> }`, solo alumnos con ≥1 actividad aprobada (RN-09).
- `GET /api/v1/analisis/reportes` → `200` con `{ total_alumnos: int; total_actividades: int; tasa_abrobacion_pct: float; alumnos_atrasados: int; alumnos_al_dia: int; sin_datos: bool }`.
- `GET /api/v1/analisis/notas-finales` → `200` con la nota final agrupada por alumno (`items: Array<NotaFinalAlumno>`).
- `GET /api/v1/analisis/entregas-pendientes` → `200` con `{ items: Array<{ alumno: string; actividad: string; fecha_submission: string; materia: string }>; todas_corregidas: bool }` (RN-07, RN-08).

#### Scenario: Tabla de atrasados muestra el motivo
- **WHEN** se carga el dashboard con una comisión seleccionada
- **THEN** se llama a `GET /api/v1/analisis/atrasados?materia_id=&cohorte_id=` y cada fila muestra la clasificación (`missing` o `below_threshold`)

#### Scenario: Ranking excluye alumnos sin aprobadas
- **WHEN** el backend devuelve el ranking
- **THEN** la tabla de ranking lista solo alumnos con al menos una actividad aprobada, ordenados por cantidad de aprobadas, mostrando nombre, apellido, actividades aprobadas, total y porcentaje

#### Scenario: Estado vacío sin datos importados
- **WHEN** la comisión seleccionada aún no tiene calificaciones importadas o no se seleccionaron actividades
- **THEN** la UI muestra un estado informativo en lugar de tablas vacías o errores

### Requirement: Detección y export de entregas sin corregir
La pantalla SHALL permitir ver las posibles entregas sin corregir (cruce reporte de finalización × calificaciones, solo escala textual — RN-07, RN-08) y exportar ese listado a archivo descargable.

#### Scenario: Tabla de entregas pendientes se carga desde el endpoint
- **WHEN** el usuario accede a la sección de entregas sin corregir
- **THEN** se solicita `GET /api/v1/analisis/entregas-pendientes?materia_id=&cohorte_id=` y se muestra la tabla con alumno, actividad, fecha y materia
- **AND** si `todas_corregidas` es `true`, se muestra un mensaje informativo

#### Scenario: Export dispara descarga de archivo
- **WHEN** el usuario pulsa exportar entregas sin corregir
- **THEN** se solicita la misma data con `format=csv` y el navegador descarga el archivo (blob) devuelto por el backend

### Requirement: Selección de alumnos para comunicación
La tabla de atrasados SHALL permitir seleccionar uno o más alumnos y pasar esa selección al flujo de comunicación (feature comunicaciones) sin que las features se importen entre sí: la transición se hace por navegación con la selección codificada (URL/estado de navegación), no por import directo.

#### Scenario: Selección de atrasados habilita la acción de comunicar
- **WHEN** el usuario marca uno o más alumnos atrasados
- **THEN** se habilita la acción "comunicar a seleccionados", visible solo si el usuario tiene `comunicacion:enviar`

### Requirement: Fetch de atrasados vía hooks de TanStack Query
Todo acceso de datos del feature atrasados SHALL realizarse mediante hooks de TanStack Query que envuelven `atrasadosApi`. Las queries SHALL estar keyed por `(materia_id, cohorte_id)` para que cambiar de comisión recargue el análisis correcto.

#### Scenario: Cambio de comisión recarga el análisis
- **WHEN** el usuario cambia la materia o cohorte activa
- **THEN** las queries de atrasados/ranking/reportes se invalidan y recargan para la nueva comisión

### Requirement: Tests del feature atrasados
El sistema SHALL incluir tests con Vitest + React Testing Library que mockean `api` y cubren: render de la tabla de atrasados con clasificación, ranking que excluye alumnos sin aprobadas, estado vacío sin datos, y la selección de alumnos que habilita la acción de comunicar.

#### Scenario: Ranking sin aprobadas testeado
- **WHEN** el test monta el ranking con un mock donde un alumno tiene 0 aprobadas
- **THEN** ese alumno no aparece en la tabla renderizada
