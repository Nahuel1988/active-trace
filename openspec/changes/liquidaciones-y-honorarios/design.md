## Context

activia-trace necesita un módulo de liquidaciones y honorarios (Épica 10) que permita a FINANZAS configurar la grilla salarial, calcular liquidaciones por período, cerrarlas con inmutabilidad, gestionar facturas de monotributistas y exponer KPIs contables. El módulo se apoya en los modelos de `C-07` (Usuario con flag `facturador`, Asignacion con rol, materia, cohorte y vigencia). Las preguntas abiertas PA-22 (5 claves de Plus: PROG, BD, ARQ, MAT, MET) y PA-23 (Plus se aplica UNA vez por clave, sin tope) están resueltas.

**Stack**: Python 3.13, FastAPI async, SQLAlchemy 2.0 async, Pydantic v2, Alembic, PostgreSQL. Arquitectura Clean: Routes → Services → Repositories → Models.

**Stakeholders**: FINANZAS (opera liquidaciones y facturas), ADMIN (supervisa), docentes (impactados por los montos).

## Goals / Non-Goals

**Goals:**
- Modelar `SalarioBase`, `SalarioPlus`, `Liquidacion` y `Factura` con sus migraciones.
- Implementar motor de cálculo que produzca `Liquidacion` por (cohorte × período × usuario_id) respetando Base vigente al mes + Plus una vez por clave (PA-23).
- Exponer endpoints REST para grilla salarial (CRUD), liquidaciones (calcular, ver, cerrar, historial) y facturas (CRUD + transición de estado).
- Segmentar respuesta de liquidación en tres bloques: general, NEXO, facturantes (RN-36) con KPIs (RN-38).
- Cobertura ≥90% en reglas de negocio.

**Non-Goals:**
- Interfaz de frontend (corresponde a `C-24 frontend-finanzas-y-admin`).
- Integración con sistemas contables externos (pago automático, conciliación bancaria).
- Notificaciones a docentes sobre liquidaciones generadas o facturas vencidas.
- Historial de cambios en grilla salarial (cada cambio es append-only vía soft-delete, pero el tracking de quién cambió qué es responsabilidad de `C-05 audit-log`).
- Exportación a formatos específicos (PDF, XLSX) — se diseña el endpoint de exportación pero el formato concreto se define en `C-24`.

## Decisions

### D1 — Granularidad de Liquidacion: (cohorte × mes × usuario_id)
- **Opción A (elegida)**: un registro `Liquidacion` por docente, cohorte y período. Cada docente tiene su propia línea con rol, comisiones, base, plus y total.
- **Opción B**: un registro por (cohorte × mes) con todos los docentes embebidos en JSONB.
- **Por qué A**: consultas individuales simples (historial por docente, cierre individual si aplica), indexing eficiente por `usuario_id`, alineado con E19 del modelo de datos. Opción B dificulta consultas, auditoría y cierre individual.

### D2 — Cálculo on-demand (POST /calcular), no automático
- **Opción A (elegida)**: el usuario FINANZAS invoca explícitamente `POST /api/liquidaciones/calcular` seleccionando cohorte y período. El cálculo es síncrono (no worker) porque opera sobre datos ya cargados.
- **Opción B**: cálculo automático al abrir la vista del período.
- **Por qué A**: el usuario controla cuándo se calcula; evita sorpresas de performance; permite recalcular si cambió la grilla antes del cierre. Es consistente con FL-08 paso 2 ("cálculo automático" significa "automático tras la solicitud", no "automático al navegar").

### D3 — Cálculo de Plus: distinct (grupo, rol) sobre asignaciones activas
- Dado PA-22 (5 claves) y PA-23 (una aplicación por clave):
  1. Obtener todas las asignaciones activas del docente para la cohorte en el período.
  2. Agrupar por clave de materia (obtenida del mapeo materia → grupo, configurable por tenant).
  3. Para cada (grupo, rol) distinto, buscar `SalarioPlus` vigente en el período.
  4. Sumar los montos de cada plus aplicable.
- **No** se multiplica por N comisiones de la misma clave (PA-23 explícito: una sola vez por clave).

### D4 — Versionado de grilla vía desde/hasta
- `SalarioBase` y `SalarioPlus` usan `desde` (obligatorio) y `hasta` (nullable = abierto). Para calcular el valor vigente en un mes:
  ```sql
  WHERE desde <= :periodo_fin
    AND (hasta IS NULL OR hasta >= :periodo_inicio)
  ```
- Se valida que no haya solapamiento de vigencia para el mismo (rol) o (grupo, rol). Esto se implementa en el service de grilla al crear/actualizar.

### D5 — Cierre inmutable con flag + check
- `Liquidacion.estado = Cerrada` impide cualquier modificación.
- El service de liquidación valida en cada operación de escritura: `if liquidacion.estado == Cerrada: raise HTTPException(409, "Liquidación cerrada")`.
- El cierre se audita con código `LIQUIDACION_CERRAR` (C-05 audit-log).

### D6 — Segmentación de la respuesta de liquidación
- La respuesta de `GET /api/liquidaciones?cohorte_id=X&periodo=YYYY-MM` devuelve:
  ```json
  {
    "segmentos": {
      "general": [ ... Liquidacion con rol != NEXO y excluido_por_factura=false ... ],
      "nexo": [ ... Liquidacion con rol == NEXO ... ],
      "facturantes": [ ... Liquidacion con excluido_por_factura=true ... ]
    },
    "kpis": {
      "total_sin_factura": "suma total de segmentos general + nexo",
      "total_con_factura": "suma de montos de facturantes (facturas pendientes + abonadas del período)"
    }
  }
  ```

### D7 — Factura: Pendiente → Abonada, no borrado
- `Factura` tiene dos estados: Pendiente (default) y Abonada. Transición solo forward.
- No se eliminan facturas (soft delete). Se permite corregir el detalle solo si está Pendiente.
- El archivo adjunto se referencia por nombre (`referencia_archivo`); el almacenamiento físico es responsabilidad de infraestructura (volumen compartido / S3).

### D8 — Permisos nuevos en formato `modulo:accion`
Los 6 permisos se agregan al catálogo RBAC existente (C-04):
| Permiso | Roles |
|---------|-------|
| `liquidaciones:configurar-salarios` | FINANZAS |
| `liquidaciones:calcular` | FINANZAS |
| `liquidaciones:ver` | FINANZAS, ADMIN |
| `liquidaciones:cerrar` | FINANZAS |
| `liquidaciones:exportar` | FINANZAS |
| `facturas:gestionar` | FINANZAS |

### D9 — Endpoints REST
```
POST   /api/v1/liquidaciones/calcular          → liquidaciones:calcular
GET    /api/v1/liquidaciones                    → liquidaciones:ver (con filtros cohorte_id, periodo, usuario_id)
GET    /api/v1/liquidaciones/{id}               → liquidaciones:ver
POST   /api/v1/liquidaciones/{id}/cerrar        → liquidaciones:cerrar
GET    /api/v1/liquidaciones/historial           → liquidaciones:ver (cerradas, filtros)
POST   /api/v1/liquidaciones/exportar           → liquidaciones:exportar

GET    /api/v1/grilla/salarios-base             → liquidaciones:configurar-salarios
POST   /api/v1/grilla/salarios-base             → liquidaciones:configurar-salarios
PUT    /api/v1/grilla/salarios-base/{id}        → liquidaciones:configurar-salarios
DELETE /api/v1/grilla/salarios-base/{id}        → liquidaciones:configurar-salarios
GET    /api/v1/grilla/salarios-plus             → liquidaciones:configurar-salarios
POST   /api/v1/grilla/salarios-plus             → liquidaciones:configurar-salarios
PUT    /api/v1/grilla/salarios-plus/{id}        → liquidaciones:configurar-salarios
DELETE /api/v1/grilla/salarios-plus/{id}        → liquidaciones:configurar-salarios

GET    /api/v1/facturas                         → facturas:gestionar
POST   /api/v1/facturas                         → facturas:gestionar
GET    /api/v1/facturas/{id}                    → facturas:gestionar
PUT    /api/v1/facturas/{id}                    → facturas:gestionar (solo si Pendiente)
POST   /api/v1/facturas/{id}/abonar             → facturas:gestionar (Pendiente → Abonada)
```

### D10 — Flujo de cálculo del motor
1. Validar que no existan liquidaciones Cerradas para (cohorte_id, período).
2. Obtener todas las asignaciones activas del tenant para la cohorte en el período (C-07).
3. Agrupar por `usuario_id`. Para cada docente:
   - Determinar rol desde asignación.
   - Obtener `SalarioBase` vigente para (rol, período).
   - Obtener materias de sus asignaciones → mapear a claves de Plus (configuración por tenant).
   - Obtener `SalarioPlus` vigente para cada (grupo, rol) distinto.
   - Si el docente no tiene datos bancarios (CBU, alias, banco) → RN-26: no se liquida (se omite con warning).
   - Si `usuario.facturador == true` → `excluido_por_factura = true`, se calcula igual pero marcado.
4. Crear o actualizar (upsert) registros `Liquidacion` en estado `Abierta`.
5. Retornar resumen del cálculo.

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|-----------|
| **R1 — Rendimiento del cálculo con muchos docentes**: el cálculo es O(N) sobre asignaciones activas. Para un tenant grande (>500 docentes) puede tomar segundos. | El cálculo es on-demand (síncrono pero el usuario lo invoca explícitamente). Si escala, migrar a worker async. |
| **R2 — Data race en cierre concurrente**: dos usuarios FINANZAS intentan cerrar la misma liquidación. | Optimistic locking vía `updated_at` o version column en `Liquidacion`. Alternativa: la validación de estado se hace en DB (`UPDATE ... WHERE estado='Abierta'` y verificar filas afectadas). |
| **R3 — Solapamiento de vigencia en grilla**: entrada maliciosa o error humano crea dos `SalarioBase` vigentes para el mismo rol. | Validación en service al crear/actualizar: no permitir solapamiento. Query de chequeo antes de insert. |
| **R4 — Cambio de grilla después de cálculo abierto**: si FINANZAS modifica la grilla mientras hay una liquidación `Abierta`, el cálculo queda desactualizado. | Se documenta como comportamiento esperado: el usuario debe recalcular explícitamente antes de cerrar. El GET muestra la fecha del último cálculo. |
| **R5 — Archivos adjuntos de facturas**: `referencia_archivo` asume almacenamiento externo; no hay control de tamaño ni tipo. | Se registra `tamano_kb` como metadata. La validación de tipo/tamaño se delega al frontend o al middleware de archivos (fuera de scope). |
| **R6 — Claves de Plus desactualizadas**: si ADMIN no configura el mapeo materia→grupo, el Plus será cero. | Se documenta como requisito operativo. El cálculo omite claves sin mapping (no falla). |

## Migration Plan

1. **Crear migración Alembic** `0NN_liquidaciones_y_honorarios` con:
   - `salario_base`: id, tenant_id, rol (enum), monto (Decimal), desde (Date), hasta (Date nullable).
   - `salario_plus`: id, tenant_id, grupo (String), rol (enum), descripcion (String), monto (Decimal), desde (Date), hasta (Date nullable).
   - `liquidacion`: id, tenant_id, cohorte_id (FK), periodo (String), usuario_id (FK), rol (enum), comisiones (ARRAY(String)), monto_base (Decimal), monto_plus (Decimal), total (Decimal), es_nexo (Boolean), excluido_por_factura (Boolean), estado (enum: Abierta|Cerrada).
   - `factura`: id, tenant_id, usuario_id (FK), periodo (String), detalle (Text), referencia_archivo (String), tamano_kb (Decimal), estado (enum: Pendiente|Abonada), cargada_at (DateTime), abonada_at (DateTime nullable).
   - Índices: (tenant_id, cohorte_id, periodo) en liquidacion; (tenant_id, periodo) en factura; (tenant_id, rol, desde, hasta) en salario_base y salario_plus.
2. **Seed de permisos**: agregar los 6 permisos al catálogo RBAC.
3. **Implementar en orden**: modelos → migración → repositorios → services → routers → tests.
4. **Rollback**: `alembic downgrade -1` elimina las 4 tablas.
5. **Datos preexistentes**: no hay — es funcionalidad nueva.

## Open Questions

- **OQ-1**: ¿El mapeo materia → grupo/clave de Plus se almacena como configuración del tenant (JSONB en tabla `tenant_config`) o como tabla separada `materia_clave_plus`? Pendiente de definir con el equipo pero no bloquea el diseño del cálculo — el service acepta un dict o función de mapping.
- **OQ-2**: Formato de exportación (`liquidaciones:exportar`). Se diseña el endpoint pero el formato concreto (CSV, JSON, XLSX) se define en `C-24 frontend-finanzas-y-admin`.
