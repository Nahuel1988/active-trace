## ADDED Requirements

### Requirement: Contrato de API de la cola de comunicaciones
El sistema SHALL definir el contrato esperado del backend (`C-12 comunicaciones-cola-worker`) para preview, envío, aprobación y tracking de comunicaciones, y consumirlo con la instancia Axios centralizada. Los DTOs SHALL estar tipados sin `any`. Enviar requiere `comunicacion:enviar`; aprobar requiere `comunicacion:aprobar` (la UI recibe `403` como `ForbiddenError`).

El contrato esperado SHALL incluir:
- `POST /api/comunicaciones/preview` con `{ materia_id, cohorte_id, destinatarios: string[] }` → `200` con `{ items: Array<{ alumno_id: string; nombre: string; email: string; asunto: string; cuerpo: string }> }` (F3.1). No encola.
- `POST /api/comunicaciones/enviar` con `{ materia_id, cohorte_id, destinatarios: string[] }` → `202` con `{ lote_id: string; requiere_aprobacion: boolean }`. Encola en estado `pendiente` (RN-15).
- `GET /api/comunicaciones?materia_id=&cohorte_id=` → `200` con `{ items: Array<{ comunicacion_id: string; alumno_nombre: string; email: string; estado: 'pendiente' | 'enviando' | 'ok' | 'fallido' | 'cancelado' }> }`.
- `POST /api/comunicaciones/{lote_id}/aprobar` y `POST /api/comunicaciones/{lote_id}/cancelar` → `200`. También por destinatario: `POST /api/comunicaciones/{comunicacion_id}/aprobar` y `/cancelar`.

#### Scenario: Preview muestra asunto y cuerpo por destinatario
- **WHEN** el usuario solicita el preview de una comunicación a un conjunto de alumnos
- **THEN** se llama a `POST /api/comunicaciones/preview` y la UI muestra el asunto y cuerpo personalizado por cada destinatario, sin haber encolado nada

#### Scenario: Envío encola en estado pendiente
- **WHEN** el usuario confirma el envío desde el preview
- **THEN** se llama a `POST /api/comunicaciones/enviar`, los mensajes aparecen en la cola en estado `pendiente` y la UI indica si el lote `requiere_aprobacion`

### Requirement: Tracking de estado en tiempo real mediante polling
La pantalla de cola SHALL reflejar el estado de cada comunicación en tiempo real (Pendiente → Enviando → OK/Fallido/Cancelado, RN-15) mediante `useQuery` con `refetchInterval`. El polling SHALL estar activo mientras exista al menos un mensaje en estado no terminal (`pendiente` o `enviando`) y SHALL detenerse cuando todos los mensajes estén en estado terminal (`ok`, `fallido`, `cancelado`).

#### Scenario: Polling activo con mensajes pendientes
- **WHEN** la cola tiene al menos un mensaje en estado `pendiente` o `enviando`
- **THEN** la query de la cola se refresca periódicamente (`refetchInterval` activo) y la UI actualiza los estados sin recargar la página

#### Scenario: Polling se detiene en estados terminales
- **WHEN** todos los mensajes de la cola están en `ok`, `fallido` o `cancelado`
- **THEN** el `refetchInterval` se desactiva y no se realizan más requests periódicas

### Requirement: Aprobación y cancelación por lote y por destinatario
La pantalla SHALL ofrecer aprobar o cancelar el lote completo, y también aprobar o cancelar comunicaciones individuales (FL-04). Las acciones de aprobación SHALL ser visibles solo para usuarios con `comunicacion:aprobar`; ocultarse en caso contrario (fail-closed visual). Tras una acción, la cola SHALL invalidarse para reflejar el nuevo estado.

#### Scenario: Acciones de aprobación ocultas sin permiso
- **WHEN** el usuario no tiene `comunicacion:aprobar`
- **THEN** los controles de aprobar/cancelar lote y por destinatario no se renderizan

#### Scenario: Aprobar lote actualiza la cola
- **WHEN** un aprobador aprueba el lote
- **THEN** se llama a `POST /api/comunicaciones/{lote_id}/aprobar`, se invalida la query de la cola y los mensajes transicionan hacia `enviando`/`ok`

#### Scenario: Cancelar por destinatario
- **WHEN** un aprobador cancela una comunicación individual pendiente
- **THEN** se llama a `POST /api/comunicaciones/{comunicacion_id}/cancelar` y esa fila pasa a estado `cancelado`

### Requirement: Fetch de comunicaciones vía hooks de TanStack Query
Todo acceso de datos del feature comunicaciones SHALL realizarse mediante hooks de TanStack Query que envuelven `comunicacionesApi`. No SHALL usarse `useEffect` + fetch manual ni instancias Axios secundarias.

#### Scenario: Preview y envío como mutations
- **WHEN** el usuario dispara el preview o el envío
- **THEN** ambas operaciones se ejecutan como `useMutation`, exponiendo estados de carga y error a la UI

### Requirement: Tests del feature comunicaciones
El sistema SHALL incluir tests con Vitest + React Testing Library que mockean `api` y cubren: preview de comunicación, envío que encola en `pendiente`, transiciones de estado de la cola mediante polling (mock con respuestas sucesivas), ocultamiento de acciones de aprobación sin permiso, y aprobar/cancelar por lote y por destinatario.

#### Scenario: Transición de estado por polling testeada
- **WHEN** el test configura el mock de la cola para devolver `pendiente` y luego `ok` en refetches sucesivos
- **THEN** la UI refleja primero `pendiente` y luego `ok` tras el intervalo de refetch simulado

#### Scenario: Acciones de aprobación testeadas según permiso
- **WHEN** el test monta la cola con un usuario sin `comunicacion:aprobar`
- **THEN** los controles de aprobar/cancelar no están presentes en el DOM
