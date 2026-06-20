## Why

Una vez que el docente importa las calificaciones desde el LMS (C-10), el sistema necesita transformar esos datos en información accionable: identificar alumnos en riesgo, ranking de rendimiento, reportes rápidos y monitores de seguimiento. Sin esta capa de análisis, los datos importados quedan inertes — el valor del sistema está en la detección temprana de atrasados y la capacidad de exportar reportes.

## What Changes

- **Nuevo endpoint** `GET /api/analisis/atrasados` — calcula alumnos atrasados por materia×cohorte usando calificaciones (C-10) + umbral (C-10, RN-06)
- **Nuevo endpoint** `GET /api/analisis/ranking` — ranking de actividades aprobadas por alumno (RN-09)
- **Nuevo endpoint** `GET /api/analisis/reportes` — métricas rápidas por materia (actividades, aprobaciones, tendencias)
- **Nuevo endpoint** `GET /api/analisis/notas-finales` — notas finales agrupadas por alumno
- **Nuevo endpoint** `GET /api/analisis/entregas-pendientes` — cruza reporte de finalización con calificaciones para detectar TPs sin corregir (RN-07, RN-08)
- **Nuevos endpoints** `GET /api/monitores/general`, `/api/monitores/seguimiento` — vistas transversales de actividad con filtros
- **Nuevo permiso** `atrasados:ver` — protege todos los endpoints de análisis
- **Auditoría** — las consultas y exportaciones generan registros en AuditLog

## Capabilities

### New Capabilities
- `analisis-atrasados`: Cómputo de alumnos atrasados por materia×cohorte (RN-06); endpoint GET con filtros (materia, cohorte, estado atrasado/no-atrasado)
- `ranking-aprobadas`: Ranking descendente de alumnos por cantidad de actividades aprobadas (RN-09); excluye alumnos sin aprobadas
- `reportes-rapidos`: Métricas agregadas por materia (total alumnos, actividades, aprobación pct, tendencias)
- `notas-finales`: Notas finales agrupadas por alumno × actividad, calculadas a partir de calificaciones importadas
- `export-entregas-pendientes`: Cruce entre reporte de finalización y calificaciones para identificar TPs sin corregir (RN-07, RN-08); export CSV
- `monitor-alumnos`: Monitores transversales de actividad — vista general (F2.7), vista tutor/profesor (F2.8), vista coordinación/admin con rango de fechas (F2.9)

### Modified Capabilities
- *(ninguna — C-11 consume C-10 sin modificar sus requisitos)*

## Impact

- **Nuevos endpoints**: 6 nuevos routers bajo `app/api/v1/routers/analisis.py` y `app/api/v1/routers/monitores.py`
- **Nuevos servicios**: `app/services/analisis_service.py` (cómputo de atrasados, ranking, notas finales), `app/services/monitor_service.py` (monitores transversales)
- **Nuevos schemas**: Pydantic para request/response de análisis y monitores
- **Nuevos repositorios** (opcional): si la lógica de agregación requiere queries complejas, repositorios dedicados en `app/repositories/`
- **Dependencias**: consume modelos `Calificacion` y `UmbralMateria` de C-10
- **Permisos**: seed del permiso `atrasados:ver` en matriz RBAC
- **Auditoría**: códigos `ANALISIS_CONSULTAR`, `ANALISIS_EXPORTAR`, `MONITOR_CONSULTAR`
- **Tests**: ≥90% cobertura en reglas de negocio (RN-06, RN-07, RN-08, RN-09)
