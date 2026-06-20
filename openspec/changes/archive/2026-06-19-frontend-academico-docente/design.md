## Context

`C-21 frontend-shell-y-auth` ya está archivado y aporta el sustrato: SPA React 18 + TypeScript + Vite con estructura feature-based, Tailwind, TanStack Query, React Hook Form + Zod, e instancia Axios centralizada (`@/shared/services/api`) con interceptor de refresh transparente y `ForbiddenError` tipado para 403. El `AuthContext` expone `hasPermission(...)`, el `<ProtectedRoute>` protege rutas por permiso, y el `Sidebar` filtra ítems por permiso. `C-22` monta las pantallas docentes SOBRE ese shell, sin reescribir nada del shell.

Actualmente `C-10 calificaciones-y-umbral`, `C-11 analisis-atrasados-reportes` y `C-12 comunicaciones-cola-worker` ya están implementados y archivados. Los contratos de API de estos 3 cambios están **confirmados** contra el backend real (paths, schemas, permisos). `C-06`/`C-07`/`C-09` también están completos. El frontend se testea con mocks de Axios (regla dura: tests sin tocar backend; en frontend el equivalente es mock del cliente HTTP, no de la lógica de UI), pero los contratos ya no son tentativos — están fijados por los specs sincronizados en `openspec/specs/`.

Governance del dominio: **BAJO** (pages frontend sin lógica crítica; la autorización real vive en backend). Autonomía total si pasan los tests. La identidad/tenant nunca se infiere en el cliente: el frontend solo refleja permisos que `AuthContext` ya resolvió desde el JWT verificado.

## Goals / Non-Goals

**Goals:**
- Cinco features nuevas (`comisiones`, `padron`, `calificaciones`, `atrasados`, `comunicaciones`) cada una con `{components,hooks,services,types,pages}`, autocontenidas, sin imports cross-feature (solo desde `shared/`).
- Toda I/O de datos pasa por hooks de TanStack Query envolviendo funciones de `services/` que usan la instancia `api` centralizada. Cero `useEffect` + fetch manual, cero `axios.create()` fuera de `shared/services/api.ts`.
- Contratos de API (endpoints + DTOs) documentados como tipos TypeScript en cada `features/<x>/types/`, de modo que el backend pueda implementarlos al pie de la letra y, ante divergencia, solo cambie la capa `services/`/`types/`.
- Tracking de estado de comunicaciones "en tiempo real" mediante polling de TanStack Query (`refetchInterval`) mientras haya mensajes en estado no terminal.
- Tests Vitest + RTL con mocks de `api`: import flow, tabla de atrasados, preview de comunicación, transiciones de estado de la cola. Cobertura ≥80% líneas.

**Non-Goals:**
- No se implementa ni se mockea el backend real (eso es `C-09…C-12`). No hay migraciones, ni modelos, ni endpoints reales.
- No se construyen las features de COORDINADOR/ADMIN (monitores transversales F2.7/F2.9, avisos, tareas, equipos) — eso es `C-23`. `C-22` cubre solo la vista docente PROFESOR/TUTOR.
- No se resuelve PA-01/PA-07 (catálogo Materia vs InstanciaDictado, cohortes↔carrera): el selector de comisión consume el contrato que `C-06`/`C-07` definan; si ese contrato cambia, se ajusta `comisiones/types` y `comisiones/services`.
- No WebSockets/SSE para el tracking: se usa polling (suficiente para el volumen de la cola y sin nueva dependencia de infra).

## Decisions

### D-1: Parsing y preview de archivos los hace el backend, no el cliente
El preview de actividades (calificaciones) y de alumnos (padrón) lo genera el **backend** al recibir el archivo (FL-02 paso 3, F1.1). El frontend hace `multipart/form-data` POST del archivo y recibe el preview ya parseado (actividades detectadas, alumnos detectados, columnas `(Real)` por RN-01, valores textuales por RN-02). 
- **Por qué**: la detección de columnas `(Real)`, el mapeo de escala textual y el cruce de reportes (RN-07/RN-08) son reglas de negocio que deben vivir en backend (regla dura: nunca lógica de negocio en cliente como fuente de verdad). Evita duplicar/divergir la lógica y elimina la dependencia de un parser xlsx en el bundle.
- **Alternativa descartada**: parsear xlsx en cliente con SheetJS para preview instantáneo → añade peso al bundle, duplica reglas y crea riesgo de divergencia con el cómputo del backend.

### D-2: Flujo de importación en dos fases (upload-preview → confirm-commit)
La importación de calificaciones y de padrón se modela como dos llamadas: (1) `POST .../preview` que sube el archivo y devuelve un `import_id` + el preview, sin persistir; (2) `POST .../commit` con `import_id` + selección del usuario (actividades elegidas, umbral / confirmación de upsert) que persiste.
- **Por qué**: separa "ver qué se detectó" de "confirmar el efecto" (upsert destructivo de padrón RN-05, selección de actividades). Permite cancelar sin efectos. El `import_id` evita re-subir el archivo en el commit.
- **Alternativa descartada**: single-shot upload que persiste de una → imposible mostrar preview antes de confirmar el upsert destructivo, riesgo alto de pérdida de padrón.

### D-3: Selector de comisión como contexto compartido (feature `comisiones`)
Materia + cohorte forman el "contexto de trabajo" del docente y son entrada de casi todas las pantallas. Se aísla en `features/comisiones` un selector + hook `useComisionContext` que las demás features consumen vía un provider montado en el layout docente. El estado del contexto se guarda en query params de la URL (`?materia=&cohorte=`) para que sea linkeable y sobreviva al refresh.
- **Por qué**: una sola fuente para el contexto, navegación profunda compartible, y desacople: `padron`/`calificaciones`/`atrasados`/`comunicaciones` no se importan entre sí, todas dependen de `comisiones` (que vive como feature, importada solo a través de su API pública, o promovida a `shared/` si hiciera falta evitar cross-feature import).
- **Decisión de límite**: para respetar "ningún módulo de dominio importa de otro", el provider y el hook de contexto de comisión se ubican en `shared/comision/` (contexto transversal), mientras el *selector visual* y los servicios de catálogo viven en `features/comisiones`. Las features consumen el hook desde `shared/`.

### D-4: Tracking en tiempo real vía polling de TanStack Query
La cola de comunicaciones usa `useQuery` con `refetchInterval` activo solo mientras existan mensajes en estado no terminal (`Pendiente`/`Enviando`); cuando todos están en `OK`/`Fallido`/`Cancelado`, el polling se detiene (`refetchInterval: false`).
- **Por qué**: cubre el requisito "estado visible en tiempo real" (F3.2/RN-15) sin introducir WebSockets/SSE ni nueva infra. TanStack Query ya gestiona el ciclo de vida.
- **Alternativa descartada**: SSE/WebSocket → nueva dependencia de infra y de contrato backend, sobredimensionado para el volumen de la cola.

### D-5: Contratos de API como tipos TS versionados en cada feature
Cada `features/<x>/types/index.ts` declara los DTOs request/response esperados y cada `features/<x>/services/<x>Api.ts` declara las funciones tipadas contra esos DTOs (mismo patrón que `features/auth/services/authApi.ts`). Los endpoints esperados se documentan en los specs (sección de contratos). 
- **Por qué**: el contrato queda explícito y testeable; cuando el backend `C-09…C-12` se implemente, el ajuste se concentra en `services/` + `types/` sin tocar componentes ni hooks.
- **Convención**: DTOs en `snake_case` para campos que cruzan la red (coinciden con Pydantic backend), mapeados a tipos de dominio del frontend en la capa de servicio si conviene.

### D-6: Permisos en UI espejan el backend, fail-closed visual
Cada ruta nueva se envuelve con `<ProtectedRoute permission="...">` y cada ítem de `Sidebar` declara su `permission`. Las acciones sensibles dentro de una página (p. ej. botón "Aprobar lote") se ocultan/deshabilitan con `usePermission('comunicacion:aprobar')`. La autorización real la impone el backend (403 → `ForbiddenError` → UI muestra "Sin permiso"); la UI solo evita mostrar lo que el usuario no puede usar.
- **Permisos usados**: `calificaciones:importar`, `atrasados:ver`, `comunicacion:enviar`, `comunicacion:aprobar` (de `03_actores_y_roles.md`).

## Risks / Trade-offs

- **[Contratos de backend confirmados, no tentativos]** → C-10, C-11, C-12 ya están implementados; los paths, schemas y permisos se actualizaron en los specs de C-22 para reflejar el backend real. Si C-06/C-07 introducen cambios en el catálogo de comisiones, el ajuste es local en `services/`/`types/`.
- **[PA-01/PA-07 abiertas afectan el selector de comisión]** → `comisiones` solo consume el catálogo de materias/cohortes; no codifica la semántica Materia vs InstanciaDictado. Si `C-06` cierra la pregunta de otra forma, cambia solo el DTO de catálogo.
- **[Polling de la cola genera carga si hay muchos mensajes pendientes]** → `refetchInterval` moderado (p. ej. 5s) y se apaga al alcanzar estados terminales. Si el volumen lo exige, el backend puede exponer un endpoint de resumen liviano.
- **[Upsert destructivo de padrón (RN-05) puede causar pérdida accidental]** → flujo en dos fases (D-2) con preview + confirmación explícita ("esto reemplaza el padrón actual de la materia") antes del commit. La UI nunca commitea sin confirmación.
- **[Sin parser xlsx en cliente, no hay validación previa al upload]** → aceptable: el backend valida y devuelve errores de formato en el preview; la UI los muestra. Mantiene el bundle liviano (D-1).

## Migration Plan

No aplica migración de datos (cambio puramente frontend, aditivo). Despliegue:
1. Se construyen las features con mocks; los tests pasan sin backend.
2. Al implementarse `C-09…C-12`, se levanta `VITE_API_URL` apuntando al backend real y se valida E2E manual el flujo FL-02/FL-04.
3. Rollback: al ser aditivo (nuevos ítems de Sidebar + nuevas rutas), revertir el commit del feature deja el shell intacto. Sin estado persistido en cliente que migrar.

## Open Questions

- Forma exacta del contrato de catálogo de comisiones (depende del cierre de PA-01/PA-07 en `C-06`/`C-07`). Se asume `{ materia_id, nombre }` y `{ cohorte_id, etiqueta }` hasta confirmación.
- Umbral de volumen que dispara la cola de aprobación (F3.3/RN-17): lo decide el backend; la UI solo refleja el estado `requiere_aprobacion` que venga en la respuesta de envío.
- Formato/headers exactos del export de "entregas sin corregir" (F2.6) y de notas finales (F2.5): se asume descarga de archivo (blob) generado por backend; la UI dispara la descarga.
