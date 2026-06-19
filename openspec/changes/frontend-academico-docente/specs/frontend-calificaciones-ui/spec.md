## ADDED Requirements

### Requirement: Contrato de API de importación de calificaciones
El sistema SHALL definir el contrato esperado del backend (`C-10 calificaciones-y-umbral`) para importar calificaciones en dos fases con preview de actividades, y consumirlo con la instancia Axios centralizada. Los DTOs SHALL estar tipados sin `any`.

El contrato esperado SHALL incluir:
- `POST /api/materias/{materia_id}/calificaciones/preview` (multipart/form-data, campo `file`) → `200` con `{ import_id: string; actividades: Array<{ id: string; nombre: string; escala: 'numerica' | 'textual' }>; total_alumnos: number; errores: string[] }`. El backend detecta columnas numéricas `(Real)` (RN-01) y valores textuales de aprobado (RN-02); el frontend NO replica esa lógica.
- `POST /api/materias/{materia_id}/calificaciones/commit` con `{ import_id: string; actividades_seleccionadas: string[] }` → `200` con `{ total_procesados: number }`.

#### Scenario: Preview lista actividades detectadas con su escala
- **WHEN** el usuario sube el archivo de calificaciones exportado del LMS
- **THEN** se llama a `POST .../calificaciones/preview` y la UI muestra las actividades detectadas con su escala (numérica/textual) para que el usuario elija cuáles incluir

#### Scenario: Solo las actividades seleccionadas van al commit
- **WHEN** el usuario selecciona un subconjunto de actividades y confirma
- **THEN** `POST .../calificaciones/commit` recibe únicamente los ids de `actividades_seleccionadas` elegidos por el usuario

### Requirement: Configuración del umbral de aprobación por materia
La pantalla SHALL permitir configurar el umbral de aprobación en porcentaje por materia, con valor por defecto 60% (RN-03). El valor SHALL persistirse contra el contrato esperado y validarse en cliente con Zod (entero entre 0 y 100).

El contrato esperado SHALL incluir:
- `GET /api/materias/{materia_id}/umbral` → `200` con `{ umbral_porcentaje: number }` (default 60 si no fue configurado).
- `PUT /api/materias/{materia_id}/umbral` con `{ umbral_porcentaje: number }` → `200`.

#### Scenario: Umbral por defecto 60%
- **WHEN** la materia no tiene umbral configurado
- **THEN** el formulario muestra 60% como valor inicial

#### Scenario: Validación del umbral con Zod
- **WHEN** el usuario ingresa un umbral fuera del rango 0–100 o no entero
- **THEN** se muestra un error de validación inline y no se realiza la request `PUT .../umbral`

#### Scenario: Guardado del umbral invalida análisis
- **WHEN** el usuario guarda un nuevo umbral
- **THEN** se llama a `PUT .../umbral` y se invalidan las queries de atrasados/ranking de esa materia para que el análisis se recalcule

### Requirement: Fetch de calificaciones vía hooks de TanStack Query
Todo acceso de datos del feature calificaciones SHALL realizarse mediante hooks de TanStack Query que envuelven `calificacionesApi`. No SHALL usarse `useEffect` + fetch manual ni instancias Axios secundarias.

#### Scenario: Selección de actividades sin disparar lógica de detección en cliente
- **WHEN** el usuario interactúa con la lista de actividades del preview
- **THEN** la selección es estado local de UI sobre datos ya parseados por el backend; el cliente no interpreta encabezados `(Real)` ni escalas textuales

### Requirement: Tests del feature calificaciones
El sistema SHALL incluir tests con Vitest + React Testing Library que mockean `api` y cubren: render de la pantalla de importación, flujo preview→selección→commit con verificación de que solo las actividades elegidas se envían, y configuración/validación del umbral.

#### Scenario: Validación de umbral testeada
- **WHEN** el test ingresa un umbral inválido y envía el formulario
- **THEN** el mock de `PUT .../umbral` no recibe llamada y se muestra el error de validación
