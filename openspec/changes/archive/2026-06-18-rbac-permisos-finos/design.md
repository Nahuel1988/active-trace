## Context

C-03 (`auth-jwt-2fa`, archivado) entregó autenticación completa y los modelos `Role` y `UserRole` (este último con vigencia `desde`/`hasta`). `app/core/permissions.py` quedó como stub reservado:

```python
"""RESERVADO para C-04: matriz rol × permiso, require_permission."""
```

Falta toda la capa de **autorización**. La KB exige (regla dura #10, `03_actores_y_roles.md §3`, `08_arquitectura_propuesta.md §3.2`):

- RBAC de permisos finos `modulo:accion`, **sin** flag de superusuario.
- Matriz rol × permiso como **datos administrables por tenant**, no hardcode.
- Permisos efectivos = unión de roles, acotados por **tenant** y por **vigencia** de asignación (`03 §3.2`, `§5`).
- Fail-closed: endpoint sin permiso explícito → 403.
- Identidad/roles/tenant siempre desde el JWT verificado; permisos resueltos server-side por request, jamás en el token.

Estado de migraciones: 001 (tenant/base mixin), 002 (user, role, user_role, refresh_token, totp_secret, password_reset_token). Las tablas `role` y `user_role` YA existen. C-04 agrega `permiso` y `rol_permiso`.

Restricciones de stack (CLAUDE.md): Clean Architecture estricta (Routers → Services → Repositories → Models), repos tenant-scoped por defecto, soft delete siempre, Pydantic `extra='forbid'`, ≤500 LOC por archivo, una migración por cambio de schema, Strict TDD, sin mocks de DB. Governance del dominio: **CRÍTICO** (auth/RBAC) → solo architect, aprobación humana antes de escribir código.

## Goals / Non-Goals

**Goals:**
- Modelar `Permiso` (`modulo:accion`) y la matriz `RolPermiso` como catálogo administrable y tenant-scoped.
- Migración 003 con seed de la matriz base de `03_actores_y_roles.md §3.3` para los 7 roles del dominio.
- Resolver permisos efectivos server-side por request: unión de roles vigentes, scope por tenant.
- Proveer `require_permission("modulo:accion")` fail-closed (403) reutilizable por todo endpoint futuro.
- Distinguir alcance `global` vs `(propio)` y exponerlo para validación de ownership en el Service.
- Endpoints de administración del catálogo (roles, permisos, matriz) protegidos por `usuarios:gestionar`.

**Non-Goals:**
- **Impersonación** (`impersonacion:usar`): el permiso se siembra en el catálogo, pero el flujo de suplantación (sesión distinguible, atribución al actor real) es de un change posterior. C-04 solo registra el permiso.
- **Audit log** (C-05): C-04 no implementa el registro de auditoría; los endpoints administrativos quedan listos para que C-05 los instrumente.
- Reasignación de roles a usuarios desde UI / endpoints de asignación `UserRole` masiva (gestión de equipos docentes con vigencia académica es C-07/C-09); C-04 cubre el CRUD de catálogo + matriz, no la asignación operativa de comisiones.
- Caché de permisos efectivos (Redis): por ahora se resuelve con un query por request; ver Risks.

## Decisions

### D1 — `Permiso` con clave `modulo:accion` desnormalizada
`Permiso` tendrá `modulo` (str) + `accion` (str) y una columna derivada/única `code = "modulo:accion"` por tenant. Se valida formato `^[a-z_]+:[a-z_]+$`.
- **Por qué**: `require_permission("comunicacion:aprobar")` compara contra un único string; tener `code` indexado y único `(tenant_id, code)` hace la resolución un lookup directo. Guardar `modulo`/`accion` por separado permite listar el catálogo agrupado por módulo en la UI de administración.
- **Alternativa descartada**: solo `code` string → pierde la capacidad de agrupar por módulo sin parsear; solo `modulo`+`accion` sin `code` → obliga a concatenar en cada comparación.

### D2 — Matriz `RolPermiso` como tabla de asociación con datos (no enum, no hardcode)
`RolPermiso(tenant_id, role_id, permiso_id, scope)` con PK compuesta `(tenant_id, role_id, permiso_id)`. La matriz de `03 §3.3` se carga como **filas seed** en la migración 003, no como código.
- **Por qué**: regla dura #10 y `03 §3.3` exigen catálogo administrable. Una institución puede añadir/quitar permisos a un rol sin redeploy.
- **`scope`** ∈ {`global`, `propio`} en la fila `RolPermiso`: codifica el `(propio)` de la matriz (ej. PROFESOR `calificaciones:importar` es `propio`, COORDINADOR es `global`). El scope vive en la asociación, no en el permiso, porque depende del rol.
- **Alternativa descartada**: dos permisos distintos (`calificaciones:importar_propio` vs `calificaciones:importar`) → duplica el catálogo y rompe la semántica `modulo:accion` única por capacidad.

### D3 — Resolución de permisos efectivos: un query con join + vigencia, sin permisos en el token
`PermissionService.get_effective_permissions(user_id, tenant_id, now)` ejecuta:
`UserRole` (vigente: `desde ≤ now AND (hasta IS NULL OR now < hasta)`, soft-delete excluido) → `RolPermiso` → `Permiso`, filtrado por `tenant_id`, devolviendo `{code: scope_más_permisivo}`. Si el mismo permiso llega por dos roles con scopes distintos, **global gana sobre propio**.
- **Por qué**: `03 §3.2` define efectivos como unión de roles acotada por tenant y vigencia. Mantener permisos fuera del JWT (regla #8, `08 §3.1`) obliga a resolver por request contra DB; un único query con joins evita N+1.
- **Alternativa descartada**: permisos en el JWT → revocar/cambiar la matriz no surtiría efecto hasta expirar el token (15 min de ventana insegura); contradice la KB.

### D4 — `require_permission` como dependency factory de FastAPI, fail-closed
`require_permission("modulo:accion")` retorna una dependency que: toma `get_current_user` (identidad desde JWT), resuelve permisos efectivos vía `PermissionService`, y si el `code` requerido NO está → `HTTPException(403)`. Si está, retorna un objeto `PermissionGrant(code, scope)` inyectable al Router para pasarlo al Service.
- **Por qué**: declara el permiso por endpoint de forma legible; fail-closed por defecto (regla #10). Exponer el `scope` resuelto permite que el Service aplique la verificación de ownership cuando el scope es `propio`.
- **Alternativa descartada**: decorador sobre la función del Router → FastAPI no inyecta dependencies limpio vía decorador custom; la dependency factory es el patrón idiomático y testeable.

### D5 — La verificación de `(propio)` la hace el Service, no el guard
`require_permission` concede acceso y entrega el `scope`. Cuando `scope == "propio"`, el Service compara la identidad del JWT contra el dueño del recurso solicitado (ej. el `profesor_id` de la comisión). El guard NO conoce el recurso de negocio.
- **Por qué**: regla #11 (sin lógica de negocio en Routers; la pertenencia de un recurso es regla de negocio). El guard es transversal y no debe conocer el modelo de cada feature.
- **Consecuencia para C-04**: como C-04 no tiene recursos de negocio propios aún (solo catálogo, todo `global`), la verificación `propio` se especifica y testea a nivel de `PermissionService.is_allowed(grant, owner_id, current_user_id)` como utilidad reutilizable; los features que la consuman llegan después.

### D6 — Migración 003 incluye seed idempotente por tenant existente
La 003 crea `permiso` y `rol_permiso`, y siembra el catálogo de permisos + la matriz base para los roles ya seedeados. El seed se aplica a cada tenant existente y debe ser idempotente (re-run seguro). Los roles del dominio (incluido NEXO, ausente de la tabla §3.3) se siembran; NEXO se siembra con el conjunto de permisos transversales mínimos documentado en `03 §2`/`§7` (confirmar set exacto — ver Open Questions).
- **Por qué**: regla dura "una migración por cambio de schema" y la KB pide seed de la matriz base. Idempotencia evita romper si la migración corre dos veces o sobre datos parciales.

## Risks / Trade-offs

- **[Un query de permisos por request añade latencia]** → El join está acotado por `tenant_id` + índices en `user_role(user_id, tenant_id)` y `rol_permiso(tenant_id, role_id)`. Si se vuelve cuello de botella, se cachea por (user_id, tenant_id) con invalidación al editar la matriz (out of scope C-04, anotado para C-05+).
- **[Matriz mal seedeada concede permisos de más]** → Dominio CRÍTICO: el seed se deriva 1:1 de `03 §3.3`, se testea que cada celda `✅`/`—`/`(propio)` corresponda a una fila esperada, y se valida fail-closed (un rol sin la fila → 403).
- **[NEXO no figura en la matriz §3.3]** → Riesgo de seedear permisos incorrectos. Mitigación: NEXO se siembra como rol vacío de capacidades de negocio salvo las transversales explícitas (`avisos:confirmar`), hasta cerrar PA-25 (semántica de NEXO). No bloquea C-04 porque NEXO no está en el camino crítico.
- **[Confundir `roles` del token con autorización]** → Los `roles` en el JWT son solo informativos/UX; la autorización SIEMPRE se resuelve desde DB. Se documenta en el spec `auth-session` modificado y se testea que manipular `roles` en el token no altere los permisos efectivos.
- **[Scope `propio` sin recurso que validar en C-04]** → Se entrega la primitiva (`is_allowed`) y sus tests; el riesgo de mal uso queda en los features consumidores, fuera de C-04.

## Migration Plan

1. Alembic `003_rbac`: `create_table permiso`, `create_table rol_permiso` (FKs a `role`, `permiso`, `tenant`; PK compuesta; índices tenant-scoped).
2. Data migration (mismo 003): insertar catálogo de permisos + filas `rol_permiso` de la matriz base, por tenant, idempotente (`ON CONFLICT DO NOTHING` / check-then-insert).
3. Rollback: `downgrade` borra `rol_permiso` y `permiso` (las tablas son nuevas; sin pérdida de datos de auth previos).
4. Despliegue: como `role`/`user_role` ya existen, no hay backfill de asignaciones; los usuarios existentes mantienen sus roles y ganan los permisos efectivos derivados del seed automáticamente.

## Open Questions

- **PA-25 (semántica de NEXO)**: ¿qué permisos exactos lleva NEXO? `03 §3.3` no lo lista. Decisión interina (D6): NEXO solo con permisos transversales (`avisos:confirmar`). Confirmar con el usuario antes de seedear; no bloquea el resto de C-04.
- ¿`impersonacion:usar` y `auditoria:ver` se siembran ya en el catálogo aunque sus flujos sean de changes posteriores? Decisión interina: sí, se registran como permisos en el catálogo (la capacidad existe en `03 §3.1`), pero ningún endpoint los exige en C-04.
- ¿Los endpoints de administración de la matriz deben emitir audit log desde C-04 o esperar a C-05? Decisión interina: dejar el hook listo, instrumentar en C-05.
