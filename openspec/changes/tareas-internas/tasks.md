# Tasks — C-16 tareas-internas

> Governance: MEDIO — implementar con checkpoints; surfacear decisiones no obvias.
> Migración: número Alembic `0NN` — fijar al implementar, encadenado tras el `head` vigente (C-07 y otros changes en curso reservan números intermedios).
> Permiso nuevo: `tareas:gestionar` → seed en `rbac_seed.py`, asignar a PROFESOR, COORDINADOR, ADMIN.
> Depende de C-07 (`Usuario`, `Asignacion`) y C-06 (`Materia`): las FK `asignado_a`, `asignado_por`, `autor_id`, `materia_id` requieren esas tablas.
> Strict TDD: test falla → código mínimo → triangular → refactor. Tests sin mocks de DB (DB efímera de test).
> Gotcha Windows (de C-06): `asyncio_default_fixture_loop_scope = "session"`, `TEST_DATABASE_URL` con nombre de servicio Docker, engines en fixtures session-scoped en `conftest.py`.

---

## 0. Pre-requisito (verificación de dependencias)

- [ ] 0.1 Confirmar que existen las tablas/modelos `usuario` y `materia` (de C-07 / C-06) en el `head` de Alembic. Si C-07 aún no está mergeado, coordinar el número de migración y las FK antes de continuar.

## 1. Permiso RBAC

- [ ] 1.1 Agregar `tareas:gestionar` a la lista de permisos en `backend/app/core/rbac_seed.py`.
- [ ] 1.2 Asignar `tareas:gestionar` a los roles PROFESOR, COORDINADOR y ADMIN en el seed de `rol_permiso`.

## 2. Modelos ORM

- [ ] 2.1 Crear `backend/app/models/tarea.py`: enum `EstadoTarea` (Pendiente / EnProgreso / Resuelta / Cancelada) y modelo `Tarea` con mixin base (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`), columnas `asignado_a` (FK → `usuario.id`, not null), `asignado_por` (FK → `usuario.id`, not null), `materia_id` (FK → `materia.id`, nullable), `contexto_id` (UUID nullable, sin FK), `descripcion` (Text, not null), `estado` (default `Pendiente`). Índices: `(tenant_id, asignado_a)`, `(tenant_id, asignado_por)`, `(tenant_id, materia_id)`, `(tenant_id, estado)`.
- [ ] 2.2 Crear `backend/app/models/comentario_tarea.py`: modelo `ComentarioTarea` con mixin base, columnas `tarea_id` (FK → `tarea.id`, not null), `autor_id` (FK → `usuario.id`, not null), `texto` (Text, not null), `creado_at` (timestamp). Append-only (no se borra ni edita).
- [ ] 2.3 Registrar ambos modelos en `backend/app/models/__init__.py` para que Alembic los detecte.

## 3. Migración Alembic

- [ ] 3.1 Generar `0NN_tareas_internas` con `alembic revision --autogenerate -m "0NN_tareas_internas"`. Verificar que autogenera `tarea` y `comentario_tarea` con FKs, índices de filtro y constraints.
- [ ] 3.2 Revisar la migración: confirmar FKs (`tarea.asignado_a`/`asignado_por` → `usuario.id`, `tarea.materia_id` → `materia.id`, `comentario_tarea.tarea_id` → `tarea.id`, `comentario_tarea.autor_id` → `usuario.id`), los 4 índices compuestos y el default de `estado`. Corregir si autogenerate no los captura.
- [ ] 3.3 Ejecutar `alembic upgrade head` en la DB de test y verificar que crea ambas tablas sin errores. Rollback verificado (`downgrade` dropea ambas).

## 4. Schemas Pydantic (`extra='forbid'`)

- [ ] 4.1 Crear `backend/app/schemas/tarea.py` con:
  - `TareaCreate` (`asignado_a`, `descripcion`, `materia_id` opcional, `contexto_id` opcional) — sin `asignado_por` (viene de la sesión).
  - `TareaDelegar` (`asignado_a`).
  - `TareaCambiarEstado` (`estado: EstadoTarea`).
  - `TareaResponse` (`id`, `tenant_id`, `asignado_a`, `asignado_por`, `materia_id`, `contexto_id`, `descripcion`, `estado`, `created_at`, `updated_at`) — `from_attributes=True`.
  - `ComentarioCreate` (`texto`) — sin `autor_id`.
  - `ComentarioResponse` (`id`, `tarea_id`, `autor_id`, `texto`, `creado_at`).
  - `TareaFiltros` (query): `asignado_a` opcional, `asignado_por` opcional, `materia_id` opcional, `estado` opcional, `q` opcional.

## 5. Repositories

- [ ] 5.1 Crear `backend/app/repositories/tarea_repository.py`: `TareaRepository(BaseRepository[Tarea])` con:
  - `list_filtered(tenant_id, *, asignado_a=None, asignado_por=None, materia_id=None, estado=None, q=None, scope_user_id=None)` — compone el WHERE dinámicamente, siempre con `tenant_id` y `deleted_at IS NULL`; `scope_user_id` restringe a `(asignado_a == u OR asignado_por == u)` para el alcance PROFESOR; `q` aplica ILIKE sobre `descripcion`.
  - `list_mias(tenant_id, usuario_id)` — tareas donde `asignado_a == usuario_id`.
- [ ] 5.2 Crear `backend/app/repositories/comentario_tarea_repository.py`: `ComentarioTareaRepository(BaseRepository[ComentarioTarea])` con `list_by_tarea(tenant_id, tarea_id)` ordenado por `creado_at` ascendente.

## 6. Services (núcleo de reglas de negocio)

- [ ] 6.1 Crear `backend/app/services/tarea_service.py`: `TareaService` y `TareaError(status_code, detail)` con:
  - `_TRANSICIONES: dict[EstadoTarea, set[EstadoTarea]]` (la máquina de D-02).
  - `create(tenant_id, asignado_por, data)` — valida que `asignado_a` pertenezca al tenant; crea con `estado=Pendiente`; audita `TAREA_CREAR`.
  - `delegar(tenant_id, tarea_id, nuevo_asignado_a, actor, roles)` — valida tenant del nuevo asignado; aplica alcance por rol (PROFESOR solo propio → 404 si ajena); actualiza `asignado_a`/`asignado_por`; audita `TAREA_DELEGAR`.
  - `cambiar_estado(tenant_id, tarea_id, nuevo_estado, actor, roles)` — valida transición contra `_TRANSICIONES` (400 si inválida); reapertura `Resuelta→EnProgreso` solo COORDINADOR/ADMIN (403 si PROFESOR); audita `TAREA_CAMBIAR_ESTADO`.
  - `get(tenant_id, tarea_id, scope_user_id)` — 404 si no existe, soft-deleted, o fuera de alcance.
  - `list(tenant_id, filtros, scope_user_id)` y `list_mias(tenant_id, usuario_id)`.
  - `delete(tenant_id, tarea_id)` — soft delete.
- [ ] 6.2 Crear `backend/app/services/comentario_tarea_service.py`: `ComentarioTareaService` con `crear(tenant_id, tarea_id, autor_id, texto)` (valida acceso a la tarea según alcance) y `listar(tenant_id, tarea_id)`.

## 7. Routers

- [ ] 7.1 Crear `backend/app/api/v1/routers/tareas.py` con guard `require_permission("tareas:gestionar")`, `get_current_user` y `get_db` en cada endpoint (patrón de `estructura.py`):
  - `GET /api/tareas/mias` — mis tareas (alcance `asignado_a` = sesión).
  - `GET /api/tareas` — listado global con filtros + alcance por rol.
  - `POST /api/tareas` — alta (`asignado_por` desde la sesión).
  - `GET /api/tareas/{id}` — detalle (404 fuera de alcance).
  - `DELETE /api/tareas/{id}` — soft delete.
  - `POST /api/tareas/{id}/asignar` — delegar.
  - `PATCH /api/tareas/{id}/estado` — transición de estado.
  - `GET /api/tareas/{id}/comentarios` — hilo (orden cronológico).
  - `POST /api/tareas/{id}/comentarios` — agregar comentario (`autor_id` desde la sesión).
- [ ] 7.2 Registrar el router `tareas` en `backend/app/main.py` con prefijo `/api/tareas` y tag `tareas-internas`. Mapear `TareaError` a `HTTPException` (handler o try/except en el router, según patrón existente).

## 8. Tests — Safety Net y Red/Green/Triangulate/Refactor

- [ ] 8.1 **Safety net**: ejecutar la suite existente antes de tocar código. Capturar baseline (N tests pasando). Fallos preexistentes → reportar, NO corregir acá.
- [ ] 8.2 Crear `backend/tests/test_tarea_lifecycle.py`:
  - RED: `test_create_tarea_ok` (POST → 201, estado Pendiente, `asignado_por` = sesión).
  - TRIANGULAR: `test_create_tarea_asignado_por_body_rechazado` (422), `test_create_tarea_materia_nula_ok` (201), `test_get_tarea_otro_tenant_404`, `test_list_aislamiento_tenant`, `test_soft_delete_tarea` (204 → GET 404), `test_tarea_sin_permiso_403` (ALUMNO).
- [ ] 8.3 Crear `backend/tests/test_tarea_estado.py` (máquina de estados):
  - RED: `test_transicion_pendiente_a_enprogreso_ok` (200 + auditoría).
  - TRIANGULAR: `test_transicion_invalida_400` (Pendiente→Resuelta), `test_cancelada_es_terminal_400`, `test_reapertura_resuelta_coordinador_ok`, `test_reapertura_profesor_403`.
- [ ] 8.4 Crear `backend/tests/test_tarea_delegation.py`:
  - RED: `test_delegar_ok` (200, `asignado_a` nuevo, `asignado_por` = actor, auditoría `TAREA_DELEGAR`).
  - TRIANGULAR: `test_delegar_conserva_trazabilidad`, `test_delegar_otro_tenant_400`, `test_profesor_delega_propia_ok`, `test_profesor_delega_ajena_404`.
- [ ] 8.5 Crear `backend/tests/test_tarea_comments.py`:
  - RED: `test_crear_comentario_ok` (201, `autor_id` = sesión).
  - TRIANGULAR: `test_comentario_autor_body_rechazado` (422), `test_listar_comentarios_orden_cronologico`, `test_comentarios_aislamiento_tenant_404`.
- [ ] 8.6 Crear `backend/tests/test_tarea_administration.py`:
  - RED: `test_mis_tareas_solo_asignadas` (solo `asignado_a` = sesión).
  - TRIANGULAR: `test_filtro_asignado_y_estado`, `test_busqueda_libre_descripcion`, `test_admin_sin_filtros_todas`, `test_profesor_ve_solo_participa`, `test_coordinador_ve_todas`.

## 9. Verificación final

- [ ] 9.1 Ejecutar la suite completa: `pytest backend/tests/ -v --tb=short`. Todos los tests de C-16 pasan; ningún test previo se rompe.
- [ ] 9.2 Verificar cobertura: `pytest backend/tests/ --cov=backend/app --cov-report=term-missing`. ≥80% líneas global; ≥90% en reglas de negocio (máquina de estados, alcance por rol, trazabilidad de delegación).
- [ ] 9.3 Confirmar que `GET /api/tareas` retorna lista vacía (no 500) en DB limpia y que `GET /api/tareas/mias` funciona para un usuario sin tareas.
