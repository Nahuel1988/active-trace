## 1. Setup & Dependency Wiring

- [x] 1.1 `atrasados:ver` ya existe en RBAC (C-04)
- [x] 1.2 Create `AnalisisService` class stub in `backend/app/services/analisis.py`
- [x] 1.3 Create `MonitorService` class stub in `backend/app/services/monitores.py`
- [x] 1.4 Create `backend/app/api/endpoints/analisis.py` router
- [x] 1.5 Create `backend/app/api/endpoints/monitores.py` router
- [x] 1.6 Register both routers in `backend/app/api/main.py`

## 2. AnalisisService — Atrasados Computation

- [x] 2.1 Implement `get_atrasados(materia_id, cohorte_id, tenant_id)` method
- [x] 2.2 Numeric grade check: flag student if grade < `umbral_pct`
- [x] 2.3 Textual grade check: flag student if grade NOT in `valores_aprobatorios`
- [x] 2.4 Missing activity detection: flag student if activity has no submission
- [x] 2.5 Fallback: use 60% threshold when no `UmbralMateria` configured
- [x] 2.6 Return classification: `missing` vs `below_threshold` per student

## 3. AnalisisService — Ranking de Aprobadas

- [x] 3.1 Implement `get_ranking(materia_id, cohorte_id, tenant_id)` method
- [x] 3.2 Compute approved count + total activities per student
- [x] 3.3 Compute approval percentage per student
- [x] 3.4 Exclude students with zero approved activities
- [x] 3.5 Tie-breaking: alphabetical by last name, then first name

## 4. AnalisisService — Quick Reports

- [x] 4.1 Implement `get_reporte_rapido(materia_id, cohorte_id, tenant_id)` method
- [x] 4.2 Compute: total_alumnos, total_actividades, tasa_aprobacion_pct
- [x] 4.3 Compute: alumnos_atrasados count, alumnos_al_dia count
- [x] 4.4 Return `sin_datos: true` when no grade data exists

## 5. AnalisisService — Final Grades

- [x] 5.1 Implement `get_notas_finales(materia_id, cohorte_id, tenant_id)` method
- [x] 5.2 Per-student: per-activity breakdown with grade + approved boolean
- [x] 5.3 Compute final numeric average from numeric-grade activities only
- [x] 5.4 List textual-grade activities separately without affecting average
- [x] 5.5 Support `format=json` (default) and `format=csv` output

## 6. AnalisisService — Pending Submissions Export

- [x] 6.1 Implement `get_entregas_pendientes(uploaded_report_id, tenant_id)` method
- [x] 6.2 Cross-reference completion report with existing `Calificacion` records
- [x] 6.3 Filter: only textual-scale activities (RN-08)
- [x] 6.4 Return `todas_corregidas: true` when no pendings found
- [x] 6.5 Export as CSV: student name, activity name, submission date, subject

## 7. MonitorService — General & Seguimiento

- [x] 7.1 Implement `get_monitor_general(filters, tenant_id)` with pagination
- [x] 7.2 Support filters: `materia_id`, `regional`, `comision`, `q` (free text), `estado`
- [x] 7.3 Implement `get_monitor_seguimiento(current_user, filters)` scoped to user's assignments
- [x] 7.4 For COORDINADOR/ADMIN: support `fecha_desde`/`fecha_hasta` in seguimiento
- [x] 7.5 Support `format=csv` export in both monitor endpoints

## 8. Router & Permissions

- [x] 8.1 Wire `GET /api/analisis/atrasados` → AnalisisService.get_atrasados
- [x] 8.2 Wire `GET /api/analisis/ranking` → AnalisisService.get_ranking
- [x] 8.3 Wire `GET /api/analisis/reportes` → AnalisisService.get_reporte_rapido
- [x] 8.4 Wire `GET /api/analisis/notas-finales` → AnalisisService.get_notas_finales
- [x] 8.5 Wire `GET /api/analisis/entregas-pendientes/export` → AnalisisService.get_entregas_pendientes
- [x] 8.6 Wire `GET /api/monitores/general` → MonitorService.get_monitor_general
- [x] 8.7 Wire `GET /api/monitores/seguimiento` → MonitorService.get_monitor_seguimiento
- [x] 8.8 Add `require_permission("atrasados:ver")` to all 8 endpoints
- [x] 8.9 Add audit logging on every endpoint call (who, what, when)

## 9. Tests

- [x] 9.1 Test atrasados computation (numeric below threshold, textual non-passing, missing, no-data)
- [x] 9.2 Test ranking (descending order, zero-approved excluded, tie-breaking)
- [x] 9.3 Test quick report (metrics aggregation, empty data edge case)
- [x] 9.4 Test final grades (numeric average, textual-only activities, CSV format)
- [x] 9.5 Test pending export (cross-reference, textual-only filter, todas_corregidas)
- [x] 9.6 Test monitors (general with filters, seguimiento scoping, date range)
- [x] 9.7 Test permissions (reject without atrasados:ver, accept with correct role)
