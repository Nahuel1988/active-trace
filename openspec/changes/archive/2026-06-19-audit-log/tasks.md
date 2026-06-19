## 1. Catálogo de códigos de acción

- [x] 1.1 Crear `backend/app/core/audit_codes.py` con clase `AuditCodes` que expone las constantes tipadas: `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, `ASIGNACION_MODIFICAR`, `LIQUIDACION_CERRAR`, `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`
- [x] 1.2 Escribir tests unitarios: verificar que cada código es un string con el valor exacto esperado; verificar que mypy acepta `AuditCodes.PADRON_CARGAR` como argumento tipado

## 2. Modelo AuditLog y migración 003

- [x] 2.1 Crear `backend/app/models/audit_log.py` con el modelo SQLAlchemy `AuditLog` (campos: id UUID PK, tenant_id FK, fecha_hora, actor_id FK→User, impersonado_id FK→User nullable, materia_id FK nullable, accion str, detalle JSONB, filas_afectadas int, ip str, user_agent str). Sin `updated_at` ni soft-delete (inmutable por diseño). Sin `__tablename__` que exponga métodos de mutación en la clase.
- [x] 2.2 Crear migración Alembic `004_audit_log`: tabla `audit_log` + índice compuesto `(tenant_id, fecha_hora)` + reglas PostgreSQL `audit_log_no_update` y `audit_log_no_delete` con `op.execute(sa.text(...))`. Downgrade elimina reglas y tabla.
- [x] 2.3 Ejecutar `alembic upgrade head` en el entorno de tests y verificar que la migración aplica sin errores
- [x] 2.4 Escribir tests de migración: insertar un registro, intentar UPDATE directo con `session.execute(text("UPDATE audit_log SET accion=... WHERE id=..."))`, verificar que el registro no cambió; ídem DELETE.

## 3. AuditLogRepository

- [x] 3.1 Crear `backend/app/repositories/audit_log_repository.py` con `AuditLogRepository` que hereda de `BaseRepository[AuditLog]`. Exponer solo: `add(entry: AuditLog) -> AuditLog` y `list(tenant_id: UUID, ...) -> list[AuditLog]`. `update` y `soft_delete` lanzan `NotImplementedError`.
- [x] 3.2 Escribir tests: insertar vía `add`, listar vía `list` scope-tenant; verificar que el list de tenant A no devuelve registros de tenant B; verificar que métodos de mutación lanzan error (5 tests).

## 4. AuditContext y helper audit_action

- [x] 4.1 Crear dataclass `AuditContext` en `backend/app/core/audit.py` con campos: `actor_id: UUID`, `tenant_id: UUID`, `ip: str`, `user_agent: str`, `impersonado_id: UUID | None = None`. Dataclass frozen (inmutable).
- [x] 4.2 Implementar función async `audit_action(ctx: AuditContext, accion: str, detalle: dict, filas_afectadas: int = 0, materia_id: UUID | None = None, repo: AuditLogRepository = ..., session: AsyncSession)` que construye y persiste un `AuditLog`.
- [x] 4.3 Escribir tests unitarios del helper: acción con contexto normal registra correctamente; acción con `impersonado_id` no nulo registra ambos IDs; verificar todos los campos del registro (6 tests: 3 de AuditContext + 3 de audit_action).

## 5. Decorator @audited

- [x] 5.1 Implementar decorator `@audited(accion: str)` en `backend/app/core/audit.py` que envuelve funciones async de routers FastAPI: extrae `AuditContext` del `Request`, llama a `audit_action` solo si la función no lanzó excepción. Asegurar que `filas_afectadas` puede provenir de un campo `_filas_afectadas` en el response o valor 0 por default.
- [x] 5.2 Escribir tests: endpoint decorado que completa con éxito → registro creado; endpoint que lanza HTTPException → sin registro nuevo.

## 6. Extensión de CurrentUser y get_current_user

- [x] 6.1 Actualizar el schema/dataclass `CurrentUser` en `backend/app/core/dependencies.py` (o donde esté definido) para agregar: `impersonated: bool = False` y `actor_id: UUID` (default igual a `user_id`)
- [x] 6.2 Actualizar `get_current_user` para leer `impersonated` y `actor_id` de los claims del JWT verificado y poblar el `CurrentUser` extendido
- [x] 6.3 Actualizar `TokenService.issue_token_pair` para aceptar parámetros opcionales `impersonated: bool = False` y `actor_id: UUID | None = None` e incluirlos en el payload del JWT
- [x] 6.4 Actualizar tests existentes de `get_current_user`: verificar que token normal produce `impersonated=False` y `actor_id=user_id`; agregar caso token de impersonación produce `impersonated=True` y `actor_id` correcto

## 7. Endpoints de impersonación

- [x] 7.1 Crear router `backend/app/routers/impersonation.py` con:
  - `POST /api/auth/impersonate/{user_id}`: require_permission(`impersonacion:usar`); validar mismo tenant, usuario activo, no auto-impersonación; emitir token de impersonación; registrar `IMPERSONACION_INICIAR` en audit log
  - `DELETE /api/auth/impersonate`: validar que el token sea de impersonación (`impersonated=True`); registrar `IMPERSONACION_FINALIZAR`; responder 204
- [x] 7.2 Registrar el router en `backend/app/main.py` bajo el prefix `/api/auth`
- [x] 7.3 Crear schemas Pydantic para la respuesta: `ImpersonationTokenResponse(access_token: str, token_type: str, impersonated_user_id: UUID)`

## 8. Tests de impersonación (Strict TDD — ciclo completo)

- [x] 8.1 Test: POST exitoso devuelve 200 + token válido con claims de impersonación correctos
- [x] 8.2 Test: POST registra `IMPERSONACION_INICIAR` en `audit_log` con `actor_id` del admin e `impersonado_id` del usuario objetivo
- [x] 8.3 Test: POST sin permiso `impersonacion:usar` → 403
- [x] 8.4 Test: POST con `user_id` de otro tenant → 404
- [x] 8.5 Test: POST con `user_id` inexistente → 404
- [x] 8.6 Test: POST con propio `user_id` → 400
- [x] 8.7 Test: DELETE con token de impersonación → 204 + registro `IMPERSONACION_FINALIZAR`
- [x] 8.8 Test: DELETE con token normal → 400

## 9. Integración y cobertura

- [x] 9.1 Ejecutar suite completa de tests (`pytest --cov`); verificar ≥80% líneas y ≥90% reglas de negocio del módulo
- [x] 9.2 Verificar que los tests previos de C-03 (auth) siguen pasando con el `CurrentUser` extendido
- [x] 9.3 Revisar que `AuditContext` puede construirse desde `get_current_user` en un endpoint de prueba; documentar el patrón en un comentario de ejemplo en `audit.py`
