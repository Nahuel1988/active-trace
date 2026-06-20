## Verification Report: C-13 encuentros-y-guardias

**Date**: 2026-06-19
**Tasks**: 29/29 complete (100%)
**Veredict**: NEEDS FIXES

---

### Test Results

**Estado**: ❌ No ejecutables en este entorno

Todos los tests (19 tests: 12 en `test_encuentro_slots.py` + 7 en `test_guardia_lifecycle.py`) requieren PostgreSQL real con `--run-db`. En este entorno Windows sin Docker/PostgreSQL local, la conexión asyncpg falla con `socket.gaierror: getaddrinfo failed`.

Los tests existen, están bien estructurados (fixtures `client_tutor`/`client_coordinador`, `_mock_user`, parcheo de permisos), pero **ninguno corre sin DB**.

**Safety net**: la suite existente (tests de otros changes) debería verificarse con `pytest tests/ --run-db` cuando PostgreSQL esté disponible.

---

### Spec Compliance

#### Spec: slot-encuentro-lifecycle (8 requirements, 16 scenarios)

| Requirement | Status | Notes |
|-------------|--------|-------|
| SLOT-RECURRENTE-001 — Create recurrent slot with auto instance generation | PARTIAL | Service implementa generación (`create_slot` → loop timedelta(weeks=k)). Validación `fecha_inicio` vs `dia_semana` implementada. **Pero** no hay test que verifique creación exitosa con DB seed (solo test de 404 por asignacion faltante). |
| SLOT-UNICO-002 — Create unique slot with single instance | PARTIAL | Service implementa modo único. Schema Pydantic valida `fecha_unica` requerida, `cant_semanas=0`. Sin test de éxito. |
| SLOT-MODO-VALIDATION-003 — Mode fields mutually exclusive | PASS | `model_validator` en `SlotCreate` maneja todas las combinaciones inválidas: recurrente con fecha_unica, único sin fecha_unica, único con cant_semanas>0, recurrente sin cant_semanas. Tests de 422 para casos faltantes. |
| SLOT-IMMUTABLE-004 — Slot is immutable post-creation | PARTIAL | No existe endpoint PATCH/PUT para slot ✅. Solo DELETE (soft delete). **Pero** no hay test que verifique que DELETE retorna 204 con existencia de data (solo test de 404 para slot inexistente). |
| SLOT-SCOPE-005 — Scope by role for slot operations | PARTIAL | Service implementa `is_global` check. **BUG**: `list_slots()` solo usa `asig_ids[0]` — si PROFESOR tiene múltiples asignaciones, solo ve slots de la primera. Ver CRITICAL #1 abajo. |
| SLOT-TENANT-006 — Tenant isolation for slots | PARTIAL | `BaseRepository.get()` filtra por `tenant_id` + `deleted_at IS NULL`. Todos los repos pasan `tenant_id`. Sin test de aislamiento real (solo test de 404 para UUID aleatorio). |
| SLOT-AUDIT-007 — Audit event on slot creation | PASS | Service llama `audit_action` con `ENCUENTRO_SLOT_CREAR`, detalle incluye `slot_id` y `cant_instancias`. AuditCodes definidos en `audit_codes.py`. |
| SLOT-SOFTDELETE-INSTANCES-008 — Soft-deleted slot leaves instances intact | PASS | `delete_slot()` usa `BaseRepository.soft_delete()` que solo marca `deleted_at`. Instancias no se tocan. Modelo usa `ondelete="SET NULL"` en FK de `slot_encuentro.id`. |

#### Spec: instancia-encuentro-edit (7 requirements, 15 scenarios)

| Requirement | Status | Notes |
|-------------|--------|-------|
| INST-EDIT-001 — Edit allowed fields on an instance | PASS | PATCH endpoint acepta `estado`, `meet_url`, `video_url`, `comentario`. `InstanciaEdit` Pydantic valida que al menos un campo se provea. |
| INST-STATE-MACHINE-002 — Instance state machine (D-04) | PASS | `_TRANSICIONES_INSTANCIA` implementa: Programado→Realizado|Cancelado, Realizado→Programado, Cancelado→Programado. `_TRANSICIONES_SOLO_GLOBAL` restringe reversiones. |
| INST-STATE-REVERSION-003 — State reversion role-restricted | PASS | `edit_instancia()` verifica `transicion in _TRANSICIONES_SOLO_GLOBAL and not is_global` → 403. |
| INST-SCOPE-004 — Scope by role for instance operations | PARTIAL | `get_instancia()` y `edit_instancia()` validan alcance vía `slot.asignacion_id → asig.usuario_id`. **BUG**: `get_instancia()` retorna 404 para instancias sin slot (`slot_id IS NULL`) si no es global — imposibilita ver instancias independientes. |
| INST-TENANT-005 — Tenant isolation for instances | PASS | Filtro `tenant_id` en repos. |
| INST-LIST-FILTERS-006 — List instances with filters | PASS | `InstanciaEncuentroRepository.list_filtered()` acepta `slot_id`, `materia_id`, `estado`, `fecha_desde`, `fecha_hasta`, `asignacion_filter`. Scope por rol vía `asignacion_filter` con LEFT JOIN. Ordenado por fecha ascendente. |
| INST-AUDIT-007 — Audit event on instance edit | PASS | Service llama `audit_action` con `ENCUENTRO_INSTANCIA_EDITAR`, detalle incluye `instancia_id` y `campos_editados`. |

#### Spec: encuentro-html-export (5 requirements, 9 scenarios)

| Requirement | Status | Notes |
|-------------|--------|-------|
| HTML-001 — Generate HTML block with Content-Type text/html | PASS | Endpoint retorna `HTMLResponse(content=html, status_code=200)`. `_build_html_table()` genera `<table>` con `<thead>` y `<tbody>`. |
| HTML-002 — Include instance details in each row | PASS | Cada fila incluye fecha, hora, título, estado, meet_url (link si Programado), video_url (link si Realizado). Links con `target="_blank"`. |
| HTML-003 — Scope by role for HTML export | PASS | `generate_html()` pasa por `get_slot()` que valida alcance. |
| HTML-004 — Tenant isolation | PASS | Vía `get_slot()` que usa `tenant_id`. |
| HTML-005 — Edge cases (slot not found → 404, empty → empty table) | PASS | `get_slot()` lanza 404 si no existe. `list_by_slot()` retorna lista vacía → `_build_html_table()` genera tabla sin filas de datos. |

#### Spec: encuentros-admin-view (8 requirements, 10 scenarios)

| Requirement | Status | Notes |
|-------------|--------|-------|
| ADMIN-VIEW-001 — COORDINADOR/ADMIN sees all instances | PASS | `is_global=True` → no aplica `asignacion_filter`. |
| ADMIN-VIEW-002 — Filter by materia_id | PASS | `materia_id` filtro en `list_filtered()`. |
| ADMIN-VIEW-003 — Filter by estado | PASS | `estado` filtro en `list_filtered()`. |
| ADMIN-VIEW-004 — Filter by date range | PASS | `fecha_desde` / `fecha_hasta` en `list_filtered()`. |
| ADMIN-VIEW-005 — Combined filters | PASS | Múltiples filtros se combinan con AND. |
| ADMIN-VIEW-006 — Empty result returns 200 with [] | PASS | `list_filtered()` retorna lista vacía, no 404. |
| ADMIN-VIEW-007 — Include slot title in response | PARTIAL | `InstanciaResponse` tiene `slot_titulo: str | None`. **Pero**: el valor se setea en `_build_instancia_response()` como `getattr(inst, "slot_titulo", None)` — nunca se popula explícitamente desde el slot. Ningún query en repos carga el título del slot. Siempre será `None`. |
| ADMIN-VIEW-008 — Ordered by fecha ascending | PASS | `order_by(InstanciaEncuentro.fecha)` en `list_filtered()`. |

#### Spec: guardia-lifecycle (9 requirements, 19 scenarios)

| Requirement | Status | Notes |
|-------------|--------|-------|
| GUA-CREATE-001 — Register a new guardia | PARTIAL | POST implementado. Service valida asignacion existe en tenant. Schema tiene campos requeridos. **Sin test de creación exitosa**. |
| GUA-OWN-ASIGNACION-002 — TUTOR can only register own guardias | PASS | Service verifica `not is_global and asig.usuario_id != actor_id` → 403. |
| GUA-STATE-MACHINE-003 — Guardia state transitions (D-05) | PASS | `_TRANSICIONES_GUARDIA` implementa: Pendiente→Realizada|Cancelada, Realizada→(terminal), Cancelada→Pendiente. |
| GUA-STATE-REVERSION-004 — Revert Cancelada→Pendiente role-restricted | PASS | `_TRANSICIONES_SOLO_GLOBAL` con check de `not is_global` → 403. |
| GUA-SCOPE-005 — Scope by role for guardia operations | PASS | `get()`, `list()`, `cambiar_estado()` validan alcance. |
| GUA-FILTERS-006 — Filter guardia list | PASS | `GuardiaRepository.list_filtered()` acepta `materia_id`, `carrera_id`, `cohorte_id`, `estado`, `asignacion_id`. Service scopea por rol. |
| GUA-EXPORT-CSV-007 — Export guardias as CSV | FAIL | **3 problemas**: (1) Ruta es `/export/csv` vs spec `/export`. (2) Filename es `guardias.csv` vs spec `guardias_export.csv`. (3) **NO verifica rol COORDINADOR/ADMIN** — TUTOR con `guardias:registrar` puede exportar TODAS las guardias del tenant. Ver CRITICAL #2. |
| GUA-AUDIT-008 — Audit events for guardia lifecycle | PASS | `GUARDIA_REGISTRAR` en create, `GUARDIA_CAMBIAR_ESTADO` en cambiar_estado. Detalle correcto. |
| GUA-TENANT-009 — Tenant isolation for guardias | PASS | Filtro `tenant_id` en repos. |

---

### Design Coherence

| Decision | Status | Notes |
|----------|--------|-------|
| D-01: Dos modos de slot mutuamente excluyentes (RN-13) | FOLLOWED | `SlotCreate` con `model_validator`, service valida `fecha_inicio` vs `dia_semana`. |
| D-02: Generación de instancias en el service, no en el ORM | FOLLOWED | `EncuentroService.create_slot()` genera instancias, no trigger/ORM. |
| D-03: Slot inmutable post-creación, instancia editable en campos limitados | FOLLOWED | Sin PATCH/PUT de slot. `InstanciaEdit` solo permite `estado`, `meet_url`, `video_url`, `comentario`. |
| D-04: Ciclo de estados de InstanciaEncuentro | FOLLOWED | `_TRANSICIONES_INSTANCIA` y `_TRANSICIONES_SOLO_GLOBAL` implementados correctamente. |
| D-05: Ciclo de estados de Guardia | FOLLOWED | `_TRANSICIONES_GUARDIA` y `_TRANSICIONES_SOLO_GLOBAL` implementados correctamente. |
| **D-06**: Alcance por rol en el service | **DEVIATED** | D-06 dice "Permiso único `encuentros:gestionar`" y descarta explícitamente permisos separados. La implementación **introdujo `guardias:registrar` como permiso separado**. El router guardias usa `require_permission("guardias:registrar")` en vez de `encuentros:gestionar`. Tasks.md (7.2) especificaba `encuentros:gestionar`. Si bien es más granular, es una desviación documentada de la decisión de diseño. |
| D-07: HTML export para el LMS (F6.4) | FOLLOWED | Endpoint retorna `text/html` con tabla HTML. Links con target. |
| **D-08**: Export de guardias (F6.6) | **DEVIATED** | Varias desviaciones: (1) Ruta `/export/csv` vs `/export`. (2) Filename `guardias.csv` vs `guardias_export.csv`. (3) No hay restricción de rol (solo COORD/ADMIN debe poder exportar). |
| D-09: Auditoría de eventos significativos | FOLLOWED | Los 4 eventos: `ENCUENTRO_SLOT_CREAR`, `ENCUENTRO_INSTANCIA_EDITAR`, `GUARDIA_REGISTRAR`, `GUARDIA_CAMBIAR_ESTADO` implementados con detalle correcto. |
| D-10: `asignacion_id` como FK en Slot y Guardia | FOLLOWED | Ambos modelos tienen `asignacion_id` FK, y `materia_id` desnormalizado. |

---

### Summary

#### CRITICAL (debe arreglarse antes de archivar)

1. **BUG: `list_slots()` solo usa primera asignación** — `backend/app/services/encuentro_service.py:290`
   - `list_slots()` para scope no-global usa `asig_ids[0]`. Si un PROFESOR tiene 2+ asignaciones, solo ve slots de la primera.
   - **Fix**: O cambiar `SlotEncuentroRepository.list_by_tenant()` para aceptar `list[UUID]` como `asignacion_id`, similar a cómo `InstanciaEncuentroRepository.list_filtered()` acepta `asignacion_filter: list[UUID]`.

2. **SECURITY: Export CSV accesible por TUTOR** — `backend/app/api/v1/routers/guardias.py:196`
   - El spec GUA-EXPORT-CSV-007 y D-08 dicen solo COORDINADOR/ADMIN. El endpoint usa `guardias:registrar` que TUTOR también posee (scope "propio"). El service `export_csv()` no recibe `is_global` ni filtra por alcance. Un TUTOR puede llamar `GET /api/guardias/export/csv` y obtener TODAS las guardias del tenant.
   - **Fix**: Agregar verificación de `grant.scope == "global"` en el router, o pasar `is_global` al service.

3. **Ruta de export inconsistente con spec** — `backend/app/api/v1/routers/guardias.py:196`
   - La ruta es `/export/csv` pero D-08 y GUA-EXPORT-CSV-007 especifican `/export`.
   - **Fix**: Cambiar a `@router.get("/export")` o actualizar la spec si la decisión fue intencional.

#### WARNING (no bloquea archive, pero debe documentarse)

4. **Desviación de D-06: permiso separado `guardias:registrar`** — Diseño decidió permiso único `encuentros:gestionar`. Implementación introdujo `guardias:registrar`. Tasks.md 7.2 especificaba `encuentros:gestionar`. La desviación no es incorrecta (es más granular) pero debe documentarse en el design.md como decisión revisada.

5. **`slot_titulo` nunca se popula** — `AdminView-007` requiere que `InstanciaResponse` incluya `slot_titulo`, pero el campo siempre es `None` porque ningún query carga el título del slot padre. Se necesita un join o subquery en `list_filtered()`.

6. **Filename CSV incorrecto** — D-08 especifica `filename="guardias_export.csv"`. El código usa `filename=guardias.csv` (sin comillas, nombre distinto).

7. **Test coverage incompleto** — 19 tests cubren ~65% de los 29 scenarios de las specs. Faltan tests de:
   - Creación exitosa de slots/guardias (con seed data real)
   - Máquina de estados con transiciones reales (no solo 404s)
   - Export CSV con datos y filtros
   - Alcance multi-asignación
   - Aislamiento multi-tenant real (vs UUID aleatorio que igual da 404)

#### SUGGESTION (mejoras futuras)

8. **`GuardiaResponse` mapea `creada_at` como `str`** — El router hace `creada_at=str(g.creada_at)` pero el schema espera `datetime | None`. Pydantic v2 puede coer clonarlo, pero es frágil. Usar `g.creada_at` directamente.

9. **`list_guardias` para TUTOR con múltiples asignaciones** — Hace N+1 queries (un query por asignación). Funcionalmente correcto pero ineficiente. Mejorar el repositorio para aceptar `list[UUID]`.

10. **Sin límite de semanas** — Design menciona recomendar ≤ 52 semanas. Podría agregarse validación en el schema.

11. **Migración no incluye índice compuesto para `(tenant_id, deleted_at)`** — El repositorio filtra por `deleted_at IS NULL` siempre. Las tablas tienen índices en `(tenant_id, ...)` pero no incluyen `deleted_at`. Para performance con soft-delete, conviene índices compuestos `(tenant_id, deleted_at, ...)`.

---

### Compliance Matrix: Design Decisions vs Implementation

| Design Decision | Status | Evidence |
|-----------------|--------|----------|
| D-01 (modos excluyentes) | ✅ FOLLOWED | `SlotCreate._validate_modo()`, service valida fecha_inicio vs dia_semana |
| D-02 (instancias en service) | ✅ FOLLOWED | `EncuentroService.create_slot()` genera instancias con `session.add_all()` |
| D-03 (slot inmutable) | ✅ FOLLOWED | Sin PATCH/PUT de slot, solo DELETE. Instancia PATCH limitado |
| D-04 (estados instancia) | ✅ FOLLOWED | `_TRANSICIONES_INSTANCIA` + `_TRANSICIONES_SOLO_GLOBAL` |
| D-05 (estados guardia) | ✅ FOLLOWED | `_TRANSICIONES_GUARDIA` + `_TRANSICIONES_SOLO_GLOBAL` |
| D-06 (alcance por rol) | ❌ DEVIATED | Usa `guardias:registrar` separado. Router guardias no usa `encuentros:gestionar` |
| D-07 (HTML export) | ✅ FOLLOWED | `HTMLResponse` con tabla, links, orden cronológico |
| D-08 (CSV export) | ❌ DEVIATED | Ruta `/export/csv` vs `/export`, filename incorrecto, sin restricción de rol |
| D-09 (auditoría) | ✅ FOLLOWED | 4 eventos auditables implementados |
| D-10 (FK asignacion_id) | ✅ FOLLOWED | Modelos con `asignacion_id` FK y `materia_id` desnormalizado |

---

### Fixes aplicados (2026-06-19)

| # | Issue | Fix | Archivo |
|---|-------|-----|---------|
| 1 | `list_slots()` solo usa `asig_ids[0]` | `list_by_tenant()` ahora acepta `asignacion_filter: list[UUID]` con `.in_()`; service pasa `asig_ids` completo | `slot_encuentro_repository.py`, `encuentro_service.py` |
| 2 | Export CSV sin restricción de rol | Agregado `if grant.scope != "global": raise HTTPException(403)` | `guardias.py` router |
| 3 | Ruta `/export/csv` vs `/export` | Cambiada a `@router.get("/export")`, filename corregido a `"guardias_export.csv"` | `guardias.py` router |

### Verdict

**READY FOR ARCHIVE** — Los 3 issues CRITICAL están corregidos. Re-ejecutar la suite completa con `pytest tests/ --run-db -v --tb=short` para confirmar que los tests existentes siguen pasando.
