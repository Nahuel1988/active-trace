# Tasks — C-10 calificaciones-y-umbral

> Governance: MEDIO — implementar con checkpoints; surfacear decisiones no obvias.
> Strict TDD obligatorio (RED → GREEN → TRIANGULATE → REFACTOR).
> Cobertura: ≥80% líneas, ≥90% reglas de negocio (derivación aprobado, aislamiento por usuario, umbral por asignación).
> Tests SIN mock de DB (contenedor efímero). Schemas con `extra='forbid'`. snake_case.
> Migración 009: tablas `calificacion`, `umbral_materia`, índices.
> Permisos nuevos: `calificaciones:importar`, `calificaciones:configurar-umbral`, `calificaciones:vaciar` → seed en `rbac_seed.py`, asignar a PROFESOR y COORDINADOR.
> Multi-tenancy: `tenant_id` en ambas tablas; todos los queries filtran por tenant del JWT.
> Depende de C-09 (`EntradaPadron`, `VersionPadron`) — no modifica sus contratos. Implementación bloqueada hasta que C-09 esté completo.

---

## 1. Permisos RBAC

- [x] 1.1 Agregar `calificaciones:importar`, `calificaciones:configurar-umbral` y `calificaciones:vaciar` a la lista de permisos en `backend/app/core/rbac_seed.py`.
- [x] 1.2 Asignar `calificaciones:importar` a PROFESOR (scope propio) y COORDINADOR (scope global) en el seed de `rol_permiso`.
- [x] 1.3 Asignar `calificaciones:configurar-umbral` a PROFESOR (scope propio) y COORDINADOR (scope global).
- [x] 1.4 Asignar `calificaciones:vaciar` a PROFESOR (scope propio) y COORDINADOR (scope global).

## 2. Schemas Pydantic (`app/schemas/calificacion.py`)

- [x] 2.1 RED: test que `CalificacionCreate` rechaza campos extra (`extra='forbid'`), acepta `nota_numerica` nullable y `nota_textual` nullable, pero rechaza ambos nulos.
- [x] 2.2 GREEN+REFACTOR: definir `CalificacionCreate(entrada_padron_id, materia_id, actividad, nota_numerica=None, nota_textual=None, origen=OrigenCalificacion.IMPORTADO)`; con validator que exige al menos uno de los dos campos de nota.
- [x] 2.3 RED: tests de `PreviewResponse` (columnas_detectadas con clasificación numérica/textual/ignorada, total_filas, muestra_primeras_3, errores[]), `ConfirmarImportRequest` (materia_id, actividades_seleccionadas: list[str]).
- [x] 2.4 GREEN+REFACTOR: schemas de preview y confirm request/response.
- [x] 2.5 RED: tests de `CalificacionResponse` (id, entrada_padron_id, actividad, nota_numerica, nota_textual, aprobado, origen, creado_por, creada_at).
- [x] 2.6 GREEN+REFACTOR: `CalificacionResponse` incorpora campo `aprobado: bool` derivado (no almacenado).
- [x] 2.7 RED: tests de `UmbralMateriaCreate` (umbral_pct: int 0-100, valores_aprobatorios: list[str] opcional) y `UmbralMateriaResponse`.
- [x] 2.8 GREEN+REFACTOR: schemas de umbral con `extra='forbid'` y validación de rango 0-100.
- [x] 2.9 RED: tests de `ReporteFinalizacionResponse` (items: list[EntregaSinCalificar]) y `VaciarRequest` (materia_id).
- [x] 2.10 GREEN+REFACTOR: schemas de reporte y vaciado.

## 3. Modelos ORM (`app/models/calificacion.py`)

- [x] 3.1 RED: test que `Calificacion` tiene mixin base (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`, `deleted_by`), FK a `entrada_padron.id` y `materia.id`, campos `nota_numerica` (nullable), `nota_textual` (nullable), `origen` (enum), `creado_por` FK a `usuario.id`.
- [x] 3.2 GREEN: crear `Calificacion` con columnas: `tenant_id`, `entrada_padron_id` (FK → entrada_padron), `materia_id` (FK → materia), `actividad` (text), `nota_numerica` (Decimal, nullable), `nota_textual` (text, nullable), `origen` (Enum: importado | manual), `creado_por` (FK → usuario). Soft-delete fields: `deleted_at`, `deleted_by`. Índices compuestos: `(tenant_id, materia_id, creado_por)`, `(tenant_id, entrada_padron_id)`.
- [x] 3.3 RED: test que `Calificacion` NO tiene campo `aprobado` almacenado (se deriva en read-time).
- [x] 3.4 GREEN+REFACTOR: verificar que `Calificacion` no incluye columna `aprobado`.
- [x] 3.5 RED: test que `UmbralMateria` tiene FK a `asignacion.id` y `materia.id`, campo `umbral_pct` con default 60, campo `valores_aprobatorios` como JSONB.
- [x] 3.6 GREEN: crear `UmbralMateria` con columnas: `tenant_id`, `asignacion_id` (FK → asignacion), `materia_id` (FK → materia), `umbral_pct` (Integer, default 60), `valores_aprobatorios` (JSONB, default lista del tenant). Índice compuesto `(tenant_id, asignacion_id)`.
- [x] 3.7 RED: test que `UmbralMateria (asignacion_id, materia_id)` tiene unique constraint scoped al tenant.
- [x] 3.8 GREEN+REFACTOR: agregar `UniqueConstraint(tenant_id, asignacion_id, materia_id)`.
- [x] 3.9 RED: test que `Calificacion` y `UmbralMateria` tienen `__repr__` seguro (sin PII ni datos sensibles).
- [x] 3.10 GREEN+REFACTOR: implementar `__repr__` en ambos modelos.
- [x] 3.11 Registrar ambos modelos en `app/models/__init__.py`.

## 4. Migración Alembic 009

- [x] 4.1 Crear migración `009_calificacion_umbral_materia.py` manualmente con:
  1. Tabla `calificacion` con FKs hacia `entrada_padron`, `materia` y `usuario` (creado_por).
  2. Tabla `umbral_materia` con FK hacia `asignacion` y `materia`.
  3. Índices compuestos según diseño.
  4. Unique constraint `(tenant_id, asignacion_id, materia_id)` en `umbral_materia`.
- [x] 4.2 Revisar migración: confirmar FKs, enums correctos y defaults.
- [x] 4.3 Verificar migración contra DB de test al ejecutar `pytest` (vía `_head_check.py`): `009_calificacion_umbral_materia` es el nuevo head único.

## 5. CalificacionRepository (`app/repositories/calificacion_repository.py`)

- [x] 5.1 RED: test `get_by_materia_y_usuario` devuelve calificaciones para `(tenant_id, materia_id, creado_por)` excluyendo soft-delete.
- [x] 5.2 GREEN+TRIANGULATE: implementar `CalificacionRepository.get_by_materia_y_usuario`; casos: con datos, sin datos, otro tenant excluido, soft-deleted excluidas.
- [x] 5.3 RED: test `bulk_create` inserta N calificaciones en una transacción y devuelve los IDs creados.
- [x] 5.4 GREEN+TRIANGULATE: implementar `bulk_create` con inserción batch; caso lista vacía → OK sin insertar.
- [x] 5.5 RED: test `soft_delete_by_materia_y_usuario` marca `deleted_at` y `deleted_by` para `(tenant_id, materia_id, creado_por)`.
- [x] 5.6 GREEN+TRIANGULATE: implementar `soft_delete_by_materia_y_usuario`; caso sin registros → OK (0 afectados).
- [x] 5.7 RED: test `get_by_entrada_padron` devuelve calificaciones de un alumno para una materia.
- [x] 5.8 GREEN+TRIANGULATE: implementar `get_by_entrada_padron` para cruce con reporte de finalización.

## 6. UmbralRepository (`app/repositories/umbral_repository.py`)

- [x] 6.1 RED: test `get_by_asignacion` devuelve `UmbralMateria` para una `(tenant_id, asignacion_id)`, o `None` si no existe.
- [x] 6.2 GREEN+TRIANGULATE: implementar `UmbralRepository.get_by_asignacion`; caso existe, no existe, otro tenant excluido.
- [x] 6.3 RED: test `upsert` crea o actualiza `UmbralMateria` para `(tenant_id, asignacion_id, materia_id)`.
- [x] 6.4 GREEN+TRIANGULATE: implementar `upsert` con PostgreSQL `ON CONFLICT`; caso crear nuevo, caso actualizar existente.

## 7. CalificacionService — preview y detección de columnas

- [x] 7.1 RED: test `preview_archivo` parsea `.xlsx`/`.csv` válido, detecta columnas numéricas (cabeceras `(Real)`) y textuales, devuelve `PreviewResponse`.
- [x] 7.2 GREEN: implementar `CalificacionService.preview_archivo` con lógica de clasificación de columnas (D-04).
- [x] 7.3 TRIANGULATE: archivo sin columnas reconocibles → error 422; archivo vacío → 0 filas con columnas detectadas; formato no soportado → error 422.
- [x] 7.4 REFACTOR: extraer lógica de clasificación de columnas a método `_clasificar_columnas`.

## 8. CalificacionService — confirmar importación

- [x] 8.1 RED: test `confirmar_importacion` con `actividades_seleccionadas` crea calificaciones en bulk con `origen=Importado`, `creado_por=actor_id`, y audita `CALIFICACIONES_IMPORTAR`.
- [x] 8.2 GREEN: implementar `confirmar_importacion(tenant_id, materia_id, archivo_parseado, actividades_seleccionadas, actor_id, auditor)`.
- [x] 8.3 TRIANGULATE: actividad seleccionada no existe en el archivo → error 422; materia de otro tenant → 404; actor sin asignación a la materia → 403; más de `MAX_CALIFICACIONES_IMPORT` (5000) → 413.
- [x] 8.4 TRIANGULATE: reimportación de mismas actividades → se crean duplicados (no hay upsert); usuario puede vaciar antes de reimportar.
- [x] 8.5 REFACTOR: asegurar que `tenant_id` y `creado_por` se setean correctamente en cada calificación.

## 9. CalificacionService — reporte de finalización (F1.2)

- [x] 9.1 RED: test `reporte_finalizacion` cruza archivo de finalización contra calificaciones existentes, detecta actividades textuales finalizadas sin calificar.
- [x] 9.2 GREEN: implementar `reporte_finalizacion(tenant_id, materia_id, archivo, actor_id)` — parsea archivo, filtra solo actividades textuales (RN-08), cruza contra `get_by_entrada_padron`, devuelve items no calificados.
- [x] 9.3 TRIANGULATE: todas las actividades ya calificadas → lista vacía; archivo sin actividades textuales → lista vacía; archivo sin actividades finalizadas → lista vacía; no hay calificaciones previas → todas las actividades textuales finalizadas aparecen como sin corregir.

## 10. CalificacionService — aprobado derivado

- [x] 10.1 RED: test `compute_aprobado` con `nota_numerica >= umbral_pct` devuelve `true`; con `nota_numerica < umbral_pct` devuelve `false`.
- [x] 10.2 GREEN: implementar `_compute_aprobado(calificacion, umbral: UmbralMateria | None) → bool`.
- [x] 10.3 TRIANGULATE: nota textual en `valores_aprobatorios` → `true`; nota textual NO en `valores_aprobatorios` → `false`; sin umbral configurado → usa defaults (60, catálogo del tenant); cambio de umbral afecta resultado retrospectivamente.
- [x] 10.4 REFACTOR: integrar `_compute_aprobado` en los métodos de lectura del service (`get_calificaciones`).

## 11. CalificacionService — vaciar (F1.5, RN-04)

- [x] 11.1 RED: test `vaciar_materia` soft-deletea calificaciones del `(actor_id, materia_id)`, preserva datos de otros docentes, audita `CALIFICACIONES_IMPORTAR`.
- [x] 11.2 GREEN: implementar `vaciar_materia(tenant_id, materia_id, actor_id, auditor)` — ejecuta `soft_delete_by_materia_y_usuario`.
- [x] 11.3 TRIANGULATE: materia de otro tenant → 404; actor sin asignación a la materia → 403; doble vaciado (ya vaciado) → 204 (0 afectados).

## 12. UmbralService — leer y configurar (F2.1)

- [x] 12.1 RED: test `get_umbral` devuelve `UmbralMateria` si existe, o defaults si no existe (sin crear registro).
- [x] 12.2 GREEN: implementar `UmbralService.get_umbral(tenant_id, asignacion_id)`.
- [x] 12.3 RED: test `configurar_umbral` crea o actualiza `UmbralMateria`, audita `CALIFICACIONES_IMPORTAR`.
- [x] 12.4 GREEN: implementar `configurar_umbral(tenant_id, asignacion_id, materia_id, umbral_pct, valores_aprobatorios, auditor)`.
- [x] 12.5 TRIANGULATE: umbral_pct fuera de rango 0-100 → error 422; asignación vencida → 403; asignación de otro tenant → 404.

## 13. Router (`app/api/v1/routers/calificaciones.py`)

- [x] 13.1 RED: test `POST /calificaciones/preview` 200 con archivo válido; 422 sin archivo; 403 sin permiso `calificaciones:importar`.
- [x] 13.2 GREEN: endpoint `POST /calificaciones/preview` con `UploadFile`, guard `require_permission("calificaciones:importar")`.
- [x] 13.3 RED: test `POST /calificaciones/confirmar` 201 con resumen de importación; 422 datos inválidos; 403 sin permiso.
- [x] 13.4 GREEN: endpoint `POST /calificaciones/confirmar` con body `ConfirmarImportRequest`.
- [x] 13.5 RED: test `POST /calificaciones/reporte-finalizacion` 200 con listado de entregas sin corregir; 403 sin permiso.
- [x] 13.6 GREEN: endpoint `POST /calificaciones/reporte-finalizacion` con `UploadFile`.
- [x] 13.7 RED: test `GET /calificaciones` 200 lista calificaciones del usuario para una materia; 403 sin permiso.
- [x] 13.8 GREEN: endpoint `GET /calificaciones?materia_id=X` con `aprobado` computado.
- [x] 13.9 RED: test `GET /calificaciones/umbral` 200 con umbral configurado o defaults.
- [x] 13.10 GREEN: endpoint `GET /calificaciones/umbral?materia_id=X`.
- [x] 13.11 RED: test `PUT /calificaciones/umbral` 200 umbral actualizado; 422 valores inválidos; 403 sin permiso `calificaciones:configurar-umbral`.
- [x] 13.12 GREEN: endpoint `PUT /calificaciones/umbral` con body `UmbralMateriaCreate`.
- [x] 13.13 RED: test `POST /calificaciones/vaciar` 204 sin contenido; 403 sin permiso `calificaciones:vaciar`.
- [x] 13.14 GREEN: endpoint `POST /calificaciones/vaciar` con body `VaciarRequest`.
- [x] 13.15 Registrar router en `app/main.py`: prefijo `/api/v1/calificaciones`, tag `calificaciones`. Mapear `CalificacionError` a `HTTPException`.
- [x] 13.16 REFACTOR: verificar archivo <500 LOC.

## 14. Tests — integración y aislamiento

- [x] 14.1 **Safety net**: ejecutar suite existente antes de tocar código. Capturar baseline (N tests pasando). Fallos preexistentes → reportar, NO corregir acá.
- [x] 14.2 Crear `backend/tests/test_calificaciones_import.py` (carga por archivo E2E):
  - RED: `test_preview_y_confirmar_carga_completa` (subir .csv → preview → confirm → 201 con calificaciones creadas).
  - TRIANGULAR: `test_preview_archivo_formato_invalido_422`, `test_confirmar_actividad_inexistente_422`, `test_confirmar_max_filas_excedido_413`, `test_import_con_notas_numericas_y_textuales`.
- [x] 14.3 Crear `backend/tests/test_calificaciones_aprobado.py` (derivación RN-01, RN-02, RN-03):
  - RED: `test_aprobado_numerico_supera_umbral_true`, `test_aprobado_numerico_no_supera_umbral_false`.
  - TRIANGULAR: `test_aprobado_textual_en_valores_true`, `test_aprobado_textual_fuera_de_valores_false`, `test_aprobado_cambio_umbral_retroactivo`, `test_aprobado_sin_umbral_configurado_usa_default`.
- [x] 14.4 Crear `backend/tests/test_calificaciones_reporte_finalizacion.py`:
  - RED: `test_reporte_detecta_entregas_sin_calificar`, `test_reporte_todo_calificado_lista_vacia`.
  - TRIANGULAR: `test_reporte_solo_actividades_textuales_RN08`, `test_reporte_sin_calificaciones_previas`.
- [x] 14.5 Crear `backend/tests/test_calificaciones_umbral.py`:
  - RED: `test_configurar_umbral_numerico`, `test_leer_umbral_sin_configuracion_devuelve_defaults`.
  - TRIANGULAR: `test_configurar_umbral_fuera_rango_422`, `test_umbral_independiente_por_asignacion`, `test_umbral_asignacion_vencida_403`.
- [x] 14.6 Crear `backend/tests/test_calificaciones_vaciar.py`:
  - RED: `test_vaciar_calificaciones_propias`, `test_vaciar_no_afecta_otro_docente`.
  - TRIANGULAR: `test_vaciar_sin_calificaciones_204`, `test_vaciar_materia_otro_tenant_404`, `test_doble_vaciado_204`.
- [x] 14.7 Crear `backend/tests/test_calificaciones_aislamiento.py` (multi-tenant):
  - RED: `test_calificaciones_aislamiento_tenant` (calificaciones de tenant A invisibles para tenant B).
  - TRIANGULAR: `test_umbral_aislamiento_tenant`, `test_vaciar_solo_propio_tenant`, `test_sin_permiso_calificaciones_403`.

## 15. Verificación final

- [x] 15.1 Ejecutar suite completa: `pytest backend/tests/ -v --tb=short`. Todos los tests de C-10 pasan; ningún test previo se rompe.
- [x] 15.2 Verificar cobertura: `pytest backend/tests/ --cov=backend/app --cov-report=term-missing`. ≥80% líneas global; ≥90% en reglas de negocio (derivación aprobado, aislamiento por usuario, umbral por asignación).
- [x] 15.3 Confirmar que ningún test mockea la DB (contenedor efímero) y que todos los schemas usan `extra='forbid'`.
- [x] 15.4 Confirmar que C-09 (`EntradaPadron`, `VersionPadron`) quedó intacto (sin modificación de schema, solo tablas nuevas en migración 009).
- [x] 15.5 Marcar `[x]` C-10 en CHANGES.md.
