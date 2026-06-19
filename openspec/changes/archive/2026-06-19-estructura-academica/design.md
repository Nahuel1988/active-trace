## Context

C-04 RBAC está completo: existe el guard `require_permission`, el seed de roles y la matriz rol × permiso. C-06 es el siguiente paso del camino crítico: establece las entidades raíz del dominio académico (`Carrera`, `Cohorte`, `Materia`) que todos los módulos posteriores (C-07 en adelante) usan como FK.

El sistema ya tiene el mixin base (C-02) con `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at` (soft delete) y el repositorio genérico tenant-scoped. Estas tres entidades heredan ese mixin directamente.

**Decisión de alcance**: C-06 NO implementa la entidad `Dictado` (instancia de Materia × Carrera × Cohorte, referida en ADR-006). Esa relación queda representada implícitamente mediante la triple FK `(materia_id, carrera_id, cohorte_id)` en las entidades de módulos posteriores (Asignacion, VersionPadron, etc.). La decisión fue tomada para mantener el modelo más plano y compatible con el modelo de datos documentado en `04_modelo_de_datos.md`.

## Goals / Non-Goals

**Goals:**

- Crear los modelos ORM `Carrera`, `Cohorte`, `Materia` con mixin base.
- Definir las reglas de unicidad por tenant para cada entidad.
- Implementar ABM REST completo bajo `/api/admin/` para las tres entidades.
- Proteger todos los endpoints con `require_permission("estructura:gestionar")` (rol ADMIN).
- Agregar el permiso `estructura:gestionar` al seed RBAC y asignarlo al rol ADMIN.
- Migración 004 que crea las tres tablas.
- Tests de: CRUD, unicidad por tenant, aislamiento multi-tenant, regla carrera inactiva.

**Non-Goals:**

- Entidad `Dictado` (Materia × Carrera × Cohorte) — diferida.
- Asignación de docentes a materias — C-07.
- Padrón, calificaciones, encuentros, coloquios — C-09+.
- Administración de materias por cohorte o plan de estudios — fuera de MVP.

## Decisions

### D-01: Una migración para las tres tablas

Las tablas `carrera`, `cohorte`, `materia` son independientes entre sí (excepto que `cohorte` tiene FK a `carrera`) y forman un único cambio atómico de schema. Se usan en una sola migración `004_estructura_academica`. Alternativa descartada: tres migraciones separadas (añade complejidad sin beneficio real; no hay módulos intermedios que dependan de solo una de las tres tablas).

### D-02: Permiso único `estructura:gestionar` para los tres ABM

Los tres ABM (carreras, cohortes, materias) están destinados exclusivamente al rol ADMIN. Un único permiso simplifica la matriz y es coherente con el alcance del change. Alternativa descartada: permisos granulares `carreras:gestionar`, `cohortes:gestionar`, `materias:gestionar` — prematura para MVP; se puede particionar en el futuro si surge la necesidad.

### D-03: `estado` como enum de dos valores (Activa/Inactiva)

Las tres entidades tienen el mismo ciclo de vida binario. Soft delete vía `deleted_at` maneja la eliminación lógica; `estado` modela la operatividad de la entidad. Una carrera `Inactiva` no admite nuevas cohortes `Activas`. Una materia `Inactiva` no puede recibir nuevas asignaciones. Alternativa descartada: campo booleano `activa` — menos expresivo que un enum cuando se agregan estados futuros.

### D-04: Unicidad enforceada en DB y en service

Las restricciones de unicidad `(tenant_id, codigo)` en Carrera y Materia, y `(tenant_id, carrera_id, nombre)` en Cohorte se definen como `UniqueConstraint` en el modelo ORM Y se validan en el Service antes de persistir (para retornar 400 con mensaje descriptivo en lugar de dejar que explote la DB con 409 opaco). Alternativa descartada: solo DB constraint — el error de integridad de PostgreSQL es más difícil de mapear a un mensaje amigable de API.

### D-05: Rutas bajo `/api/admin/` (no `/api/v1/`)

El prefijo `/api/admin/` señaliza que estos endpoints son exclusivos del rol ADMIN, separados de los endpoints de dominio que consumirán otros roles en módulos futuros. Es consistente con la convención establecida en ARQUITECTURA.md para ABM administrativos.

## Risks / Trade-offs

- **[Riesgo] Carrera con cohortes activas se desactiva** → La regla "carrera inactiva no admite cohortes abiertas" se aplica al crear/activar una cohorte, pero NO se aplica retroactivamente a cohortes ya abiertas al desactivar una carrera. Mitigación: el service valida al crear/activar cohorte; las cohortes existentes quedan en su estado actual. Este comportamiento queda documentado en el spec.

- **[Riesgo] Materia referenciada por módulos futuros no puede borrarse** → El soft delete protege la integridad referencial (la fila existe pero `deleted_at` está poblado). No hay hard delete. Los módulos futuros filtran por `deleted_at IS NULL` vía el mixin. Mitigación: la restricción es intencional y consistente con el contrato de soft delete de C-02.

- **[Trade-off] Sin Dictado** → Los módulos futuros usan triple FK `(materia_id, carrera_id, cohorte_id)`. Esto introduce algo de redundancia de FK pero evita una entidad intermedia que el modelo de dominio documentado no contempla. Si en el futuro se necesita Dictado, la migración es aditiva (agregar tabla + FK en entidades que la referencian).

## Migration Plan

1. Agregar `estructura:gestionar` a la tabla `permiso` (seed en `rbac_seed.py`).
2. Asignar `estructura:gestionar` al rol ADMIN en `rol_permiso` (seed).
3. Ejecutar migración 004: crea `carrera`, `cohorte`, `materia`.
4. No hay datos previos que migrar; rollback = `op.drop_table` en las tres tablas.

## Open Questions

*(ninguna — ADR-006 resuelto, PA-01 cerrada por decisión de alcance, PA-07 resuelta por el modelo: Cohorte tiene `carrera_id`)*
