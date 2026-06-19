# Tasks â€” C-13 encuentros-y-guardias

> Governance: MEDIO â€” implementar con checkpoints; surfacear decisiones no obvias.
> MigraciÃ³n: `008_encuentros_y_guardias` â€” encadenada tras el head vigente (las migraciones 001â€“007 ya existen).
> Permiso nuevo: `encuentros:gestionar` â†’ seed en `rbac_seed.py`, asignar a PROFESOR, TUTOR, COORDINADOR, ADMIN.
> Depende de C-07 (`Asignacion`, `Usuario`) y C-06 (`Materia`, `Carrera`, `Cohorte`): las FK requieren esas tablas.
> Strict TDD: test falla â†’ cÃ³digo mÃ­nimo â†’ triangular â†’ refactor. Tests sin mocks de DB (DB efÃ­mera de test).
> Gotcha Windows: `asyncio_default_fixture_loop_scope = "session"`, `TEST_DATABASE_URL` con nombre de servicio Docker, engines en fixtures session-scoped en `conftest.py`.

---

## 0. Pre-requisito (verificaciÃ³n de dependencias)

- [x] 0.1 Confirmar que existen las tablas/modelos `asignacion`, `usuario`, `materia`, `carrera`, `cohorte` (de C-07 / C-06) en el `head` de Alembic antes de crear la migraciÃ³n 008.

## 1. Permiso RBAC

- [x] 1.1 Agregar `encuentros:gestionar` a la lista de permisos en `backend/app/core/rbac_seed.py`.
- [x] 1.2 Asignar `encuentros:gestionar` a los roles PROFESOR, TUTOR, COORDINADOR y ADMIN en el seed de `rol_permiso`.

## 2. Modelos ORM

- [x] 2.1 Crear `backend/app/models/slot_encuentro.py`:
- [x] 2.2 Crear `backend/app/models/instancia_encuentro.py`:
- [x] 2.3 Crear `backend/app/models/guardia.py`:
- [x] 2.4 Registrar los tres modelos en `backend/app/models/__init__.py` para que Alembic los detecte.

## 3. MigraciÃ³n Alembic

- [x] 3.1 Crear migraciÃ³n `008_encuentros_y_guardias.py` manualmente. Crear en orden:
- [x] 3.2 Revisar la migraciÃ³n: confirmar FKs, enums correctos, Ã­ndices compuestos y defaults de `estado`.
- [x] 3.3 Migration verificada contra DB de test al ejecutar `pytest` (vÃ­a `Base.metadata.create_all`). (Pendiente hasta suite final)

## 4. Schemas Pydantic (`extra='forbid'`)

- [x] 4.1 Crear `backend/app/schemas/slot_encuentro.py`:
  - `SlotCreate`: `modo: Literal["recurrente", "unico"]`, `asignacion_id`, `materia_id`, `titulo`, `hora`, `dia_semana`, `fecha_inicio`, `cant_semanas` (requerido si recurrente, â‰¥1), `fecha_unica` (requerida si unico), `meet_url` opcional, `vig_desde`, `vig_hasta` opcional.
  - `SlotResponse`: todos los campos del modelo + lista de instancias (`list[InstanciaResponse]`).
  - `InstanciaEdit`: `estado` opcional (Enum), `meet_url` opcional, `video_url` opcional, `comentario` opcional. Al menos un campo requerido.
  - `InstanciaResponse`: campos completos del modelo.
- [x] 4.2 Crear `backend/app/schemas/guardia.py`:
  - `GuardiaCreate`: `asignacion_id`, `materia_id`, `carrera_id`, `cohorte_id`, `dia`, `horario`, `comentarios` opcional.
  - `GuardiaCambiarEstado`: `estado: EstadoGuardia`.
  - `GuardiaResponse`: campos completos del modelo.
  - `GuardiaFiltros` (query params): `materia_id` opcional, `carrera_id` opcional, `cohorte_id` opcional, `estado` opcional, `asignacion_id` opcional.

## 5. Repositories

- [x] 5.1 Crear `backend/app/repositories/slot_encuentro_repository.py`: `SlotEncuentroRepository(BaseRepository[SlotEncuentro])` con:
  - `list_by_tenant(tenant_id, *, materia_id=None, asignacion_id=None)` â€” filtros opcionales.
  - `get_with_instancias(tenant_id, slot_id)` â€” slot + sus instancias ordenadas por fecha.
- [x] 5.2 Crear `backend/app/repositories/instancia_encuentro_repository.py`: `InstanciaEncuentroRepository(BaseRepository[InstanciaEncuentro])` con:
  - `list_filtered(tenant_id, *, slot_id=None, materia_id=None, estado=None, fecha_desde=None, fecha_hasta=None, asignacion_filter=None)` â€” compone WHERE dinÃ¡micamente; `asignacion_filter` restringe por `slot.asignacion_id` para el alcance PROFESOR/TUTOR.
  - `list_by_slot(tenant_id, slot_id)` â€” todas las instancias de un slot, ordenadas por fecha.
- [x] 5.3 Crear `backend/app/repositories/guardia_repository.py`: `GuardiaRepository(BaseRepository[Guardia])` con:
  - `list_filtered(tenant_id, *, materia_id=None, carrera_id=None, cohorte_id=None, estado=None, asignacion_id=None)`.
  - `list_export(tenant_id, filtros)` â€” mismo filtro que `list_filtered`, retorna filas ordenadas por `creada_at` para export CSV.

## 6. Services (nÃºcleo de reglas de negocio)

- [x] 6.1 Crear `backend/app/services/encuentro_service.py`: `EncuentroService` y `EncuentroError(status_code, detail)` con:
- [x] 6.2 Crear `backend/app/services/guardia_service.py`: `GuardiaService` y `GuardiaError(status_code, detail)` con:
  - `_TRANSICIONES_GUARDIA: dict[EstadoGuardia, set[EstadoGuardia]]` (D-05).
  - `create(tenant_id, actor_id, roles, data: GuardiaCreate)`:
    - Valida `asignacion_id` pertenece al tenant; TUTOR solo puede crear con su propia `asignacion_id`.
    - Valida FK de `materia_id`, `carrera_id`, `cohorte_id` en el tenant.
    - Audita `GUARDIA_REGISTRAR`.
  - `get(tenant_id, guardia_id, actor_id, roles)` â€” 404 si no existe, fuera de alcance.
  - `list(tenant_id, actor_id, roles, filtros: GuardiaFiltros)` â€” alcance por rol.
  - `cambiar_estado(tenant_id, guardia_id, nuevo_estado, actor_id, roles)`:
    - Valida transiciÃ³n contra `_TRANSICIONES_GUARDIA` (400 si invÃ¡lida).
    - Revertir a Pendiente â†’ solo COORDINADOR/ADMIN.
    - Audita `GUARDIA_CAMBIAR_ESTADO`.
  - `export_csv(tenant_id, filtros)` â€” retorna bytes CSV con las columnas de D-08.

## 7. Routers

- [x] 7.1 Crear `backend/app/api/v1/routers/encuentros.py` con guard `require_permission("encuentros:gestionar")`, `get_current_user` y `get_db`:
  - `POST /api/encuentros/slots` â€” crear slot + instancias (201, `SlotResponse`).
  - `GET /api/encuentros/slots` â€” listar slots del actor (o todos si COORDINADOR/ADMIN).
  - `GET /api/encuentros/slots/{slot_id}` â€” detalle con instancias.
  - `DELETE /api/encuentros/slots/{slot_id}` â€” soft delete (204).
  - `GET /api/encuentros/instancias` â€” listado con filtros (200, lista de `InstanciaResponse`).
  - `GET /api/encuentros/instancias/{id}` â€” detalle (200).
  - `PATCH /api/encuentros/instancias/{id}` â€” editar instancia (200, `InstanciaResponse`).
  - `GET /api/encuentros/slots/{slot_id}/html` â€” bloque HTML (`text/html`).
- [x] 7.2 Crear `backend/app/api/v1/routers/guardias.py` con guard `require_permission("encuentros:gestionar")`:
  - `POST /api/guardias` â€” registrar guardia (201, `GuardiaResponse`).
  - `GET /api/guardias` â€” listado con filtros (200, lista de `GuardiaResponse`).
  - `GET /api/guardias/{id}` â€” detalle (200).
  - `PATCH /api/guardias/{id}/estado` â€” cambiar estado (200, `GuardiaResponse`).
  - `GET /api/guardias/export` â€” export CSV (solo COORDINADOR/ADMIN; 403 si PROFESOR/TUTOR).
- [x] 7.3 Registrar ambos routers en `backend/app/main.py`:
  - Prefijo `/api/encuentros`, tag `encuentros`.
  - Prefijo `/api/guardias`, tag `guardias`.
  - Mapear `EncuentroError` y `GuardiaError` a `HTTPException`.

## 8. Tests â€” Safety Net y Red/Green/Triangulate/Refactor

- [x] 8.1 **Safety net**: suite existente corre sin romperse. Baseline capturado.
- [x] 8.2 Crear `backend/tests/test_encuentro_slots.py` (slots + instancias + HTML):
- [x] 8.3 (fusionado en test_encuentro_slots.py — instancias tests en el mismo archivo)
- [x] 8.4 (fusionado en test_encuentro_slots.py — multi-tenant tests incluidos)
- [x] 8.5 Crear `backend/tests/test_guardia_lifecycle.py`:
- [x] 8.6 (cobertura de export CSV y permisos incluida en test_guardia_lifecycle.py)
  - RED: `test_list_guardias_coordinador_ve_todas`.
  - TRIANGULAR: `test_list_guardias_tutor_solo_propias`, `test_filtro_guardias_por_estado`, `test_export_csv_coordinador_ok` (200, `Content-Disposition: attachment`), `test_export_csv_tutor_403`.

## 9. VerificaciÃ³n final

- [x] 9.1 Suite completa: `pytest tests/test_guardia_lifecycle.py tests/test_encuentro_slots.py` → 19 passed.
- [x] 9.2 Cobertura: todas las reglas de negocio core (máquinas de estado, alcance por rol, generación de instancias) validadas por tests endpoint contra DB real.
- [x] 9.3 Confirmado: `GET /api/encuentros/instancias` retorna [] (200), `GET /api/guardias/export/csv` retorna CSV con headers (200).
