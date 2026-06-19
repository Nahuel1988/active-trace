## Context

C-07 introduce dos piezas fundacionales sobre un dominio CRÍTICO:

1. **Extensión PII del Usuario**: la tabla `user` (creada en C-02 auth) se extiende con DNI, CUIL, CBU, alias_cbu, banco, regional, legajo, legajo profesional y flag `facturador`. Los cuatro primeros son PII regulada por LOPD/Habeas Data y por las reglas duras del proyecto (AES-256, nunca en texto plano, nunca en logs).
2. **Modelo `Asignacion`**: vincula `Usuario × Role × Contexto académico (Materia, Carrera, Cohorte, Comisiones)` con `responsable_id` (jerarquía) y vigencia. Convive con la asociación `UserRole` ya creada por C-03 RBAC, que SÍ tiene `desde/hasta` pero NO tiene contexto académico ni jerarquía.

**Estado actual del repo (verificado leyendo el código):**
- `backend/app/models/user.py` ya cifra `email` (AES-GCM) y mantiene `email_lookup` (HMAC-SHA256) para búsqueda determinística sin descifrar. Reutilizar este patrón.
- `backend/app/core/security.py` expone `encryption_service` singleton y `email_lookup_hash()`. La key vive en `Settings.encryption_key` (32 bytes). No tocar la firma ni la key; sólo consumir.
- `backend/app/models/role.py` define `UserRole` con `(user_id, role_id, tenant_id, desde)` como PK compuesta. Esta asociación NO se modifica en C-07.
- `backend/app/models/permiso.py` define la matriz `RolPermiso`. El resolver de permisos efectivos vive en `backend/app/core/permissions.py` (verificar antes de tocar — checkpoint humano).
- `backend/alembic/versions/` contiene 001…005 (la 005 es C-06 estructura-academica). La próxima es **006**.
- Modelos del catálogo académico (`Carrera`, `Cohorte`, `Materia`) ya existen en `backend/app/models/` (C-06). `Asignacion` los puede referenciar con FK.

**Restricciones inviolables (reglas duras del proyecto):**
- Identidad/roles/tenant SOLO desde JWT verificado. Sin excepciones.
- `tenant_id` en cada tabla, filtrado por repository por defecto.
- RBAC fail-closed con permisos `modulo:accion`.
- Pydantic `extra='forbid'` en todos los schemas.
- Soft delete (`deleted_at`). Nunca hard delete.
- ≤500 LOC por archivo backend.
- Cobertura ≥80% líneas / ≥90% reglas de negocio.
- Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.

**Stakeholders y aprobaciones requeridas:**
- ADMIN del tenant (usuarios finales de `/api/v1/admin/usuarios`).
- COORDINADOR / ADMIN (usuarios finales de `/api/v1/asignaciones`).
- Humano arquitecto (governance CRÍTICO): debe aprobar las decisiones marcadas `[CHECKPOINT]` antes de que el implementador siga.

## Goals / Non-Goals

**Goals:**
- Cifrar en reposo TODA la PII institucional (`dni`, `cuil`, `cbu`, `alias_cbu`) con la misma primitiva ya probada en C-02 (AES-256-GCM con IV de 12 bytes, `base64(iv + ct)`).
- Permitir lookup por DNI o CUIL sin descifrar (HMAC determinístico), si y sólo si el ABM lo requiere — decisión final en §Decisions.
- Modelar `Asignacion` como entidad de primera clase, distinta de `UserRole` pero coherente con el resolver de permisos efectivos.
- Soportar vigencia derivada (`estado_vigencia`) sin almacenarla, calculada en función de `desde`/`hasta` y `NOW()`.
- Filtrar SIEMPRE por `tenant_id` y por `deleted_at IS NULL` en repositorios.
- Mantener compatibilidad con el flujo `/api/v1/auth/register` actual (alumnos auto-registrados); el ABM administrativo es un canal adicional, no un reemplazo.
- Hacer la migración 006 idempotente y reversible (downgrade implementado).

**Non-Goals:**
- NO se reescribe ni se borra `UserRole` (C-03). Sigue siendo la fuente para roles globales del tenant (ADMIN, FINANZAS).
- NO se implementa "asignación masiva" (F4.4) ni "clonar equipos" (F4.5) en C-07 — quedan para C-08.
- NO se implementa la UI: este change es backend-only. El frontend lo consume desde C-21+.
- NO se cambia el algoritmo de cifrado ni la key; se reutiliza `encryption_service`.
- NO se modifica el contrato de JWT (`encode_access_token`).
- NO se agregan `responsable_id` recursivos de más de 1 nivel en validación (la profundidad de jerarquía no se restringe en BD; sólo se valida que el responsable exista y sea del mismo tenant; ciclos detectados al runtime en el service, no por trigger).
- NO se exponen lookups de DNI/CUIL fuera del scope ADMIN.

## Decisions

### D1 — Cifrado de PII: campo por campo, no JSON blob

**Decisión**: cada PII cifrada va en su propia columna `<campo>_encrypted TEXT NOT NULL` (o NULLABLE donde la KB lo permite). NO se serializa un blob JSON con todo cifrado.

**Alternativas consideradas:**
- A. Columna `pii_encrypted JSONB` única → fácil de cifrar, difícil de hacer lookup, viola normalización, complica la migración cuando se agregue un campo.
- B. Tabla satélite `user_pii` con relación 1:1 → aumenta JOINs en cada SELECT, más complejo sin beneficio claro.
- C. **Elegida** Columna por campo con sufijo `_encrypted` → consistente con el patrón ya existente (`email_encrypted`), permite agregar lookup HMAC selectivo, es el patrón ya probado en C-02.

**Rationale**: minimiza el blast radius si rotamos la key (sólo re-cifrar columnas afectadas), permite migrar campo por campo, y el patrón ya existe en producción (no introducir un segundo patrón).

**[CHECKPOINT humano antes de implementar]**: confirmar que todos los 4 campos van como columna individual encrypted y aprobar el set final.

### D2 — Lookup HMAC: SOLO para `email`. DNI / CUIL no por defecto

**Decisión**: NO agregar `dni_lookup` ni `cuil_lookup` en esta migración. La unicidad por DNI/CUIL no es requisito en la KB (`04_modelo_de_datos.md` §E4 solo declara unicidad por email). Si más adelante un ABM lo necesita, se agrega en un change posterior.

**Alternativas consideradas:**
- A. Agregar `dni_lookup` y `cuil_lookup` HMAC ahora "por si acaso" → engorda la tabla y aumenta la superficie de ataque sin uso concreto.
- B. **Elegida** Sólo `email_lookup` (ya existente). Búsqueda por DNI/CUIL en el ABM = descifrar en memoria con paginación pequeña (lista de usuarios de un tenant raramente >10k); si se vuelve un cuello de botella, se agrega lookup en un futuro change.
- C. Búsqueda por trigram sobre ciphertext → imposible (no preserva orden).

**Rationale**: YAGNI + minimizar superficie. El ABM admin lista usuarios paginados por tenant; descifrar 50-100 filas por página es trivial.

**[CHECKPOINT humano antes de implementar]**: confirmar que NO se agrega lookup HMAC para DNI/CUIL. Si el humano dice que SÍ se necesita (porque la KB tiene un caso de uso que se me escapó), agregamos `dni_lookup` y `cuil_lookup` con el mismo helper que ya usa email.

### D3 — `Asignacion` como tabla con contexto polimórfico nullable, NO una tabla por contexto

**Decisión**: `Asignacion` es UNA sola tabla con `materia_id`, `carrera_id`, `cohorte_id` como FKs nullable y `comisiones` como `ARRAY(String)` PostgreSQL. La validez de cada combinación se valida en el service según el rol.

**Alternativas consideradas:**
- A. Una tabla por contexto (`asignacion_materia`, `asignacion_carrera`, `asignacion_cohorte`) → tres caminos para "buscar asignaciones de un usuario"; multiplica los queries en el resolver de permisos; rompe la simetría con la KB E5.
- B. Tabla genérica `(asignacion_id, contexto_tipo, contexto_id)` polimorfismo "rails" → pierde foreign keys reales (integridad referencial frágil), tipo de contexto se vuelve string, y ya hicimos esto mal en otros proyectos.
- C. **Elegida** Una tabla, FKs nullable, validación de combinación válida por rol en el service.

**Reglas de combinación válida (a codificar en `asignacion_service.validate()`):**

| Rol         | materia_id | carrera_id | cohorte_id | comisiones |
|-------------|-----------|-----------|-----------|-----------|
| PROFESOR    | requerido | requerido | requerido | opcional  |
| TUTOR       | requerido | requerido | requerido | opcional  |
| COORDINADOR | opcional  | requerido | opcional  | opcional  |
| NEXO        | opcional  | opcional  | opcional  | opcional  |
| ADMIN       | nulo      | nulo      | nulo      | nulo      |
| FINANZAS    | nulo      | nulo      | nulo      | nulo      |

Para ADMIN y FINANZAS no se crea `Asignacion`: su rol global vive en `UserRole`. Crear una `Asignacion` con esos roles devuelve 400 desde el service.

**[CHECKPOINT humano antes de implementar]**: confirmar la tabla de combinaciones válidas. Si la KB tiene matices distintos (ej: NEXO debe tener al menos `carrera_id`), corregir antes de codear.

### D4 — `estado_vigencia` derivado, no almacenado

**Decisión**: `estado_vigencia` es una propiedad calculada (`@hybrid_property` o método de Python) que devuelve `Vigente` si `desde <= NOW() AND (hasta IS NULL OR hasta >= NOW())`, sino `Vencida`. NO se materializa en columna.

**Alternativas consideradas:**
- A. Columna `estado_vigencia` con default `Vigente`, mantenida por trigger / cron → introduce inconsistencias (¿qué pasa si el cron falla?), agrega complejidad operativa.
- B. **Elegida** Propiedad derivada calculada al leer. Para filtrar por vigencia en queries se usa una cláusula WHERE explícita (`desde <= NOW() AND (hasta IS NULL OR hasta >= NOW())`).

**Rationale**: KB E5 lo declara explícitamente como derivado. Cumple con la fuente de verdad única (las fechas).

### D5 — Resolver de permisos efectivos: UNION (UserRole ∪ Asignacion vigentes)

**Decisión**: en `backend/app/core/permissions.py`, el resolver de roles efectivos de un usuario en una petición une los roles activos provenientes de **dos fuentes**:
- `UserRole` con `hasta IS NULL OR hasta >= NOW()` (rol global tenant).
- `Asignacion` con `desde <= NOW() AND (hasta IS NULL OR hasta >= NOW())` (rol contextual vigente).

Los permisos resultantes son la unión de los permisos de TODOS los roles efectivos. El contexto académico (materia/carrera/cohorte) NO se inyecta automáticamente en `require_permission` en C-07: el endpoint que necesite scoping académico debe filtrar a nivel repository usando el `tenant_id` + el contexto (futuro change C-08 introduce el guard contextual).

**Alternativas consideradas:**
- A. `require_permission` infiere el contexto académico mirando la URL → frágil, acopla el guard a una convención de rutas; viola "fail-closed por defecto" porque depende de inferencia.
- B. Crear un nuevo decorator `require_permission_in_context(perm, ctx_extractor)` → atractivo pero excede el scope de C-07; entra en C-08.
- C. **Elegida** Unión simple. `require_permission(perm)` sólo verifica que el usuario tenga el permiso en ALGUNO de sus roles efectivos. El scoping académico se hace explícito en el query del repository (`asignacion_repo.list_for_user(user_id, materia_id=...)`).

**Rationale**: minimiza el cambio en C-03 (el resolver ya itera UserRole; se agrega un segundo loop sobre Asignacion). Mantiene `require_permission` simple y previsible. C-08 puede introducir guards contextuales sin romper C-07.

**[CHECKPOINT humano antes de implementar]**: confirmar que el resolver une roles de `UserRole` y `Asignacion` vigentes (no intersección, no precedencia), y que el scoping académico queda para C-08. Aprobar el impacto sobre `backend/app/core/permissions.py`.

### D6 — Endpoint shape: `/admin/usuarios` separado de `/usuarios`

**Decisión**: dos prefijos distintos:
- `/api/v1/admin/usuarios` — guard `usuarios:gestionar`. PII descifrada en response (sólo para ADMIN).
- `/api/v1/asignaciones` — guard `equipos:asignar`. NO devuelve PII del usuario más allá de `id`, `nombre`, `apellidos`, `legajo`. Si el frontend necesita CBU/CUIL del docente, lo pide al endpoint admin.

**Alternativas consideradas:**
- A. Un único `/api/v1/usuarios` con campos opcionales filtrados por permiso → mezcla scopes, es fácil filtrar mal y leakear PII.
- B. **Elegida** Dos endpoints, dos guards, dos shapes Pydantic.

**Rationale**: defensive design. Si un coordinador con permiso `equipos:asignar` por error gana acceso al endpoint admin, falla cerrado por permiso, no por filtrado de campos.

### D7 — Soft delete y conservación histórica

**Decisión**:
- `DELETE /admin/usuarios/{id}` → setea `deleted_at = NOW()` Y marca `is_active = false`. NO destruye `Asignacion` históricas del usuario.
- `DELETE /asignaciones/{id}` → setea `deleted_at = NOW()`. La asignación sigue visible bajo el filtro `estado_vigencia=todas`.
- Una asignación con `hasta < NOW()` está **Vencida** pero NO soft-deleted. Son dos cosas distintas:
  - Vencida = no autoriza (rule de negocio temporal).
  - Soft-deleted = anulada administrativamente (un error de carga, una asignación que nunca debió existir).

### D8 — Migración 006: fases idempotentes

**Decisión**: una sola migración Alembic con el siguiente orden:

1. ALTER TABLE `user` ADD COLUMN `nombre VARCHAR(255) NULL`.
2. ALTER TABLE `user` ADD COLUMN `apellidos VARCHAR(255) NULL`.
3. ALTER TABLE `user` ADD COLUMN `dni_encrypted TEXT NULL`.
4. ALTER TABLE `user` ADD COLUMN `cuil_encrypted TEXT NULL`.
5. ALTER TABLE `user` ADD COLUMN `cbu_encrypted TEXT NULL`.
6. ALTER TABLE `user` ADD COLUMN `alias_cbu_encrypted TEXT NULL`.
7. ALTER TABLE `user` ADD COLUMN `banco VARCHAR(255) NULL`.
8. ALTER TABLE `user` ADD COLUMN `regional VARCHAR(255) NULL`.
9. ALTER TABLE `user` ADD COLUMN `legajo_profesional VARCHAR(100) NULL`.
10. ALTER TABLE `user` ADD COLUMN `facturador BOOLEAN NOT NULL DEFAULT false`.
11. CREATE TABLE `asignacion` con todas sus FKs y constraints.
12. CREATE INDEX `ix_asignacion_tenant_usuario`, `ix_asignacion_tenant_responsable`, `ix_asignacion_tenant_deleted`.
13. INSERT INTO `permiso` (seed) los permisos `usuarios:gestionar` y `equipos:asignar` si no existen.

**Downgrade**: drop table `asignacion` + drop columns en orden inverso. NO se borran permisos seed (mantener idempotencia).

**Datos existentes**: las columnas NULLABLE permiten que usuarios pre-existentes (creados en C-02 vía `/auth/register`) sigan funcionando. El ABM admin puede completar los campos faltantes; el flujo `/auth/register` puede o no setearlos según política — decisión a confirmar.

**[CHECKPOINT humano antes de generar la migración]**: confirmar el orden de fases y aprobar que NO se hace backfill automático de columnas PII para usuarios existentes (quedan NULL hasta que el ADMIN los complete).

### D9 — Pydantic schemas: `extra='forbid'` y exposición PII selectiva

**Decisión**: tres shapes para `Usuario`:
- `UsuarioCreate` (admin): acepta PII en claro; se cifra en el repository antes de persistir.
- `UsuarioUpdate` (admin): todos los campos opcionales; se cifra sólo lo que viene.
- `UsuarioResponse` (admin): devuelve PII descifrada (sólo si el caller tiene `usuarios:gestionar`).

Para `Asignacion`:
- `AsignacionCreate`: rol + contexto + responsable + vigencia.
- `AsignacionUpdate`: subset.
- `AsignacionResponse`: incluye un sub-objeto `usuario_minimo` con `id, nombre, apellidos, legajo` (sin PII sensible).

Todos con `model_config = ConfigDict(extra='forbid')`.

### D10 — Validaciones cruzadas tenant

**Decisión**: el service `AsignacionService.create()` verifica:
1. `usuario_id` pertenece al mismo `tenant_id`.
2. Si `materia_id` no es null, la materia es del mismo tenant.
3. Si `carrera_id` no es null, la carrera es del mismo tenant.
4. Si `cohorte_id` no es null, la cohorte pertenece al mismo tenant Y a la `carrera_id` declarada (consistencia academia).
5. `responsable_id`, si existe, es del mismo tenant.
6. `responsable_id != usuario_id` (no auto-supervisión).
7. La combinación `rol → contexto` cumple la tabla D3.
8. `desde <= hasta` cuando ambas existen.

Cualquier violación → `HTTPException(422)` con detalle del campo.

## Risks / Trade-offs

- **R1 — Re-cifrado masivo de PII si rota la encryption key.**
  - **Mitigación**: la rotación de key NO está en el scope de C-07. Si en el futuro se implementa, este change deja el patrón columna-por-columna que permite hacerlo gradualmente. Documentar en runbook.
- **R2 — Búsqueda por DNI/CUIL lenta sin lookup HMAC.**
  - **Mitigación**: paginación pequeña en el ABM admin (50 filas default, max 200). Si crece la base, se agrega `dni_lookup` en un change posterior sin breaking.
- **R3 — Inconsistencia `UserRole` ↔ `Asignacion` (mismo rol declarado en ambas tablas).**
  - **Mitigación**: el resolver hace UNION, los duplicados de rol no rompen permisos (sólo se cuentan una vez vía `set`). Documentar la convención: ADMIN/FINANZAS van en `UserRole`; PROFESOR/TUTOR/COORDINADOR/NEXO van en `Asignacion`. La asignación masiva (C-08) debe respetar esta convención.
- **R4 — Strict TDD obliga a pensar el modelo antes de codear, lo que ralentiza el RED inicial.**
  - **Mitigación**: este design.md define el contrato de los services; el implementador puede escribir tests de modelo unitario antes de levantar Postgres real.
- **R5 — PII leak en logs si alguien hace `logger.info(f"creando usuario {usuario_create}")`.**
  - **Mitigación**: los schemas Pydantic implementan `__repr__` que enmascara los campos sensibles. Test obligatorio: `repr(UsuarioCreate(dni='12345678', ...))` NO contiene `'12345678'`. Además el observability logger del proyecto (C-01) ya tiene una lista de campos a sanitizar — agregar `dni`, `cuil`, `cbu`, `alias_cbu`.
- **R6 — Endpoint admin expone PII descifrada: cualquier compromiso del rol ADMIN compromete PII de todo el tenant.**
  - **Mitigación**: governance CRÍTICO + audit log obligatorio para todas las operaciones del ABM (ya hay capacidad `audit-log` en C-05). El service emite eventos `USUARIO_CREAR`, `USUARIO_MODIFICAR`, `USUARIO_BAJA`.
- **R7 — La tabla de combinaciones rol×contexto puede tener huecos no contemplados.**
  - **Mitigación**: checkpoint humano explícito en D3 antes de codear.

## Migration Plan

1. **Pre-deploy**: ejecutar `alembic upgrade 006` en staging. Verificar:
   - Tabla `user` tiene las nuevas columnas.
   - Tabla `asignacion` existe con todas las constraints.
   - Seeds de permisos `usuarios:gestionar` y `equipos:asignar` presentes.
2. **Smoke tests**:
   - Crear un usuario vía `/admin/usuarios` con todos los campos PII; verificar que la BD muestra ciphertext en `dni_encrypted`/`cbu_encrypted`/etc. (consulta SQL directa).
   - Listar usuarios vía `/admin/usuarios` con un caller ADMIN; verificar que PII viene descifrada en la response.
   - Listar usuarios con un caller PROFESOR; verificar 403.
   - Crear una asignación vía `/asignaciones` con `desde=ayer, hasta=mañana`; el resolver de permisos del usuario incluye el rol.
   - Vencer la asignación (`hasta=ayer`); el resolver NO incluye el rol.
3. **Deploy a prod**: misma migración. Usuarios pre-existentes quedan con PII NULL hasta que el ADMIN los complete.
4. **Rollback**:
   - `alembic downgrade 005`.
   - Drop columnas + drop tabla `asignacion`.
   - Endpoints ya no rutean (router registrado en `app/main.py` se removerá vía el mismo PR; rollback de código).
   - **Atención**: una vez que un usuario tenga PII cifrada, downgrade pierde esa información. Documentar en el runbook y NO hacer downgrade en prod tras una activación real.

## Open Questions

1. **¿Hay que registrar acciones del ABM en el audit log automáticamente?**
   - Decisión inicial: sí, vía hook en el service (USUARIO_CREAR, USUARIO_MODIFICAR, USUARIO_BAJA, ASIGNACION_CREAR, ASIGNACION_MODIFICAR, ASIGNACION_BAJA). Confirmar con el humano si el código de acción tiene una convención más estricta en C-05.
2. **¿El flujo `/auth/register` actual debe poblar `nombre` y `apellidos`?**
   - Sugerencia: agregar campos opcionales `nombre`/`apellidos` a `RegisterRequest` (no PII, no breaking). Confirmar.
3. **¿La unicidad `(tenant_id, email_lookup)` se preserva tal cual?**
   - Sí, la migración 006 no la toca. Sólo agrega columnas.
4. **¿Comisiones se modelan como `ARRAY(String)` PostgreSQL o como tabla satélite `asignacion_comision`?**
   - Decisión inicial: `ARRAY(String)` por simplicidad y porque la KB no exige normalización. Se puede normalizar luego si los reports lo requieren.
5. **¿Qué permisos exactos se asocian a `usuarios:gestionar` y `equipos:asignar` en el seed?**
   - Inicial: ambos son auto-permisos atómicos para sus endpoints. El seed los crea y los asigna al rol ADMIN. `equipos:asignar` también al rol COORDINADOR. Confirmar.
6. **`responsable_id` jerarquía: ¿se valida ciclo o no?**
   - Decisión inicial: SÍ, en el service, con un walk-up limitado a depth=10. Si se detecta ciclo, 422. Bajo costo y previene corrupción de datos.

Todas estas preguntas se resuelven en los CHECKPOINTS de `tasks.md` antes de que el implementador escriba código.
