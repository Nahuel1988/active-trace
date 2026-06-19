# Tasks: C-14 evaluaciones-y-coloquios

## 1. Foundation — Migración, Modelos, Schemas y Seed

- [x] 1.1 Crear migración 008 con tablas `evaluacion`, `reserva_evaluacion`, `resultado_evaluacion` incluyendo FKs a materia/cohorte/usuario, constraints de unicidad `(tenant_id, evaluacion_id, alumno_id)` en resultado y `(tenant_id, evaluacion_id, alumno_id)` con estado Activa en reserva
- [x] 1.2 Crear modelos SQLAlchemy: `Evaluacion` (con `dias_disponibles` entero, soft delete), `ReservaEvaluacion` (con estado Activa/Cancelada, `fecha_hora`), `ResultadoEvaluacion` (con `nota_final` texto, unicidad compuesta)
- [x] 1.3 Crear Pydantic schemas (request/response DTOs) para Evaluacion, ReservaEvaluacion y ResultadoEvaluacion con `extra='forbid'` en todos
- [x] 1.4 Seed de permisos `coloquios:gestionar` (COORDINADOR, ADMIN) y `coloquios:reservar` (ALUMNO) en la tabla de permisos

## 2. Evaluacion Convocatoria — CRUD, Candidatos, Métricas y Agenda

- [x] 2.1 Implementar `EvaluacionRepository`: CRUD con soft delete, filtro por tenant, importación idempotente de candidatos desde tabla usuario, consulta de métricas (convocados, reservas activas, cupos libres), agenda consolidada con filtros opcionales
- [x] 2.2 Implementar `EvaluacionService`: CRUD delegado a repository, importación de candidatos con validación de tenant y rol ALUMNO, cálculo de métricas, agenda consolidada
- [x] 2.3 Implementar router `GET/POST/PATCH/DELETE /api/v1/coloquios` con `require_permission("coloquios:gestionar")` y schema validation
- [x] 2.4 Implementar endpoint `POST /api/v1/coloquios/{id}/candidatos` con importación idempotente y respuesta `{ registrados, rechazados }`
- [x] 2.5 Implementar endpoints de métricas: `GET /api/v1/coloquios` con métricas embebidas, `GET /api/v1/coloquios/metricas` con panel global del tenant
- [x] 2.6 Implementar endpoint `GET /api/v1/coloquios/agenda` con filtros opcionales `materia_id`, `cohorte_id`, `evaluacion_id`, `fecha_desde`, `fecha_hasta`
- [x] 2.7 Escribir tests de integración para CRUD convocatorias, importación candidatos con idempotencia, métricas y agenda

## 3. Evaluacion Reserva — Reserva, Cancelación y Concurrencia

- [x] 3.1 Implementar `ReservaRepository`: crear con SELECT FOR UPDATE sobre reservas activas de la evaluación (D1), cancelar con transición Activa→Cancelada, mis-reservas con filtro por estado
- [x] 3.2 Implementar `ReservaService`: reservar con validaciones (candidato habilitado, sin reserva activa duplicada, cupo disponible, fecha_hora en ventana), cancelar con reglas de ownership (propietario o coloquios:gestionar)
- [x] 3.3 Implementar endpoint `POST /api/v1/coloquios/{id}/reservas` con `require_permission("coloquios:reservar")`, identidad desde JWT y control de cupo
- [x] 3.4 Implementar endpoint `PATCH /api/v1/coloquios/{id}/reservas/{reserva_id}/cancelar` con validación de ownership y transición de estado irreversible
- [x] 3.5 Implementar endpoint `GET /api/v1/coloquios/mis-reservas` con filtro opcional por estado y aislamiento por tenant
- [x] 3.6 Escribir tests de integración para reserva exitosa, candidato no habilitado, reserva duplicada, cupo agotado, cancelación por propietario y por COORDINADOR, cancelación de reserva ajena, y concurrencia FOR UPDATE (dos reservas simultáneas con 1 cupo)

## 4. Evaluacion Resultado — Notas y Registro Académico

- [x] 4.1 Implementar `ResultadoEvaluacionRepository`: crear con unicidad `(tenant_id, evaluacion_id, alumno_id)`, actualizar nota, consultar por convocatoria, registro académico consolidado con filtros, y consulta por alumno propio
- [x] 4.2 Implementar `ResultadoEvaluacionService`: registrar nota con validación de tenant y convocatoria activa, actualizar con emisión de audit `COLOQUIO_MODIFICAR_RESULTADO`, consultar según perfil
- [x] 4.3 Implementar endpoint `POST /api/v1/coloquios/{id}/resultados` con `require_permission("coloquios:gestionar")` y aceptación de nota numérica o cualitativa
- [x] 4.4 Implementar endpoint `PATCH /api/v1/coloquios/{id}/resultados/{resultado_id}` con auditoría y validación de tenant
- [x] 4.5 Implementar endpoint `GET /api/v1/coloquios/{id}/resultados` con datos del alumno y nota
- [x] 4.6 Implementar endpoints `GET /api/v1/coloquios/registro-academico` (COORDINADOR/ADMIN: consolidado del tenant) y `GET /api/v1/coloquios/mi-registro` (ALUMNO: solo propios)
- [x] 4.7 Escribir tests de integración para registro de nota con y sin reserva previa (D4), nota cualitativa, duplicado rechazado, actualización con audit, consultas con filtros, y aislamiento por tenant
