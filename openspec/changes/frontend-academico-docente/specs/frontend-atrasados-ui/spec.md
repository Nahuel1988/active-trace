## ADDED Requirements

### Requirement: Contrato de API de análisis de atrasados y reportes
El sistema SHALL definir el contrato esperado del backend (`C-11 analisis-atrasados-reportes`) para el dashboard docente, y consumirlo con la instancia Axios centralizada. Los DTOs SHALL estar tipados sin `any`. El acceso requiere el permiso `atrasados:ver` (la UI recibe `403` como `ForbiddenError` si no lo tiene).

El contrato esperado SHALL incluir, todos acotados por `?materia_id=&cohorte_id=`:
- `GET /api/atrasados` → `200` con `{ alumnos: Array<{ alumno_id: string; nombre: string; email: string; motivos: Array<'actividades_faltantes' | 'nota_bajo_umbral'>; actividades_faltantes: number; nota_promedio: number | null }> }` (RN-06).
- `GET /api/ranking` → `200` con `{ ranking: Array<{ alumno_id: string; nombre: string; aprobadas: number }> }`, solo alumnos con ≥1 actividad aprobada (RN-09).
- `GET /api/reportes/resumen` → `200` con métricas consolidadas por comisión.
- `GET /api/notas-finales` → `200` con la nota final agrupada por alumno.
- `GET /api/entregas-sin-corregir` → `200` con entregas finalizadas sin calificación, solo de actividades de escala textual (RN-07, RN-08).
- `GET /api/entregas-sin-corregir/export` → `200` con un archivo descargable (blob).

#### Scenario: Tabla de atrasados muestra el motivo
- **WHEN** se carga el dashboard con una comisión seleccionada
- **THEN** se llama a `GET /api/atrasados?materia_id=&cohorte_id=` y cada fila muestra el/los motivo(s) (actividades faltantes y/o nota bajo umbral)

#### Scenario: Ranking excluye alumnos sin aprobadas
- **WHEN** el backend devuelve el ranking
- **THEN** la tabla de ranking lista solo alumnos con al menos una actividad aprobada, ordenados por cantidad de aprobadas

#### Scenario: Estado vacío sin datos importados
- **WHEN** la comisión seleccionada aún no tiene calificaciones importadas o no se seleccionaron actividades
- **THEN** la UI muestra un estado informativo en lugar de tablas vacías o errores

### Requirement: Detección y export de entregas sin corregir
La pantalla SHALL permitir ver las posibles entregas sin corregir (cruce reporte de finalización × calificaciones, solo escala textual — RN-07, RN-08) y exportar ese listado a archivo descargable.

#### Scenario: Export dispara descarga de archivo
- **WHEN** el usuario pulsa exportar entregas sin corregir
- **THEN** se solicita `GET /api/entregas-sin-corregir/export` y el navegador descarga el archivo (blob) devuelto por el backend

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
El sistema SHALL incluir tests con Vitest + React Testing Library que mockean `api` y cubren: render de la tabla de atrasados con motivos, ranking que excluye alumnos sin aprobadas, estado vacío sin datos, y la selección de alumnos que habilita la acción de comunicar.

#### Scenario: Ranking sin aprobadas testeado
- **WHEN** el test monta el ranking con un mock donde un alumno tiene 0 aprobadas
- **THEN** ese alumno no aparece en la tabla renderizada
