## Context

C-06 (`estructura-academica`) ya consolidó el catálogo académico: `Carrera`, `Cohorte` y `Materia`, con mixin base (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`), aislamiento por tenant en `repositories/base.py`, soft delete y el permiso `estructura:gestionar` sembrado en `rbac_seed.py`. Este change construye sobre ese cimiento dos artefactos operativos (F5.3 y F5.4 de `knowledge-base/06_funcionalidades.md`) y los modelos E15/E16 de `knowledge-base/04_modelo_de_datos.md`.

Restricciones del proyecto (reglas duras): identidad SIEMPRE desde JWT, multi-tenancy row-level con filtro por defecto en repositories, RBAC fino fail-closed, flujo unidireccional Routers → Services → Repositories → Models, Pydantic con `extra='forbid'`, soft delete, snake_case, una migración Alembic por change, Strict TDD. Governance: **BAJO** (CRUDs sobre catálogo estructurado, sin PII sensible ni dominio de seguridad).

Gotcha de entorno heredado de C-06: en `pyproject.toml`, `asyncio_default_fixture_loop_scope = "session"`; `TEST_DATABASE_URL` usa el nombre de servicio Docker; engines en fixtures session-scoped en `conftest.py`.

## Goals / Non-Goals

**Goals:**
- Modelar `ProgramaMateria` (E16) y `FechaAcademica` (E15) con FKs a `carrera`/`cohorte`/`materia`, aislamiento por tenant y soft delete.
- Exponer `/api/programas` (upload + asociar + listar + obtener + borrar) y `/api/fechas-academicas` (CRUD + listado tabular + vista calendario).
- Generar un fragmento de contenido (texto) listo para publicar en el aula virtual del LMS a partir de las fechas de una materia × cohorte (F5.4).
- Cobertura TDD ≥80% líneas, ≥90% reglas de negocio.

**Non-Goals:**
- NO se implementa el almacenamiento físico de archivos. `ProgramaMateria.referencia_archivo` es un string opaco que apunta a un servicio de almacenamiento externo; este change solo lo persiste y devuelve. La carga binaria del archivo y su backend de storage quedan fuera de alcance.
- NO se publica automáticamente en el LMS: se genera el fragmento de contenido y se devuelve al cliente; la publicación efectiva es responsabilidad de otro flujo (integración Moodle/N8N).
- NO se modifican los modelos ni contratos de C-06.
- NO se construye UI; este change es backend. El consumo frontend vive en changes de la fase frontend.

## Decisions

### D1 — `referencia_archivo` como string opaco, no upload binario
El modelo guarda únicamente una referencia (path/URL/key) provista por el cliente o el servicio de storage. El endpoint de upload acepta la referencia ya resuelta, no el binario.
- **Por qué**: desacopla este change del backend de almacenamiento (aún no definido). El test "referencia de archivo opaca" verifica que el sistema persiste y devuelve la referencia sin interpretarla ni validar su existencia física.
- **Alternativa descartada**: recibir `multipart/form-data` y persistir el binario → acopla el change a una decisión de infraestructura de storage que no está cerrada y excede el governance BAJO.

### D2 — Unicidad de `ProgramaMateria` por `(tenant_id, materia_id, carrera_id, cohorte_id)`
Un programa es el documento oficial de una materia para una combinación carrera × cohorte; esa combinación debe ser única por tenant. Reasociar (subir una nueva versión) reemplaza la referencia vía `PUT`, no crea duplicados.
- **Por qué**: refleja "el programa vigente" de F5.3. Evita ambigüedad sobre cuál es el documento oficial.
- **Alternativa descartada**: permitir múltiples programas por combinación con versionado → no pedido por F5.3; agrega complejidad innecesaria para governance BAJO.

### D3 — Unicidad de `FechaAcademica` por `(tenant_id, materia_id, cohorte_id, tipo, numero)`
Cada instancia evaluativa se identifica por su tipo y número dentro de la materia × cohorte (ej: 1er Parcial, 2do Parcial). No puede haber dos "1er Parcial" de la misma materia × cohorte.
- **Por qué**: el `numero` es semánticamente "número de instancia" (E15); la combinación tipo+numero la hace única y editable por `PUT`.
- **Alternativa descartada**: unicidad solo por fecha → dos evaluaciones distintas podrían caer el mismo día; rompe la semántica de instancia.

### D4 — `tipo` como enum `TipoFechaAcademica`: `Parcial | TP | Coloquio | Recuperatorio`
Enum cerrado a nivel modelo y schema; Pydantic rechaza valores fuera del conjunto.
- **Por qué**: F5.4 y E15 enumeran exactamente esos tipos. Enum cerrado previene datos basura.

### D5 — Vistas tabular y calendario como dos shapes de la misma data
El listado tabular devuelve una lista plana ordenada por fecha. La vista calendario devuelve la misma data agrupada por `periodo` (y dentro, ordenada por fecha). Ambas son de solo lectura, permiso `estructura:ver`.
- **Por qué**: F5.4 pide "listado tabular y calendario visual". Reutilizar el repository con dos serializaciones evita lógica duplicada; el agrupado por período se hace en el service.

### D6 — Fragmento LMS generado en el service como texto plano/markdown
`GET /api/fechas-academicas/lms-fragment?materia_id=&cohorte_id=` arma un fragmento de contenido (texto) listando las evaluaciones de esa materia × cohorte ordenadas por fecha. Función pura `build_lms_fragment(fechas) -> str` en el service, fácilmente testeable (RED/GREEN/TRIANGULATE).
- **Por qué**: F5.4 pide "generar un fragmento de contenido listo para publicar". Una función pura sobre la lista de fechas aísla la lógica de formato de la I/O y maximiza testabilidad TDD.
- **Alternativa descartada**: render HTML acoplado al LMS específico → la salida debe ser neutra; el formato concreto lo decide el flujo de integración.

### D7 — Migración 006, manual y autogenerada-verificada
Numeración: 001 tenant, 002 auth, 003 rbac, 004 audit_log, 005 estructura_academica → **006**. Crea `programa_materia` y `fecha_academica` con índices de `tenant_id`, FKs y unique constraints de D2/D3.
- **Por qué**: una migración por change (regla dura). Se sigue el patrón de C-06 (autogenerate + revisión manual de índices/FKs/constraints).

## Risks / Trade-offs

- **Referencia de archivo colgada** → el `referencia_archivo` puede apuntar a un archivo que no existe en storage (no se valida). Mitigación: documentado como Non-Goal (D1); la validación de existencia es responsabilidad del servicio de storage cuando se integre.
- **FK a materia/carrera/cohorte borradas (soft delete)** → un programa o fecha podría referenciar una entidad C-06 soft-deleted. Mitigación: al crear/asociar, el service valida que la materia/carrera/cohorte existan y no estén borradas (404 si no); test cubre el caso.
- **Acumulación de fechas históricas** → muchas evaluaciones de cohortes viejas en el listado. Mitigación: filtrado por `cohorte_id`/`periodo` en los endpoints de lectura; índice por `(tenant_id, cohorte_id)`.
- **Trade-off PUT-reemplaza-programa** → no se guarda histórico de versiones del programa. Aceptado por governance BAJO y por D2 (solo importa el vigente); el soft delete deja rastro del registro anterior si se borra antes de re-crear.

## Migration Plan

1. Crear modelos ORM + registrarlos en `models/__init__.py`.
2. `alembic revision -m "006_programas_y_fechas_academicas"` (autogenerate), revisar índices/FKs/constraints, `alembic upgrade head` en DB de test.
3. Seed: confirmar `estructura:gestionar` existe; agregar `estructura:ver` si falta.
4. Rollback: `alembic downgrade -1` elimina ambas tablas; no hay datos productivos previos (change nuevo).

## Open Questions

- ¿El fragmento LMS debe incluir título de materia y carrera, o solo las fechas? → Decisión por defecto: incluye materia, cohorte, y por cada evaluación: tipo, número, título y fecha. Ajustable sin cambiar el contrato (es texto).
- ¿`periodo` se deriva de la cohorte o se ingresa libre? → Por E15 es texto libre (ej "2026-1"); se ingresa en el request. No se valida formato en este change.
