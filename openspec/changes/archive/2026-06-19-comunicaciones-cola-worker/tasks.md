## 1. Modelo y migración

- [x] 1.1 Crear enum `EstadoComunicacion` (Pendiente, Enviando, Enviado, Error, Cancelado) en `backend/app/models/comunicacion.py`
- [x] 1.2 Crear modelo `Comunicacion(TenantScopedMixin, Base)` con campos: `enviado_por` (FK→user), `materia_id` (FK→materia, nullable), `destinatario` (Text, cifrado), `destinatario_hash` (String), `asunto` (Text), `cuerpo` (Text), `estado` (String(32), default Pendiente), `lote_id` (UUID, nullable), `requiere_aprobacion` (Boolean, default True), `enviado_at` (DateTime, nullable), más índices para lote_id y estado
- [x] 1.3 Generar migración Alembic para la tabla `comunicacion`

## 2. Repositorio

- [x] 2.1 Crear `ComunicacionRepository(BaseRepository[Comunicacion])` con métodos heredados (get, list, create, soft_delete)
- [x] 2.2 Implementar `list_by_lote(tenant_id, lote_id, session)` filtrando por tenant + lote_id + active
- [x] 2.3 Implementar `list_pendientes_para_worker(tenant_id, limit, session)` con `FOR UPDATE SKIP LOCKED` para registros `estado='Pendiente' AND requiere_aprobacion=false`
- [x] 2.4 Implementar `list_by_estado(tenant_id, estado, session)` para aprobación/cancelación de lote
- [x] 2.5 Implementar `aprobar_lote(tenant_id, lote_id, session)` y `cancelar_lote(tenant_id, lote_id, session)` como operaciones batch

## 3. Schemas Pydantic

- [x] 3.1 Crear `ComunicacionResponse(BaseModel)` con `model_config = ConfigDict(extra='forbid', from_attributes=True)`, exponiendo todos los campos del modelo (el destinatario se descifra en service, no en schema)
- [x] 3.2 Crear `PreviewRequest(asunto_template: str, cuerpo_template: str, destinatarios: list[DestinatarioPreview])` con `ConfigDict(extra='forbid')`
- [x] 3.3 Crear `DestinatarioPreview(email: str, variables: dict[str, str])` con `ConfigDict(extra='forbid')`
- [x] 3.4 Crear `PreviewResponse(items: list[PreviewItem])` con `ConfigDict(extra='forbid')`
- [x] 3.5 Crear `PreviewItem(destinatario: str, asunto_render: str, cuerpo_render: str)` con `ConfigDict(extra='forbid')`
- [x] 3.6 Crear `ComunicacionCreate(asunto_template: str, cuerpo_template: str, destinatarios: list[DestinatarioEnvio], materia_id: UUID | None, requiere_aprobacion: bool | None)` con `ConfigDict(extra='forbid')`
- [x] 3.7 Crear `DestinatarioEnvio(email: str, variables: dict[str, str])` con `ConfigDict(extra='forbid')`
- [x] 3.8 Crear `LoteResponse(lote_id: UUID, items: list[ComunicacionResponse], resumen: LoteResumen)` con `ConfigDict(extra='forbid')`
- [x] 3.9 Crear `LoteResumen(total: int, pendientes: int, enviando: int, enviadas: int, error: int, canceladas: int)` con `ConfigDict(extra='forbid')`
- [x] 3.10 Crear `LoteActionResponse(lote_id: UUID, afectados: int)` con `ConfigDict(extra='forbid')`
- [x] 3.11 Crear `ComunicacionFiltros(estado, lote_id, materia_id, enviado_por, desde, hasta)` con `ConfigDict(extra='forbid')`

## 4. Service de comunicaciones

- [x] 4.1 Crear `ComunicacionService` con `ComunicacionRepository`, `EncryptionService` y tabla `_TRANSICIONES` con la máquina de estados
- [x] 4.2 Implementar `_render_plantilla(template: str, variables: dict[str, str])` con `str.replace()` y validación de variables conocidas
- [x] 4.3 Implementar `preview(tenant_id, data: PreviewRequest) -> PreviewResponse` sin persistir datos
- [x] 4.4 Implementar `crear_lote(tenant_id, enviado_por, data: ComunicacionCreate, session)` creando N registros en una tx, cifrando cada destinatario
- [x] 4.5 Implementar `aprobar(tenant_id, comunicacion_id, session)` validando transición Pendiente→Enviando
- [x] 4.6 Implementar `aprobar_lote(tenant_id, lote_id, session)` aprobando todas las Pendiente del lote
- [x] 4.7 Implementar `cancelar(tenant_id, comunicacion_id, session)` validando transición Pendiente→Cancelado
- [x] 4.8 Implementar `cancelar_lote(tenant_id, lote_id, session)` cancelando todas las Pendiente del lote
- [x] 4.9 Implementar `list(tenant_id, filtros: ComunicacionFiltros, scope_user_id, session)` con filtros tenant-scoped
- [x] 4.10 Implementar `obtener_lote(tenant_id, lote_id, session)` con resumen de estados
- [x] 4.11 Implementar `_cifrar_destinatario(email: str) -> tuple[str, str]` y `_descifrar_destinatario(cifrado: str) -> str`
- [x] 4.12 Implementar `_enviar_email(destinatario: str, asunto: str, cuerpo: str) -> bool` (wrapper sobre SMTP/config de envío)

## 5. Router de API

- [x] 5.1 Crear `backend/app/api/v1/routers/comunicaciones.py` con prefix `/api/comunicaciones` y dependencias
- [x] 5.2 Implementar `GET /api/comunicaciones` (listar con filtros), protegido con `require_permission("comunicacion:enviar")`
- [x] 5.3 Implementar `POST /api/comunicaciones/preview` (preview), protegido con `require_permission("comunicacion:enviar")`
- [x] 5.4 Implementar `POST /api/comunicaciones` (crear lote), protegido con `require_permission("comunicacion:enviar")`
- [x] 5.5 Implementar `POST /api/comunicaciones/{id}/aprobar`, protegido con `require_permission("comunicacion:aprobar")`
- [x] 5.6 Implementar `POST /api/comunicaciones/{id}/cancelar`, protegido con `require_permission("comunicacion:enviar")`
- [x] 5.7 Implementar `POST /api/comunicaciones/lote/{lote_id}/aprobar`, protegido con `require_permission("comunicacion:aprobar")`
- [x] 5.8 Implementar `POST /api/comunicaciones/lote/{lote_id}/cancelar`, protegido con `require_permission("comunicacion:enviar")`
- [x] 5.9 Implementar `GET /api/comunicaciones/lote/{lote_id}`, protegido con `require_permission("comunicacion:enviar")`
- [x] 5.10 Registrar el router en `backend/app/api/v1/__init__.py` o `main.py`

## 6. Worker de comunicaciones

- [x] 6.1 Crear `backend/app/workers/comunicacion_worker.py` con loop async y configuración de polling
- [x] 6.2 Implementar ciclo: pollear Pendiente sin aprobación → marcar Enviando → descifrar destinatario → enviar email → marcar Enviado/Error
- [x] 6.3 Implementar ciclo: pollear Enviando → enviar email → marcar Enviado/Error (para aprobados)
- [x] 6.4 Configurar logging, intervalo de polling, batch_size desde Settings
- [x] 6.5 Actualizar `backend/app/workers/main.py` para disparar el comunicacion_worker

## 7. Tests

- [x] 7.1 Test: máquina de estados rechaza transiciones inválidas (Pendiente→Enviado directo, Enviado→Pendiente, Cancelado→Enviando)
- [x] 7.2 Test: preview renderiza plantillas correctamente con sustitución de variables
- [x] 7.3 Test: preview rechaza variables desconocidas
- [x] 7.4 Test: creación de lote persiste N registros cifrados con mismo lote_id
- [x] 7.5 Test: creación de lote es atómica (falla en mitad → rollback)
- [x] 7.6 Test: destinatario cifrado es ilegible en DB (no contiene el email en texto plano)
- [x] 7.7 Test: aprobación individual transiciona Pendiente→Enviando
- [x] 7.8 Test: aprobación de lote transiciona todas las Pendiente del lote
- [x] 7.9 Test: cancelación individual transiciona Pendiente→Cancelado
- [x] 7.10 Test: cancelación de lote por lote_id transiciona todas las Pendiente
- [x] 7.11 Test: worker procesa Pendiente→Enviado exitosamente
- [x] 7.12 Test: worker marca Error cuando el envío falla
- [x] 7.13 Test: worker ignora Pendientes con requiere_aprobacion=true
- [x] 7.14 Test: listado con filtros retorna resultados correctos por estado, materia, lote
- [x] 7.15 Test: scope propio filtra por enviado_por, scope global retorna todo el tenant
- [x] 7.16 Test: comunicación de otro tenant no es accesible (404)
