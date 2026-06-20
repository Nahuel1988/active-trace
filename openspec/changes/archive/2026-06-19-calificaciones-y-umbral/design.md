## Context

C-09 entregó el padrón versionado (`VersionPadron` + `EntradaPadron`). Sin calificaciones ni umbral, los módulos de análisis (F2.x), detección de atrasados (F2.2) y comunicación (F3.x) no pueden operar. C-10 agrega el modelo de calificación (E7), el umbral configurable por asignación docente (E8) y los flujos de importación desde archivo del LMS (F1.1, F1.2) y configuración de umbral (F2.1).

El cambio toca: nuevo schema de DB (migración 009), nuevos modelos ORM, dos repositories, un service, un router y schemas Pydantic. Nada de la capa previa (C-01..C-09) se modifica; C-10 solo agrega tablas nuevas que referencian modelos existentes.

**Dependencia crítica**: `Calificacion.entrada_padron_id` es FK a `EntradaPadron` (C-09). La implementación de C-10 está bloqueada hasta que C-09 esté completo y la migración 008 esté aplicada.

## Goals / Non-Goals

**Goals:**

- Modelo `Calificacion` (E7) con FK a `EntradaPadron`, `nota_numerica`/`nota_textual` nullable, `origen` Importado/Manual, `creado_por` FK a Usuario, soft-delete.
- Modelo `UmbralMateria` (E8) con FK a `Asignacion` (scope por docente), `umbral_pct` default 60, `valores_aprobatorios` (lista textual).
- `aprobado` derivado en read-time (no almacenado): numérico vs umbral, textual vs conjunto aprobatorio.
- Import de calificaciones desde `.xlsx`/`.csv` con vista previa y confirmación en dos pasos (preview → confirm).
- Detección de columnas numéricas (RN-01: cabeceras `(Real)`) y textuales (RN-02: valores escala).
- Selección de actividades por el usuario en el paso de confirmación.
- Import de reporte de finalización (F1.2) con cruce contra calificaciones existentes para detectar entregas sin corregir (RN-07, RN-08).
- Configuración de umbral por `asignacion_id` con default 60% (RN-03).
- Vaciado de calificaciones scoped al usuario autenticado (RN-04: `usuario_id × materia_id`), soft-delete.
- Auditoría `CALIFICACIONES_IMPORTAR` en el audit log existente (C-05).
- Migración 009 limpia (solo tablas nuevas, sin tocar schema previo).

**Non-Goals:**

- Sincronización automática desde Moodle (se implementa en C-09 o en worker de C-11).
- Cálculo de nota final agrupada (F2.5 — scope de C-12).
- Ranking de actividades aprobadas (F2.3 — scope de C-12).
- UI frontend de calificaciones (scope de C-21 / C-22).
- Exportación de entregas sin corregir (F2.6 — scope de C-12).
- Monitor de seguimiento de alumnos (F2.7, F2.8, F2.9 — scope de C-12).

## Decisions

### D-01 — `aprobado` derivado en read-time, no almacenado

**Decisión**: el campo `aprobado` NO se almacena en la tabla `calificacion`. Se computa al leer:
- Si `nota_numerica` no es nulo: `nota_numerica >= umbral_pct` del `UmbralMateria`.
- Si solo `nota_textual` no es nulo: `nota_textual in valores_aprobatorios` del `UmbralMateria`.

**Alternativa descartada**: almacenar `aprobado` como columna computada o campo derivado → si el usuario cambia el umbral, todas las calificaciones existentes quedarían desactualizadas. Forzar un recálculo masivo es costoso y propenso a errores.

**Trade-off**: cada lectura de calificaciones requiere resolver el umbral. Aceptable porque: (a) el umbral se cachea en memoria por request (una sola query de `UmbralMateria` por `asignacion_id`), (b) el volumen de lecturas concurrentes sobre una misma materia es bajo (decenas, no miles).

### D-02 — Scope por asignación docente en UmbralMateria (RN-04)

**Decisión**: `UmbralMateria` se relaciona con `Asignacion`, no con `Materia` directamente. Cada docente tiene su propio umbral para la misma materia. Al leer calificaciones, el servicio resuelve la `Asignacion` del usuario autenticado y usa su umbral.

**Alternativa descartada**: umbral por materia (compartido entre todos los docentes) → viola RN-04 que exige aislamiento `(usuario_id × materia_id)`. Un docente no debe ver calificaciones afectadas por el umbral de otro docente.

**Implementación**: el endpoint `GET /calificaciones` recibe `materia_id` y resuelve la `Asignacion` vigente del usuario autenticado para esa materia. Si no tiene asignación → `403 Forbidden`.

### D-03 — Import en dos pasos: preview → confirm (stateless)

**Decisión**: misma estrategia que C-09 (D-02). `POST /calificaciones/preview` parsea el archivo, detecta columnas (numéricas por `(Real)`, textuales por catálogo), devuelve preview con actividades detectadas y muestra de filas. `POST /calificaciones/confirmar` recibe selección de actividades en el body y ejecuta la importación real.

**Alternativa descartada**: guardar estado entre preview y confirm → estado en servidor, complica escalado.

**Particularidad de C-10**: el preview detecta qué columnas son numéricas y cuáles textuales. El confirm recibe `actividades_seleccionadas: list[str]` (nombres de columna) para filtrar qué actividades importar.

### D-04 — Detección de columnas numéricas y textuales (RN-01, RN-02)

**Decisión**: la lógica de detección vive en el service (`CalificacionService._clasificar_columnas`), no en el router ni en una util separada. Clasifica cada columna del archivo:
- **Numérica**: cabecera termina en `(Real)` (RN-01).
- **Textual**: cabecera NO termina en `(Real)` y los valores coinciden con el catálogo de escala textual configurable (RN-02).
- **Ignorada**: columnas que no son ni numéricas ni textuales (ej: nombre, email, DNI).

El catálogo de valores textuales aprobatorios (`["Satisfactorio", "Supera lo esperado"]`) se configura a nivel de tenant como parámetro del sistema.

### D-05 — Reporte de finalización cruza contra calificaciones existentes

**Decisión**: `POST /calificaciones/reporte-finalizacion` sube el archivo de finalización del LMS. El service cruza los datos: por cada alumno × actividad que aparece como "finalizada" en el reporte pero NO tiene calificación en `Calificacion` (solo actividades textuales por RN-08), se genera un item en el reporte de "posibles entregas sin corregir".

**No cruza**: actividades numéricas (RN-08: ausencia de nota numérica = no entregado, no pendiente de corrección).

**Salida**: listado de `(alumno, actividad, fecha_finalizacion)` sin crear registros en DB — es una vista derivada.

### D-06 — Soft delete en Calificacion para vaciado (F1.5, RN-04)

**Decisión**: `DELETE /calificaciones/vaciar` marca `deleted_at = now()` y `deleted_by = actor_id` sobre las calificaciones del `(actor_id, materia_id)`. No afecta calificaciones de otros docentes ni de otras materias. Los registros se preservan para auditoría.

**Alternativa descartada**: hard delete → imposibilita auditoría histórica. El soft-delete permite revertir un vaciado accidental (aunque no es un requisito actual, preserva la opción).

### D-07 — Calificacion.creado_por resuelve identidad desde el JWT

**Decisión**: al importar calificaciones, `creado_por` se setea automáticamente desde `get_current_user` (C-03). Nunca se acepta desde datos de la petición (regla de seguridad: identidad siempre desde la sesión).

**Relación con scope**: `creado_por` permite aplicar RN-04 en vaciado (solo borra calificaciones donde `creado_por = actor_id`) y en lecturas (cada docente ve solo sus propias calificaciones, salvo COORDINADOR que puede ver todas).

### D-08 — Sin PII adicional en Calificacion

**Decisión**: `Calificacion` no contiene PII. Los campos `nota_numerica`, `nota_textual`, `actividad` y `origen` no son datos personales. No se requiere cifrado. La PII del alumno se resuelve a través de `EntradaPadron` (que ya maneja cifrado de email desde C-09).

## Risks / Trade-offs

- **[Risk] Umbral no existe al consultar calificaciones** → Mitigación: si no existe `UmbralMateria` para la `asignacion_id`, se usa el default global (60%). Se crea automáticamente al primera consulta o importación (lazy creation).
- **[Risk] Archivo de calificaciones con formato no estándar** → Mitigación: el preview valida que existan columnas reconocibles; si no detecta ninguna columna numérica ni textual → error 422 con detalle de columnas encontradas.
- **[Risk] Actividades seleccionadas en confirm no existen en el archivo** → Mitigación: el service valida que todos los nombres de `actividades_seleccionadas` existan en las columnas detectadas del preview original; si no → error 422.
- **[Risk] Carga duplicada de calificaciones** → Mitigación: no hay UK por `(entrada_padron_id, actividad)` — se permite reimportar. El usuario puede vaciar y reimportar si quiere reemplazar datos. No hay upsert automático para evitar pérdida accidental de datos.
- **[Risk] Reporte de finalización sin calificaciones previas** → Mitigación: si no hay calificaciones importadas para la materia, el cruce reporta todas las actividades finalizadas como "posibles entregas sin corregir" (escenario válido: el docente importa finalización antes que calificaciones).
- **[Risk] Performance con muchas calificaciones** → Mitigación: índices compuestos `(tenant_id, materia_id, creado_por)` y `(tenant_id, entrada_padron_id)`. Límite configurable `MAX_CALIFICACIONES_IMPORT` (default 5000 filas por importación).
- **[Risk] Transacción larga al importar muchas calificaciones** → Mitigación: inserción batch con SQLAlchemy `INSERT` bulk (no row-by-row). Con 5000 filas, tiempo esperado <1s en PostgreSQL local.

## Migration Plan

1. Ejecutar migración 009 (`calificacion`, `umbral_materia`, índices).
2. Deploy del código nuevo (router, service, repositories, schemas).
3. No hay datos previos que migrar (tablas nuevas).
4. **Rollback**: `alembic downgrade -1` elimina ambas tablas. No hay dependencias en tablas existentes que impidan el rollback (FKs son todas salientes desde las tablas nuevas hacia existentes).

## Open Questions

- **OQ-01**: ¿Cuál es el formato exacto del archivo de calificaciones exportado desde Moodle? La implementación de detección de columnas (RN-01, RN-02) depende de conocer las cabeceras reales del LMS. Requiere muestras de exportaciones reales de Moodle.
- **OQ-02**: ¿El catálogo de valores textuales (`["Satisfactorio", "Supera lo esperado"]`) es configurable por tenant o global? Se asume global por ahora, pero puede necesitar una tabla `TenantConfig` o un parámetro por tenant.
- **OQ-03**: ¿COORDINADOR puede ver calificaciones de todos los docentes de una materia, o solo las suyas? Se asume que COORDINADOR puede ver todas (alcance global), consistente con el modelo de permisos del proyecto.
- **OQ-04**: ¿El límite `MAX_CALIFICACIONES_IMPORT` debe ser configurable por tenant? Se implementa como constante en `CalificacionService` (5000), pero puede externalizarse a configuración del tenant si el negocio lo requiere.
