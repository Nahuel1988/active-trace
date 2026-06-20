## Context

C-11 `analisis-atrasados-reportes` es el tercer eslabón de la cadena crítica del PROFESOR: después de importar calificaciones (C-09) y configurar umbrales (C-10), el sistema necesita computar indicadores académicos. Este cambio consume los modelos `Calificacion` y `UmbralMateria` de C-10 (aún no implementados — el diseño es tentativo y se ajustará cuando existan los endpoints reales).

## Goals / Non-Goals

**Goals:**
- Cómputo de alumnos atrasados por materia×cohorte (RN-06)
- Ranking descendente de actividades aprobadas por alumno (RN-09)
- Reportes rápidos con métricas agregadas por materia
- Cálculo de notas finales agrupadas
- Export de entregas sin corregir (RN-07, RN-08)
- Monitores transversales de actividad (general, tutor, coordinación)
- Todo endpoint protegido con permiso `atrasados:ver`
- Auditoría de consultas y exportaciones

**Non-Goals:**
- NO modificar los modelos de C-10 (Calificacion, UmbralMateria)
- NO incluir comunicación con alumnos (eso es C-12)
- NO incluir frontend (eso es C-22)

## Decisions

### D1 — Lógica de cómputo en Services dedicados
Se crean dos servicios: `AnalisisService` (atrasados, ranking, notas, reportes) y `MonitorService` (monitores transversales). Los repositorios de C-10 (`CalificacionRepository`, `UmbralMateriaRepository`) se reusan — no se crean repos nuevos salvo que la complejidad de las agregaciones lo requiera.

### D2 — Aggregate queries en repositories, no en services
Las agregaciones (count de atrasados, rankings, métricas) se implementan como métodos específicos en los repositorios de C-10, no como SQL en servicios. Si C-10 no los provee, se extienden con nuevos métodos de agregación.

### D3 — Endpoints de análisis como GET puros (sin side effects)
Todos los endpoints de análisis son read-only. Las exportaciones no modifican estado. La única excepción es el log de auditoría, que se escribe al servir cada request.

### D4 — Filtros via query params, no request body
Todos los filtros (materia_id, cohorte_id, rango fechas, etc.) se pasan como query params GET para facilitar cacheabilidad y enlace directo.

### D5 — Monitor general vs seguimiento comparten lógica base
F2.7 (monitor general) y F2.8/F2.9 (monitores de seguimiento) comparten el mismo motor de cómputo pero difieren en:
- Scope de datos: global vs acotado al usuario
- Filtros disponibles: coordinación agrega rango de fechas
Se implementa un único `MonitorService` con parámetros de scope.

## Risks / Trade-offs

- **[Alto] C-10 no está implementado**: los endpoints de C-10 (Calificacion, UmbralMateria) pueden cambiar en API, nombres de campos o estructura. Mitigación: usar los modelos de datos de la KB como contrato y ajustar en implementación.
- **[Medio] Rendimiento en monitores transversales**: los monitores generales pueden requerir agregaciones sobre miles de registros. Mitigación: implementar con queries SQL optimizadas (índices compuestos materia_id+cohorte_id) y paginación.
- **[Bajo] Ranking con empates**: RN-09 no especifica criterio de desempate. Decisión: ordenar alfabéticamente por apellido+nombre en caso de empate.
