## Why

C-09 introdujo el padrón versionado (E6), pero sin calificaciones ni umbral de aprobación los módulos de análisis (F2.x), detección de atrasados y comunicación no pueden operar. El docente necesita importar las notas reales de sus alumnos desde el LMS, configurar su criterio de aprobación y detectar entregas sin corregir para poder tomar acciones pedagógicas. C-10 cierra esta brecha agregando el modelo de calificaciones (E7), el umbral configurable por asignación docente (E8) y los flujos de importación desde archivo del LMS (F1.1, F1.2, F2.1).

## What Changes

- **Modelos `Calificacion` (E7) + `UmbralMateria` (E8)**: `Calificacion` FK a `EntradaPadron` y `Materia`, con `nota_numerica` (nullable), `nota_textual` (nullable), `aprobado` derivado en read-time, `origen` (Importado | Manual), `creado_por` FK a Usuario. `UmbralMateria` FK a `Asignacion` (scope por docente) y `Materia`, con `umbral_pct` (default 60) y `valores_aprobatorios` (lista textual).
- **Migración 009**: tablas `calificacion` y `umbral_materia` con FKs, índices y constraint de unicidad.
- **Importar calificaciones por archivo (F1.1)**: sube `.xlsx`/`.csv` exportado del LMS → detecta columnas numéricas (RN-01: cabeceras terminadas en `(Real)`) y textuales (RN-02) → vista previa con actividades detectadas → usuario selecciona actividades a incluir → confirmación.
- **Importar reporte de finalización (F1.2)**: sube archivo de finalización del LMS → cruza contra calificaciones existentes → detecta actividades finalizadas por el alumno sin nota registrada (RN-07, RN-08: solo textuales).
- **Configurar umbral por materia (F2.1, RN-03)**: endpoint para leer/configurar `UmbralMateria` por `asignacion_id`. Default 60%. Audit `CALIFICACIONES_IMPORTAR`.
- **`aprobado` derivado en read-time**: no se almacena. Se computa al leer comparando `nota_numerica ≥ umbral_pct` o verificando `nota_textual ∈ valores_aprobatorios`. Esto permite que cambios en el umbral afecten retroactivamente.
- **Vaciar calificaciones (F1.5, RN-04)**: soft delete de calificaciones del usuario autenticado para una materia, sin afectar datos de otros docentes.
- **Auditoría**: `CALIFICACIONES_IMPORTAR` en el audit log existente (C-05).

## Capabilities

### New Capabilities

- `calificacion-modelo`: modelo `Calificacion` (E7) con FK a `EntradaPadron`, `nota_numerica`/`nota_textual` nullable, `aprobado` derivado en read-time, `origen` enum Importado/Manual, `creado_por` FK Usuario, soft-delete. Migración 009.
- `umbral-materia-modelo`: modelo `UmbralMateria` (E8) con FK a `Asignacion` y `Materia`, `umbral_pct` default 60, `valores_aprobatorios` (lista textual). Migración 009.
- `calificaciones-importar-archivo`: import de calificaciones desde `.xlsx`/`.csv` del LMS con vista previa y confirmación en dos pasos; detección de columnas numéricas (RN-01) y textuales (RN-02); selección de actividades por el usuario.
- `calificaciones-reporte-finalizacion`: import de reporte de finalización del LMS para detectar entregas sin corregir (RN-07, RN-08); cruce contra calificaciones existentes.
- `umbral-materia-configurar`: configuración de umbral de aprobación por asignación docente (RN-03); default 60%; `valores_aprobatorios` textuales; auditoría.
- `calificaciones-vaciar`: vaciado de calificaciones scoped al usuario autenticado (RN-04); soft-delete conserva historial.

### Modified Capabilities

<!-- C-10 NO modifica los contratos de EntradaPadron, Materia, Asignacion ni Usuario.
     Las capabilities de C-07, C-08 y C-09 quedan intactas; C-10 las referencia sin alterar sus requisitos. -->

## Impact

- **Código nuevo**: `app/models/calificacion.py` (Calificacion, UmbralMateria), `app/repositories/calificacion_repository.py`, `app/repositories/umbral_repository.py`, `app/services/calificacion_service.py`, `app/api/v1/routers/calificaciones.py`, `app/schemas/calificacion.py`.
- **Reutiliza sin modificar**: `AuditLogRepository` (C-05), `require_permission("calificaciones:importar")` (C-04), `get_current_user` / JWT (C-03), `Materia` (C-06), `Asignacion` (C-07), `EntradaPadron` (C-09), cifrado AES-256 util (C-02).
- **Migración**: `migrations/versions/009_calificacion_umbral_materia.py` — tablas nuevas, FKs, índices.
- **RBAC**: permisos `calificaciones:importar`, `calificaciones:configurar-umbral`, `calificaciones:vaciar` se agregan al catálogo; asignados a PROFESOR (scope propio) y COORDINADOR (scope global).
- **Multi-tenancy**: `tenant_id` en ambas tablas; todos los queries filtran por tenant del JWT.
- **Dependencia directa de C-09**: `Calificacion.entrada_padron_id` FK a `EntradaPadron`. Implementación bloqueada hasta que C-09 esté completo.
