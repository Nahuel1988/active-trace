## ADDED Requirements

### Requirement: Listado de facturas con filtros

El sistema SHALL renderizar el listado de facturas (permiso `facturas:gestionar`) consumiendo `GET /api/v1/facturas?periodo=&estado=` con la instancia Axios centralizada. La tabla SHALL mostrar `usuario`, `periodo`, `detalle`, `estado` (Pendiente|Abonada con badge) y fechas (`cargada_at`, `abonada_at`). SHALL ofrecer filtros por período y estado. Los DTOs SHALL estar tipados sin `any`, en `snake_case`.

#### Scenario: Listado filtrado por período y estado
- **WHEN** el usuario aplica `periodo=2026-06` y `estado=Pendiente`
- **THEN** la query se invalida y recarga, mostrando solo las facturas que cumplen ambos filtros

#### Scenario: Estado con badge visual
- **WHEN** se renderiza una factura
- **THEN** su estado se muestra como badge (Pendiente / Abonada) con color diferenciado

#### Scenario: Sin facturas muestra estado vacío
- **WHEN** el backend retorna lista vacía
- **THEN** la tabla muestra un estado informativo en lugar de filas vacías

### Requirement: Alta de factura solo para docentes facturantes

El sistema SHALL ofrecer un formulario de alta (React Hook Form + Zod) consumiendo `POST /api/v1/facturas`, con campos `usuario_id` (seleccionable SOLO entre docentes con `facturador=true`), `periodo` (AAAA-MM), `detalle`, `referencia_archivo` y `tamano_kb`. Un `422` del backend (usuario no facturador) SHALL mostrarse como error de formulario.

#### Scenario: Selector limitado a docentes facturantes
- **WHEN** el usuario abre el formulario de alta de factura
- **THEN** el selector de `usuario_id` ofrece únicamente docentes con `facturador=true`

#### Scenario: Alta exitosa invalida el listado
- **WHEN** el usuario completa el formulario con datos válidos y envía
- **THEN** la mutación llama `POST /api/v1/facturas`, y al responder 201 invalida la lista y cierra el modal

#### Scenario: Rechazo de docente no facturador
- **WHEN** el backend responde 422 por usuario no facturador
- **THEN** el formulario muestra el error inline y conserva los datos cargados

### Requirement: Edición de facturas pendientes

El sistema SHALL permitir editar una factura en estado Pendiente vía `PUT /api/v1/facturas/{id}`. Un `409` (factura ya abonada) SHALL mostrarse como error inline. La UI NO SHALL ofrecer edición de facturas abonadas.

#### Scenario: Editar factura pendiente
- **WHEN** el usuario edita el `detalle` de una factura Pendiente y guarda
- **THEN** la mutación llama `PUT /api/v1/facturas/{id}` y refresca la tabla al responder 200

#### Scenario: Edición de factura abonada bloqueada
- **WHEN** una factura está en estado Abonada
- **THEN** la UI no ofrece la acción de editar (o si se intenta, el 409 del backend se muestra como error inline)

### Requirement: Transición Pendiente → Abonada

El sistema SHALL ofrecer una acción "Abonar" para facturas Pendientes (`POST /api/v1/facturas/{id}/abonar`), con confirmación previa. La transición es unidireccional. Tras abonar, la UI SHALL invalidar el listado. Un `409` (ya abonada) SHALL mostrarse como mensaje, sin crash.

#### Scenario: Abonar factura exitosamente
- **WHEN** el usuario confirma abonar una factura Pendiente y el backend responde 200
- **THEN** la UI invalida la lista y la factura pasa a mostrarse como Abonada

#### Scenario: Confirmación previa al abono
- **WHEN** el usuario pulsa "Abonar"
- **THEN** se muestra un diálogo de confirmación antes de enviar la request

#### Scenario: Abonar factura ya abonada
- **WHEN** el backend responde 409 al abonar una factura ya Abonada
- **THEN** la UI muestra un mensaje indicando que ya estaba abonada, sin romper el listado

### Requirement: Fetch de facturas vía hooks de TanStack Query

El sistema SHALL realizar todo acceso de datos de facturas mediante hooks de TanStack Query con query keys keyed por los filtros (lista) y por `id` (detalle). Cada mutación SHALL invalidar el listado afectado.

#### Scenario: Abonar invalida el listado filtrado
- **WHEN** se abona una factura mientras hay filtros aplicados
- **THEN** la query del listado con esos filtros se invalida y recarga
