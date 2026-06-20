## 1. Modelos SQLAlchemy

- [x] 1.1 Crear `backend/app/models/salario_base.py` con `SalarioBase(TenantScopedMixin, Base)`: columnas rol (String enum), monto (Decimal), desde (Date), hasta (Date nullable). Índice compuesto (tenant_id, rol, desde, hasta).
- [x] 1.2 Crear `backend/app/models/salario_plus.py` con `SalarioPlus(TenantScopedMixin, Base)`: columnas grupo (String), rol (String enum), descripcion (String), monto (Decimal), desde (Date), hasta (Date nullable). Índice compuesto (tenant_id, grupo, rol, desde, hasta).
- [x] 1.3 Crear `backend/app/models/liquidacion.py` con `Liquidacion(TenantScopedMixin, Base)`: cohorte_id (FK), periodo (String AAAA-MM), usuario_id (FK), rol (String), comisiones (ARRAY(String)), monto_base (Decimal), monto_plus (Decimal), total (Decimal), es_nexo (Boolean d=False), excluido_por_factura (Boolean d=False), estado (String: Abierta|Cerrada). Índice (tenant_id, cohorte_id, periodo).
- [x] 1.4 Crear `backend/app/models/factura.py` con `Factura(TenantScopedMixin, Base)`: usuario_id (FK), periodo (String), detalle (Text), referencia_archivo (String), tamano_kb (Decimal), estado (String: Pendiente|Abonada), cargada_at (DateTime server_default=now), abonada_at (DateTime nullable). Índice (tenant_id, periodo).
- [x] 1.5 Registrar los 4 modelos en `backend/app/models/__init__.py`.

## 2. Migración Alembic

- [x] 2.1 Generar migración `0NN_liquidaciones_y_honorarios` con `alembic revision --autogenerate -m "liquidaciones_y_honorarios"`.
- [x] 2.2 Verificar y ajustar manualmente la migración: tablas salario_base, salario_plus, liquidacion, factura con tipos correctos (ARRAY(String), Enum para estados/roles, Decimal).
- [x] 2.3 Agregar índices compuestos según diseño: (tenant_id, cohorte_id, periodo) en liquidacion; (tenant_id, periodo) en factura; (tenant_id, rol, desde, hasta) en salario_base; (tenant_id, grupo, rol, desde, hasta) en salario_plus.
- [x] 2.4 Ejecutar `alembic upgrade head` y verificar que las tablas se crearon correctamente.

## 3. Esquemas Pydantic (DTOs)

- [x] 3.1 Crear `backend/app/schemas/salario_base.py`: SalarioBaseCreate (rol, monto, desde, hasta? ), SalarioBaseUpdate (monto?, hasta?), SalarioBaseResponse (todos los campos). Config: `extra='forbid'`.
- [x] 3.2 Crear `backend/app/schemas/salario_plus.py`: SalarioPlusCreate (grupo, rol, descripcion, monto, desde, hasta?), SalarioPlusUpdate, SalarioPlusResponse. `extra='forbid'`.
- [x] 3.3 Crear `backend/app/schemas/liquidacion.py`: LiquidacionResponse (todos los campos), LiquidacionResumen (cantidad_generada, total_general, docentes_omitidos_sin_cbu), CalculoRequest (cohorte_id, periodo), LiquidacionSegmentadaResponse (segmentos: {general, nexo, facturantes}, kpis: {total_sin_factura, total_con_factura}). `extra='forbid'`.
- [x] 3.4 Crear `backend/app/schemas/factura.py`: FacturaCreate (usuario_id, periodo, detalle, referencia_archivo, tamano_kb), FacturaUpdate (detalle, referencia_archivo, tamano_kb), FacturaResponse. `extra='forbid'`.
- [x] 3.5 Registrar schemas en `backend/app/schemas/__init__.py` si existe.

## 4. Repositorios

- [x] 4.1 Crear `backend/app/repositories/salario_base_repository.py`: métodos get_vigente(tenant_id, rol, periodo) → SalarioBase | None, get_by_id, list (con filtros por rol, vigencia), create, update, soft_delete. Validar solapamiento de vigencia en create/update.
- [x] 4.2 Crear `backend/app/repositories/salario_plus_repository.py`: métodos get_vigente(tenant_id, grupo, rol, periodo) → SalarioPlus | None, get_vigentes_por_grupos(tenant_id, grupos: list, rol, periodo) → list[SalarioPlus], create, update, soft_delete. Validar solapamiento de vigencia para (grupo, rol).
- [x] 4.3 Crear `backend/app/repositories/liquidacion_repository.py`: métodos get_by_cohorte_periodo, get_by_id, get_cerradas (con filtros), create_or_update_batch (upsert para recalculo), cerrar (UPDATE estado SET 'Cerrada' WHERE id AND estado='Abierta' — retorna filas afectadas), exists_cerradas(cohorte_id, periodo) → bool.
- [x] 4.4 Crear `backend/app/repositories/factura_repository.py`: CRUD estándar con métodos list (filtros: periodo, estado, usuario_id), get_by_id, create, update (solo si Pendiente), abonar (UPDATE estado='Abonada', abonada_at=now WHERE id AND estado='Pendiente').
- [x] 4.5 Registrar repositorios en `backend/app/repositories/__init__.py`.

## 5. Services — Grilla Salarial

- [x] 5.1 Crear `backend/app/services/grilla_service.py`:
   - `configurar_salario_base(tenant_id, data)`: crear/actualizar con validación de solapamiento.
   - `listar_salarios_base(tenant_id, filtros)`: listar con paginación.
   - `obtener_base_vigente(tenant_id, rol, periodo)`: devuelve el SalarioBase vigente para ese rol en el mes.
   - `configurar_salario_plus(tenant_id, data)`: crear/actualizar con validación de solapamiento.
   - `listar_salarios_plus(tenant_id, filtros)`: listar con paginación.
   - `obtener_plus_vigentes(tenant_id, grupos: list[str], rol, periodo)`: devuelve lista de SalarioPlus vigentes.

- [x] 5.2 Tests para grilla_service: creación con solapamiento rechazado, selección de base vigente por período, base con hasta abierto vs cerrado, plus por (grupo, rol).

## 6. Services — Cálculo de Liquidación

- [x] 6.1 Crear `backend/app/services/liquidacion_service.py` con método `calcular(tenant_id, cohorte_id, periodo)`:
   - Validar que no existan liquidaciones Cerradas para (cohorte_id, periodo) → si existen, 409.
   - Obtener asignaciones activas del tenant para la cohorte en el período (inyectar AsignacionRepository de C-07).
   - Agrupar por usuario_id. Por cada docente:
        a. Obtener rol (desde asignación).
        b. Buscar SalarioBase vigente.
        c. Obtener materias de asignaciones → mapear a claves de Plus (vía config tenant o función externa).
        d. Obtener SalarioPlus vigentes para (grupos_distintos, rol).
        e. Si no tiene datos bancarios (usuario.cbu IS NULL) → omitir con warning.
        f. Si usuario.facturador == true → excluido_por_factura = true.
        g. Si rol == NEXO → es_nexo = true.
   - Crear/actualizar (upsert) Liquidacion en estado Abierta.
   - Retornar resumen.

- [x] 6.2 Tests para cálculo: cálculo exitoso genera liquidaciones, plus se aplica una vez por clave (PA-23), docentes sin CBU omitidos, facturantes marcados, NEXO marcado, recalcular reemplaza abiertas, recalcular rechazado si hay cerradas.

## 7. Services — Vista, Cierre e Historial

- [x] 7.1 Agregar a `liquidacion_service.py`:
   - `obtener_liquidaciones(tenant_id, cohorte_id, periodo, usuario_id?)`: retorna estructura segmentada (general, nexo, facturantes) con KPIs.
   - `obtener_historial(tenant_id, cohorte_id?, periodo?, usuario_id?)`: retorna liquidaciones Cerradas.
   - `cerrar(tenant_id, liquidacion_id)`: cambia estado a Cerrada, registra auditoría LIQUIDACION_CERRAR.
   - `exportar(tenant_id, cohorte_id, periodo)`: genera datos planos para exportación (formato a definir en C-24).

- [x] 7.2 Tests para vista y cierre: segmentación correcta, KPIs suman bien, cierre inmutable, re-auditado, historial solo cerradas.

## 8. Services — Facturas

- [x] 8.1 Crear `backend/app/services/factura_service.py`: CRUD delegado al repositorio + validación de que usuario_id tenga facturador=true. Método `abonar(tenant_id, factura_id)`: transición Pendiente→Abonada con registro de abonada_at.

- [x] 8.2 Tests para facturas: creación exitosa, rechazo si usuario no facturador, edición de pendiente permitida, edición de abonada rechazada, abonar exitoso, abonar duplicado rechazado.

## 9. Seed de Permisos RBAC

- [x] 9.1 Agregar al script de seed o migración los 6 permisos nuevos: `liquidaciones:configurar-salarios`, `liquidaciones:calcular`, `liquidaciones:ver`, `liquidaciones:cerrar`, `liquidaciones:exportar`, `facturas:gestionar`.
- [x] 9.2 Asignar permisos al rol FINANZAS (los 6) y a ADMIN solo `liquidaciones:ver` (según matriz de capacidades).

## 10. Routers FastAPI

- [x] 10.1 Crear `backend/app/api/v1/routers/grilla.py` con router `GrillaRouter(tag="Grilla Salarial")`:
   - GET /salarios-base → require_permission("grilla:operar")
   - POST /salarios-base → require_permission("grilla:operar")
   - PUT /salarios-base/{id} → require_permission("grilla:operar")
   - DELETE /salarios-base/{id} → require_permission("grilla:operar")
   - GET /salarios-plus → require_permission("grilla:operar")
   - POST /salarios-plus → require_permission("grilla:operar")
   - PUT /salarios-plus/{id} → require_permission("grilla:operar")
   - DELETE /salarios-plus/{id} → require_permission("grilla:operar")

- [x] 10.2 Crear `backend/app/api/v1/routers/liquidaciones.py` con router `LiquidacionRouter(tag="Liquidaciones")`:
   - POST /calcular → require_permission("liquidaciones:calcular")
   - GET / → require_permission("liquidaciones:ver") (filtros: cohorte_id, periodo, usuario_id)
   - GET /{id} → require_permission("liquidaciones:ver")
   - POST /{id}/cerrar → require_permission("liquidaciones:cerrar")
   - GET /historial → require_permission("liquidaciones:ver")
   - POST /exportar → require_permission("liquidaciones:exportar")

- [x] 10.3 Crear `backend/app/api/v1/routers/facturas.py` con router `FacturaRouter(tag="Facturas")`:
   - GET / → require_permission("facturas:gestionar")
   - POST / → require_permission("facturas:gestionar")
   - GET /{id} → require_permission("facturas:gestionar")
   - PUT /{id} → require_permission("facturas:gestionar")
   - POST /{id}/abonar → require_permission("facturas:gestionar")

- [x] 10.4 Registrar los 3 routers en el router principal de la API v1.

## 11. Auditoría

- [x] 11.1 Agregar código `LIQUIDACION_CERRAR` al catálogo de acciones de auditoría (C-05).
- [x] 11.2 Implementar registro de auditoría en `liquidacion_service.cerrar()`: llamar a `audit_log_repository.create` con action_code="LIQUIDACION_CERRAR", detalles incluyendo liquidacion_id, cohorte_id, periodo.

## 12. Tests de Integración

- [x] 12.1 Test E2E: flujo completo — crear SalarioBase → crear SalarioPlus → asignar docente → calcular liquidación → ver segmentos → cerrar → ver historial → verificar inmutabilidad.
- [x] 12.2 Test E2E: flujo de factura — crear factura para docente facturante → ver en segmento facturantes → abonar → verificar estado.
- [x] 12.3 Test de KPIs: verificar que total_sin_factura y total_con_factura sean correctos con datos mixtos.
- [x] 12.4 Test de seguridad: verificar 403 para roles sin permiso en cada endpoint, verificar 401 sin autenticación.
- [x] 12.5 Verificar cobertura ≥80% líneas y ≥90% reglas de negocio.
