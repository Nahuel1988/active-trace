## ADDED Requirements

### Requirement: Vista de liquidaciones del período segmentada con KPIs

El sistema SHALL renderizar la vista de liquidaciones acotada por `cohorte_id` (del `useComisionContext` compartido) y `periodo` (AAAA-MM, selector propio del feature persistido en query param `?periodo=`), consumiendo `GET /api/v1/liquidaciones?cohorte_id=&periodo=&usuario_id=` con la instancia Axios centralizada. La respuesta SHALL renderizarse en tres segmentos visualmente separados — `general`, `nexo`, `facturantes` — y una cabecera con dos KPIs: `total_sin_factura` y `total_con_factura`. Los DTOs SHALL estar tipados sin `any`, en `snake_case`.

#### Scenario: Tres segmentos renderizados por separado
- **WHEN** se carga la vista con una cohorte y período seleccionados y el backend devuelve `{ segmentos: { general, nexo, facturantes }, kpis }`
- **THEN** la UI muestra tres tablas separadas (general, NEXO, facturantes), cada una con sus docentes, rol y monto

#### Scenario: KPIs de cabecera visibles
- **WHEN** el backend devuelve `kpis.total_sin_factura` y `kpis.total_con_factura`
- **THEN** la cabecera muestra ambos KPIs con sus montos formateados

#### Scenario: NEXO se muestra separado pero el KPI lo incluye
- **WHEN** existen liquidaciones con `es_nexo=true`
- **THEN** aparecen en el segmento NEXO separado del general, y el KPI `total_sin_factura` incluye su monto (no se recalcula en el cliente, se toma del backend)

#### Scenario: Período sin liquidaciones muestra estado vacío
- **WHEN** el backend retorna segmentos vacíos y KPIs en cero
- **THEN** la UI muestra un estado informativo ("Sin liquidaciones para el período") en lugar de tablas vacías o errores

#### Scenario: Sin comisión o período seleccionado no dispara request
- **WHEN** no hay `cohorte_id` o `periodo` seleccionados
- **THEN** la página muestra un estado pidiendo seleccionar comisión y período, sin disparar una request sin scope

### Requirement: Cierre de liquidación con confirmación e inmutabilidad

El sistema SHALL permitir a un usuario con permiso `liquidaciones:cerrar` cerrar una liquidación vía `POST /api/v1/liquidaciones/{id}/cerrar`, mostrando un diálogo de confirmación previo. Tras el cierre exitoso, la UI SHALL invalidar la vista del período y el historial. Un 409 (liquidación ya cerrada) SHALL mostrarse como mensaje de error inline, no como crash.

#### Scenario: Cierre exitoso invalida la vista
- **WHEN** un usuario con `liquidaciones:cerrar` confirma el cierre de una liquidación Abierta y el backend responde 200
- **THEN** la UI invalida la query de la vista y del historial, y refleja el nuevo estado Cerrada

#### Scenario: Confirmación previa al cierre
- **WHEN** el usuario pulsa "Cerrar liquidación"
- **THEN** se muestra un diálogo de confirmación antes de enviar la request

#### Scenario: Cierre de liquidación ya cerrada
- **WHEN** el backend responde 409 al intentar cerrar una liquidación ya Cerrada
- **THEN** la UI muestra un mensaje de error inline indicando que la liquidación ya está cerrada, sin romper la vista

#### Scenario: Usuario sin permiso no ve la acción de cierre
- **WHEN** el usuario no tiene el permiso `liquidaciones:cerrar`
- **THEN** el botón de cierre no se renderiza (la vista queda en modo solo-lectura)

### Requirement: ADMIN ve la vista en modo solo-lectura

El sistema SHALL permitir a ADMIN (permiso `liquidaciones:ver`) consultar la vista de liquidaciones, pero NO SHALL renderizar las acciones de calcular, cerrar ni exportar. Estas acciones se condicionan por permiso.

#### Scenario: ADMIN consulta sin acciones de mutación
- **WHEN** un usuario ADMIN con `liquidaciones:ver` pero sin `liquidaciones:cerrar`/`liquidaciones:calcular` abre la vista
- **THEN** ve los segmentos y KPIs, pero no ve botones de calcular, cerrar ni exportar

### Requirement: Historial de liquidaciones cerradas con filtros

El sistema SHALL renderizar el historial consumiendo `GET /api/v1/liquidaciones/historial?cohorte_id=&periodo=&usuario_id=` con permiso `liquidaciones:ver`. SHALL ofrecer filtros independientes (cohorte, período, docente) y mostrar solo liquidaciones cerradas, ordenadas por período descendente. Las queries SHALL estar keyed por los filtros aplicados.

#### Scenario: Historial sin filtros lista todas las cerradas
- **WHEN** se abre el historial sin filtros
- **THEN** la tabla lista las liquidaciones cerradas ordenadas por período descendente

#### Scenario: Filtrar el historial por docente
- **WHEN** el usuario aplica el filtro de docente
- **THEN** la query se invalida y recarga, mostrando solo las cerradas de ese docente

#### Scenario: El historial no muestra liquidaciones abiertas
- **WHEN** existen liquidaciones Abiertas y Cerradas
- **THEN** el historial muestra únicamente las Cerradas (según devuelve el backend)

### Requirement: Acción de cálculo de período condicionada por permiso

El sistema SHALL renderizar una acción "Calcular período" solo si el usuario tiene el permiso correspondiente (FINANZAS). Al ejecutarse, SHALL mostrar estado de carga, deshabilitar reintentos hasta resolver, e invalidar la vista del período al completar.

#### Scenario: FINANZAS calcula y la vista se actualiza
- **WHEN** un usuario FINANZAS pulsa "Calcular período" y el backend responde 200
- **THEN** la UI muestra estado de carga durante la operación e invalida la query de la vista al terminar

#### Scenario: ADMIN no ve la acción de calcular
- **WHEN** un usuario ADMIN sin permiso de cálculo abre la vista
- **THEN** la acción "Calcular período" no se renderiza

### Requirement: Fetch de liquidaciones vía hooks de TanStack Query

El sistema SHALL realizar todo acceso de datos del feature finanzas mediante hooks de TanStack Query que envuelven los service modules, con query keys keyed por `(cohorte_id, periodo, usuario_id?)` para la vista y por los filtros para el historial.

#### Scenario: Cambio de período recarga la vista
- **WHEN** el usuario cambia el período seleccionado
- **THEN** la query de la vista se invalida y recarga para el nuevo `(cohorte_id, periodo)`
