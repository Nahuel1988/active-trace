## Context

C-14 introduce el módulo de convocatorias de evaluación (coloquios). Depende de C-07 (Usuario, Asignacion) y C-06 (Materia, Cohorte). La migración será la 008 (001-007 ya existen).

El modelo tiene tres entidades: `Evaluacion` (convocatoria con cupos por día), `ReservaEvaluacion` (turno reservado por ALUMNO) y `ResultadoEvaluacion` (nota final registrada por COORDINADOR/ADMIN). El riesgo principal es la condición de carrera en la reserva de cupos cuando múltiples ALUMNOs reservan simultáneamente.

## Goals / Non-Goals

**Goals**:
- CRUD completo de convocatorias (Evaluacion) con días disponibles y cupos por día
- Importación de candidatos habilitados a una convocatoria
- Reserva de turno por ALUMNO con control de cupo (concurrencia segura)
- Métricas operativas: convocados / reservas activas / cupos libres
- Registro de resultado (nota final) por convocatoria × alumno

**Non-Goals**:
- Notificaciones automáticas a alumnos (es C-12)
- Integración con LMS/Moodle para publicar la agenda
- Firma digital de actas de coloquio

## Decisions

### D1 — Control de cupo con SELECT FOR UPDATE

Para evitar doble reserva cuando ALUMNOs reservan en simultáneo, el repositorio usa `SELECT FOR UPDATE` sobre las reservas activas de la evaluación antes de decrementar cupos. Alternativa considerada: columna `cupos_disponibles` en `Evaluacion` con decremento atómico — descartada porque dificulta reconstruir el historial y no es compatible con soft delete.

**Implementación**: `ReservaRepository.create()` hace `SELECT count(*) FROM reserva_evaluacion WHERE evaluacion_id=? AND estado='Activa' FOR UPDATE`, compara con `Evaluacion.dias_disponibles` (cupo total), y lanza `HTTP 409` si lleno.

### D2 — `dias_disponibles` como ventana, no lista de fechas

El campo `dias_disponibles` (entero) define cuántos días tiene la convocatoria, no las fechas exactas. La `fecha_hora` de cada `ReservaEvaluacion` la elige el ALUMNO dentro de la ventana. Esto simplifica el modelo inicial; fechas exactas con calendario se puede agregar en iteraciones futuras.

### D3 — Candidatos habilitados como subconjunto del padrón

F7.2 "importar alumnos a convocatoria" se implementa como un endpoint `POST /api/coloquios/{id}/candidatos` que recibe una lista de `usuario_id` (ALUMNOs ya registrados). No crea un modelo separado: los candidatos son ALUMNOs cuya presencia se verifica antes de permitir la reserva. La alternativa (tabla `CandidatoEvaluacion`) se consideró innecesaria para el alcance actual.

### D4 — `ResultadoEvaluacion` independiente de `ReservaEvaluacion`

Un resultado puede existir aunque el ALUMNO no haya reservado (registro manual por el COORDINADOR). Relación: `ResultadoEvaluacion.evaluacion_id + alumno_id` con unicidad `(tenant_id, evaluacion_id, alumno_id)`.

## Risks / Trade-offs

- [Race condition en cupos] → Mitigado con `SELECT FOR UPDATE` (D1). Bajo carga alta puede ser un cuello de botella; aceptable para el volumen actual.
- [Modelo de dias_disponibles poco expresivo] → Mitigado dejando `fecha_hora` libre en `ReservaEvaluacion`. Se puede evolucionar a fechas explícitas sin migración destructiva.
- [Candidatos sin tabla propia] → Si en el futuro se necesita filtrar "quién está habilitado", se agrega tabla. Por ahora el guard del endpoint es suficiente.

## Migration Plan

1. Crear `Migracion 008`: tablas `evaluacion`, `reserva_evaluacion`, `resultado_evaluacion` con FK a `materia`, `cohorte`, `usuario` y constraints de unicidad.
2. Seed de permisos: `coloquios:gestionar` (COORDINADOR, ADMIN) y `coloquios:reservar` (ALUMNO).
3. Sin rollback destructivo: tablas nuevas no afectan tablas existentes.

## Open Questions

- ¿Se notifica al ALUMNO cuando su reserva es confirmada? (depende de C-12; por ahora no)
- ¿Un ALUMNO puede tener más de una reserva activa por convocatoria? (asumir NO — unicidad `(evaluacion_id, alumno_id)` en estado Activa)
