> TDD estricto en cada tarea de implementación: RED (test que falla) → GREEN (mínimo) → TRIANGULAR (2+ casos: happy + edge) → REFACTOR. Sin mocks de DB: usar DB efímera de test. Cobertura ≥80% líneas, ≥90% reglas de negocio.

## 1. Preparación y verificación de dependencias

- [ ] 1.1 Inspeccionar el estado real de `backend/app/models/user.py` y de la migración de C-07 (`backend/alembic/versions/`): determinar qué columnas de perfil ya existen (`nombre`, `apellidos`, `dni`, `cuil`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo_profesional`, `facturador`, `estado`)
- [ ] 1.2 Confirmar el número de migración libre siguiente (último actual: `005_estructura_academica`) → planear `006_perfil_y_mensajeria`
- [ ] 1.3 Coordinar con C-07: registrar en el resumen qué columnas agrega ESTE change vs. las ya provistas por C-07 (no duplicar)

## 2. Modelo de perfil (extensión de User/Usuario)

- [ ] 2.1 RED: test de modelo para los campos de perfil faltantes en `User` (al menos `modalidad_cobro` con valores `factura`/`liquidacion`, y los de PII si C-07 no los entregó), incluyendo que la PII se persiste cifrada
- [ ] 2.2 GREEN: agregar los campos faltantes a `backend/app/models/user.py` (cifrados para PII vía patrón existente), mínimo para pasar
- [ ] 2.3 TRIANGULAR: caso `modalidad_cobro` válida vs. valor fuera de dominio; PII cifrada legible vía `encryption_service`
- [ ] 2.4 REFACTOR: limpiar, mantener `<500 LOC`, snake_case

## 3. Repositorio de perfil

- [ ] 3.1 RED: test de `user_repository.get_perfil(tenant_id, user_id)` y `update_perfil(...)` filtrando por tenant; test de que un user de otro tenant no es alcanzable
- [ ] 3.2 GREEN: implementar lectura/actualización de perfil en `backend/app/repositories/user_repository.py` (filtro por `tenant_id` por defecto)
- [ ] 3.3 TRIANGULAR: actualización parcial (solo un campo) preserva el resto; aislamiento cross-tenant negado
- [ ] 3.4 REFACTOR

## 4. Schemas de perfil (Pydantic v2)

- [ ] 4.1 RED: test de `PerfilUpdate` que rechaza `cuil` (`extra='forbid'` → 422) y campos desconocidos; `PerfilRead` expone PII descifrada del dueño
- [ ] 4.2 GREEN: crear `backend/app/schemas/perfil.py` con `PerfilRead` y `PerfilUpdate` (SIN campo `cuil`), `model_config = ConfigDict(extra='forbid')`
- [ ] 4.3 TRIANGULAR: `modalidad_cobro` inválida rechazada; campo extra rechazado; payload válido aceptado
- [ ] 4.4 REFACTOR

## 5. Servicio de perfil

- [ ] 5.1 RED: test de `perfil_service.get_perfil` (descifra PII para el dueño) y `update_perfil` (cifra `dni`/`cbu`/`alias_cbu`, ignora/rechaza `cuil`)
- [ ] 5.2 GREEN: crear `backend/app/services/perfil_service.py` usando `encryption_service` y el repositorio; identidad SIEMPRE del usuario recibido (no del body)
- [ ] 5.3 TRIANGULAR: la PII no aparece en texto plano (verificar logs/respuestas); CUIL inalterado tras update
- [ ] 5.4 REFACTOR

## 6. Router de perfil

- [ ] 6.1 RED: test de endpoints `GET /api/perfil` y `PATCH /api/perfil` con `get_current_user` (identidad del JWT, no del body); 401 sin token; 422 si se envía `cuil`
- [ ] 6.2 GREEN: crear `backend/app/api/v1/routers/perfil.py` (sin lógica de negocio; delega a `perfil_service`); registrar el router en `app.main`
- [ ] 6.3 TRIANGULAR: `usuario_id` en body/query es ignorado (usa `sub` del JWT); update parcial OK; aislamiento por tenant
- [ ] 6.4 REFACTOR

## 7. Modelos de mensajería interna

- [ ] 7.1 RED: test de modelos `HiloMensaje` (`tenant_id`, `asunto`, `iniciado_por`, `destinatario_id`, soft delete) y `MensajeInterno` (`tenant_id`, `hilo_id`, `autor_id`, `cuerpo`, `creado_at`, `leido_at` nullable, soft delete)
- [ ] 7.2 GREEN: crear `backend/app/models/hilo_mensaje.py` y `backend/app/models/mensaje_interno.py` (usar `TenantScopedMixin` + base con soft delete; índices `(tenant_id, destinatario_id)` y `(tenant_id, hilo_id)`)
- [ ] 7.3 TRIANGULAR: hilo con 2 mensajes comparten `hilo_id` y ordenan por `creado_at`; ambos llevan `tenant_id`
- [ ] 7.4 REFACTOR

## 8. Repositorios de mensajería

- [ ] 8.1 RED: test de `hilo_mensaje_repository` (listar hilos donde el user participa, filtro por tenant) y `mensaje_interno_repository` (mensajes de un hilo, marcar leído)
- [ ] 8.2 GREEN: implementar `backend/app/repositories/hilo_mensaje_repository.py` y `mensaje_interno_repository.py` (filtran por tenant por defecto)
- [ ] 8.3 TRIANGULAR: hilo ajeno NO aparece para no-participante; aislamiento cross-tenant; marcado de leído solo de mensajes dirigidos al usuario
- [ ] 8.4 REFACTOR

## 9. Schemas de inbox (Pydantic v2)

- [ ] 9.1 RED: test de `IniciarHilo` (`destinatario_id`, `asunto`, `cuerpo`) y `ResponderMensaje` (`cuerpo`) que rechazan `autor_id`/`remitente_id` y campos extra (`extra='forbid'` → 422)
- [ ] 9.2 GREEN: crear `backend/app/schemas/inbox.py` con `HiloListItem`, `HiloRead`, `MensajeRead`, `IniciarHilo`, `ResponderMensaje`
- [ ] 9.3 TRIANGULAR: payload válido aceptado; `autor_id` en body rechazado; campo desconocido rechazado
- [ ] 9.4 REFACTOR

## 10. Servicio de mensajería

- [ ] 10.1 RED: test de `mensajeria_service`: `listar_inbox`, `abrir_hilo` (marca leído + 403 si no participa), `iniciar_hilo` (remitente = sesión, valida destinatario mismo tenant/activo), `responder` (autor = sesión, 403 si no participa)
- [ ] 10.2 GREEN: crear `backend/app/services/mensajeria_service.py` (identidad del remitente/autor SIEMPRE de la sesión; fail-closed 403 para no-participantes)
- [ ] 10.3 TRIANGULAR: destinatario de otro tenant rechazado; no-participante no abre ni responde; abrir marca leído
- [ ] 10.4 REFACTOR

## 11. Router de inbox

- [ ] 11.1 RED: test de endpoints `GET /api/inbox`, `GET /api/inbox/{hilo_id}`, `POST /api/inbox`, `POST /api/inbox/{hilo_id}/responder` con `get_current_user`; 401 sin token; 403 para no-participante
- [ ] 11.2 GREEN: crear `backend/app/api/v1/routers/inbox.py` (delega a `mensajeria_service`); registrar el router en `app.main`
- [ ] 11.3 TRIANGULAR: participante lee/responde OK; no-participante recibe 403; remitente nunca falsificable desde body
- [ ] 11.4 REFACTOR

## 12. Migración Alembic

- [ ] 12.1 RED: test de migración `006` (upgrade/downgrade) que verifica las tablas `hilo_mensaje`, `mensaje_interno` y las columnas de perfil agregadas por ESTE change
- [ ] 12.2 GREEN: crear `backend/alembic/versions/006_perfil_y_mensajeria.py` (aditiva: solo columnas de perfil faltantes + tablas de mensajería; NO duplicar columnas de C-07)
- [ ] 12.3 TRIANGULAR: downgrade revierte solo lo de esta migración; índices de aislamiento creados
- [ ] 12.4 REFACTOR

## 13. Cierre de sesión (reutilización de C-03)

- [ ] 13.1 Verificar que NO se reimplementa logout en este change; documentar que la UI de perfil invoca `POST /api/auth/logout` (contrato C-03)
- [ ] 13.2 Test/aserción de que no existe endpoint de logout propio bajo `/api/perfil`

## 14. Verificación final

- [ ] 14.1 Ejecutar la suite de tests del change; confirmar cobertura ≥80% líneas y ≥90% en reglas de negocio (CUIL read-only, aislamiento por participante/tenant, PII cifrada)
- [ ] 14.2 Verificar que la PII (`dni`, `cbu`, `alias_cbu`, `cuil`) no aparece en texto plano en logs ni respuestas ajenas
- [ ] 14.3 Marcar tareas `[x]` y registrar desviaciones/decisiones en el resumen y en engram
