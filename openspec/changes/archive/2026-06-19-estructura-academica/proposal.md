## Why

Los módulos de dominio (padrón, calificaciones, equipos docentes, encuentros, liquidaciones) todos referencian la estructura académica del tenant, pero esa estructura no existe aún. Sin `Carrera`, `Cohorte` y `Materia` no hay FK válidas para construir ningún módulo posterior al RBAC. C-06 cierra ese gap para habilitar el camino crítico.

## What Changes

- Nuevo modelo `Carrera` con código único por tenant, nombre y estado Activa/Inactiva.
- Nuevo modelo `Cohorte` vinculada a una `Carrera`, con nombre, año, vigencia y estado.
- Nuevo modelo `Materia` como catálogo único por tenant (ADR-006): código único, nombre y estado.
- Migración 004 que crea las tablas `carrera`, `cohorte`, `materia`.
- ABM REST bajo `/api/admin/carreras`, `/api/admin/cohortes`, `/api/admin/materias`, todos protegidos con `estructura:gestionar` (ADMIN).
- Soft delete sobre las tres entidades (consistente con el mixin base de C-02).
- Tests de unicidad por tenant, aislamiento multi-tenant y reglas de estado (carrera inactiva no admite cohortes abiertas).

## Capabilities

### New Capabilities

- `carrera-management`: ABM de carreras del tenant con unicidad `(tenant_id, codigo)` y regla de estado.
- `cohorte-management`: ABM de cohortes con unicidad `(tenant_id, carrera_id, nombre)` y vínculo a carrera.
- `materia-catalog`: Catálogo único de materias del tenant con unicidad `(tenant_id, codigo)` (ADR-006).

### Modified Capabilities

*(ninguna — no hay specs existentes de estructura académica)*

## Impact

- **Nuevas tablas**: `carrera`, `cohorte`, `materia` (Migración 004).
- **Nuevos endpoints**: `GET/POST /api/admin/carreras`, `GET/PUT/DELETE /api/admin/carreras/{id}` (ídem para cohortes y materias).
- **Permiso nuevo**: `estructura:gestionar` — requiere seed en la tabla `permiso` y asignación al rol ADMIN en `rol_permiso`.
- **Dependencia inmediata hacia adelante**: C-07 (`Asignacion`), C-09 (`VersionPadron`), C-10 (`Calificacion`), C-13 (`SlotEncuentro`), C-14 (`Evaluacion`) necesitan las FKs definidas acá.
- **Sin breaking changes**: es la primera vez que estas entidades se definen en el sistema.
