# Tasks — C-09 padron-ingesta-moodle

> Governance: MEDIO — implementar con checkpoints; surfacear decisiones no obvias.
> Strict TDD obligatorio (RED → GREEN → TRIANGULATE → REFACTOR).
> Cobertura: ≥80% líneas, ≥90% reglas de negocio (invariante versión activa, cifrado email, aislamiento multi-tenant).
> Tests SIN mock de DB (contenedor de test efímero). Schemas con `extra='forbid'`. snake_case.
> Migración 008: tablas `version_padron`, `entrada_padron`, índices, constraint parcial `UNIQUE (tenant_id, materia_id, cohorte_id) WHERE activa = true`.
> Permisos nuevos: `padron:cargar`, `padron:vaciar` → seed en `rbac_seed.py`, asignar a PROFESOR y COORDINADOR.
> PII: `EntradaPadron.email` cifrado AES-256 vía `app/core/crypto.py` (C-02). Nunca en texto plano en logs.
> Multi-tenancy: `tenant_id` en ambas tablas; todos los queries filtran por tenant del JWT.
> Depende de C-06 (`Materia`, `Cohorte`) y C-07 (`Usuario`, `Asignacion`) — no modifica sus contratos.

---

## 1. Permisos RBAC

- [ ] 1.1 Agregar `padron:cargar` y `padron:vaciar` a la lista de permisos en `backend/app/core/rbac_seed.py`.
- [ ] 1.2 Asignar `padron:cargar` a PROFESOR (scope propio) y COORDINADOR (scope global) en el seed de `rol_permiso`.
- [ ] 1.3 Asignar `padron:vaciar` a PROFESOR (scope propio) y COORDINADOR (scope global) en el seed de `rol_permiso`.

## 2. Schemas Pydantic (`app/schemas/padron.py`)

- [ ] 2.1 RED: test que `EntradaPadronCreate` rechaza campos extra (`extra='forbid'`), valida formato email, y acepta `usuario_id` nullable.
- [ ] 2.2 GREEN+REFACTOR: definir `EntradaPadronCreate(nombre, apellidos, email, comision, regional, usuario_id=None)`.
- [ ] 2.3 RED: tests de `PreviewResponse` (total_filas, columnas_detectadas, muestra_primeras_5, errores[]) y `ConfirmarRequest` (materia_id, cohorte_id, entradas: list[EntradaPadronCreate]).
- [ ] 2.4 GREEN+REFACTOR: schemas de preview y confirm request/response.
- [ ] 2.5 RED: tests de `VersionPadronResponse` (id, materia_id, cohorte_id, activa, total_entradas, creada_at) y `VaciarRequest` (materia_id).
- [ ] 2.6 GREEN+REFACTOR: schemas de versión y vaciado con `extra='forbid'`.
- [ ] 2.7 RED: tests de `MoodleSyncResponse` (versión creada, total_sincronizadas, errores[]).
- [ ] 2.8 GREEN+REFACTOR: schema de respuesta de sync Moodle.

## 3. Modelos ORM (`app/models/padron.py`)

- [ ] 3.1 RED: test que `VersionPadron` tiene mixin base (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`), FK a `materia.id` y `cohorte.id`, campo `activa: bool`.
- [ ] 3.2 GREEN: crear `VersionPadron` con columnas: `tenant_id`, `materia_id` (FK), `cohorte_id` (FK), `activa` (default True), `total_entradas` (Integer, default 0), `origen` (Enum: archivo | moodle | manual), `created_at`, `updated_at`, `deleted_at`. Índice compuesto `(tenant_id, materia_id, cohorte_id)`.
- [ ] 3.3 RED: test que `EntradaPadron` tiene FK a `version_padron.id`, email cifrado (no texto plano en DB), `usuario_id` nullable, y FK opcional a `usuario.id`.
- [ ] 3.4 GREEN: crear `EntradaPadron` con columnas: `tenant_id`, `version_padron_id` (FK), `nombre`, `apellidos`, `email` (cifrado AES-256), `comision`, `regional` nullable, `usuario_id` (FK → `usuario.id`, nullable). Índices: `(tenant_id, version_padron_id)`, `(tenant_id, email)`.
- [ ] 3.5 RED: test que `EntradaPadron.__repr__` NO incluye el email en texto plano (solo `id`, `nombre`, `apellidos`).
- [ ] 3.6 GREEN+REFACTOR: implementar `__repr__` seguro; ocultar campo cifrado.
- [ ] 3.7 Registrar ambos modelos en `app/models/__init__.py`.

## 4. Migración Alembic 008

- [ ] 4.1 Crear migración `008_version_padron_entrada_padron.py` manualmente con:
  1. Tabla `version_padron` con FKs hacia `materia` y `cohorte`.
  2. Tabla `entrada_padron` con FK hacia `version_padron` y FK nullable hacia `usuario`.
  3. Índice parcial `UNIQUE (tenant_id, materia_id, cohorte_id) WHERE activa = true` para invariante de versión activa.
  4. Índices compuestos adicionales según diseño.
- [ ] 4.2 Revisar migración: confirmar FKs, constraint parcial, enums correctos y defaults.
- [ ] 4.3 Verificar migración contra DB de test al ejecutar `pytest` (vía `Base.metadata.create_all`).

## 5. Repository (`app/repositories/padron_repository.py`)

- [ ] 5.1 RED: test `get_version_activa` devuelve la versión con `activa=true` para `(tenant_id, materia_id, cohorte_id)`, o `None` si no existe.
- [ ] 5.2 GREEN+TRIANGULATE: implementar `PadronRepository.get_version_activa`; casos: existe activa, no existe ninguna, activa de otro tenant excluida, soft-deleted excluida.
- [ ] 5.3 RED: test `get_entradas_by_version` devuelve todas las entradas de una versión scoped al tenant; emails desencriptados.
- [ ] 5.4 GREEN+TRIANGULATE: implementar `get_entradas_by_version` con desencriptado de email; caso versión sin entradas → lista vacía; otro tenant excluido.
- [ ] 5.5 RED: test `bulk_insert_entradas` inserta N entradas en una transacción y devuelve los IDs creados.
- [ ] 5.6 GREEN+TRIANGULATE: implementar `bulk_insert_entradas` con cifrado de email; caso lista vacía → OK sin insertar; caso email repetido dentro del batch.
- [ ] 5.7 RED: test `desactivar_version` marca `activa=false` para la versión activa de la tupla; no afecta versiones de otras tuplas.
- [ ] 5.8 GREEN+TRIANGULATE: implementar `desactivar_version`; caso no hay activa → no-op; otro tenant intacto.
- [ ] 5.9 RED: test `activar_version` crea nueva versión como activa (desactivando la anterior si existe).
- [ ] 5.10 GREEN+TRIANGULATE: implementar `activar_version` en una transacción (desactivar anterior + crear nueva); caso primera versión → sin desactivar.
- [ ] 5.11 RED: test `soft_delete_version` marca `deleted_at` en la versión activa (vaciar); entradas preservadas.
- [ ] 5.12 GREEN+TRIANGULATE: implementar `soft_delete_version`; caso no hay activa → error 404; soft-delete ya existente → error 409; otro tenant excluido.

## 6. PadronService — preview (`app/services/padron_service.py`)

- [ ] 6.1 RED: test `preview_archivo` parsea `.xlsx`/`.csv` válido, devuelve `PreviewResponse` con total_filas, columnas detectadas y muestra.
- [ ] 6.2 GREEN: implementar `preview_archivo` reusando util de parseo; valida columnas requeridas (`nombre`, `apellidos`, `email`, `comision`).
- [ ] 6.3 TRIANGULATE: archivo sin columnas requeridas → errores de validación por columna; archivo vacío → 0 filas; formato no soportado → error 422.
- [ ] 6.4 REFACTOR: extraer lógica de parseo a método interno `_parse_archivo` sin cambiar comportamiento.

## 7. PadronService — confirmar carga

- [ ] 7.1 RED: test `confirmar_carga` crea nueva versión activa, inserta N entradas, desactiva versión anterior, audita `PADRON_CARGAR` con `filas_afectadas=N`.
- [ ] 7.2 GREEN: implementar `confirmar_carga(tenant_id, materia_id, cohorte_id, entradas, auditor)` — llama a `activar_version` + `bulk_insert_entradas` en transacción.
- [ ] 7.3 TRIANGULATE: materia/cohorte no existen o son de otro tenant → 404 sin tocar datos; más de `MAX_PADRON_ROWS` (2000) → error 413; versión anterior queda preservada (no borrada); email repetido en la misma carga se inserta igual (no hay UK por email).
- [ ] 7.4 REFACTOR: asegurar que `entradas` se insertan con `tenant_id` y `version_padron_id` correctos.

## 8. PadronService — sync Moodle

- [ ] 8.1 RED: test `sync_moodle` llama al cliente Moodle WS, procesa respuesta, crea versión con `origen='moodle'`, audita `PADRON_CARGAR`.
- [ ] 8.2 GREEN: implementar `sync_moodle(tenant_id, materia_id, cohorte_id, auditor)` — llama `MoodleWsClient.get_padron()`, mapea columnas, delega a `confirmar_carga`.
- [ ] 8.3 TRIANGULATE: Moodle WS no disponible → error `503 MoodleUnavailable` sin crear versión ni entradas; Moodle devuelve lista vacía → versión con 0 entradas; tenant sin Moodle configurado → 503 con mensaje claro.

## 9. PadronService — vaciar (F1.5, RN-04)

- [ ] 9.1 RED: test `vaciar_materia` marca versión activa como soft-delete, preserva entradas, audita `PADRON_VACIAR`, scoped al `(actor_id, materia_id)`.
- [ ] 9.2 GREEN: implementar `vaciar_materia(tenant_id, materia_id, actor_id, auditor)` — valida que `actor_id` tenga asignación vigente a `materia_id` (o COORDINADOR), ejecuta `soft_delete_version`.
- [ ] 9.3 TRIANGULATE: materia sin versión activa → error 404; actor sin asignación a la materia → error 403 (fail-closed); vaciado no afecta otras materias ni otros tenants.
- [ ] 9.4 TRIANGULATE: doble vaciado sobre misma materia → error 409 (ya vaciada, no hay versión activa que desactivar).

## 10. Integración Moodle WS (`app/integrations/moodle_ws.py`)

- [ ] 10.1 RED: test que `MoodleWsClient` se configura con `MOODLE_URL` y `MOODLE_TOKEN` del entorno.
- [ ] 10.2 GREEN: implementar `MoodleWsClient.__init__` con lectura de entorno.
- [ ] 10.3 RED: test `get_padron(materia_id, cohorte_id)` retorna lista de dicts con keys `nombre, apellidos, email, comision, regional` mapeadas desde el WS de Moodle.
- [ ] 10.4 GREEN: implementar `get_padron` con HTTP GET asíncrono a Moodle WS; mapeo de columnas.
- [ ] 10.5 TRIANGULATE: error de red → `MoodleWsError(502, detail)`; Moodle devuelve error → `MoodleWsError(status_code, detail)`; timeout → `MoodleWsError(504)`; response OK pero columnas faltantes → error de mapeo.
- [ ] 10.6 REFACTOR: extraer lógica de mapeo de columnas y manejo de errores.

## 11. Router (`app/api/v1/routers/padron.py`)

- [ ] 11.1 RED: test `POST /padron/preview` 200 con archivo válido; 422 sin archivo; 403 sin permiso `padron:cargar`.
- [ ] 11.2 GREEN: endpoint `POST /padron/preview` con `UploadFile`, guard `require_permission("padron:cargar")`, propaga IP/user_agent al audit.
- [ ] 11.3 RED: test `POST /padron/confirmar` 201 con resumen de carga; 422 entradas inválidas; 403 sin permiso.
- [ ] 11.4 GREEN: endpoint `POST /padron/confirmar` con body `ConfirmarRequest`.
- [ ] 11.5 RED: test `POST /padron/sync-moodle` 201 con resultado de sync; 503 Moodle no disponible; 403 sin permiso.
- [ ] 11.6 GREEN: endpoint `POST /padron/sync-moodle` con query params `materia_id`, `cohorte_id`.
- [ ] 11.7 RED: test `POST /padron/vaciar` 204 sin contenido; 403 sin permiso `padron:vaciar`; 404 materia sin padrón.
- [ ] 11.8 GREEN: endpoint `POST /padron/vaciar` con body `VaciarRequest`.
- [ ] 11.9 RED: test `GET /padron/versiones` 200 lista versiones del tenant; filtra por `materia_id`, `cohorte_id`; 403 sin permiso.
- [ ] 11.10 GREEN: endpoint `GET /padron/versiones` con query params opcionales.
- [ ] 11.11 Registrar router en `app/main.py`: prefijo `/api/v1/padron`, tag `padrón`. Mapear `PadronError` a `HTTPException`.
- [ ] 11.12 REFACTOR: verificar archivo <500 LOC.

## 12. Tests — integración y aislamiento

- [ ] 12.1 **Safety net**: ejecutar suite existente antes de tocar código. Capturar baseline (N tests pasando). Fallos preexistentes → reportar, NO corregir acá.
- [ ] 12.2 Crear `backend/tests/test_padron_import.py` (carga por archivo E2E):
  - RED: `test_preview_y_confirmar_carga_completa` (subir .csv → preview → confirmar → 201 con entradas creadas).
  - TRIANGULAR: `test_preview_archivo_formato_invalido_422`, `test_confirmar_sin_preview_ok` (confirm directo con datos), `test_confirmar_max_filas_excedido_413`.
- [ ] 12.3 Crear `backend/tests/test_padron_version_activa.py` (invariante D-01):
  - RED: `test_activar_nueva_version_desactiva_anterior` (segunda carga → activa anterior=false).
  - TRIANGULAR: `test_primera_version_activa_sin_previa` (sin versión previa → activa ok), `test_no_puede_haber_dos_versiones_activas` (intento manual de activar dos).
- [ ] 12.4 Crear `backend/tests/test_padron_vaciar.py`:
  - RED: `test_vaciar_materia_con_padron` (204, versión activa eliminada, entradas preservadas).
  - TRIANGULAR: `test_vaciar_materia_sin_padron_404`, `test_vaciar_materia_otro_tenant_404`, `test_doble_vaciado_409`.
- [ ] 12.5 Crear `backend/tests/test_padron_moodle.py`:
  - RED: `test_sync_moodle_ok` (mockear cliente Moodle, verificar versión creada con `origen='moodle'`).
  - TRIANGULAR: `test_sync_moodle_no_disponible_503`, `test_sync_moodle_mapping_error`.
- [ ] 12.6 Crear `backend/tests/test_padron_aislamiento.py` (multi-tenant):
  - RED: `test_padron_aislamiento_tenant` (entradas de tenant A invisibles para tenant B).
  - TRIANGULAR: `test_version_activa_aislamiento`, `test_vaciar_solo_propio_tenant`, `test_sin_permiso_padron_403`.

## 13. Verificación final

- [ ] 13.1 Ejecutar suite completa: `pytest backend/tests/ -v --tb=short`. Todos los tests de C-09 pasan; ningún test previo se rompe.
- [ ] 13.2 Verificar cobertura: `pytest backend/tests/ --cov=backend/app --cov-report=term-missing`. ≥80% líneas global; ≥90% en reglas de negocio (invariante versión activa, cifrado/desencriptado email, aislamiento multi-tenant).
- [ ] 13.3 Confirmar que ningún test mockea la DB (contenedor efímero) y que todos los schemas usan `extra='forbid'`.
- [ ] 13.4 Confirmar que C-06 (`Materia`, `Cohorte`) y C-07 (`Usuario`, `Asignacion`) quedaron intactos (sin modificación de schema, solo tablas nuevas en migración 008).
- [ ] 13.5 Marcar `[x]` C-09 en CHANGES.md.
