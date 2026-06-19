## Why

El sistema carece de un módulo para gestionar convocatorias de evaluación oral (coloquios): no existe forma de crear convocatorias con turnos y cupos, ni de que los alumnos reserven su turno, ni de que el coordinador vea la agenda consolidada. Sin este módulo, la coordinación de coloquios se hace fuera del sistema (planillas, WhatsApp), perdiendo trazabilidad.

## What Changes

- Nuevo CRUD de convocatorias de evaluación (`Evaluacion`): tipo, instancia, materia × cohorte, días disponibles y cupos
- Importación de padrón de candidatos habilitados a una convocatoria (F7.2)
- Reserva de turno por ALUMNO con control de cupo (resta cupo al reservar, restaura al cancelar)
- Panel de métricas por convocatoria: convocados / reservas activas / cupos libres (F7.1)
- Listado de convocatorias activas con métricas operativas (F7.4)
- Agenda consolidada de reservas para COORDINADOR/ADMIN (F7.5)
- Registro académico de resultados (`ResultadoEvaluacion`): nota final numérica o cualitativa
- Migración 008: tablas `evaluacion`, `reserva_evaluacion`, `resultado_evaluacion`
- Endpoints `/api/coloquios/*` con RBAC: COORDINADOR/ADMIN gestionan, ALUMNO reserva

## Capabilities

### New Capabilities
- `evaluacion-convocatoria`: ABM de convocatorias de evaluación con días y cupos; importación de candidatos; métricas y listado operativo
- `evaluacion-reserva`: reserva de turno por ALUMNO en día disponible con cupo; estado Activa/Cancelada; control de concurrencia en cupos
- `evaluacion-resultado`: registro de nota final por alumno por convocatoria; consulta de registro académico consolidado

### Modified Capabilities
- (ninguna — módulo completamente nuevo)

## Impact

- **Modelos nuevos**: `Evaluacion`, `ReservaEvaluacion`, `ResultadoEvaluacion`
- **Migración**: 008 (nuevas tablas)
- **Endpoints**: `/api/coloquios/` (convocatorias, métricas, agenda), `/api/coloquios/{id}/reservas/`, `/api/coloquios/{id}/resultados/`
- **Permisos nuevos**: `coloquios:gestionar` (COORDINADOR, ADMIN), `coloquios:reservar` (ALUMNO)
- **Dependencias**: C-07 (Usuario, Asignacion), C-06 (Materia, Cohorte)
