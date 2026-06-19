# Tasks — C-17 programas-y-fechas-academicas

> Governance: **BAJO** — autonomía total si pasan los tests; reportar en el resumen.
> Migración: **006** (004 = audit_log, 005 = estructura_academica). Una sola migración para este change.
> Permiso `estructura:gestionar` ya sembrado en C-06; agregar `estructura:ver` al seed si falta.
> Strict TDD por tarea: RED (test falla) → GREEN (mínimo) → TRIANGULATE (≥2 casos, +edge) → REFACTOR. Sin mocks de DB (DB efímera/contenedor). `extra='forbid'` en todos los schemas. snake_case.
> Gotcha entorno (de C-06): `asyncio_default_fixture_loop_scope = "session"` en pyproject.toml; `TEST_DATABASE_URL` con nombre de servicio Docker; engines en fixtures session-scoped en conftest.py.

---

## 1. Modelos ORM

- [ ] 1.1 RED: test de modelo `ProgramaMateria` — instanciar y persistir con columnas `materia_id`, `carrera_id`, `cohorte_id`, `titulo`, `referencia_archivo`, `cargado_at` + mixin base (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`); assert que sin uno de los FK falla.
- [ ] 1.2 GREEN: crear `backend/app/models/programa_materia.py` con mixin base, FKs a `materia.id`/`carrera.id`/`cohorte.id`, `UniqueConstraint("tenant_id", "materia_id", "carrera_id", "cohorte_id")`. TRIANGULATE: segundo caso con otra combinación; verificar que la unicidad NO dispara entre combinaciones distintas. REFACTOR.
- [ ] 1.3 RED: test de modelo `FechaAcademica` — persistir con `materia_id`, `cohorte_id`, `tipo` (enum `TipoFechaAcademica`: Parcial/TP/Coloquio/Recuperatorio), `numero`, `periodo`, `fecha`, `titulo` + mixin base.
- [ ] 1.4 GREEN: crear `backend/app/models/fecha_academica.py` con mixin base, FKs a `materia.id`/`cohorte.id`, enum `TipoFechaAcademica`, `UniqueConstraint("tenant_id", "materia_id", "cohorte_id", "tipo", "numero")`. TRIANGULATE: mismo tipo distinto número (OK) vs mismo tipo+número (viola constraint). REFACTOR.
- [ ] 1.5 Registrar ambos modelos en `backend/app/models/__init__.py` para que Alembic los detecte.

## 2. Migración 006

- [ ] 2.1 Generar `006_programas_y_fechas_academicas` con `alembic revision --autogenerate -m "006_programas_y_fechas_academicas"`.
- [ ] 2.2 Revisar el archivo generado: índices de `tenant_id` en ambas tablas, FKs (`programa_materia` → carrera/cohorte/materia; `fecha_academica` → cohorte/materia), unique constraints de §D2/§D3, índice `(tenant_id, cohorte_id)` en `fecha_academica`. Corregir lo que autogenerate no capture.
- [ ] 2.3 Ejecutar `alembic upgrade head` en la DB de test y verificar que crea `programa_materia` y `fecha_academica` sin errores; probar `alembic downgrade -1` y volver a `upgrade head`.

## 3. Schemas Pydantic (extra='forbid')

- [ ] 3.1 Crear `backend/app/schemas/programa_materia.py`: `ProgramaMateriaCreate` (`materia_id`, `carrera_id`, `cohorte_id`, `titulo`, `referencia_archivo`), `ProgramaMateriaUpdate` (`titulo?`, `referencia_archivo?`), `ProgramaMateriaResponse` (`from_attributes=True`, incluye `cargado_at`, `created_at`, `updated_at`). RED: test que un campo extra es rechazado; test que `referencia_archivo` se acepta como string opaco.
- [ ] 3.2 Crear `backend/app/schemas/fecha_academica.py`: `FechaAcademicaCreate` (`materia_id`, `cohorte_id`, `tipo`, `numero`≥1, `periodo`, `fecha`, `titulo`), `FechaAcademicaUpdate` (`periodo?`, `fecha?`, `titulo?`), `FechaAcademicaResponse`, y `CalendarioPeriodo` (`periodo` + lista de fechas) para la vista agrupada. RED: test que `tipo` fuera del enum y `numero=0` son rechazados (422). TRIANGULATE: enum válido + numero=1 pasa.

## 4. Repositories (aislamiento por tenant)

- [ ] 4.1 RED: test de `ProgramaMateriaRepository` — `create`, `get_by_id` (scope tenant), `list` con filtros (`materia_id`/`carrera_id`/`cohorte_id`), `get_by_combination` (para unicidad), `soft_delete`. Assert que `get_by_id` de otro tenant retorna None.
- [ ] 4.2 GREEN: crear `backend/app/repositories/programa_materia_repository.py` heredando de `repositories/base.py` (filtro tenant por defecto + exclusión de `deleted_at`). TRIANGULATE: listado de tenant A no incluye registros de tenant B; programa soft-deleted no aparece. REFACTOR.
- [ ] 4.3 RED: test de `FechaAcademicaRepository` — `create`, `get_by_id`, `list` (filtros `materia_id`/`cohorte_id`/`periodo`/`tipo`, orden por `fecha` asc), `get_by_instance` (para unicidad tipo+numero), `soft_delete`. Assert orden por fecha y aislamiento tenant.
- [ ] 4.4 GREEN: crear `backend/app/repositories/fecha_academica_repository.py` heredando de base. TRIANGULATE: orden ascendente con ≥2 fechas; aislamiento tenant; fecha borrada excluida. REFACTOR.

## 5. Services — Programas

- [ ] 5.1 RED: test de `ProgramaMateriaService.create` — valida que materia/carrera/cohorte existan y no estén soft-deleted (404 si no), rechaza combinación duplicada (409/conflict), persiste referencia opaca y `cargado_at`.
- [ ] 5.2 GREEN: crear `backend/app/services/programa_materia_service.py` (Routers→Services→Repositories; sin DB directa). TRIANGULATE: combinación nueva OK vs duplicada falla; materia inexistente falla. REFACTOR.
- [ ] 5.3 RED+GREEN: `update` (reemplaza titulo/referencia sin duplicar), `get`, `list` con filtros, `soft_delete`. TRIANGULATE happy + not-found.

## 6. Services — Fechas académicas

- [ ] 6.1 RED: test de `FechaAcademicaService.create` — valida materia/cohorte existentes y no borradas (404), rechaza tipo+numero duplicado (409), acepta enum válido.
- [ ] 6.2 GREEN: crear `backend/app/services/fecha_academica_service.py`. TRIANGULATE: alta OK vs duplicado vs materia inexistente. REFACTOR.
- [ ] 6.3 RED+GREEN: `update` (periodo/fecha/titulo), `soft_delete`, `list_tabular` (orden por fecha), `list_calendario` (agrupado por `periodo`, cada grupo ordenado por fecha). TRIANGULATE: ≥2 períodos agrupados correctamente.
- [ ] 6.4 RED: test de función pura `build_lms_fragment(fechas) -> str` — con ≥2 fechas produce texto ordenado por fecha que incluye tipo, número, título y fecha de cada evaluación.
- [ ] 6.5 GREEN: implementar `build_lms_fragment` en el service. TRIANGULATE: lista vacía → fragmento que indica "sin evaluaciones registradas" (sin error); lista con 1 vs N fechas. REFACTOR.

## 7. Routers — /api/programas

- [ ] 7.1 RED: test de integración `POST /api/programas` con `require_permission("estructura:gestionar")` — 201 con permiso, 403 sin él (fail-closed), identidad/tenant desde JWT (no del body).
- [ ] 7.2 GREEN: crear `backend/app/api/v1/programas.py` con POST/PUT/DELETE (`estructura:gestionar`) y GET list / GET by id (`estructura:ver`); registrar el router. TRIANGULATE: 201 vs 403 vs 409 (duplicado).
- [ ] 7.3 RED+GREEN: `GET /api/programas` filtrado por cohorte, `GET /api/programas/{id}`, `DELETE` (204 + soft delete). TRIANGULATE: aislamiento tenant (404 cross-tenant), borrado no recuperable (404).

## 8. Routers — /api/fechas-academicas

- [ ] 8.1 RED: test de integración `POST /api/fechas-academicas` — 201 con `estructura:gestionar`, 403 sin permiso, 422 tipo fuera del enum, tenant desde JWT.
- [ ] 8.2 GREEN: crear `backend/app/api/v1/fechas_academicas.py` con POST/PUT/DELETE (`estructura:gestionar`) y GET list / `GET /calendario` / `GET /lms-fragment` (`estructura:ver`); registrar el router. TRIANGULATE: 201 vs 403 vs 409 (tipo+numero duplicado).
- [ ] 8.3 RED+GREEN: `GET /api/fechas-academicas` (tabular, orden por fecha), `GET /calendario` (agrupado por período), `PUT`, `DELETE` (204 soft delete). TRIANGULATE: aislamiento tenant (404 cross-tenant en PUT), orden correcto.
- [ ] 8.4 RED+GREEN: `GET /api/fechas-academicas/lms-fragment?materia_id=&cohorte_id=` — 200 con fragmento de las fechas; caso sin fechas → 200 con texto "sin evaluaciones". TRIANGULATE: con permiso vs 403 sin `estructura:ver`.

## 9. RBAC seed y wiring

- [ ] 9.1 Confirmar `estructura:gestionar` en `rbac_seed.py`; agregar `estructura:ver` si no existe, asignándolo a ADMIN y COORDINADOR (lectura) y `estructura:gestionar` a ADMIN/COORDINADOR (gestión) según F5.3/F5.4.
- [ ] 9.2 Verificar que ambos routers están incluidos en el agregador de `backend/app/api/v1/__init__.py` (o equivalente) bajo `/api`.

## 10. Cobertura y cierre

- [ ] 10.1 Ejecutar la suite completa; confirmar ≥80% líneas y ≥90% en reglas de negocio (unicidad, validación de FKs, aislamiento tenant, generación de fragmento LMS).
- [ ] 10.2 Verificar reglas duras: sin lógica de negocio en routers, sin DB directa en services, `extra='forbid'` en todos los schemas, soft delete (sin hard delete), identidad siempre desde JWT, ≤500 LOC por archivo backend.
- [ ] 10.3 Marcar tareas completas y reportar deviations/decisiones no obvias en el resumen.
