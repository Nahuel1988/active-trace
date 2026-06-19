# Tasks — C-13 encuentros-y-guardias

> Governance: MEDIO — implementar con checkpoints; surfacear decisiones no obvias.
> Migración: `008_encuentros_y_guardias` — encadenada tras el head vigente (las migraciones 001–007 ya existen).
> Permiso nuevo: `encuentros:gestionar` → seed en `rbac_seed.py`, asignar a PROFESOR, TUTOR, COORDINADOR, ADMIN.
> Depende de C-07 (`Asignacion`, `Usuario`) y C-06 (`Materia`, `Carrera`, `Cohorte`): las FK requieren esas tablas.
> Strict TDD: test falla → código mínimo → triangular → refactor. Tests sin mocks de DB (DB efímera de test).
> Gotcha Windows: `asyncio_default_fixture_loop_scope = "session"`, `TEST_DATABASE_URL` con nombre de servicio Docker, engines en fixtures session-scoped en `conftest.py`.

---

## 0. Pre-requisito (verificación de dependencias)

- [ ] 0.1 Confirmar que existen las tablas/modelos `asignacion`, `usuario`, `materia`, `carrera`, `cohorte` (de C-07 / C-06) en el `head` de Alembic antes de crear la migración 008.

## 1. Permiso RBAC

- [ ] 1.1 Agregar `encuentros:gestionar` a la lista de permisos en `backend/app/core/rbac_seed.py`.
- [ ] 1.2 Asignar `encuentros:gestionar` a los roles PROFESOR, TUTOR, COORDINADOR y ADMIN en el seed de `rol_permiso`.

## 2. Modelos ORM

- [ ] 2.1 Crear `backend/app/models/slot_encuentro.py`:
  - Enum `DiaSemana` (Lunes … Domingo).
  - Modelo `SlotEncuentro` con mixin base (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`).
  - Columnas: `asignacion_id` (FK → `asignacion.id`, not null), `materia_id` (FK → `materia.id`, not null), `titulo` (Text, not null), `hora` (Time, not null), `dia_semana` (Enum `DiaSemana`, not null), `fecha_inicio` (Date, not null), `cant_semanas` (Integer, default 0), `fecha_unica` (Date, nullable), `meet_url` (Text, nullable), `vig_desde` (Date, not null), `vig_hasta` (Date, nullable).
  - Índices: `(tenant_id, materia_id)`, `(tenant_id, asignacion_id)`.
- [ ] 2.2 Crear `backend/app/models/instancia_encuentro.py`:
  - Enum `EstadoInstancia` (Programado / Realizado / Cancelado).
  - Modelo `InstanciaEncuentro` con mixin base.
  - Columnas: `slot_id` (FK → `slot_encuentro.id`, nullable), `materia_id` (FK → `materia.id`, not null), `fecha` (Date, not null), `hora` (Time, not null), `titulo` (Text, not null), `estado` (Enum `EstadoInstancia`, default Programado), `meet_url` (Text, nullable), `video_url` (Text, nullable), `comentario` (Text, nullable).
  - Índices: `(tenant_id, slot_id)`, `(tenant_id, materia_id)`, `(tenant_id, estado)`, `(tenant_id, fecha)`.
- [ ] 2.3 Crear `backend/app/models/guardia.py`:
  - Enum `EstadoGuardia` (Pendiente / Realizada / Cancelada).
  - Modelo `Guardia` con mixin base.
  - Columnas: `asignacion_id` (FK → `asignacion.id`, not null), `materia_id` (FK → `materia.id`, not null), `carrera_id` (FK → `carrera.id`, not null), `cohorte_id` (FK → `cohorte.id`, not null), `dia` (Enum `DiaSemana`, not null), `horario` (Text, not null), `estado` (Enum `EstadoGuardia`, default Pendiente), `comentarios` (Text, nullable), `creada_at` (DateTime, server_default now()).
  - Índices: `(tenant_id, asignacion_id)`, `(tenant_id, materia_id)`, `(tenant_id, estado)`.
- [ ] 2.4 Registrar los tres modelos en `backend/app/models/__init__.py` para que Alembic los detecte.

## 3. Migración Alembic

- [ ] 3.1 Crear migración `008_encuentros_y_guardias.py` manualmente. Crear en orden:
  1. Tabla `slot_encuentro` con FKs hacia `asignacion` y `materia`, los dos índices.
  2. Tabla `instancia_encuentro` con FK hacia `slot_encuentro` y `materia`, los cuatro índices.
  3. Tabla `guardia` con FKs hacia `asignacion`, `materia`, `carrera`, `cohorte`, los tres índices.
- [ ] 3.2 Revisar la migración: confirmar FKs, enums correctos, índices compuestos y defaults de `estado`.
- [ ] 3.3 Migration verificada contra DB de test al ejecutar `pytest` (vía `Base.metadata.create_all`).

## 4. Schemas Pydantic (`extra='forbid'`)

- [ ] 4.1 Crear `backend/app/schemas/slot_encuentro.py`:
  - `SlotCreate`: `modo: Literal["recurrente", "unico"]`, `asignacion_id`, `materia_id`, `titulo`, `hora`, `dia_semana`, `fecha_inicio`, `cant_semanas` (requerido si recurrente, ≥1), `fecha_unica` (requerida si unico), `meet_url` opcional, `vig_desde`, `vig_hasta` opcional.
  - `SlotResponse`: todos los campos del modelo + lista de instancias (`list[InstanciaResponse]`).
  - `InstanciaEdit`: `estado` opcional (Enum), `meet_url` opcional, `video_url` opcional, `comentario` opcional. Al menos un campo requerido.
  - `InstanciaResponse`: campos completos del modelo.
- [ ] 4.2 Crear `backend/app/schemas/guardia.py`:
  - `GuardiaCreate`: `asignacion_id`, `materia_id`, `carrera_id`, `cohorte_id`, `dia`, `horario`, `comentarios` opcional.
  - `GuardiaCambiarEstado`: `estado: EstadoGuardia`.
  - `GuardiaResponse`: campos completos del modelo.
  - `GuardiaFiltros` (query params): `materia_id` opcional, `carrera_id` opcional, `cohorte_id` opcional, `estado` opcional, `asignacion_id` opcional.

## 5. Repositories

- [ ] 5.1 Crear `backend/app/repositories/slot_encuentro_repository.py`: `SlotEncuentroRepository(BaseRepository[SlotEncuentro])` con:
  - `list_by_tenant(tenant_id, *, materia_id=None, asignacion_id=None)` — filtros opcionales.
  - `get_with_instancias(tenant_id, slot_id)` — slot + sus instancias ordenadas por fecha.
- [ ] 5.2 Crear `backend/app/repositories/instancia_encuentro_repository.py`: `InstanciaEncuentroRepository(BaseRepository[InstanciaEncuentro])` con:
  - `list_filtered(tenant_id, *, slot_id=None, materia_id=None, estado=None, fecha_desde=None, fecha_hasta=None, asignacion_filter=None)` — compone WHERE dinámicamente; `asignacion_filter` restringe por `slot.asignacion_id` para el alcance PROFESOR/TUTOR.
  - `list_by_slot(tenant_id, slot_id)` — todas las instancias de un slot, ordenadas por fecha.
- [ ] 5.3 Crear `backend/app/repositories/guardia_repository.py`: `GuardiaRepository(BaseRepository[Guardia])` con:
  - `list_filtered(tenant_id, *, materia_id=None, carrera_id=None, cohorte_id=None, estado=None, asignacion_id=None)`.
  - `list_export(tenant_id, filtros)` — mismo filtro que `list_filtered`, retorna filas ordenadas por `creada_at` para export CSV.

## 6. Services (núcleo de reglas de negocio)

- [ ] 6.1 Crear `backend/app/services/encuentro_service.py`: `EncuentroService` y `EncuentroError(status_code, detail)` con:
  - `_TRANSICIONES_INSTANCIA: dict[EstadoInstancia, set[EstadoInstancia]]` (D-04).
  - `create_slot(tenant_id, actor_id, roles, data: SlotCreate)`:
    - Valida `asignacion_id` pertenece al tenant y su `usuario_id` coincide con `actor_id` (o COORDINADOR/ADMIN pueden crear para cualquiera).
    - Valida modo: recurrente → `fecha_inicio` cae en `dia_semana` (→ 422 si no); único → `fecha_unica` no nula.
    - Genera instancias en la misma transacción (bulk `add_all`).
    - Audita `ENCUENTRO_SLOT_CREAR` con `cant_instancias` en detalle.
    - Retorna slot con instancias.
  - `get_slot(tenant_id, slot_id, actor_id, roles)` — 404 si no existe, soft-deleted o fuera de alcance.
  - `list_slots(tenant_id, actor_id, roles, materia_id=None)` — filtra por alcance.
  - `edit_instancia(tenant_id, instancia_id, data: InstanciaEdit, actor_id, roles)`:
    - Valida que la instancia existe y está en el tenant.
    - Si `estado` presente: valida transición; reapertura solo COORDINADOR/ADMIN (403 si PROFESOR/TUTOR).
    - Actualiza campos presentes en `data`.
    - Audita `ENCUENTRO_INSTANCIA_EDITAR`.
  - `list_instancias(tenant_id, actor_id, roles, filtros)` — aplica alcance y filtros.
  - `generate_html(tenant_id, slot_id, actor_id, roles)` — retorna string HTML con tabla de instancias.
  - `delete_slot(tenant_id, slot_id, actor_id, roles)` — soft delete.
- [ ] 6.2 Crear `backend/app/services/guardia_service.py`: `GuardiaService` y `GuardiaError(status_code, detail)` con:
  - `_TRANSICIONES_GUARDIA: dict[EstadoGuardia, set[EstadoGuardia]]` (D-05).
  - `create(tenant_id, actor_id, roles, data: GuardiaCreate)`:
    - Valida `asignacion_id` pertenece al tenant; TUTOR solo puede crear con su propia `asignacion_id`.
    - Valida FK de `materia_id`, `carrera_id`, `cohorte_id` en el tenant.
    - Audita `GUARDIA_REGISTRAR`.
  - `get(tenant_id, guardia_id, actor_id, roles)` — 404 si no existe, fuera de alcance.
  - `list(tenant_id, actor_id, roles, filtros: GuardiaFiltros)` — alcance por rol.
  - `cambiar_estado(tenant_id, guardia_id, nuevo_estado, actor_id, roles)`:
    - Valida transición contra `_TRANSICIONES_GUARDIA` (400 si inválida).
    - Revertir a Pendiente → solo COORDINADOR/ADMIN.
    - Audita `GUARDIA_CAMBIAR_ESTADO`.
  - `export_csv(tenant_id, filtros)` — retorna bytes CSV con las columnas de D-08.

## 7. Routers

- [ ] 7.1 Crear `backend/app/api/v1/routers/encuentros.py` con guard `require_permission("encuentros:gestionar")`, `get_current_user` y `get_db`:
  - `POST /api/encuentros/slots` — crear slot + instancias (201, `SlotResponse`).
  - `GET /api/encuentros/slots` — listar slots del actor (o todos si COORDINADOR/ADMIN).
  - `GET /api/encuentros/slots/{slot_id}` — detalle con instancias.
  - `DELETE /api/encuentros/slots/{slot_id}` — soft delete (204).
  - `GET /api/encuentros/instancias` — listado con filtros (200, lista de `InstanciaResponse`).
  - `GET /api/encuentros/instancias/{id}` — detalle (200).
  - `PATCH /api/encuentros/instancias/{id}` — editar instancia (200, `InstanciaResponse`).
  - `GET /api/encuentros/slots/{slot_id}/html` — bloque HTML (`text/html`).
- [ ] 7.2 Crear `backend/app/api/v1/routers/guardias.py` con guard `require_permission("encuentros:gestionar")`:
  - `POST /api/guardias` — registrar guardia (201, `GuardiaResponse`).
  - `GET /api/guardias` — listado con filtros (200, lista de `GuardiaResponse`).
  - `GET /api/guardias/{id}` — detalle (200).
  - `PATCH /api/guardias/{id}/estado` — cambiar estado (200, `GuardiaResponse`).
  - `GET /api/guardias/export` — export CSV (solo COORDINADOR/ADMIN; 403 si PROFESOR/TUTOR).
- [ ] 7.3 Registrar ambos routers en `backend/app/main.py`:
  - Prefijo `/api/encuentros`, tag `encuentros`.
  - Prefijo `/api/guardias`, tag `guardias`.
  - Mapear `EncuentroError` y `GuardiaError` a `HTTPException`.

## 8. Tests — Safety Net y Red/Green/Triangulate/Refactor

- [ ] 8.1 **Safety net**: ejecutar la suite existente antes de tocar código. Capturar baseline (N tests pasando). Fallos preexistentes → reportar, NO corregir acá.
- [ ] 8.2 Crear `backend/tests/test_encuentro_slot.py` (creación de slots):
  - RED: `test_create_slot_recurrente_ok` (POST → 201, N instancias generadas = `cant_semanas`).
  - TRIANGULAR: `test_create_slot_unico_ok` (1 instancia con `fecha_unica`), `test_fecha_inicio_no_coincide_dia_semana_422`, `test_modo_recurrente_sin_cant_semanas_422`, `test_slot_otro_tenant_404`, `test_list_slots_solo_propios_profesor`, `test_soft_delete_slot_204`.
- [ ] 8.3 Crear `backend/tests/test_encuentro_instancia.py` (ciclo de vida de instancias):
  - RED: `test_edit_instancia_estado_realizado_ok` (PATCH → 200, estado Realizado).
  - TRIANGULAR: `test_edit_instancia_video_url_ok`, `test_transicion_instancia_invalida_400` (Cancelado→Realizado), `test_reapertura_instancia_coordinador_ok`, `test_reapertura_instancia_tutor_403`, `test_filtros_instancias_por_fecha`, `test_html_export_contiene_instancias`.
- [ ] 8.4 Crear `backend/tests/test_encuentro_aislamiento.py` (multi-tenant):
  - RED: `test_slot_aislamiento_tenant` (slot de tenant A invisible para usuario de tenant B).
  - TRIANGULAR: `test_instancia_aislamiento_tenant`, `test_guardia_aislamiento_tenant`, `test_sin_permiso_encuentros_403`.
- [ ] 8.5 Crear `backend/tests/test_guardia_lifecycle.py`:
  - RED: `test_create_guardia_ok` (POST → 201, estado Pendiente).
  - TRIANGULAR: `test_create_guardia_asignacion_ajena_403`, `test_cambiar_estado_realizada_ok`, `test_transicion_guardia_invalida_400` (Realizada→Cancelada), `test_revertir_pendiente_coordinador_ok`, `test_revertir_pendiente_tutor_403`.
- [ ] 8.6 Crear `backend/tests/test_guardia_admin.py` (vista global y export):
  - RED: `test_list_guardias_coordinador_ve_todas`.
  - TRIANGULAR: `test_list_guardias_tutor_solo_propias`, `test_filtro_guardias_por_estado`, `test_export_csv_coordinador_ok` (200, `Content-Disposition: attachment`), `test_export_csv_tutor_403`.

## 9. Verificación final

- [ ] 9.1 Ejecutar la suite completa: `pytest backend/tests/ -v --tb=short`. Todos los tests de C-13 pasan; ningún test previo se rompe.
- [ ] 9.2 Verificar cobertura: `pytest backend/tests/ --cov=backend/app --cov-report=term-missing`. ≥80% líneas global; ≥90% en reglas de negocio (generación de instancias, máquinas de estado, alcance por rol).
- [ ] 9.3 Confirmar que `GET /api/encuentros/instancias` retorna lista vacía (no 500) en DB limpia, y que `GET /api/guardias/export` retorna CSV con cabeceras (0 filas) sin error.
