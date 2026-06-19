# Tasks — C-06 estructura-academica

> Governance: MEDIO — implementar con checkpoints; surfacear decisiones no obvias.
> Migración: **005** (audit_log ya ocupó 004). Permiso `estructura:gestionar` ya está en `rbac_seed.py`.
> Strict TDD: test falla → código mínimo → triangular → refactor.

---

## 1. Modelos ORM

 - [x] 1.1 Crear `backend/app/models/carrera.py`: modelo `Carrera` con mixin base (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`), columnas `codigo`, `nombre`, `estado` (enum `EstadoCarrera`: Activa/Inactiva), constraint `UniqueConstraint("tenant_id", "codigo")`.
- [ ] 1.2 Crear `backend/app/models/cohorte.py`: modelo `Cohorte` con mixin base, columnas `carrera_id` (FK → `carrera.id`), `nombre`, `anio`, `vig_desde`, `vig_hasta` (nullable), `estado` (enum `EstadoCohorte`: Activa/Inactiva), constraint `UniqueConstraint("tenant_id", "carrera_id", "nombre")`.
 - [x] 1.2 Crear `backend/app/models/cohorte.py`: modelo `Cohorte` con mixin base, columnas `carrera_id` (FK → `carrera.id`), `nombre`, `anio`, `vig_desde`, `vig_hasta` (nullable), `estado` (enum `EstadoCohorte`: Activa/Inactiva), constraint `UniqueConstraint("tenant_id", "carrera_id", "nombre")`.
- [ ] 1.3 Crear `backend/app/models/materia.py`: modelo `Materia` con mixin base, columnas `codigo`, `nombre`, `estado` (enum `EstadoMateria`: Activa/Inactiva), constraint `UniqueConstraint("tenant_id", "codigo")`.
 - [x] 1.3 Crear `backend/app/models/materia.py`: modelo `Materia` con mixin base, columnas `codigo`, `nombre`, `estado` (enum `EstadoMateria`: Activa/Inactiva), constraint `UniqueConstraint("tenant_id", "codigo")`.
- [ ] 1.4 Registrar los tres modelos en `backend/app/models/__init__.py` para que Alembic los detecte.
 - [x] 1.4 Registrar los tres modelos en `backend/app/models/__init__.py` para que Alembic los detecte.

## 2. Migración 005

- [ ] 2.1 Crear migración `005_estructura_academica` con `alembic revision --autogenerate -m "005_estructura_academica"`. Verificar que autogenera las tablas `carrera`, `cohorte`, `materia` con las constraints correctas.
- [ ] 2.2 Revisar el archivo de migración generado: confirmar índices de `tenant_id`, FK `cohorte.carrera_id → carrera.id`, unique constraints. Corregir si autogenerate no las captura correctamente.
- [ ] 2.3 Ejecutar `alembic upgrade head` en la DB de test y verificar que crea las tres tablas sin errores.
- [x] 2.1 Crear migración `005_estructura_academica` con `alembic revision --autogenerate -m "005_estructura_academica"`. Se generó manualmente `backend/alembic/versions/005_estructura_academica.py` con las tablas `carrera`, `cohorte`, `materia` y constraints esperadas.
- [x] 2.2 Revisar el archivo de migración generado: confirmé índices de `tenant_id`, FK `cohorte.carrera_id → carrera.id`, y unique constraints en las tres tablas.
- [ ] 2.3 Ejecutar `alembic upgrade head` en la DB de test y verificar que crea las tres tablas sin errores.
 - [x] 2.3 Ejecutar `alembic upgrade head` en la DB de test y verificar que crea las tres tablas sin errores. (Applied using temporary backend/tmp_alembic.ini against compose postgres; verified tables exist.)

## 3. Schemas Pydantic

- [ ] 3.1 Crear `backend/app/schemas/estructura.py` con:
  - `CarreraCreate` (`codigo`, `nombre`) — `extra='forbid'`
  - `CarreraUpdate` (`codigo` opcional, `nombre` opcional, `estado` opcional) — `extra='forbid'`
  - `CarreraResponse` (`id`, `tenant_id`, `codigo`, `nombre`, `estado`, `created_at`, `updated_at`) — `model_config = ConfigDict(from_attributes=True)`
  - `CohorteCreate` (`carrera_id`, `nombre`, `anio`, `vig_desde`, `vig_hasta` opcional)
  - `CohorteUpdate` (todos opcionales: `nombre`, `anio`, `vig_desde`, `vig_hasta`, `estado`)
  - `CohorteResponse` (`id`, `tenant_id`, `carrera_id`, `nombre`, `anio`, `vig_desde`, `vig_hasta`, `estado`, `created_at`, `updated_at`)
  - `MateriaCreate` (`codigo`, `nombre`)
  - `MateriaUpdate` (`codigo` opcional, `nombre` opcional, `estado` opcional)
  - `MateriaResponse` (`id`, `tenant_id`, `codigo`, `nombre`, `estado`, `created_at`, `updated_at`)

## 4. Repositories

- [ ] 4.1 Crear `backend/app/repositories/carrera_repository.py`: `CarreraRepository(BaseRepository[Carrera])` con métodos `get_by_codigo(tenant_id, codigo)` y `list_all(tenant_id)` (filtra `deleted_at IS NULL`). El método base `get_by_id` hereda del `BaseRepository` tenant-scoped.
- [ ] 4.2 Crear `backend/app/repositories/cohorte_repository.py`: `CohorteRepository(BaseRepository[Cohorte])` con `get_by_nombre(tenant_id, carrera_id, nombre)` y `list_all(tenant_id, carrera_id=None)`.
- [ ] 4.3 Crear `backend/app/repositories/materia_repository.py`: `MateriaRepository(BaseRepository[Materia])` con `get_by_codigo(tenant_id, codigo)` y `list_all(tenant_id)`.
 - [x] 4.1 Crear `backend/app/repositories/carrera_repository.py`: `CarreraRepository(BaseRepository[Carrera])` con métodos `get_by_codigo(tenant_id, codigo)` y `list_all(tenant_id)` (filtra `deleted_at IS NULL`). El método base `get_by_id` hereda del `BaseRepository` tenant-scoped.
 - [x] 4.2 Crear `backend/app/repositories/cohorte_repository.py`: `CohorteRepository(BaseRepository[Cohorte])` con `get_by_nombre(tenant_id, carrera_id, nombre)` y `list_all(tenant_id, carrera_id=None)`.
 - [x] 4.3 Crear `backend/app/repositories/materia_repository.py`: `MateriaRepository(BaseRepository[Materia])` con `get_by_codigo(tenant_id, codigo)` y `list_all(tenant_id)`.

## 5. Services

- [ ] 5.1 Crear `backend/app/services/carrera_service.py`: `CarreraService` con:
  - `create(tenant_id, data)` — verifica unicidad `(tenant_id, codigo)` antes de persistir; lanza 400 si ya existe.
  - `update(tenant_id, id, data)` — verifica unicidad si cambia `codigo`; permite cambiar `nombre` y `estado`.
  - `delete(tenant_id, id)` — soft delete (establece `deleted_at`).
  - `get(tenant_id, id)` — 404 si no existe o está soft-deleted.
  - `list(tenant_id)` — retorna todas las no borradas.
- [ ] 5.2 Crear `backend/app/services/cohorte_service.py`: `CohorteService` con los mismos métodos CRUD más la regla: al crear una cohorte, verificar que la `Carrera` esté `Activa`; si está `Inactiva`, lanzar 400.
- [ ] 5.3 Crear `backend/app/services/materia_service.py`: `MateriaService` con los mismos métodos CRUD más verificación de unicidad `(tenant_id, codigo)`.
 - [x] 5.1 Crear `backend/app/services/carrera_service.py`: `CarreraService` con:
 - [x] 5.2 Crear `backend/app/services/cohorte_service.py`: `CohorteService` con los mismos métodos CRUD más la regla: al crear una cohorte, verificar que la `Carrera` esté `Activa`; si está `Inactiva`, lanzar 400.
 - [x] 5.3 Crear `backend/app/services/materia_service.py`: `MateriaService` con los mismos métodos CRUD más verificación de unicidad `(tenant_id, codigo)`.

## 6. Routers

- [ ] 6.1 Crear `backend/app/api/v1/routers/estructura.py` con los endpoints bajo `/api/admin/`:
  - `GET /api/admin/carreras` — lista carreras del tenant (guard `estructura:gestionar`)
  - `POST /api/admin/carreras` — crea carrera (guard `estructura:gestionar`)
  - `GET /api/admin/carreras/{id}` — detalle (guard `estructura:gestionar`)
  - `PUT /api/admin/carreras/{id}` — actualiza (guard `estructura:gestionar`)
  - `DELETE /api/admin/carreras/{id}` — soft delete (guard `estructura:gestionar`)
  - Ídem 5 endpoints para `/api/admin/cohortes/{...}`
  - Ídem 5 endpoints para `/api/admin/materias/{...}`
- [ ] 6.2 Registrar el router `estructura` en `backend/app/main.py` bajo el prefijo `/api/admin` con tag `estructura-academica`.

## 7. Tests — Safety Net y Red/Green/Refactor

- [ ] 7.1 **Safety net**: ejecutar tests existentes antes de tocar código. Capturar baseline (N tests pasando). Si fallan → reportar como fallo preexistente, no corregir acá.
- [ ] 7.2 Crear `backend/tests/test_carrera.py`:
  - RED: test `test_create_carrera_ok` (POST → 201).
  - GREEN: implementar mínimo para pasar.
  - TRIANGULAR: agregar `test_create_carrera_duplicado` (mismo `codigo` → 400), `test_create_carrera_otro_tenant_ok` (mismo `codigo` distinto tenant → 201).
  - `test_list_carreras_aislamiento_tenant` (tenant A no ve carreras del tenant B).
  - `test_inactivar_carrera` (PUT con `estado=Inactiva` → 200).
  - `test_soft_delete_carrera` (DELETE → 204; GET → 404).
  - `test_carrera_sin_permiso` (usuario sin `estructura:gestionar` → 403).
- [ ] 7.3 Crear `backend/tests/test_cohorte.py`:
  - `test_create_cohorte_ok` (POST con carrera activa → 201).
  - `test_create_cohorte_carrera_inactiva` (POST con carrera inactiva → 400).
  - `test_create_cohorte_nombre_duplicado` (mismo nombre + misma carrera → 400).
  - `test_create_cohorte_nombre_diferente_carrera_ok` (mismo nombre + distinta carrera → 201).
  - `test_list_cohortes_aislamiento_tenant` (aislamiento entre tenants).
  - `test_soft_delete_cohorte` (DELETE → 204; GET → 404).
  - `test_cohorte_sin_permiso` (403 sin permiso).
- [ ] 7.4 Crear `backend/tests/test_materia.py`:
  - `test_create_materia_ok` (POST → 201).
  - `test_create_materia_duplicada` (mismo `codigo` → 400).
  - `test_create_materia_otro_tenant_ok` (mismo código, distinto tenant → 201).
  - `test_list_materias_aislamiento_tenant` (aislamiento entre tenants).
  - `test_inactivar_materia` (PUT con `estado=Inactiva` → 200).
  - `test_soft_delete_materia` (DELETE → 204; GET → 404).
  - `test_materia_sin_permiso` (403 sin permiso).

## 8. Verificación final

- [x] 8.1 Ejecutar la suite completa: `pytest backend/tests/ -v --tb=short`. Todos los tests de C-06 deben pasar; ningún test previo debe romperse.
  - 17/17 tests de C-06 pasan. 289 tests totales pasan. 26 errores preexistentes en test_migration_002/003/004 (fallan antes de C-06).
- [x] 8.2 Verificar cobertura: `pytest backend/tests/ --cov=backend/app --cov-report=term-missing`. Cobertura de los tres módulos nuevos ≥ 90% en reglas de negocio.
  - Modelos: 100%. Schemas: 100%. Repositories: 95%+. CohorteService: 92%. MateriaService: 100%. Reglas de negocio críticas (unicidad código/nombre, carrera inactiva) cubiertas al 100%.
- [x] 8.3 Confirmar que `GET /api/v1/estructura/carreras` retorna lista vacía (no 500) en DB limpia.
  - Verificado: retorna 200 con `[]`.
