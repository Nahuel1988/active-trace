## 1. Modelos ORM

- [x] 1.1 Crear `backend/app/models/aviso.py`: modelo `Aviso` con mixin base (`id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`), columnas `alcance` (enum `AlcanceAviso`: Global/PorMateria/PorCohorte/PorRol), `materia_id` (FK → materia.id, nullable), `cohorte_id` (FK → cohorte.id, nullable), `rol_destino` (String, nullable), `severidad` (enum `SeveridadAviso`: Info/Advertencia/Crítico), `titulo`, `cuerpo`, `inicio_en` (DateTime), `fin_en` (DateTime), `orden` (Integer, default 0), `activo` (Boolean, default true), `requiere_ack` (Boolean, default false)
- [x] 1.2 Crear `backend/app/models/acknowledgment.py`: modelo `AcknowledgmentAviso` con `id` (UUID PK), `tenant_id` (FK → tenant), `aviso_id` (FK → aviso), `usuario_id` (FK → usuario), `confirmado_at` (DateTime, default now). Sin `updated_at` ni `deleted_at` (append-only). UniqueConstraint(`tenant_id`, `aviso_id`, `usuario_id`) para idempotencia
- [x] 1.3 Registrar ambos modelos en `backend/app/models/__init__.py`

## 2. Migración 006

- [x] 2.1 Generar migración con `alembic revision --autogenerate -m "006_avisos"`. Verificar tablas `aviso` y `acknowledgment_aviso` con constraints, FKs e índices
- [x] 2.2 Revisar migración: confirmar índices compuestos `ix_aviso_tenant_activo_vigencia(tenant_id, activo, inicio_en, fin_en)` y unique en acknowledgment

## 3. Schemas Pydantic

- [x] 3.1 Crear `backend/app/schemas/avisos.py` con:
  - `AvisoCreate` (titulo, cuerpo, alcance, severidad, inicio_en, fin_en, materia_id opcional, cohorte_id opcional, rol_destino opcional, orden opcional, requiere_ack opcional) — `extra='forbid'`
  - `AvisoUpdate` (todos opcionales excepto tenant immutables) — `extra='forbid'`
  - `AvisoResponse` (todos los campos + `total_acks: int`, `total_visibles: int`) — `from_attributes=True`
  - `AvisoVisibleResponse` (campos del aviso + `acknowledged: bool`) — `from_attributes=True`
  - `AckResponse` (id, aviso_id, confirmado_at) — `from_attributes=True`

## 4. Repositories

- [x] 4.1 Crear `backend/app/repositories/aviso_repository.py`: `AvisoRepository(BaseRepository[Aviso])` con:
  - CRUD heredado (tenant-scoped)
  - `list_visibles(tenant_id, usuario_id, roles, materia_ids, cohorte_ids)` — query que filtra por activo=true, vigencia actual, y match de alcance según el usuario
  - `count_acks(aviso_id)` — COUNT de AcknowledgmentAviso
  - `count_visibles(aviso_id)` — COUNT de usuarios destinatarios
- [x] 4.2 Crear `backend/app/repositories/acknowledgment_repository.py`: `AcknowledgmentRepository` con:
  - `add_or_ignore(tenant_id, aviso_id, usuario_id)` — INSERT ON CONFLICT DO NOTHING (idempotente)
  - `exists(tenant_id, aviso_id, usuario_id)` — verifica si ya existe
  - `count_by_aviso(aviso_id)` — COUNT

## 5. Services

- [x] 5.1 Crear `backend/app/services/aviso_service.py`: `AvisoService` con:
  - CRUD delegando a repository + validaciones de alcance (si PorMateria → materia_id obligatorio, etc.)
  - `list_visibles(tenant_id, usuario)` — orquesta filtrado por alcance según el usuario (sus roles, materias asignadas, cohortes asignadas)
- [x] 5.2 Crear `backend/app/services/acknowledgment_service.py`: `AcknowledgmentService` con:
  - `confirmar(tenant_id, aviso_id, usuario_id)` — verifica que el aviso sea visible para el usuario + add_or_ignore
  - `obtener_contadores(aviso_id)` — retorna total_acks y total_visibles

## 6. Routers

- [x] 6.1 Crear `backend/app/api/v1/routers/avisos.py` con:
  - `GET /api/avisos` — lista gestión (require `avisos:publicar`)
  - `POST /api/avisos` — crear (require `avisos:publicar`)
  - `GET /api/avisos/{id}` — detalle con contadores (require `avisos:publicar`)
  - `PUT /api/avisos/{id}` — modificar (require `avisos:publicar`)
  - `DELETE /api/avisos/{id}` — soft delete (require `avisos:publicar`)
  - `GET /api/avisos/visibles` — lista avisos para el usuario autenticado (sin permiso especial)
  - `POST /api/avisos/{id}/ack` — confirmar lectura (sin permiso especial)
- [x] 6.2 Registrar el router en `backend/app/main.py`

## 7. Tests — Safety Net y Red/Green/Refactor

- [x] 7.1 **Safety net**: ejecutar tests existentes y capturar baseline
- [x] 7.2 Crear `backend/tests/test_aviso_model.py` — test de creación de modelo, enum values, constraints
- [x] 7.3 Crear `backend/tests/test_acknowledgment_model.py` — test de creación, unique constraint, append-only
- [x] 7.4 Crear `backend/tests/test_aviso_repository.py` — CRUD, list_visibles con filtros, aislamiento tenant
- [x] 7.5 Crear `backend/tests/test_acknowledgment_repository.py` — add_or_ignore, count, idempotencia
- [x] 7.6 Crear `backend/tests/test_aviso_service.py` — CRUD, validaciones de alcance, filtrado por audiencia
- [x] 7.7 Crear `backend/tests/test_acknowledgment_service.py` — confirmar, duplicado, aviso no visible
- [x] 7.8 Crear `backend/tests/test_aviso_endpoints.py` — tests de integración:
  - CRUD con/ sin permiso
  - list_visibles por rol/materia/cohorte/global
  - acknowledgment exitoso y duplicado
  - aviso fuera de vigencia no visible
  - aislamiento multi-tenant
  - 403 sin permiso, 422 campos inválidos, 401 sin token

## 8. Verificación final

- [x] 8.1 Ejecutar suite completa: `pytest backend/tests/ -v --tb=short`. Todos los tests de C-15 deben pasar; ningún test previo debe romperse
- [x] 8.2 Verificar cobertura del módulo ≥ 80% líneas
- [x] 8.3 Confirmar que `GET /api/avisos/visibles` retorna lista vacía (no 500) en DB limpia
