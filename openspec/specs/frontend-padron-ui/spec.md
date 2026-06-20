## ADDED Requirements

### Requirement: Contrato de API de importación de padrón
El sistema SHALL definir el contrato esperado del backend (`C-09 padron-ingesta-moodle`) para importar el padrón de alumnos en dos fases, y consumirlo con la instancia Axios centralizada. Los DTOs SHALL estar tipados sin `any`.

El contrato esperado SHALL incluir:
- `POST /api/materias/{materia_id}/padron/preview` (multipart/form-data, campo `file`) → `200` con `{ import_id: string; alumnos: Array<{ nombre: string; apellido: string; email: string; grupo?: string }>; total_detectados: number; errores: string[] }`. No persiste.
- `POST /api/materias/{materia_id}/padron/commit` con `{ import_id: string }` → `200` con `{ total_importados: number; total_reemplazados: number }`. Aplica upsert destructivo (RN-05).
- `403` cuando el usuario no tiene `calificaciones:importar` sobre la materia (el frontend lo recibe como `ForbiddenError`).

#### Scenario: Preview no persiste y devuelve alumnos detectados
- **WHEN** el usuario sube un archivo de padrón válido a la pantalla de importación
- **THEN** se llama a `POST /api/materias/{materia_id}/padron/preview` y se muestran los alumnos detectados sin que el padrón actual de la materia se haya modificado

#### Scenario: Errores de formato se muestran desde el preview
- **WHEN** el backend devuelve `errores` no vacíos en el preview
- **THEN** la UI muestra los errores y deshabilita la confirmación del commit

### Requirement: Confirmación explícita del upsert destructivo
La pantalla de importación de padrón SHALL exigir una confirmación explícita del usuario advirtiendo que el commit REEMPLAZA el padrón actual de la materia (RN-05) antes de llamar al endpoint de commit. La UI NUNCA SHALL ejecutar el commit sin esa confirmación.

#### Scenario: Commit requiere confirmación
- **WHEN** el usuario revisa el preview y pulsa importar
- **THEN** se le presenta una confirmación que advierte el reemplazo destructivo del padrón actual, y solo al confirmar se llama a `POST .../padron/commit`

#### Scenario: Resultado del commit se informa al usuario
- **WHEN** el commit responde con éxito
- **THEN** la UI muestra el total importado y el total reemplazado, e invalida la query del padrón de esa materia

### Requirement: Fetch de padrón vía hooks de TanStack Query
Todo acceso de datos del feature padron SHALL realizarse mediante hooks de TanStack Query (`useQuery`/`useMutation`) que envuelven funciones del servicio `padronApi`. No SHALL usarse `useEffect` + fetch manual.

#### Scenario: Importación modela como mutation
- **WHEN** el usuario dispara el preview o el commit
- **THEN** la operación se ejecuta mediante un `useMutation` de TanStack Query, con estados de carga y error expuestos a la UI

### Requirement: Tests del feature padron
El sistema SHALL incluir tests con Vitest + React Testing Library que mockean la instancia `api` y cubren: render de la pantalla de importación, flujo preview→confirmación→commit, despliegue de errores de formato, y que el commit no se dispara sin confirmación.

#### Scenario: Commit no se ejecuta sin confirmar
- **WHEN** el test simula subir un archivo y pulsar importar sin confirmar el diálogo destructivo
- **THEN** el mock de `POST .../padron/commit` no recibe ninguna llamada
