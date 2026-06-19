## Context

C-06 entregó `Carrera`, `Cohorte` y `Materia` con CRUD, migrations 001-005 y repositories. La migración `601bb609ae5b_006_programas_y_fechas_academicas.py` ya existe en el árbol de Alembic (down_revision `005_estructura_academica`), con las tablas `programa_materia` y `fecha_academica` creadas correctamente.

El código de C-17 también ha sido parcialmente avanzado: existen `app/models/programa_materia.py`, `app/models/fecha_academica.py`, los repositories, services, schemas y routers en `app/api/v1/programas.py` y `app/api/v1/fechas_academicas.py`. El estado actual es: **código funcional, tests incompletos** (faltan aislamiento multi-tenant, cobertura de LMS fragment, tests de repository y endpoints de programas).

## Goals / Non-Goals

**Goals:**
- Documentar el diseño de `ProgramaMateria` y `FechaAcademica` con sus contratos de API.
- Especificar las reglas de unicidad, aislamiento y validación de entidades referenciadas.
- Definir la lógica del fragmento LMS (`build_lms_fragment`) y las vistas de calendario.
- Guiar los tests faltantes para alcanzar ≥80% líneas, ≥90% reglas de negocio.

**Non-Goals:**
- Almacenamiento real de archivos (el sistema guarda solo la `referencia_archivo` opaca; el upload al storage externo es responsabilidad del cliente o de una integración separada).
- UI/Frontend: este change es puramente backend.
- Modificar modelos de C-06.

## Decisions

### D1 — `referencia_archivo` es una referencia opaca, no un path de disco
`ProgramaMateria.referencia_archivo` almacena un identificador o URL del archivo en el servicio de almacenamiento externo (ej. `"s3://bucket/prog/xyz.pdf"` o un ID en el sistema de almacenamiento del tenant). El backend no valida ni procesa el contenido — solo lo guarda y lo devuelve. El cliente es responsable de subir el archivo al storage antes o después de crear el programa; el sistema no gestiona el ciclo de vida del archivo.
- **Alternativa descartada**: multipart upload en el mismo endpoint. Rechazada: acopla el backend al servicio de storage específico y complica el endpoint con lógica binaria fuera del scope del change.

### D2 — Unicidad de combinación: `(tenant_id, materia_id, carrera_id, cohorte_id)` para ProgramaMateria
Un tenant no puede tener dos programas activos para la misma combinación. La constraint `uq_programa_materia_combinacion` garantiza integridad a nivel DB. A nivel servicio, se detecta la duplicidad antes del INSERT y se devuelve 409.
- El soft-delete no afecta la unicidad: si un programa es soft-deleted, la constraint solo aplica a registros con `deleted_at IS NULL` (implementado en la capa de service, no como partial index en DB, para mantener la migration simple).

### D3 — Unicidad de instancia evaluativa: `(tenant_id, materia_id, cohorte_id, tipo, numero)` para FechaAcademica
Cada instancia evaluativa (ej. "Parcial #1" de una materia en una cohorte) es única. El `numero` permite distinguir "1er Parcial" de "2do Parcial" del mismo tipo. La constraint `uq_fecha_academica_combinacion` está en la DB y el service la detecta antes del INSERT (409).

### D4 — Validación de entidades referenciadas antes del INSERT
Tanto `ProgramaMateriaService` como `FechaAcademicaService` validan que las entidades referenciadas (Materia, Carrera, Cohorte) existan y pertenezcan al mismo tenant antes de insertar. Si cualquiera no existe, se devuelve 404 con el detalle de qué entidad falta. Esto previene FK violations y da mensajes de error claros al cliente.

### D5 — `build_lms_fragment`: función pura que genera texto formateado
`build_lms_fragment(fechas: list[FechaAcademica]) -> str` es una función pura (sin I/O). Ordena las fechas por `fecha` ascendente y genera un bloque de texto tipo:
```
- [Parcial #1] Primer Parcial — 15/04/2026
- [TP #1] TP Integrador — 10/05/2026
- [Coloquio #1] Coloquio Final — 20/06/2026
```
Si la lista es vacía, retorna `"Sin evaluaciones registradas"`. El endpoint `GET /lms-fragment` recibe `materia_id` y `cohorte_id` como query params obligatorios, llama a `list_tabular` (que ya filtra por tenant) y pasa el resultado a `build_lms_fragment`. El resultado se envuelve en `{"fragment": "..."}`.

### D6 — Vista calendario: agrupación por período en memoria
`list_calendario` (en el service) llama a `list` del repository (ya ordenada por `fecha ASC`), luego agrupa en un dict `{periodo: [FechaAcademica]}` y devuelve una lista de `{"periodo": str, "fechas": [...]}` ordenada alfabéticamente por período. No requiere GROUP BY en SQL — la operación se hace en Python, ya que el volumen esperado por request es bajo (≤200 fechas por defecto).

### D7 — Permisos RBAC: `estructura:gestionar` para escritura, `estructura:ver` para lectura
Ambos permisos ya existen en el catálogo de C-04. COORDINADOR y ADMIN tienen `estructura:gestionar`; todos los roles docentes tienen `estructura:ver`. Fail-closed: sin permiso explícito → 403.

### D8 — Routers en `app/api/v1/` (fuera del subdirectorio `routers/`)
Los routers `programas.py` y `fechas_academicas.py` viven en `app/api/v1/` (no en `app/api/v1/routers/`) para seguir el patrón establecido por C-06 (`estructura.py` también está en ese nivel). Se registran en el app factory igual que los demás.

### D9 — `tipo` como enum Python, almacenado como String(32) en DB
`TipoFechaAcademica` es un `str PyEnum` con valores `Parcial | TP | Coloquio | Recuperatorio`. Se almacena como String(32) en la columna para máxima compatibilidad con Alembic. El schema Pydantic usa el enum para validación en el request. La response serializa el valor como string.

### D10 — Tests: DB real (contenedor efímero), sin mocks de DB
Todos los tests de service y repository usan la DB de test real (fixture `db_session` + `create_test_schema`), consistente con la regla dura del proyecto. Los tests de endpoint usan mocks de autenticación/permisos (como el resto del proyecto) pero no mockean la DB.

## API Contract

### `/api/v1/programas`

| Verbo | Path | Guard | Body / Params | Response |
|-------|------|-------|---------------|----------|
| POST | `/api/v1/programas` | `estructura:gestionar` | `ProgramaMateriaCreate` | 201 `ProgramaMateriaResponse` |
| GET | `/api/v1/programas` | `estructura:ver` | `?materia_id, carrera_id, cohorte_id` | 200 `list[ProgramaMateriaResponse]` |
| GET | `/api/v1/programas/{id}` | `estructura:ver` | — | 200 `ProgramaMateriaResponse` / 404 |
| PUT | `/api/v1/programas/{id}` | `estructura:gestionar` | `ProgramaMateriaUpdate` | 200 `ProgramaMateriaResponse` |
| DELETE | `/api/v1/programas/{id}` | `estructura:gestionar` | — | 204 / 404 |

### `/api/v1/fechas-academicas`

| Verbo | Path | Guard | Body / Params | Response |
|-------|------|-------|---------------|----------|
| POST | `/api/v1/fechas-academicas` | `estructura:gestionar` | `FechaAcademicaCreate` | 201 `FechaAcademicaResponse` |
| GET | `/api/v1/fechas-academicas` | `estructura:ver` | `?materia_id, cohorte_id, periodo, tipo` | 200 `list[FechaAcademicaResponse]` |
| GET | `/api/v1/fechas-academicas/calendario` | `estructura:ver` | `?materia_id, cohorte_id` | 200 `list[CalendarioPeriodo]` |
| GET | `/api/v1/fechas-academicas/lms-fragment` | `estructura:ver` | `?materia_id*,cohorte_id*` | 200 `{"fragment": str}` |
| GET | `/api/v1/fechas-academicas/{id}` | `estructura:ver` | — | 200 `FechaAcademicaResponse` / 404 |
| PUT | `/api/v1/fechas-academicas/{id}` | `estructura:gestionar` | `FechaAcademicaUpdate` | 200 `FechaAcademicaResponse` |
| DELETE | `/api/v1/fechas-academicas/{id}` | `estructura:gestionar` | — | 204 / 404 |

### Schemas clave

**ProgramaMateriaCreate** (`extra='forbid'`):
```
materia_id: str (UUID)
carrera_id: str (UUID)
cohorte_id: str (UUID)
titulo: str
referencia_archivo: Optional[str]
```

**FechaAcademicaCreate** (`extra='forbid'`):
```
materia_id: str (UUID)
cohorte_id: str (UUID)
tipo: TipoFechaAcademica  # enum: Parcial | TP | Coloquio | Recuperatorio
numero: int (ge=1)
periodo: str  # ej: "2026-1"
fecha: str  # ISO 8601
titulo: str
```

**FechaAcademicaUpdate** (`extra='forbid'`, todos opcionales):
```
periodo: Optional[str]
fecha: Optional[str]
titulo: Optional[str]
```

## Risks / Trade-offs

- **[Unicidad de ProgramaMateria ignora soft-deleted]**: si un programa es soft-deleted, técnicamente podría crearse uno nuevo para la misma combinación. Esto es intencional — el soft-delete representa "fue archivado"; un nuevo programa para la misma combinación es un reemplazo legítimo. La constraint de DB usa solo `deleted_at IS NULL` a nivel service (no partial index).
- **[`referencia_archivo` puede ser null]**: el sistema permite crear el registro del programa sin asociar un archivo todavía (`referencia_archivo` nullable). Esto facilita el flujo de "reservar el slot primero, subir el archivo después", pero requiere que el cliente maneje el estado parcial.
- **[Calendario en memoria con límite 200]**: la paginación del listado del calendario está fija en 200 registros. Para tenants con muchas fechas podría ser insuficiente, pero el volumen típico (decenas de fechas por cohorte) es muy inferior a ese límite.

## Migration Plan

La migración `601bb609ae5b_006_programas_y_fechas_academicas.py` ya existe con:
- Tabla `programa_materia`: columnas estándar (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`) + `materia_id`, `carrera_id`, `cohorte_id`, `titulo`, `referencia_archivo`, `cargado_at`. FKs a `tenant`, `materia`, `carrera`, `cohorte`. Índices de tenant y unicidad.
- Tabla `fecha_academica`: columnas estándar + `materia_id`, `cohorte_id`, `tipo` (String 32), `numero` (Integer), `periodo` (String 64), `fecha` (DateTime TZ), `titulo`. FKs a `tenant`, `materia`, `cohorte`. Índices de tenant, cohorte y unicidad.
- `down_revision = '005_estructura_academica'`.

No se requieren cambios en la migración. Despliegue = `alembic upgrade head` + deploy de código. Rollback = `alembic downgrade -1` (que hace `drop_table` de ambas tablas).

## Open Questions

- Ninguna bloqueante. La referencia opaca de archivo (`referencia_archivo`) no requiere resolver PA-01 (catálogo de materias) porque trabaja con el `materia_id` ya existente del catálogo de C-06.
