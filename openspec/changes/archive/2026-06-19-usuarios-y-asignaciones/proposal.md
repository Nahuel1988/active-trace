## Why

El sistema necesita gestionar el ciclo de vida de los usuarios del tenant y las asignaciones que los vinculan con roles en contextos académicos concretos (materia × carrera × cohorte × comisiones). Hoy `User` solo expone email y password (C-02/C-03): no almacena PII institucional (DNI, CUIL, CBU, alias, banco, regional, legajo, legajo profesional, facturador) ni permite ABM administrativo, y la asociación `UserRole` actual carece de contexto académico, jerarquía (`responsable_id`) y vigencia explícita por contexto. Sin ambas piezas no podemos armar equipos docentes (F4.1, F4.3), modelar la cadena de responsabilidad coordinador → docente, ni autorizar acciones acotadas a una materia/cohorte sin filtrar por algo que el sistema no representa.

## What Changes

- **Usuario (extensión PII)**
  - Extender la tabla `user` con columnas cifradas AES-256-GCM: `dni_encrypted`, `cuil_encrypted`, `cbu_encrypted`, `alias_cbu_encrypted`.
  - Agregar columnas claras (no sensibles): `nombre`, `apellidos`, `banco`, `regional` (nullable), `legajo_profesional` (nullable), `facturador` (booleano, default `false`).
  - Reutilizar `legajo` ya existente (atributo de negocio, no credencial).
  - Conservar `email_encrypted` + `email_lookup` (HMAC) y la unicidad `(tenant_id, email_lookup)` ya implementadas en C-02.
  - Helpers de lookup determinístico opcionales para `dni` y `cuil` (HMAC) si el ABM lo requiere — decisión a confirmar en design.
- **Asignación (nueva entidad)**
  - Nuevo modelo `Asignacion` que vincula `usuario_id` ↔ `role_id` ↔ contexto académico `(materia_id?, carrera_id?, cohorte_id?, comisiones[])`, con `responsable_id` (jerarquía), `desde` / `hasta` y `estado_vigencia` derivado por fechas (no persistido).
  - `Asignacion` convive con `UserRole` (C-03 RBAC): `UserRole` queda como vínculo global usuario↔rol-en-tenant (para roles sin contexto como ADMIN o FINANZAS); `Asignacion` añade la dimensión académica para roles operativos (PROFESOR, TUTOR, COORDINADOR, NEXO). El detalle de coexistencia, incluida la fuente de verdad de los roles efectivos en `require_permission`, va al design.
  - Una asignación vencida (`hasta < hoy`) no otorga permisos pero se conserva (histórico, sin hard delete).
- **API REST**
  - `BREAKING` parcial: el endpoint `/api/v1/auth/register` deja de ser el único punto de creación de usuarios. Se introducen los siguientes:
  - ABM Usuarios: `GET/POST/PUT/DELETE /api/v1/admin/usuarios` — guard `usuarios:gestionar` (rol ADMIN). DELETE = soft delete.
  - CRUD Asignaciones: `GET/POST/PUT/DELETE /api/v1/asignaciones` — guard `equipos:asignar` (roles COORDINADOR, ADMIN). DELETE = soft delete (no destruye histórico).
  - Filtros disponibles para `GET /asignaciones`: por `usuario_id`, `materia_id`, `carrera_id`, `cohorte_id`, `rol`, `estado_vigencia` (vigente / vencida / todas).
- **Migraciones**
  - Una sola migración Alembic `006_usuarios_y_asignaciones.py` con dos pasos lógicos: (a) ALTER `user` agregando columnas, (b) CREATE TABLE `asignacion`. Confirmado que `005` queda reservada para C-06 estructura-academica.
- **Validación Pydantic**
  - Schemas `UsuarioCreate`, `UsuarioUpdate`, `UsuarioResponse`, `AsignacionCreate`, `AsignacionUpdate`, `AsignacionResponse` con `extra='forbid'`. Los DTOs response NO incluyen ciphertext: sólo PII descifrada bajo permiso explícito, o totalmente omitida si no aplica el alcance del endpoint.
- **Logs y observabilidad**
  - El logger debe mascarar siempre `dni`, `cuil`, `cbu`, `alias_cbu`, `email` (texto plano), repitiendo el patrón ya usado por `email` en C-02.

## Capabilities

### New Capabilities
- `usuario-pii-extendida`: Extensión del modelo Usuario con PII cifrada (dni, cuil, cbu, alias_cbu) y atributos institucionales (nombre, apellidos, banco, regional, legajo, legajo_profesional, facturador). Define qué se cifra, qué se enmascara en logs/respuestas y qué identificadores son únicos por tenant.
- `usuarios-abm`: ABM de usuarios del tenant vía `/api/v1/admin/usuarios` con guard `usuarios:gestionar`. Operaciones: alta, edición, baja lógica, listado paginado. Define cómo se entrega PII descifrada al ADMIN sin filtrarse por otros canales.
- `asignacion-modelo`: Entidad `Asignacion` que vincula usuario × rol × contexto académico, con vigencia y jerarquía. Define qué combinaciones de contexto son válidas para cada rol y cómo se calcula `estado_vigencia`.
- `asignacion-crud`: CRUD de asignaciones vía `/api/v1/asignaciones` con guard `equipos:asignar`. Define filtros, paginación, validaciones cruzadas con `Carrera`/`Cohorte`/`Materia` (todas del mismo tenant) y comportamiento ante intentos de borrado destructivo.

### Modified Capabilities
- `user-identity`: La identidad del usuario incorpora atributos PII cifrados adicionales (`dni`, `cuil`, `cbu`, `alias_cbu`) y atributos institucionales. La unicidad `(tenant_id, email_lookup)` se mantiene; se decide en design si se agrega lookup HMAC para `dni`/`cuil`. La regla de oro "identidad SIEMPRE desde la sesión" sigue intacta.
- `rbac-effective-permissions`: La derivación de permisos efectivos del usuario en una petición debe consultar tanto `UserRole` (rol global del tenant) como `Asignacion` (rol contextual vigente), unión, acotada por vigencia. El diseño exacto (qué fuente prima cuando hay conflicto, cómo se inyecta el contexto académico en `require_permission`) va al design y se valida con el humano antes de implementar.

## Impact

- **Código backend afectado**:
  - `backend/app/models/user.py` — nuevas columnas (Alter table).
  - `backend/app/models/asignacion.py` — nuevo (CREATE).
  - `backend/app/models/__init__.py` — registrar `Asignacion`.
  - `backend/app/schemas/usuario.py`, `backend/app/schemas/asignacion.py` — nuevos.
  - `backend/app/repositories/usuario_repository.py`, `asignacion_repository.py` — nuevos.
  - `backend/app/services/usuario_service.py`, `asignacion_service.py` — nuevos.
  - `backend/app/api/v1/routers/admin_usuarios.py`, `asignaciones.py` — nuevos; registrar en `app/main.py`.
  - `backend/app/core/permissions.py` — extender el resolver de roles efectivos para incluir `Asignacion` (decisión a confirmar en design por su impacto en C-03).
  - `backend/alembic/versions/006_usuarios_y_asignaciones.py` — nueva migración.
- **APIs**: dos nuevos prefijos `/api/v1/admin/usuarios` y `/api/v1/asignaciones`. No se modifican los contratos de auth/refresh/me ya estables.
- **Dependencias**: ninguna nueva (`cryptography` AES-GCM ya está disponible vía C-02).
- **Datos en producción**: la migración 006 agrega columnas NULLABLE primero y backfill diferido (o constante simbólica cifrada para no romper NOT NULL). El plan exacto se decide en design (Tabla de fases) y se aprueba con el humano antes de generar la migración.
- **Catálogo RBAC**: seeds nuevos para los permisos `usuarios:gestionar` y `equipos:asignar` (este último ya está documentado en la KB §3.1 pero conviene verificar el seed real de C-03).
- **Cobertura de tests**: ≥80% líneas / ≥90% reglas de negocio; tests obligatorios de PII (cipher round-trip, no log/no response leak), unicidad email por tenant, vigencia (vencida no autoriza), multi-rol, jerarquía `responsable_id`, filtrado tenant.
- **Riesgo**: CRÍTICO. Modifica el modelo de identidad (PII) y el cálculo de permisos efectivos, ambos dominios CRÍTICOS según governance. Se requiere validación humana explícita en los checkpoints declarados en `tasks.md` antes de avanzar fases de implementación.
