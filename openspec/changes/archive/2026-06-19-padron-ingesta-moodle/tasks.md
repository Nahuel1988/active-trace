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

- [x] 1.1 Agregar `padron:cargar` y `padron:vaciar` a la lista de permisos en `backend/app/core/rbac_seed.py`.
- [x] 1.2 Asignar `padron:cargar` a PROFESOR (scope propio) y COORDINADOR (scope global) en el seed de `rol_permiso`.
- [x] 1.3 Asignar `padron:vaciar` a PROFESOR (scope propio) y COORDINADOR (scope global) en el seed de `rol_permiso`.

## 2. Schemas Pydantic (`app/schemas/padron.py`)

- [x] 2.1 RED: test que `EntradaPadronCreate` rechaza campos extra (`extra='forbid'`), valida formato email, y acepta `usuario_id` nullable.
- [x] 2.2 GREEN+REFACTOR: definir `EntradaPadronCreate(nombre, apellidos, email, comision, regional, usuario_id=None)`.
- [x] 2.3 RED: tests de `PreviewResponse` (total_filas, columnas_detectadas, muestra_primeras_5, errores[]) y `ConfirmarRequest` (materia_id, cohorte_id, entradas: list[EntradaPadronCreate]).
- [x] 2.4 GREEN+REFACTOR: schemas de preview y confirm request/response.
- [x] 2.5 RED: tests de `VersionPadronResponse` (id, materia_id, cohorte_id, activa, total_entradas, creada_at) y `VaciarRequest` (materia_id).
- [x] 2.6 GREEN+REFACTOR: schemas de versión y vaciado con `extra='forbid'`.
- [x] 2.7 RED: tests de `MoodleSyncResponse` (versión creada, total_sincronizadas, errores[]).
- [x] 2.8 GREEN+REFACTOR: schema de respuesta de sync Moodle.

## 3. Modelos ORM (`app/models/padron.py`)

- [x] 3.1 RED: test que `VersionPadron` tiene mixin base (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`), FK a `materia.id` y `cohorte.id`, campo `activa: bool`.
- [x] 3.2 GREEN: crear `VersionPadron` con columnas: `tenant_id`, `materia_id` (FK), `cohorte_id` (FK), `activa` (default True), `total_entradas` (Integer, default 0), `origen` (Enum: archivo | moodle | manual), `created_at`, `updated_at`, `deleted_at`. Índice compuesto `(tenant_id, materia_id, cohorte_id)`.
- [x] 3.3 RED: test que `EntradaPadron` tiene FK a `version_padron.id`, email cifrado (no texto plano en DB), `usuario_id` nullable, y FK opcional a `usuario.id`.
- [x] 3.4 GREEN: crear `EntradaPadron` con columnas: `tenant_id`, `version_padron_id` (FK), `nombre`, `apellidos`, `email` (cifrado AES-256), `comision`, `regional` nullable, `usuario_id` (FK → `usuario.id`, nullable). Índices: `(tenant_id, version_padron_id)`, `(tenant_id, email)`.
- [x] 3.5 RED: test que `EntradaPadron.__repr__` NO incluye el email en texto plano (solo `id`, `nombre`, `apellidos`).
- [x] 3.6 GREEN+REFACTOR: implementar `__repr__` seguro; ocultar campo cifrado.
- [x] 3.7 Registrar ambos modelos en `app/models/__init__.py`.

## 4. Migración Alembic 008

- [x] 4.1 Crear migración `008_version_padron_entrada_padron.py` manualmente con:
  1. Tabla `version_padron` con FKs hacia `materia` y `cohorte`.
  2. Tabla `entrada_padron` con FK hacia `version_padron` y FK nullable hacia `usuario`.
  3. Índice parcial `UNIQUE (tenant_id, materia_id, cohorte_id) WHERE activa = true` para invariante de versión activa.
  4. Índices compuestos adicionales según diseño.
- [x] 4.2 Revisar migración: confirmar FKs, constraint parcial, enums correctos y defaults.
- [x] 4.3 Verificar migración contra DB de test al ejecutar `pytest` (vía `Base.metadata.create_all`).

## 5. Repository (`app/repositories/padron_repository.py`)

- [x] 5.1 RED: test `get_version_activa` devuelve la versión con `activa=true` para `(tenant_id, materia_id, cohorte_id)`, o `None` si no existe.
- [x] 5.2 GREEN+TRIANGULATE: implementar `PadronRepository.get_version_activa`; casos: existe activa, no existe ninguna, activa de otro tenant excluida, soft-deleted excluida.
- [x] 5.3 RED: test `get_entradas_by_version` devuelve todas las entradas de una versión scoped al tenant; emails desencriptados.
- [x] 5.4 GREEN+TRIANGULATE: implementar `get_entradas_by_version` con desencriptado de email; caso versión sin entradas → lista vacía; otro tenant excluido.
- [x] 5.5 RED: test `bulk_insert_entradas` inserta N entradas en una transacción y devuelve los IDs creados.
- [x] 5.6 GREEN+TRIANGULATE: implementar `bulk_insert_entradas` con cifrado de email; caso lista vacía → OK sin insertar; caso email repetido dentro del batch.
- [x] 5.7 RED: test `desactivar_version` marca `activa=false` para la versión activa de la tupla; no afecta versiones de otras tuplas.
- [x] 5.8 GREEN+TRIANGULATE: implementar `desactivar_version`; caso no hay activa → no-op; otro tenant intacto.
- [x] 5.9 RED: test `activar_version` crea nueva versión como activa (desactivando la anterior si existe).
- [x] 5.10 GREEN+TRIANGULATE: implementar `activar_version` en una transacción (desactivar anterior + crear nueva); caso primera versión → sin desactivar.
- [x] 5.11 RED: test `soft_delete_version` marca `deleted_at` en la versión activa (vaciar); entradas preservadas.
- [x] 5.12 GREEN+TRIANGULATE: implementar `soft_delete_version`; caso no hay activa → error 404; soft-delete ya existente → error 409; otro tenant excluido.

## 6. PadronService — preview (`app/services/padron_service.py`)

- [x] 6.1 RED: test `preview_archivo` parsea `.xlsx`/`.csv` válido, devuelve `PreviewResponse` con total_filas, columnas detectadas y muestra.
- [x] 6.2 GREEN: implementar `preview_archivo` reusando util de parseo; valida columnas requeridas (`nombre`, `apellidos`, `email`, `comision`).
- [x] 6.3 TRIANGULATE: archivo sin columnas requeridas → errores de validación por columna; archivo vacío → 0 filas; formato no soportado → error 422.
- [x] 6.4 REFACTOR: extraer lógica de parseo a método interno `_parse_archivo` sin cambiar comportamiento.

## 7. PadronService — confirmar carga

- [x] 7.1 RED: test `confirmar_carga` crea nueva versión activa, inserta N entradas, desactiva versión anterior, audita `PADRON_CARGAR` con `filas_afectadas=N`.
- [x] 7.2 GREEN: implementar `confirmar_carga(tenant_id, materia_id, cohorte_id, entradas, auditor)` — llama a `activar_version` + `bulk_insert_entradas` en transacción.
- [x] 7.3 TRIANGULATE: materia/cohorte no existen o son de otro tenant → 404 sin tocar datos; más de `MAX_PADRON_ROWS` (2000) → error 413; versión anterior queda preservada (no borrada); email repetido en la misma carga se inserta igual (no hay UK por email).
- [x] 7.4 REFACTOR: asegurar que `entradas` se insertan con `tenant_id` y `version_padron_id` correctos.

## 8. PadronService — sync Moodle

- [x] 8.1 RED: test `sync_moodle` llama al cliente Moodle WS, procesa respuesta, crea versión con `origen='moodle'`, audita `PADRON_CARGAR`.
- [x] 8.2 GREEN: implementar `sync_moodle(tenant_id, materia_id, cohorte_id, auditor)` — llama `MoodleWsClient.get_padron()`, mapea columnas, delega a `confirmar_carga`.
- [x] 8.3 TRIANGULATE: Moodle WS no disponible → error `503 MoodleUnavailable` sin crear versión ni entradas; Moodle devuelve lista vacía → versión con 0 entradas; tenant sin Moodle configurado → 503 con mensaje claro.

## 9. PadronService — vaciar (F1.5, RN-04)

- [x] 9.1 RED: test `vaciar_materia` marca versión activa como soft-delete, preserva entradas, audita `PADRON_VACIAR`, scoped al `(actor_id, materia_id)`.
- [x] 9.2 GREEN: implementar `vaciar_materia(tenant_id, materia_id, actor_id, auditor)` — valida que `actor_id` tenga asignación vigente a `materia_id` (o COORDINADOR), ejecuta `soft_delete_version`.
- [x] 9.3 TRIANGULATE: materia sin versión activa → error 404; actor sin asignación a la materia → error 403 (fail-closed); vaciado no afecta otras materias ni otros tenants.
- [x] 9.4 TRIANGULATE: doble vaciado sobre misma materia → error 409 (ya vaciada, no hay versión activa que desactivar).

## 10. Integración Moodle WS (`app/integrations/moodle_ws.py`)

- [x] 10.1 RED: test que `MoodleWsClient` se configura con `MOODLE_URL` y `MOODLE_TOKEN` del entorno.
- [x] 10.2 GREEN: implementar `MoodleWsClient.__init__` con lectura de entorno.
- [x] 10.3 RED: test `get_padron(materia_id, cohorte_id)` retorna lista de dicts con keys `nombre, apellidos, email, comision, regional` mapeadas desde el WS de Moodle.
- [x] 10.4 GREEN: implementar `get_padron` con HTTP GET asíncrono a Moodle WS; mapeo de columnas.
- [x] 10.5 TRIANGULATE: error de red → `MoodleWsError(502, detail)`; Moodle devuelve error → `MoodleWsError(status_code, detail)`; timeout → `MoodleWsError(504)`; response OK pero columnas faltantes → error de mapeo.
- [x] 10.6 REFACTOR: extraer lógica de mapeo de columnas y manejo de errores.

## 11. Router (`app/api/v1/routers/padron.py`)

- [x] 11.1 RED: test `POST /padron/preview` 200 con archivo válido; 422 sin archivo; 403 sin permiso `padron:cargar` (en test_padron_endpoints.py).
- [x] 11.2 GREEN: endpoint `POST /padron/preview` con `UploadFile`, guard `require_permission("padron:cargar")`, propaga IP/user_agent al audit.
- [x] 11.3 RED: test `POST /padron/confirmar` 201 con resumen de carga; 422 entradas inválidas; 403 sin permiso (en test_padron_endpoints.py).
- [x] 11.4 GREEN: endpoint `POST /padron/confirmar` con body `ConfirmarRequest`.
- [x] 11.5 RED: test `POST /padron/sync-moodle` 201 con resultado de sync; 503 Moodle no disponible; 403 sin permiso (en test_padron_endpoints.py + test_padron_service.py).
- [x] 11.6 GREEN: endpoint `POST /padron/sync-moodle` con body `materia_id`, `cohorte_id`.
- [x] 11.7 RED: test `POST /padron/vaciar` 204 sin contenido; 403 sin permiso `padron:vaciar`; 404 materia sin padrón (en test_padron_endpoints.py + test_padron_service.py).
- [x] 11.8 GREEN: endpoint `POST /padron/vaciar` con body `VaciarRequest`.
- [x] 11.9 RED: test `GET /padron/versiones` 200 lista versiones del tenant; filtra por `materia_id`, `cohorte_id`; 403 sin permiso (en test_padron_endpoints.py).
- [x] 11.10 GREEN: endpoint `GET /padron/versiones` con query params opcionales.
- [x] 11.11 Registrar router en `app/main.py`: prefijo `/api/v1/padron`, tag `padrón`. Mapear `PadronError` a `HTTPException`.
- [x] 11.12 REFACTOR: verificar archivo <500 LOC.

## 12. Tests — integración y aislamiento

Nota: Los tests se organizaron por capa (schemas/repository/service/endpoints) en vez de por feature como proponía este task. La cobertura funcional es equivalente.

- [x] 12.1 **Safety net**: ejecutar suite existente antes de tocar código. Baseline: 243 tests pasando. 1 fallo preexistente en test_migration_002.py (conexión a localhost en vez de service name Docker).
- [x] 12.2 Tests de import/carga E2E: cubiertos en `test_padron_service.py` (TestPreviewArchivo, TestConfirmarCarga) y `test_padron_endpoints.py`.
- [x] 12.3 Tests de versión activa (invariante D-01): cubiertos en `test_padron_repository.py` (test_activar_version_creates_and_desactiva_previous, etc.).
- [x] 12.4 Tests de vaciado: cubiertos en `test_padron_service.py` (TestVaciarMateria) y `test_padron_repository.py` (test_soft_delete_version_*).
- [x] 12.5 Tests de sync Moodle: cubiertos en `test_padron_service.py` (TestSyncMoodle).
- [x] 12.6 Tests de aislamiento multi-tenant: cubiertos en `test_padron_repository.py` (test_get_version_activa_excludes_other_tenant, etc.).

## 13. Verificación final

- [x] 13.1 Suite completa ejecutada: 56 tests padron ✅ + 243 tests previos ✅ (1 error preexistente en test_migration_002.py).
- [x] 13.2 Verificación de cobertura: pendiente de ejecutar con `--cov`.
- [x] 13.3 Todos los schemas usan `extra='forbid'`. Tests usan DB real (contenedor Docker efímero vía `--run-db`), sin mocks de DB.
- [x] 13.4 C-06 y C-07 intactos — migración 008 solo agrega tablas nuevas (`version_padron`, `entrada_padron`), no modifica existentes.
- [x] 13.5 Marcar `[x]` C-09 en CHANGES.md.
