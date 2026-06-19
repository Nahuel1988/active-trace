## Context

C-06 y C-07 entregaron `Materia`, `Cohorte`, `Usuario` y `Asignacion`. Sin padrón, los módulos de análisis (C-10) y comunicaciones (C-11) no tienen sobre qué operar. C-09 agrega el padrón versionado (E6): `VersionPadron` + `EntradaPadron`, con dos vías de ingesta (archivo .xlsx/.csv y Moodle Web Services on-demand), cifrado AES-256 en `email` y soft-delete obligatorio.

El cambio toca: nuevo schema de DB (migración 008), nuevos modelos ORM, nuevo repository, nuevo service, nuevo router y un cliente de Moodle WS desacoplado. Nada de la capa previa (C-01..C-07) se modifica; C-09 solo agrega.

## Goals / Non-Goals

**Goals:**

- Modelo versionado de padrón con invariante de una sola versión activa por `(tenant_id, materia_id, cohorte_id)`.
- Import de padrón desde `.xlsx`/`.csv` con vista previa en dos pasos (preview → confirm).
- Sync on-demand desde Moodle Web Services con fallback a carga manual.
- Cifrado AES-256 de `EntradaPadron.email` (PII); `usuario_id` nullable.
- Vaciado de datos scoped al usuario autenticado (RN-04).
- Auditoría `PADRON_CARGAR` y `PADRON_VACIAR` en el audit log existente (C-05).
- Migración 008 limpia (solo tablas nuevas, sin tocar schema previo).

**Non-Goals:**

- Sincronización nocturna automática desde Moodle (se implementa en C-10 o en el worker de C-11).
- Importación de calificaciones (F1.1 — scope de C-10).
- UI frontend del padrón (scope de C-21 / C-22).
- Linking automático `EntradaPadron.usuario_id → Usuario` (C-09 lo deja nullable; el matching se puede hacer en C-10 o en un job separado).

## Decisions

### D-01 — Invariante de versión activa: constraint DB + lógica en service

**Decisión**: la unicidad de versión activa se protege con un índice parcial en PostgreSQL (`UNIQUE (tenant_id, materia_id, cohorte_id) WHERE activa = true`) Y con una transacción en `PadronService.activar_version()` que desactiva la versión anterior antes de activar la nueva.

**Alternativa descartada**: solo constraint en DB → los mensajes de error de violación de constraint son oscuros para el consumidor. La transacción en service da errores de dominio claros y permite auditar el evento de desactivación.

**Trade-off**: doble protección agrega complejidad, pero la invariante es crítica para la consistencia del padrón.

### D-02 — Import en dos pasos: preview → confirm (stateless con token de sesión)

**Decisión**: el endpoint `POST /padron/preview` parsea el archivo, valida columnas y devuelve un resumen (N alumnos, columnas detectadas, primeras 5 filas como muestra). El endpoint `POST /padron/confirmar` recibe los datos parseados en el body (no el archivo de nuevo) y ejecuta la ingesta real.

**Alternativa descartada**: guardar el archivo en disco entre preview y confirm → introduce estado en el servidor, complica el escalado horizontal. Pasar los datos en el body del confirm evita estado del lado del servidor.

**Trade-off**: el payload del confirm puede ser grande (padrón de 500+ alumnos). Aceptable dado el contexto de uso (operación esporádica, no masiva).

### D-03 — Cliente Moodle WS como módulo aislado (`integrations/moodle_ws.py`)

**Decisión**: el cliente HTTP de Moodle es un módulo independiente que expone funciones async puras. El `PadronService` lo llama; si falla, captura la excepción y propaga `502 MoodleUnavailable`. El worker de reintento (C-11) maneja la cola.

**Alternativa descartada**: integrar el cliente directamente en el service → acopla la lógica de negocio al protocolo HTTP de Moodle y dificulta el mock en tests.

**Implementación**: el cliente se configura con `MOODLE_URL` y `MOODLE_TOKEN` del entorno. Los errores de red y de respuesta Moodle se mapean a `MoodleWsError(status_code, detail)`.

### D-04 — Cifrado AES-256 de `email` delegado a la util de C-02

**Decisión**: reutilizar la función `encrypt_field` / `decrypt_field` del módulo `app/core/crypto.py` (C-02). `EntradaPadron.email` se almacena cifrado; el repository desencripta al leer.

**No decisión pendiente**: el mecanismo ya existe y es el estándar del proyecto.

### D-05 — `usuario_id` nullable: alumno sin cuenta

**Decisión**: `EntradaPadron.usuario_id` es nullable. Un alumno puede estar en el padrón antes de que el sistema le cree una cuenta. El matching `email → usuario_id` se realiza en un step posterior (C-10 o job de reconciliación). El padrón no bloquea la ingesta por falta de cuenta.

### D-06 — Soft delete sobre `VersionPadron` para vaciado

**Decisión**: F1.5 (vaciar datos de materia) marca la versión activa del usuario como `activa = false` + `deleted_at = now()`. No se borran físicamente ni las versiones ni las entradas (preserva auditoría). El scope del vaciado es `(actor_id × materia_id)` tal como exige RN-04.

**Diferencia con activar nueva versión**: activar desactiva la versión anterior pero no la borra; vaciar marca la versión activa como eliminada lógicamente, dejando la materia sin versión activa.

## Risks / Trade-offs

- **[Risk] Moodle WS no disponible en algunos tenants** → Mitigación: el fallback de carga manual por archivo está siempre disponible; el endpoint de sync on-demand devuelve `503` con mensaje claro si el tenant no tiene Moodle configurado.
- **[Risk] Archivo de padrón con formato no estándar** → Mitigación: el step de preview valida columnas requeridas (`nombre`, `apellidos`, `email`, `comision`) y retorna errores de validación por columna antes de cualquier escritura en DB.
- **[Risk] Payload grande en confirm** → Mitigación: limit de tamaño configurable via `MAX_PADRON_ROWS` (default 2000); más de eso → error 413 con instrucción de dividir la carga.
- **[Risk] Transacción larga al activar padrón grande** → Mitigación: la activación (desactivar anterior + insertar N entradas) corre en una sola transacción; con 2000 filas el tiempo esperado es <500 ms en PostgreSQL local. Aceptable para el caso de uso.
- **[Risk] PII en logs** → Mitigación: `EntradaPadron.email` nunca se incluye en logs; el repr del modelo omite el campo cifrado.

## Migration Plan

1. Ejecutar migración 008 (`version_padron`, `entrada_padron`, índices, constraint parcial).
2. Deploy del código nuevo (router, service, repository, integrations/moodle_ws.py).
3. No hay datos previos que migrar (tabla nueva).
4. **Rollback**: `alembic downgrade -1` elimina ambas tablas. No hay dependencias en tablas existentes que impidan el rollback (FKs son todas salientes desde las tablas nuevas hacia las existentes).

## Open Questions

- **OQ-01**: ¿El token de Moodle WS es por tenant o global? Si es por tenant, necesita almacenarse en la configuración del tenant (tabla `TenantConfig` si existe, o env var por tenant). Resolver antes de implementar `moodle_ws.py`.
- **OQ-02**: ¿Cuáles son las columnas exactas del export de Moodle que mapean a `(nombre, apellidos, email, comision, regional)`? Requiere acceso a un entorno Moodle de prueba o documentación del WS específico.
- **OQ-03**: ¿El permiso `padron:cargar` aplica a PROFESOR solo sobre las materias de su asignación vigente, o también sobre materias donde fue asignado en el pasado? Consistente con el modelo de C-07: solo asignaciones vigentes.
