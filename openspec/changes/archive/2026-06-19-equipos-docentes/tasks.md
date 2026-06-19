# Tasks — equipos-docentes (C-08)

> Governance: ALTO. Strict TDD obligatorio (RED → GREEN → TRIANGULATE → REFACTOR).
> Cobertura: ≥80% líneas, ≥90% reglas de negocio (masiva, clonado RN-12, vigencia bloque, audit filas_afectadas).
> Tests SIN mock de DB (contenedor de test efímero). Schemas con `extra='forbid'`. snake_case.
> Reutiliza C-07 (`Asignacion`, `AsignacionService`) y C-05 (`AuditLogRepository`) sin modificarlos.

## 1. Schemas Pydantic (app/schemas/equipo.py)

- [x] 1.1 RED: test que `MisEquiposResponse` agrupa asignaciones por tupla `(materia_id, carrera_id, cohorte_id)` y rechaza campos extra (`extra='forbid'`)
- [x] 1.2 GREEN+REFACTOR: definir `MisEquiposResponse` / `EquipoResumen` con `extra='forbid'`
- [x] 1.3 RED: tests de `AsignacionMasivaRequest` (usuario_ids[], role_id, contexto, desde/hasta) — happy + rechazo de campo extra + lista vacía
- [x] 1.4 GREEN+REFACTOR: `AsignacionMasivaRequest` y `AsignacionMasivaResponse` (`creadas`, `rechazadas[]`, `omitidas[]`)
- [x] 1.5 RED: tests de `ClonarEquipoRequest` (origen tupla, destino carrera/cohorte, nueva vigencia) y `ClonarEquipoResponse` (`clonadas`, `omitidas[]`)
- [x] 1.6 GREEN+REFACTOR: schemas de clonado con `extra='forbid'`
- [x] 1.7 RED: tests de `VigenciaBloqueRequest` (tupla equipo + desde/hasta) y su response (`filas_afectadas`)
- [x] 1.8 GREEN+REFACTOR: schemas de vigencia en bloque

## 2. Repository — métodos de equipo (app/repositories/asignacion_repository.py)

- [x] 2.1 RED: test `list_by_equipo` devuelve solo asignaciones de la tupla, del tenant, no soft-deleted; flag `solo_vigentes`
- [x] 2.2 GREEN: implementar `list_by_equipo(tenant_id, materia_id, carrera_id, cohorte_id, session, solo_vigentes)`
- [x] 2.3 TRIANGULATE: caso vigentes vs todas; caso otro tenant excluido
- [x] 2.4 RED: test `exists_vigente(tenant_id, usuario_id, role_id, materia_id, carrera_id, cohorte_id)` para idempotencia
- [x] 2.5 GREEN+TRIANGULATE: implementar `exists_vigente`; casos existe/no existe/vencida-no-cuenta
- [x] 2.6 RED: test `list_distinct_equipos` devuelve tuplas distintas con conteo de vigentes, filtrado por tenant
- [x] 2.7 GREEN+TRIANGULATE+REFACTOR: implementar `list_distinct_equipos` con filtros opcionales
- [x] 2.8 RED: test `bulk_update_vigencia` actualiza solo el equipo del tenant y devuelve filas afectadas
- [x] 2.9 GREEN+TRIANGULATE+REFACTOR: implementar `bulk_update_vigencia`; caso filas=0, caso otro tenant intacto

## 3. EquipoService — mis equipos (app/services/equipo_service.py)

- [x] 3.1 RED: test `get_mis_equipos(tenant_id, usuario_id)` agrupa por tupla, solo vigentes del usuario
- [x] 3.2 GREEN+REFACTOR: implementar `get_mis_equipos` reusando `list_by_equipo`/repo
- [x] 3.3 TRIANGULATE: usuario sin asignaciones → vacío; asignaciones vencidas/soft-deleted excluidas; otro tenant excluido

## 4. EquipoService — asignación masiva (RN-30)

- [x] 4.1 RED: test bloque totalmente válido → N creadas, `filas_afectadas=N`, emite `ASIGNACION_MODIFICAR`
- [x] 4.2 GREEN: implementar `asignacion_masiva` reusando `AsignacionService.create` por fila + audit de bloque
- [x] 4.3 TRIANGULATE: bloque parcialmente inválido (best-effort) → válidas creadas, rechazadas con motivo, sin revertir
- [x] 4.4 TRIANGULATE: idempotencia → fila que ya existe vigente se reporta omitida, no se duplica (usa `exists_vigente`)
- [x] 4.5 TRIANGULATE: tenant — todas las creadas con tenant del actor
- [x] 4.6 REFACTOR: extraer construcción de resumen (creadas/rechazadas/omitidas) sin cambiar comportamiento

## 5. EquipoService — clonar equipo (RN-12)

- [x] 5.1 RED: test clonado completo → copia usuario/role/comisiones/responsable, reescribe carrera/cohorte/vigencia; `filas_afectadas=N`; audit con tupla origen+destino
- [x] 5.2 GREEN: implementar `clonar_equipo` (lee vigentes del origen, crea en destino vía service)
- [x] 5.3 TRIANGULATE: idempotencia/solapamiento → segunda corrida `clonadas=0`, todas omitidas
- [x] 5.4 TRIANGULATE: solo vigentes del origen se clonan (vencidas y soft-deleted excluidas)
- [x] 5.5 TRIANGULATE: aislamiento por tenant en origen y destino
- [x] 5.6 REFACTOR: limpiar mapeo origen→destino sin cambiar comportamiento

## 6. EquipoService — vigencia en bloque (F4.6)

- [x] 6.1 RED: test actualiza todas las asignaciones del equipo, `filas_afectadas=N`, único `ASIGNACION_MODIFICAR`
- [x] 6.2 GREEN: implementar `modificar_vigencia_bloque` (valida desde≤hasta, usa `bulk_update_vigencia`, audita)
- [x] 6.3 TRIANGULATE: rango inválido (desde>hasta) → error 422, sin tocar datos, sin audit de modificación
- [x] 6.4 TRIANGULATE: aislamiento por tenant

## 7. EquipoService — export CSV (F4.7)

- [x] 7.1 RED: test genera CSV con header fijo y N filas de datos para el equipo
- [x] 7.2 GREEN: implementar `export_equipo_csv` (header `legajo,docente,rol,materia_id,carrera_id,cohorte_id,comisiones,desde,hasta,estado`)
- [x] 7.3 TRIANGULATE: NO incluye PII sensible (dni/cuil/cbu/email); solo legajo+nombre
- [x] 7.4 TRIANGULATE: comisiones serializadas con `;`; escapado de fórmulas (`=`,`+`,`-`,`@`)
- [x] 7.5 TRIANGULATE: aislamiento por tenant en filas exportadas
- [x] 7.6 REFACTOR: extraer util de escapado/serialización CSV

## 8. Router /api/v1/equipos (app/api/v1/routers/equipos.py)

- [x] 8.1 RED: test `GET /equipos/mis-equipos` 200 con identidad de sesión; ignora `usuario_id` por query; SIN guard `equipos:asignar`
- [x] 8.2 GREEN: endpoint `mis-equipos` usando `current_user.id` del JWT
- [x] 8.3 RED+GREEN: `GET /equipos` (lista equipos) con guard `equipos:asignar`; 403 sin permiso
- [x] 8.4 RED+GREEN: `POST /equipos/asignacion-masiva` (201, resumen); 403 sin permiso; propaga IP/user_agent del request al audit
- [x] 8.5 RED+GREEN: `POST /equipos/clonar`; 403 sin permiso
- [x] 8.6 RED+GREEN: `PATCH /equipos/vigencia`; 422 rango inválido; 403 sin permiso
- [x] 8.7 RED+GREEN: `GET /equipos/export` devuelve `text/csv` + `Content-Disposition: attachment`; 403 sin permiso
- [x] 8.8 REFACTOR: registrar router en el app factory; verificar archivo <500 LOC

## 9. Cierre y verificación

- [x] 9.1 Verificar cobertura ≥80% líneas y ≥90% en reglas de negocio (masiva, clonado, vigencia, audit filas_afectadas)
- [x] 9.2 Verificar que ningún test mockea la DB (contenedor efímero) y que todos los schemas usan `extra='forbid'`
- [x] 9.3 Confirmar que C-07 (`Asignacion`, `AsignacionService`, router asignaciones) y `UserRole` quedaron intactos (sin migración de schema)
- [x] 9.4 Marcar [x] C-08 en CHANGES.md
