## Context

Sistema actual no tiene un mecanismo de comunicación masiva interna segmentada. La funcionalidad de avisos (F3.5, RN-18/19/20) requiere un tablón donde COORDINADOR/ADMIN publiquen novedades con alcance configurable y los destinatarios puedan confirmar lectura.

Se reusa el permiso `avisos:publicar` ya existente en `rbac_seed.py` (asignado a COORDINADOR y ADMIN).

## Goals / Non-Goals

**Goals:**
- Modelo `Aviso` con alcance, severidad, vigencia, orden y flag requiere_ack
- Modelo `AcknowledgmentAviso` append-only para registrar confirmaciones de lectura
- CRUD de avisos protegido con `avisos:publicar`
- Endpoint público (autenticado) que lista avisos visibles filtrados por rol/alcance/cohorte/vigencia
- Endpoint de acknowledgment por usuario
- Contadores derivados (COUNT), sin denormalizar
- Soft delete en Aviso; AcknowledgmentAviso es inmutable

**Non-Goals:**
- Notificaciones push o en tiempo real (solo consulta pull)
- Avisos programados con publicación diferida (la vigencia ya cubre visibilidad futura)
- Destinatarios individuales (solo por alcance+rol)

## Decisions

| Decisión | Opción elegida | Alternativa | Razón |
|----------|---------------|-------------|-------|
| Filtrado de avisos | Service-layer con queries SQLAlchemy | Filtrar en memoria | La cantidad de avisos activos por tenant es acotada (<500), pero filtrar en SQL es más limpio y escalable |
| Acknowledgment | Endpoint POST dedicado | PATCH sobre aviso | Desacopla la confirmación del recurso aviso; el acknowledgment es una entidad propia |
| Alcance múltiple | Un enum con 4 valores (Global/PorMateria/PorCohorte/PorRol) | Flags booleanos | Más mantenible y auto-documentado; la combinación materia+cohorte+rol se resuelve según el alcance |
| Migración | 006 (004 audit_log → 005 estructura → 006 avisos) | — | Secuencia lineal de migraciones |

## Risks / Trade-offs

- [Rendimiento] Listado de avisos visibles requiere joins contra asignaciones del usuario para filtrar por materia/cohorte. Mitigación: índices compuestos en `avisos(tenant_id, activo, inicio_en, fin_en)` y `asignacion(usuario_id, vigencia)`.
- [Consistencia] Los contadores derivados pueden tener lag si hay alta concurrencia de ack. Mitigación: el volumen esperado es bajo (un ack por usuario por aviso), no hay riesgo real de contención.
