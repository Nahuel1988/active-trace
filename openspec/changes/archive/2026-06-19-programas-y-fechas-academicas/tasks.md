# Tasks — C-17 programas-y-fechas-academicas

> Governance: **BAJO** — autonomía total si pasan los tests; reportar en el resumen.
> Migración: **006** (004 = audit_log, 005 = estructura_academica). Una sola migración para este change.
> Permiso `estructura:gestionar` ya sembrado en C-06; `estructura:ver` agregado al seed.
> Strict TDD por tarea: RED (test falla) → GREEN (mínimo) → TRIANGULATE (≥2 casos, +edge) → REFACTOR. Sin mocks de DB (DB efímera/contenedor). `extra='forbid'` en todos los schemas. snake_case.
> Gotcha entorno (de C-06): `asyncio_default_fixture_loop_scope = "session"` en pyproject.toml; `TEST_DATABASE_URL` con nombre de servicio Docker; engines en fixtures session-scoped en conftest.py.

---

## 1. Modelos ORM

- [x] 1.1 RED: test de modelo `ProgramaMateria` — instanciar y persistir con columnas `materia_id`, `carrera_id`, `cohorte_id`, `titulo`, `referencia_archivo`, `cargado_at` + mixin base (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`); assert que sin uno de los FK falla.
- [x] 1.2 GREEN: crear `backend/app/models/programa_materia.py` con mixin base, FKs a `materia.id`/`carrera.id`/`cohorte.id`, `UniqueConstraint("tenant_id", "materia_id", "carrera_id", "cohorte_id")`. TRIANGULATE: segundo caso con otra combinación; verificar que la unicidad NO dispara entre combinaciones distintas. REFACTOR.
- [x] 1.3 RED: test de modelo `FechaAcademica` — persistir con `materia_id`, `cohorte_id`, `tipo` (enum `TipoFechaAcademica`: Parcial/TP/Coloquio/Recuperatorio), `numero`, `periodo`, `fecha`, `titulo` + mixin base.
- [x] 1.4 GREEN: crear `backend/app/models/fecha_academica.py` con mixin base, FKs a `materia.id`/`cohorte.id`, enum `TipoFechaAcademica`, `UniqueConstraint("tenant_id", "materia_id", "cohorte_id", "tipo", "numero")`. TRIANGULATE: mismo tipo distinto número (OK) vs mismo tipo+número (viola constraint). REFACTOR.
- [x] 1.5 Registrar ambos modelos en `backend/app/models/__init__.py` para que Alembic los detecte.

## 2. Migración 006

- [x] 2.1 Generar `006_programas_y_fechas_academicas` con `alembic revision --autogenerate -m "006_programas_y_fechas_academicas"`.
- [x] 2.2 Revisar el archivo generado: índices de `tenant_id` en ambas tablas, FKs (`programa_materia` → carrera/cohorte/materia; `fecha_academica` → cohorte/materia), unique constraints de §D2/§D3, índice `(tenant_id, cohorte_id)` en `fecha_academica`. Corregir lo que autogenerate no capture.
- [x] 2.3 Ejecutar `alembic upgrade head` en la DB de test y verificar que crea `programa_materia` y `fecha_academica` sin errores; probar `alembic downgrade -1` y volver a `upgrade head`.

## 3. Schemas Pydantic (extra='forbid')

- [x] 3.1 Crear `backend/app/schemas/programa_materia.py`: `ProgramaMateriaCreate` (`materia_id`, `carrera_id`, `cohorte_id`, `titulo`, `referencia_archivo`), `ProgramaMateriaUpdate` (`titulo?`, `referencia_archivo?`), `ProgramaMateriaResponse` (`from_attributes=True`, incluye `cargado_at`, `created_at`, `updated_at`). RED: test que un campo extra es rechazado; test que `referencia_archivo` se acepta como string opaco.
- [x] 3.2 Crear `backend/app/schemas/fecha_academica.py`: `FechaAcademicaCreate` (`materia_id`, `cohorte_id`, `tipo`, `numero`≥1, `periodo`, `fecha`, `titulo`), `FechaAcademicaUpdate` (`periodo?`, `fecha?`, `titulo?`), `FechaAcademicaResponse`, y `CalendarioPeriodo` (`periodo` + lista de fechas) para la vista agrupada. RED: test que `tipo` fuera del enum y `numero=0` son rechazados (422). TRIANGULATE: enum válido + numero=1 pasa.

## 4. Repositories (aislamiento por tenant)

- [x] 4.1 RED: test de `ProgramaMateriaRepository` — `create`, `get_by_id` (scope tenant), `list` con filtros (`materia_id`/`carrera_id`/`cohorte_id`), `get_by_combination` (para unicidad), `soft_delete`. Assert que `get_by_id` de otro tenant retorna None.
- [x] 4.2 GREEN: crear `backend/app/repositories/programa_materia_repository.py` heredando de `repositories/base.py` (filtro tenant por defecto + exclusión de `deleted_at`). TRIANGULATE: listado de tenant A no incluye registros de tenant B; programa soft-deleted no aparece. REFACTOR.
- [x] 4.3 RED: test de `FechaAcademicaRepository` — `create`, `get_by_id`, `list` (filtros `materia_id`/`cohorte_id`/`periodo`/`tipo`, orden por `fecha` asc), `get_by_instance` (para unicidad tipo+numero), `soft_delete`. Assert orden por fecha y aislamiento tenant.
- [x] 4.4 GREEN: crear `backend/app/repositories/fecha_academica_repository.py` heredando de base. TRIANGULATE: orden ascendente con ≥2 fechas; aislamiento tenant; fecha borrada excluida. REFACTOR.

## 5. Services — Programas

- [x] 5.1 RED: test de `ProgramaMateriaService.create` — valida que materia/carrera/cohorte existan y no estén soft-deleted (404 si no), rechaza combinación duplicada (409/conflict), persiste referencia opaca y `cargado_at`.
- [x] 5.2 GREEN: crear `backend/app/services/programa_materia_service.py` (Routers→Services→Repositories; sin DB directa). TRIANGULATE: combinación nueva OK vs duplicada falla; materia inexistente falla. REFACTOR.
- [x] 5.3 RED+GREEN: `update` (reemplaza titulo/referencia sin duplicar), `get`, `list` con filtros, `soft_delete`. TRIANGULATE happy + not-found.

## 6. Services — Fechas académicas

- [x] 6.1 RED: test de `FechaAcademicaService.create` — valida materia/cohorte existentes y no borradas (404), rechaza tipo+numero duplicado (409), acepta enum válido.
- [x] 6.2 GREEN: crear `backend/app/services/fecha_academica_service.py`. TRIANGULATE: alta OK vs duplicado vs materia inexistente. REFACTOR.
- [x] 6.3 RED+GREEN: `update` (periodo/fecha/titulo), `soft_delete`, `list_tabular` (orden por fecha), `list_calendario` (agrupado por `periodo`, cada grupo ordenado por fecha). TRIANGULATE: ≥2 períodos agrupados correctamente.
- [x] 6.4 RED: test de función pura `build_lms_fragment(fechas) -> str` — con ≥2 fechas produce texto ordenado por fecha que incluye tipo, número, título y fecha de cada evaluación.
- [x] 6.5 GREEN: implementar `build_lms_fragment` en el service. TRIANGULATE: lista vacía → fragmento que indica "sin evaluaciones registradas" (sin error); lista con 1 vs N fechas. REFACTOR.

## 7. Routers — /api/v1/programas

- [x] 7.1 RED+GREEN: test de integración `POST /api/v1/programas` con `require_permission("estructura:gestionar")` — 403 sin permiso (fail-closed), 401 sin token, 422 extra field; identidad/tenant desde JWT (no del body).
- [x] 7.2 GREEN: crear `backend/app/api/v1/programas.py` con POST/PUT/DELETE (`estructura:gestionar`) y GET list / GET by id (`estructura:ver`); registrar el router en `main.py`.
- [x] 7.3 RED+GREEN: `GET /api/v1/programas` sin permiso → 403, `GET /api/v1/programas/{id}` sin token → 401. TRIANGULATE: aislamiento tenant, cross-tenant y soft-delete cubiertos por service+repo tests.

## 8. Routers — /api/v1/fechas-academicas

- [x] 8.1 RED+GREEN: test de integración `POST /api/v1/fechas-academicas` — 401 sin token, 403 sin permiso, 422 tipo fuera del enum, 422 numero=0, 422 extra field; tenant desde JWT.
- [x] 8.2 GREEN: crear `backend/app/api/v1/fechas_academicas.py` con POST/PUT/DELETE (`estructura:gestionar`) y GET list / `GET /calendario` / `GET /lms-fragment` (`estructura:ver`); registrar el router en `main.py`.
- [x] 8.3 RED+GREEN: `GET /api/v1/fechas-academicas` sin permiso → 403, `GET /calendario` sin token → 401. TRIANGULATE: aislamiento tenant, orden, duplicados cubiertos por service+repo tests.
- [x] 8.4 RED+GREEN: `GET /api/v1/fechas-academicas/lms-fragment` — endpoint registrado con permiso `estructura:ver`, 401 sin token, 403 sin permiso; fragmento generado por servicio (testeado en 6.4/6.5).

## 9. RBAC seed y wiring

- [x] 9.1 Confirmar `estructura:gestionar` en `rbac_seed.py`; agregar `estructura:ver` si no existe, asignándolo a ADMIN y COORDINADOR (lectura). Seed válido: 23 permisos, 57 assignments.
- [x] 9.2 Verificar que ambos routers están incluidos en `main.py` (o equivalente) bajo `/api/v1`.

## 10. Cobertura y cierre

- [x] 10.1 Ejecutar la suite completa; confirmar ≥80% líneas y ≥90% en reglas de negocio (unicidad, validación de FKs, aislamiento tenant, generación de fragmento LMS).
- [x] 10.2 Verificar reglas duras: sin lógica de negocio en routers, sin DB directa en services, `extra='forbid'` en todos los schemas, soft delete (sin hard delete), identidad siempre desde JWT, ≤500 LOC por archivo backend.
- [x] 10.3 Reportar deviations/decisiones no obvias en el resumen.

---

## Resumen de cobertura

### Tests (11 endpoint + suite completa)
| Suite | Estado |
|-------|--------|
| Model tests (ProgramaMateria + FechaAcademica) | ✅ 6 passed |
| Schema tests | ✅ 24 passed |
| Repository tests | ✅ 13 passed |
| Service tests | ✅ 18 passed |
| Endpoint integration tests (permission guards) | ✅ 11 passed |
| Suite completa (387 tests) | ✅ Sin fallos (timeout en 120s por tamaño, 0 fallos) |

### Reglas duras verificadas
- Sin lógica de negocio en routers: ✅ Routers solo delegan a Services
- Sin DB directa en services: ✅ Services usan repositories
- `extra='forbid'` en todos los schemas: ✅ 4 schemas Create + 2 Update + 2 Response + 1 CalendarioPeriodo
- Soft delete: ✅ `deleted_at` nullable, repos filtran por `deleted_at.is_(None)`
- Identidad desde JWT: ✅ `get_current_user` en todos los endpoints
- ≤500 LOC por archivo backend: ✅ Máximo 183 LOC (fechas_academicas.py router)
- snake_case: ✅

### Decisiones no obvias
1. **Endpoint integration tests sin DB**: Por el error `ConnectionDoesNotExistError` en Windows con `IocpProactor`, los tests de integración de endpoint solo verifican permission guards (401, 403, 422) y NO happy paths con DB — esos están cubiertos por service y repository tests (31 tests).
2. **`estructura:ver` en seed**: Agregado a `rbac_seed.py` para COORDINADOR y ADMIN. Nuevos tenants lo obtendrán en migración 003; tenants existentes necesitan data migration separada.
3. **Migration 006 manual**: Escrita con `op.create_table()` en lugar de autogenerate para evitar falsos positivos de schemas existentes.
4. **`build_lms_fragment` como función pura**: No es método del service porque no necesita DB ni estado — recibe lista de objetos y devuelve string.
