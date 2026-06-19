# Tasks — panel-auditoria-metricas (C-19)

> TDD estricto. Todo el change es **solo lectura** sobre `audit_log` (sin side effects → ideal para fixtures).
> Ciclo por comportamiento: RED (test que falla) → GREEN (mínimo) → TRIANGULAR (≥2 casos: happy + edge) → REFACTOR.
> Tests con DB efímera real (sin mockear DB). Recordar `asyncio_default_fixture_loop_scope = "session"` (Windows).
> Identidad/roles/tenant SIEMPRE desde la sesión. `tenant_id` obligatorio en cada query. Guard `auditoria:ver` fail-closed.

## 1. Preparación y fixtures

- [ ] 1.1 Confirmar que el permiso `auditoria:ver` existe en el catálogo RBAC (C-04) y está asignado a ADMIN, COORDINADOR y FINANZAS; si falta, agregar el seed de datos (no migración estructural).
- [ ] 1.2 Crear fixture de test que siembre `audit_log` con registros controlados: múltiples actores (ADMIN, COORDINADOR, otro docente), 2 tenants distintos, varias materias (incl. `materia_id` nulo), varios códigos de acción y fechas en días distintos. Reusar la fábrica de C-05 si existe.
- [ ] 1.3 Verificar baseline: correr los tests existentes de `audit_log_repository` y registrar "N passing" antes de extender el repo (Safety Net).

## 2. Repository — métodos de solo lectura (sin tocar inmutabilidad)

- [ ] 2.1 RED: test de aislamiento multi-tenant — `list_filtrado(tenant_id=X)` no devuelve registros del tenant Y. (spec audit-panel / audit-query)
- [ ] 2.2 GREEN+TRIANGULAR: implementar `list_filtrado` con `tenant_id` obligatorio + parámetros opcionales (`scope_actor_id`, `desde`, `hasta`, `materia_id`, `accion`, `limit`, `offset`); triangular con tenants A/B y con/sin registros.
- [ ] 2.3 RED→GREEN: test de scope `(propio)` — con `scope_actor_id=U`, solo devuelve registros cuyo `actor_id` es U; sin scope (None) devuelve todos los del tenant. Triangular: coordinador U vs. ADMIN global.
- [ ] 2.4 RED→GREEN: filtro por rango de fechas (cerrado e inclusive; abierto por un extremo). Triangular: dentro/fuera del rango.
- [ ] 2.5 RED→GREEN: filtro por `materia_id` (específica) y comportamiento sin filtro (incluye `materia_id` nulo). Triangular.
- [ ] 2.6 RED→GREEN: filtro por `accion` (código del catálogo) y código inexistente → lista vacía sin error. Triangular.
- [ ] 2.7 RED→GREEN: límite y orden — `limit` respetado, orden `fecha_hora` desc, recorte al tope máximo de seguridad cuando `limit > MAX`. Triangular: limit=50, limit por defecto, limit > MAX.
- [ ] 2.8 RED→GREEN: `aggregate_acciones_por_dia` — conteo por día calendario (SQL `date_trunc('day', ...)`), ordenado asc, dentro del scope. Triangular: 2 días con conteos distintos + día sin actividad.
- [ ] 2.9 RED→GREEN: `aggregate_comunicaciones_por_docente` — distribución de estados de comunicación por `actor_id` (mapeo código/`detalle`→estado según D3, confirmar catálogo). Triangular: docente con Enviado+Fallido; scope coordinador.
- [ ] 2.10 RED→GREEN: `aggregate_interacciones_docente_materia` — conteo por `(actor_id, materia_id, accion)`; agrupar `materia_id` nulo bajo clave "sin materia". Triangular: con materia + sin materia.
- [ ] 2.11 REFACTOR + invariante: verificar que el repo extendido NO expone mutación (`create`/`update`/`soft_delete` siguen lanzando `NotImplementedError`); test que lo asegura. Si el archivo supera ~500 LOC, extraer agregaciones a un repo de solo lectura (D2).

## 3. Schemas Pydantic v2 (extra='forbid')

- [ ] 3.1 RED→GREEN: `AuditoriaFiltros` (query) con `desde`, `hasta`, `materia_id`, `actor_id`, `accion`, `limit` (`Field(default=200, ge=1, le=MAX)`), `offset`; `model_config = ConfigDict(extra='forbid')`. Test: campo extra → ValidationError; `limit` por defecto = 200; `limit > MAX` rechazado o recortado según contrato.
- [ ] 3.2 RED→GREEN: DTOs de respuesta — `AccionesPorDiaResponse`, `ComunicacionesPorDocenteResponse`, `InteraccionesResponse`, `LogAccionItem`/`LogResponse` con los campos de RN-23 (`fecha_hora`, `actor_id`, `materia_id`, `accion`, `filas_afectadas`, `ip`, `user_agent`). `extra='forbid'`.

## 4. Service — orquestación y scope por rol

- [ ] 4.1 RED→GREEN: `AuditoriaService` calcula `scope_actor_id` desde los roles de la sesión — `None` para ADMIN/FINANZAS, `current_user.id` para COORDINADOR sin esos roles. Triangular: ADMIN → None; COORDINADOR → su id; FINANZAS → None.
- [ ] 4.2 RED→GREEN: el service combina filtros del DTO con el scope obligatorio (tenant de la sesión + `scope_actor_id`). Test clave de seguridad: COORDINADOR que filtra por `actor_id` ajeno → 0 registros (scope prevalece sobre el filtro).
- [ ] 4.3 RED→GREEN: métodos del service para cada vista del panel (acciones/día, comunicaciones/docente, interacciones docente×materia, log últimas acciones) y para el log completo F9.2, delegando al repository. Triangular por scope ADMIN vs COORDINADOR.
- [ ] 4.4 (Opcional, D5) Si se requiere el filtro "estado de actividad activo/inactivo" del usuario: cruzar con `UserRepository` por `tenant_id` en el service. Marcar como diferible si no es necesario.

## 5. Router /api/v1/auditoria/* (guard fail-closed)

- [ ] 5.1 RED→GREEN: guard `require_permission("auditoria:ver")` en todos los endpoints — sin permiso → 403; sin token → 401; con permiso → 200. Identidad/tenant desde `get_current_user` (nunca de la petición).
- [ ] 5.2 RED→GREEN: endpoints del panel F9.1 — `GET /panel/acciones-por-dia`, `GET /panel/comunicaciones-por-docente`, `GET /panel/interacciones`, `GET /panel/ultimas-acciones` (límite defecto 200). Aceptan `AuditoriaFiltros` por query. Sin lógica de negocio en el router (solo guard + delega al service).
- [ ] 5.3 RED→GREEN: endpoint del log completo F9.2 — `GET /log` paginado con filtros (fecha, materia, usuario, accion). Expone los campos de RN-23 vía DTO.
- [ ] 5.4 RED→GREEN: verificar que NO existe ningún endpoint de escritura sobre `/api/v1/auditoria/*` (solo lectura).
- [ ] 5.5 Registrar el router en la app `api/v1` y verificar el wiring (smoke test de ruteo).

## 6. Tests de integración E2E (scope + aislamiento)

- [ ] 6.1 E2E: ADMIN ve actividad global del tenant; COORDINADOR ve solo la suya; ambos con `auditoria:ver`.
- [ ] 6.2 E2E: aislamiento cross-tenant — usuario del tenant B no recibe ningún dato derivado de registros del tenant A en ninguna vista.
- [ ] 6.3 E2E: límite configurable end-to-end — sin límite → 200 máx; límite 50 → 50 máx; límite > MAX → recortado al tope.
- [ ] 6.4 E2E: filtros combinados (AND) respetan el scope — coordinador con materia + rango devuelve solo lo propio.

## 7. Cierre

- [ ] 7.1 Verificar cobertura: ≥80% líneas, ≥90% en la lógica de scope y agregaciones (reglas de negocio).
- [ ] 7.2 Confirmar archivos ≤500 LOC; revisar Open Questions del design (Q1 índice de agregación, Q2 mapeo de estados de comunicación, Q3 alcance de FINANZAS) y resolver/escalar las que apliquen.
- [ ] 7.3 Marcar `[x]` C-19 en `CHANGES.md` y dejar listo para `/opsx:archive`.
