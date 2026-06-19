## Why

C-06 (estructura-academica) entregó los modelos `Carrera`, `Cohorte` y `Materia` con sus CRUD y migraciones. El siguiente paso natural es enriquecer la estructura académica con los dos artefactos que la coordinación necesita para operar cada período:

1. **Programas de materias** (`ProgramaMateria`): cada materia puede tener un documento oficial (programa) diferenciado por carrera y cohorte. Sin un registro centralizado, la coordinación gestiona estos archivos de forma manual fuera del sistema, con riesgo de usar programas desactualizados o equivocados.

2. **Fechas académicas** (`FechaAcademica`): parciales, TPs y coloquios tienen fechas específicas por materia y cohorte. Sin este módulo, los docentes no pueden comunicar esas fechas desde el sistema, y la coordinación no puede generarlas automáticamente para el aula virtual del LMS.

C-17 cierra esa brecha: provee los modelos, su CRUD completo y, para fechas, la capacidad extra de generar un fragmento de contenido formateado listo para publicar en el aula virtual (F5.4).

## What Changes

- **Modelo `ProgramaMateria`** (E16): documento oficial de una materia para una combinación única `(materia_id × carrera_id × cohorte_id)` dentro del tenant. Almacena un título y una referencia opaca al archivo en el servicio de almacenamiento externo (no un path de disco). Un tenant no puede tener dos programas para la misma combinación activos al mismo tiempo.
- **Modelo `FechaAcademica`** (E15): calendarización de instancias evaluativas (Parcial, TP, Coloquio, Recuperatorio) por `(materia_id × cohorte_id × tipo × numero)`. Registra la fecha, el período (`"2026-1"`) y un título descriptivo. La combinación `(tenant_id, materia_id, cohorte_id, tipo, numero)` es única.
- **Migración 008**: tablas `programa_materia` y `fecha_academica` con sus índices y constraints de unicidad. (Nota: ya existe el archivo `601bb609ae5b_006_programas_y_fechas_academicas.py` en Alembic con revision ID y down_revision contra `005_estructura_academica`; se mantiene como está.)
- **API `/api/v1/programas`** (F5.3): CRUD completo (POST, GET lista, GET por ID, PUT, DELETE soft). Guarded por `estructura:gestionar` (escritura) y `estructura:ver` (lectura). Filtros de listado por `materia_id`, `carrera_id`, `cohorte_id`.
- **API `/api/v1/fechas-academicas`** (F5.4): CRUD completo + dos endpoints adicionales:
  - `GET /calendario`: agrupa fechas por período visual, ordenadas por fecha dentro de cada período.
  - `GET /lms-fragment`: devuelve un fragmento de texto formateado con todas las evaluaciones de una materia × cohorte, listo para publicar en el aula virtual del LMS.
- **Tests**: CRUD completo, unicidad de combinaciones, validación de entidades referenciadas, soft-delete, aislamiento por tenant, generación del fragmento LMS (con fechas, vacío, ordenamiento por fecha).

## Capabilities

### New Capabilities
- `programa-materia-crud`: gestión de programas de materias (F5.3) — upload de referencia + CRUD, con unicidad por combinación y aislamiento tenant.
- `fecha-academica-crud`: gestión de fechas de evaluaciones (F5.4) — CRUD completo, vistas tabular y calendario.
- `lms-fragment`: generación de fragmento de contenido formateado para el aula virtual del LMS (F5.4 salida adicional).

### Modified Capabilities
<!-- C-17 NO modifica los modelos de C-06 (Carrera, Cohorte, Materia) ni sus routers.
     Los reutiliza como FK y para validar existencia antes de crear. -->

## Impact

- **Código nuevo**: `app/models/programa_materia.py`, `app/models/fecha_academica.py`, `app/repositories/programa_materia_repository.py`, `app/repositories/fecha_academica_repository.py`, `app/services/programa_materia_service.py`, `app/services/fecha_academica_service.py`, `app/schemas/programa_materia.py`, `app/schemas/fecha_academica.py`, `app/api/v1/programas.py` (o `routers/programas.py`), `app/api/v1/fechas_academicas.py` (o `routers/fechas_academicas.py`).
- **Reutiliza sin modificar**: `MateriaRepository`, `CarreraRepository`, `CohorteRepository` (C-06), `require_permission` (C-04), `get_current_user` (C-03), `TenantScopedMixin` / `BaseRepository` (C-02).
- **Migración**: `601bb609ae5b_006_programas_y_fechas_academicas.py` (ya creada, down_revision `005_estructura_academica`).
- **RBAC**: permisos `estructura:gestionar` y `estructura:ver` ya existentes del catálogo de C-04; no requiere nuevos permisos.
- **Multi-tenancy**: `tenant_id` en ambas tablas; repositories filtran por tenant por defecto.
- **Sin PII cifrado**: ningún campo de estas entidades requiere cifrado AES-256.
