## Why

Sobre la estructura académica ya consolidada (C-06: Carrera, Cohorte, Materia), las instituciones necesitan centralizar dos artefactos operativos clave: el **programa oficial** de cada materia (documento por carrera × cohorte) y el **calendario de evaluaciones** (parciales, TPs y coloquios). Hoy esos datos viven dispersos en planillas y mails; el sistema debe ser su fuente de verdad, hacerlos accesibles a los actores autorizados (F5.3) y poder publicar las fechas en el aula virtual del LMS sin re-trabajo manual (F5.4).

## What Changes

- **Nuevo modelo `ProgramaMateria`**: documento oficial del programa de una materia para una combinación específica de carrera × cohorte, con título descriptivo y referencia opaca al archivo en el servicio de almacenamiento (`referencia_archivo`).
- **Nuevo modelo `FechaAcademica`**: instancia evaluativa (Parcial / TP / Coloquio / Recuperatorio) por materia × cohorte × número, con período, fecha y título.
- **Endpoints `/api/programas`**: subir y asociar un programa a materia × carrera × cohorte; listar y obtener; borrar (soft delete). Permiso `estructura:gestionar` para escritura, `estructura:ver` para lectura.
- **Endpoints `/api/fechas-academicas`**: CRUD completo de fechas evaluativas; listado tabular y vista calendario (agrupada por período). Mismos permisos.
- **Generación de fragmento LMS (F5.4)**: endpoint que produce un fragmento de contenido listo para publicar en el aula virtual a partir de las fechas de una materia × cohorte.
- **Migración Alembic 006**: tablas `programa_materia` y `fecha_academica` con sus FKs a `carrera`, `cohorte`, `materia`, índices de `tenant_id` y constraints de unicidad.
- **Aislamiento multi-tenant** en ambos repositories por defecto y soft delete en ambos modelos.

## Capabilities

### New Capabilities
- `programa-materia-management`: alta (upload + asociación), listado, obtención y soft delete de programas oficiales por materia × carrera × cohorte, con referencia de archivo opaca y aislamiento por tenant.
- `fecha-academica-management`: CRUD de fechas evaluativas (parcial/TP/coloquio/recuperatorio) por materia × cohorte × número, vistas tabular y calendario, y generación de fragmento de contenido para el LMS.

### Modified Capabilities
<!-- Ninguna: no cambian requisitos de capacidades existentes. Se consumen los modelos Carrera/Cohorte/Materia de C-06 sin modificar su contrato. -->

## Impact

- **Modelos**: `backend/app/models/programa_materia.py`, `backend/app/models/fecha_academica.py` (mixin base: `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`); registro en `backend/app/models/__init__.py`.
- **Migración**: `backend/alembic/versions/006_programas_y_fechas_academicas.py` (004 = audit_log, 005 = estructura_academica → 006 es la siguiente).
- **Repositories**: `programa_materia_repository.py`, `fecha_academica_repository.py` (heredan el filtro por tenant de `repositories/base.py`).
- **Services**: `programa_materia_service.py`, `fecha_academica_service.py` (incluye la lógica de generación del fragmento LMS).
- **Schemas Pydantic**: `backend/app/schemas/programa_materia.py`, `backend/app/schemas/fecha_academica.py` (todos con `extra='forbid'`).
- **Routers**: `backend/app/api/v1/programas.py`, `backend/app/api/v1/fechas_academicas.py` con `require_permission("estructura:gestionar" | "estructura:ver")`.
- **RBAC**: reutiliza el permiso `estructura:gestionar` ya sembrado en C-06; agrega `estructura:ver` al seed si aún no existe.
- **FK dependencias**: requiere C-06 archivado (Carrera, Cohorte, Materia disponibles). Sin impacto sobre módulos posteriores; otros changes consumen estas tablas como lectura.
