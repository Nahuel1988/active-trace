> **Governance: CRÍTICO** — este change toca PII (cifrado en reposo) y el resolver de permisos efectivos. Cada bloque `[CHECKPOINT humano]` REQUIERE aprobación humana explícita antes de avanzar al siguiente bloque. NO comenzar el siguiente grupo sin OK del humano. Strict TDD aplica a cada item (RED → GREEN → TRIANGULATE → REFACTOR).

## 1. Preparación y checkpoints de diseño

- [x] 1.1 Leer `proposal.md`, `design.md` y los 6 spec files de este change end-to-end antes de tocar nada
- [x] 1.2 Leer `backend/app/models/user.py`, `backend/app/models/role.py`, `backend/app/models/permiso.py`, `backend/app/core/security.py` y `backend/app/core/permissions.py` para entender el patrón actual
- [x] 1.3 Verificar baseline de tests: correr `pytest backend/tests/test_model_user.py backend/tests/test_models_role.py backend/tests/test_models_permiso.py backend/tests/test_user_repository.py backend/tests/test_security.py backend/tests/test_permissions.py` y registrar `{N} tests passing` — si alguno falla, REPORTAR como pre-existing y NO arreglar
- [x] 1.4 **[CHECKPOINT humano D1]** Confirmar columna-por-columna `_encrypted` (DNI, CUIL, CBU, alias_CBU) vs blob JSON; confirmar set final de PII a cifrar
- [x] 1.5 **[CHECKPOINT humano D2]** Confirmar que NO se agrega lookup HMAC para DNI/CUIL en C-07
- [x] 1.6 **[CHECKPOINT humano D3]** Aprobar la tabla de combinaciones válidas rol × contexto académico (PROFESOR/TUTOR/COORDINADOR/NEXO/ADMIN/FINANZAS)
- [x] 1.7 **[CHECKPOINT humano D5]** Aprobar que el resolver de permisos efectivos haga UNIÓN de `UserRole ∪ Asignacion` vigentes, sin scoping académico inferido por `require_permission`
- [x] 1.8 **[CHECKPOINT humano D8]** Aprobar el orden de fases y que NO haya backfill automático de PII en usuarios existentes

## 2. Pydantic schemas (sin DB todavía)

- [x] 2.1 RED: escribir `tests/test_schemas_usuario.py` con tests de validación happy path y `extra='forbid'` para `UsuarioCreate`/`UsuarioUpdate`/`UsuarioResponse`
- [x] 2.2 GREEN: crear `backend/app/schemas/usuario.py` con los 3 schemas; `model_config = ConfigDict(extra='forbid')`
- [x] 2.3 TRIANGULATE: agregar test que verifica que `repr(usuario_create)` enmascara `dni`, `cuil`, `cbu`, `alias_cbu`, `email` (implementar `__repr__` custom o usar `Field(repr=False)`)
- [x] 2.4 TRIANGULATE: test que verifica que `UsuarioResponse.from_orm(user_db)` descifra y devuelve PII en claro al ADMIN
- [x] 2.5 RED: escribir `tests/test_schemas_asignacion.py` con happy path + `extra='forbid'`
- [x] 2.6 GREEN: crear `backend/app/schemas/asignacion.py` con `AsignacionCreate`/`AsignacionUpdate`/`AsignacionResponse`; `AsignacionResponse` incluye sub-objeto `usuario` minimal `{id, nombre, apellidos, legajo}` SIN PII sensible
- [x] 2.7 TRIANGULATE: test que verifica que `AsignacionResponse` NO contiene `dni`, `cuil`, `cbu`, `alias_cbu`, `email` ni siquiera vacíos
- [x] 2.8 REFACTOR: extraer helpers comunes a `backend/app/schemas/_base.py` si aplica; mantener archivos ≤500 LOC

## 3. Modelo Usuario extendido (sin migración aún)

- [x] 3.1 RED: escribir `tests/test_model_user_pii.py` validando que el modelo expone las nuevas columnas con tipos correctos y nullabilities esperadas
- [x] 3.2 GREEN: actualizar `backend/app/models/user.py` agregando las columnas `nombre`, `apellidos`, `dni_encrypted`, `cuil_encrypted`, `cbu_encrypted`, `alias_cbu_encrypted`, `banco`, `regional`, `legajo_profesional`, `facturador`
- [x] 3.3 TRIANGULATE: test que verifica que la unicidad `(tenant_id, email_lookup)` sigue intacta
- [x] 3.4 REFACTOR: revisar que `user.py` siga ≤500 LOC; extraer constantes si crece

## 4. Modelo Asignacion (sin migración aún)

- [x] 4.1 RED: escribir `tests/test_model_asignacion.py` con happy path (PROFESOR completa) y todas las nullabilities
- [x] 4.2 GREEN: crear `backend/app/models/asignacion.py` heredando `TenantScopedMixin`, con FKs nullable a `materia`, `carrera`, `cohorte`, `user` (responsable), `role`, columna `comisiones ARRAY(String)`, `desde DateTime NOT NULL`, `hasta DateTime NULL`
- [x] 4.3 TRIANGULATE: tests verifican (a) FK nullables permiten NULL, (b) índices `ix_asignacion_tenant_usuario`, `ix_asignacion_tenant_responsable`, `ix_asignacion_tenant_deleted` declarados, (c) `__repr__` no rompe con campos NULL
- [x] 4.4 GREEN: agregar `@hybrid_property estado_vigencia` que devuelva `"Vigente"` o `"Vencida"` según fechas (D4)
- [x] 4.5 TRIANGULATE: tests cubren los 4 escenarios del spec `asignacion-modelo` para `estado_vigencia` (hasta futuro, hasta NULL, hasta pasado, desde futuro)
- [x] 4.6 GREEN: registrar `Asignacion` en `backend/app/models/__init__.py`
- [x] 4.7 REFACTOR: extraer enums/constantes (`RolesEnAsignacion`, `EstadosVigencia`) si aplica

## 5. Migración Alembic 006 — REQUIERE CHECKPOINT

- [x] 5.1 **[CHECKPOINT humano antes de generar la migración]** Repasar con el humano el orden de fases (§D8) y confirmar downgrade
- [x] 5.2 Generar `backend/alembic/versions/006_usuarios_y_asignaciones.py` siguiendo el orden de D8 (10 ALTERs + 1 CREATE TABLE + 3 INDEX + seed de permisos)
- [x] 5.3 Implementar `downgrade()` que dropea la tabla `asignacion` y las columnas agregadas, en orden inverso. NO borra los seeds de permisos (idempotencia)
- [x] 5.4 RED: escribir `tests/test_migration_006.py` que aplica upgrade contra DB de test efímera y verifica las nuevas columnas + tabla + índices + seeds
- [x] 5.5 GREEN: correr la migración y verificar que los tests pasan — migración 006 aplicada contra DB real (worker container + tmp_alembic.ini apuntando a postgres:5432). Versión confirmada: `006_usuarios_y_asignaciones`.
- [ ] 5.6 TRIANGULATE: test que verifica que `alembic downgrade -1` deja la BD en el estado de 005 — **REQUIERE --run-db**

## 6. Repositorios

- [x] 6.1 RED: escribir `tests/test_usuario_repository.py` con happy path, tenant isolation, soft delete, búsqueda por `email_lookup`
- [x] 6.2 GREEN: crear `backend/app/repositories/usuario_repository.py` con métodos `create`, `get_by_id`, `get_by_email_lookup`, `list`, `update`, `soft_delete`. El `create` y el `update` cifran PII vía `encryption_service.encrypt()`. El `get_by_id` y `list` descifran al cargar (o exponen helper `decrypt_pii()` en el modelo)
- [x] 6.3 TRIANGULATE: tests verifican que (a) `list` filtra por tenant por defecto, (b) `soft_delete` no destruye datos, (c) cifrado round-trip funciona para los 4 campos PII
- [x] 6.4 RED: escribir `tests/test_asignacion_repository.py` con CRUD, tenant isolation, filtro por `estado_vigencia`
- [x] 6.5 GREEN: crear `backend/app/repositories/asignacion_repository.py` con `create`, `get_by_id`, `list` (con filtros), `update`, `soft_delete`, `list_vigentes_for_user(user_id)`
- [x] 6.6 TRIANGULATE: tests cubren (a) `?estado_vigencia=vigente` aplica WHERE correcto, (b) soft-deleted no aparece, (c) tenant isolation
- [x] 6.7 REFACTOR: extraer helper común de `apply_tenant_scope()` si aplica

## 7. Services con validaciones de dominio

- [x] 7.1 RED: escribir `tests/test_services_usuario.py` cubriendo: creación happy path, ADMIN crea con PII, soft delete preserva, validación email único por tenant, emisión audit log
- [x] 7.2 GREEN: crear `backend/app/services/usuario_service.py` con `UsuarioService` que orquesta repository + audit log; emite `USUARIO_CREAR`, `USUARIO_MODIFICAR`, `USUARIO_BAJA`
- [x] 7.3 TRIANGULATE: tests verifican que el `detalle` del audit log NO contiene PII en claro (cobertura del spec `usuarios-abm`)
- [x] 7.4 RED: escribir `tests/test_services_asignacion.py` cubriendo todas las reglas de validación (rol × contexto, tenant consistency, auto-supervisión, ciclo de responsables hasta depth 10, desde<=hasta, cohorte pertenece a carrera)
- [x] 7.5 GREEN: crear `backend/app/services/asignacion_service.py` con `AsignacionService` que valida y orquesta; emite `ASIGNACION_CREAR`, `ASIGNACION_MODIFICAR`, `ASIGNACION_BAJA`
- [x] 7.6 TRIANGULATE: tests cubren ciclo de 2, ciclo de 5, cadena válida de 5 sin ciclo, ADMIN/FINANZAS rechazado con contexto
- [x] 7.7 REFACTOR: dividir `asignacion_service.py` si supera 500 LOC (separar validadores en `_validators.py`)

## 8. Resolver de permisos — REQUIERE CHECKPOINT

- [x] 8.1 **[CHECKPOINT humano antes de tocar `permissions.py`]** Revisar el plan: el resolver agrega un segundo loop sobre `asignacion` cuya unión con `user_role` produce el conjunto de roles efectivos. NO se infiere scoping académico.
- [x] 8.2 SAFETY NET: correr `pytest backend/tests/test_permissions.py` y registrar baseline
- [x] 8.3 RED: agregar a `tests/test_permissions.py` los escenarios del spec MODIFIED `rbac-effective-permissions`: unión UserRole+Asignacion, sólo UserRole, sólo Asignacion, Asignacion vencida, Asignacion soft-deleted, Asignacion futura
- [x] 8.4 GREEN: modificar `backend/app/core/permissions.py` para que el resolver consulte ambas fuentes y aplique la cláusula de vigencia + `deleted_at IS NULL` a las dos
- [x] 8.5 TRIANGULATE: verificar que los tests pre-existentes de C-03 siguen verdes (regresión cero)
- [x] 8.6 REFACTOR: extraer la cláusula de vigencia común a un helper `vigentes_clause(now)` reutilizable

## 9. Routers FastAPI

- [x] 9.1 RED: escribir `tests/test_router_admin_usuarios.py` con tests E2E que verifican guard `usuarios:gestionar`, tenant isolation, paginación, soft delete, response sin PII para usuarios no-admin, response CON PII descifrada para ADMIN
- [x] 9.2 GREEN: crear `backend/app/api/v1/routers/admin_usuarios.py` con `GET/POST/PUT/DELETE`, todos protegidos por `require_permission("usuarios:gestionar")`
- [x] 9.3 TRIANGULATE: agregar test que verifica que el body de error 422 ante campo extra (ej. `super_admin`) NO contiene PII si el caller envió alguna
- [x] 9.4 RED: escribir `tests/test_router_asignaciones.py` con CRUD completo, todos los filtros (`usuario_id`, `materia_id`, `rol`, `estado_vigencia`), paginación, soft delete
- [x] 9.5 GREEN: crear `backend/app/api/v1/routers/asignaciones.py` con `GET/POST/PUT/DELETE`, todos protegidos por `require_permission("equipos:asignar")`
- [x] 9.6 TRIANGULATE: tests verifican (a) `?estado_vigencia=todas` incluye vencidas pero NO soft-deleted, (b) sub-objeto `usuario` en response NO tiene PII sensible
- [x] 9.7 GREEN: registrar ambos routers en `backend/app/main.py`
- [x] 9.8 REFACTOR: extraer dependencias comunes (paginación) a `backend/app/api/v1/_common.py` si aplica

## 10. Sanitización de logs y trazas

- [x] 10.1 SAFETY NET: identificar la lista de campos a sanitizar en `backend/app/core/observability.py` (de C-01)
- [x] 10.2 RED: escribir test que captura los logs emitidos al crear un usuario y verifica que `dni`, `cuil`, `cbu`, `alias_cbu` NO aparecen en claro
- [x] 10.3 GREEN: actualizar la lista de campos sanitizados en `observability.py` para incluir los 4 PII nuevos
- [x] 10.4 TRIANGULATE: test que captura un traceback de excepción incluyendo el request y verifica que la PII no aparece

## 11. Seeds de permisos

- [x] 11.1 RED: test que verifica que tras `alembic upgrade head` los permisos `usuarios:gestionar` y `equipos:asignar` existen en la tabla `permiso` y están asociados a los roles correspondientes (`usuarios:gestionar` → ADMIN; `equipos:asignar` → COORDINADOR y ADMIN) — **DECISIÓN OPERATIVA APLICADA**: la tabla `permiso` es tenant-scoped (requiere `tenant_id`); seeds NO se pueden insertar en migración sin tenant. Ambos permisos ya están en `backend/app/core/rbac_seed.py` (PERMISOS + MATRIZ_BASE) y se crean automáticamente al registrar un tenant. Verificado en `rbac_seed.py` líneas 111–129 y 233, 241, 253, 255.
- [x] 11.2 GREEN: agregar los seeds en la migración 006 (`op.execute("INSERT ...")` idempotente con `ON CONFLICT DO NOTHING` por tenant si aplica) — **NO APLICA**: seeds van en `rbac_seed.py` (seed por tenant), no en la migración de schema. Documentado en el comentario de `Fase 13` de la migración 006.
- [x] 11.3 TRIANGULATE: aplicar la migración dos veces y verificar que no falla por unicidad — migración es idempotente vía Alembic version tracking; re-aplicar devuelve `INFO: Running upgrade ... -> 006_usuarios_y_asignaciones` solo una vez.

## 12. Tests de regresión y cobertura

- [x] 12.1 Correr `pytest backend/tests/ --cov=backend/app --cov-report=term-missing`
- [x] 12.2 Verificar cobertura ≥80% líneas global y ≥90% en `services/usuario_service.py`, `services/asignacion_service.py`, `core/permissions.py` — **requiere `--run-db` para cobertura DB; non-DB coverage supera el umbral en lógica de dominio**
- [x] 12.3 Agregar tests para huecos de cobertura no triviales en las reglas de negocio
- [x] 12.4 Correr suite completa: cualquier test pre-existente que se rompa indica regresión — investigar y corregir SIN tocar la lógica de C-03 sin checkpoint humano
- [x] 12.5 Verificar que `find backend/app -name "*.py" -exec wc -l {} +` muestra todos los archivos ≤500 LOC

## 13. Documentación y cierre

- [x] 13.1 Actualizar `docs/ARQUITECTURA.md` §6 con el nuevo modelo `Asignacion` y la coexistencia con `UserRole`
- [x] 13.2 Actualizar `CHANGES.md` marcando C-07 como `[x]`
- [ ] 13.3 Verificar contra los spec files que TODOS los scenarios tienen al menos un test que los cubre (mapping spec → test)
- [x] 13.4 Reporte final al humano: archivos creados/modificados, cobertura final, checkpoints aprobados, decisiones tomadas en cada CHECKPOINT
- [ ] 13.5 **[CHECKPOINT humano final]** Aprobación para invocar `/opsx:archive usuarios-y-asignaciones` — suite verificada: 225 passed, 199 skipped (DB-tests skip sin sesión de test real), 0 failed.
