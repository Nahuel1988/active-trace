## Context

La SPA base (C-21) provee shell con layout, auth y cliente HTTP. El backend expone endpoints completos para 5 dominios (equipos, avisos, tareas, coloquios, estructura) que los perfiles COORDINADOR y ADMIN necesitan consumir. No existe TanStack Query usage todavía (auth usa estado directo en AuthContext). El Sidebar tiene un hooks violation: `usePermission()` es llamado dentro del `.filter()` callback en el módulo.

## Goals / Non-Goals

**Goals:**
- 5 feature modules funcionales con TanStack Query (`useQuery`/`useMutation`) para server state.
- Rutas protegidas con lazy loading + permisos en App.tsx.
- Sidebar con items de dominio filtrados por permiso, sin hooks violation.
- Formularios React Hook Form + Zod con schemas tipados para cada operación de creación/edición.
- Tests unitarios de hooks y componentes críticos por módulo.
- Patrón query key factory centralizado para evitar key collisions.

**Non-Goals:**
- Módulo de liquidaciones (C-18) — preguntas PA-22/PA-23 sin cerrar.
- SSR, i18n, tema oscuro.
- Modificaciones al backend.

## Decisions

### D-01 — TanStack Query para server state de cada feature

Cada feature module define su propio conjunto de hooks con `useQuery`/`useMutation`. Los query keys siguen el patrón factory:

```
equiposKeys.all = ['equipos'] as const
equiposKeys.lists = () => [...equiposKeys.all, 'list'] as const
equiposKeys.list = (filters: EquipoFilters) => [...equiposKeys.lists(), filters] as const
equiposKeys.details = () => [...equiposKeys.all, 'detail'] as const
equiposKeys.detail = (id: string) => [...equiposKeys.details(), id] as const
```

Cada mutación invalida la lista correspondiente con `queryClient.invalidateQueries()`.

*Alternativa descartada*: un solo hook genérico de fetch — no escala con tipos y invalidaciones específicas por módulo.

### D-02 — Sidebar items array con pre-filter por permisos resuelto fuera del render

El hooks violation actual (usePermission dentro de .filter()) se corrige moviendo el filtrado a un custom hook `useMenuItems()` que itera los items y llama `usePermission(item.permission)` como hook en posición fija (no condicional). El array de definición es declarativo, el filtrado es por hook.

```
function useMenuItems(): SidebarItem[] {
  const canInicio = usePermission(undefined) // siempre true
  const canEquipos = usePermission('equipos:asignar')
  const canAvisos = usePermission('avisos:publicar')
  const canTareas = usePermission('tareas:gestionar')
  const canColoquios = usePermission('coloquios:gestionar')
  const canEstructura = usePermission('estructura:gestionar')
  const canEncuentros = usePermission('encuentros:gestionar')
  const canGuardias = usePermission('guardias:registrar')

  return sidebarItems.filter(item => {
    if (!item.permission) return true
    const permMap: Record<string, boolean> = {
      'equipos:asignar': canEquipos,
      'avisos:publicar': canAvisos,
      'tareas:gestionar': canTareas,
      'coloquios:gestionar': canColoquios,
      'estructura:gestionar': canEstructura,
      'encuentros:gestionar': canEncuentros,
      'guardias:registrar': canGuardias,
    }
    return permMap[item.permission] ?? false
  })
}
```

*Alternativa descartada*: un solo `hasPermissions()` que recibe array — viola rules of hooks porque el array length puede cambiar entre renders.

### D-03 — API service modules por feature, no shared genérico

Cada feature module define su propio `services/<feature>Api.ts` que importa la instancia `api` de `shared/services/api.ts`. Cada función es un wrapper tipado que llama al endpoint y retorna el tipo correcto. Esto mantiene el patrón establecido por `features/auth/services/authApi.ts`.

```
// features/equipos/services/equiposApi.ts
import { api } from '@/shared/services/api'
import type { Equipo, EquipoFilters, AsignacionMasivaRequest } from '../types'

export function fetchMisEquipos(): Promise<Equipo[]> {
  return api.get('/api/v1/equipos/mis-equipos').then(r => r.data)
}
```

### D-04 — Estructura de páginas: list + detail/form

Cada feature sigue el patrón:
- `Pages/FeatureListPage.tsx` — tabla/listado con filtros, acciones inline (editar, eliminar, crear).
- `Pages/FeatureDetailPage.tsx` — detalle de un registro (cuando aplica, ej. tarea individual).
- `Pages/FeatureNewPage.tsx` — formulario de creación (o modal si aplica).

Para features simples (avisos, fechas académicas), el formulario va como modal o drawer en la misma página de listado.

### D-05 — QueryClientProvider en AppLayout, no en main.tsx

`QueryClientProvider` se coloca dentro de `<ProtectedRoute>` en la ruta protegida, no globalmente. Las rutas públicas (login, recovery) no necesitan cache de server state.

## Route Structure

```
/                                     — HomePage (bienvenida, sin cambios)
/equipos                              — EquiposListPage          (equipos:asignar)
/equipos/mis-equipos                  — MisEquiposPage           (authenticated)
/equipos/asignacion-masiva            — AsignacionMasivaPage     (equipos:asignar)
/equipos/clonar                       — ClonarEquipoPage         (equipos:asignar)
/avisos                               — AvisosListPage           (avisos:publicar)
/avisos/nuevo                         — AvisoFormPage            (avisos:publicar)
/avisos/:id/editar                    — AvisoFormPage            (avisos:publicar)
/tareas                               — TareasListPage           (tareas:gestionar)
/tareas/mias                          — MisTareasPage            (authenticated)
/tareas/nueva                         — TareaFormPage            (tareas:gestionar)
/tareas/:id                           — TareaDetailPage          (tareas:gestionar)
/coloquios                            — ColoquiosListPage        (coloquios:gestionar)
/coloquios/nuevo                      — ColoquioFormPage         (coloquios:gestionar)
/coloquios/agenda                     — ColoquiosAgendaPage      (coloquios:gestionar)
/coloquios/registro-academico         — RegistroAcademicoPage    (coloquios:gestionar)
/estructura                           — Home estructura          (estructura:gestionar)
/estructura/carreras                  — CarrerasListPage         (estructura:gestionar)
/estructura/programas                 — ProgramasListPage        (estructura:ver)
/estructura/fechas                    — FechasAcademicasPage     (estructura:ver)
/encuentros                           — EncuentrosSlotsPage     (encuentros:gestionar)
/encuentros/slots/:id                 — SlotDetailPage           (encuentros:gestionar)
/guardias                             — GuardiasListPage         (guardias:registrar)
```

## Component Tree per Module

### Equipos
```
features/equipos/
├── types/index.ts                    — Equipo, Asignacion, AsignacionMasivaRequest, EquipoFilters
├── services/equiposApi.ts            — fetchMisEquipos, fetchEquipos, crearAsignacionMasiva, clonarEquipo, actualizarVigencia, exportarEquipo, fetchAsignaciones, crearAsignacion, eliminarAsignacion
├── hooks/useEquipos.ts              — useQuery hooks (useMisEquipos, useEquipos, useAsignaciones)
├── hooks/useEquipoMutations.ts      — useMutation hooks (useAsignacionMasiva, useClonarEquipo, useActualizarVigencia, useCrearAsignacion, useEliminarAsignacion)
├── components/
│   ├── EquipoCard.tsx                — Card resumen de equipo (materia, comisión, cant. docentes)
│   ├── EquipoTable.tsx              — Tabla de equipos con filtros y acciones
│   ├── AsignacionMasivaForm.tsx     — Formulario de carga masiva con select múltiple de usuarios
│   ├── ClonarEquipoForm.tsx         — Formulario de clonación: origen → destino + vigencia
│   ├── VigenciaForm.tsx             — Formulario de ajuste de vigencia (inline)
│   └── AsignacionRow.tsx            — Fila de asignación editable
├── pages/
│   ├── EquiposListPage.tsx          — Tabla + filtros + botones: asignación masiva, clonar, exportar
│   ├── MisEquiposPage.tsx           — Grid de cards "mis equipos" (propio docente)
│   ├── AsignacionMasivaPage.tsx     — Formulario paso a paso
│   └── ClonarEquipoPage.tsx         — Formulario de clonación
```

### Avisos
```
features/avisos/
├── types/index.ts                    — Aviso, AvisoFormData, Alcance, Severidad
├── services/avisosApi.ts            — fetchAvisos, crearAviso, actualizarAviso, eliminarAviso, fetchAviso
├── hooks/useAvisos.ts              — useQuery hooks
├── hooks/useAvisoMutations.ts      — useMutation hooks
├── components/
│   ├── AvisoTable.tsx              — Tabla de avisos con badges de alcance/severidad/activo
│   ├── AvisoFormDialog.tsx         — Modal de creación/edición con RHF + Zod
│   ├── AvisoCard.tsx               — Card para vista rápida
│   └── AckBadge.tsx                — Badge de acknowledge tracking
├── pages/
│   ├── AvisosListPage.tsx          — Tabla + botón nuevo + modal de form
│   └── AvisoFormPage.tsx           — Página dedicada de creación/edición (ruta directa)
```

### Tareas
```
features/tareas/
├── types/index.ts                    — Tarea, TareaFormData, TareaEstado, Comentario
├── services/tareasApi.ts            — fetchMisTareas, fetchTareas, crearTarea, eliminarTarea, reasignarTarea, cambiarEstado, fetchComentarios, agregarComentario
├── hooks/useTareas.ts              — useQuery hooks
├── hooks/useTareaMutations.ts      — useMutation hooks
├── components/
│   ├── TareaTable.tsx              — Tabla con filtros por estado, asignado, prioridad
│   ├── TareaKanban.tsx             — Vista kanban (columnas: Pendiente, En Progreso, Completada)
│   ├── TareaFormDialog.tsx         — Modal de creación/edición
│   ├── TareaDetail.tsx             — Detalle de tarea + timeline de comentarios
│   ├── ComentarioList.tsx          — Lista de comentarios con fecha y autor
│   └── ComentarioForm.tsx          — Formulario inline de nuevo comentario
├── pages/
│   ├── TareasListPage.tsx          — Tabla + kanban toggle + botón nueva tarea
│   ├── MisTareasPage.tsx           — Vista filtrada (scope propio)
│   └── TareaDetailPage.tsx         — Detalle completo + comentarios
```

### Coloquios
```
features/coloquios/
├── types/index.ts                    — Coloquio, ColoquioFormData, MetricasColoquios, AgendaItem, RegistroAcademico
├── services/coloquiosApi.ts         — fetchColoquios, crearColoquio, fetchMetricas, fetchAgenda, fetchRegistroAcademico
├── hooks/useColoquios.ts           — useQuery hooks
├── hooks/useColoquioMutations.ts   — useMutation hooks
├── components/
│   ├── MetricasPanel.tsx           — 4 cards: candidatos, instancias, reservas, notas
│   ├── ColoquioTable.tsx           — Tabla de convocatorias con métricas inline
│   ├── ColoquioFormDialog.tsx      — Modal de creación/edición
│   ├── AgendaTable.tsx             — Tabla de reservas con filtros
│   └── RegistroAcademicoTable.tsx  — Tabla de notas registradas
├── pages/
│   ├── ColoquiosDashboardPage.tsx  — Panel principal: métricas arriba + tabla abajo
│   ├── ColoquiosListPage.tsx       — Listado de convocatorias
│   ├── ColoquiosAgendaPage.tsx     — Agenda consolidada
│   └── RegistroAcademicoPage.tsx   — Registro académico
```

### Encuentros
```
features/encuentros/
├── types/index.ts                    — SlotEncuentro, InstanciaEncuentro, SlotCreateRequest, InstanciaEditRequest
├── services/encuentrosApi.ts         — fetchSlots, crearSlot, fetchSlot, eliminarSlot, fetchInstancias, fetchInstancia, editarInstancia, exportHTML
├── hooks/useEncuentros.ts           — useQuery hooks
├── hooks/useEncuentroMutations.ts   — useMutation hooks
├── components/
│   ├── SlotTable.tsx                 — Tabla de slots con acciones (ver, eliminar, export HTML)
│   ├── SlotDetail.tsx                — Detalle de slot con lista de instancias
│   ├── InstanciaRow.tsx              — Fila de instancia editable (estado, meet_url, video_url, comentario)
│   └── EncuentroFormDialog.tsx       — Modal de creación de slot (recurrente/único)
├── pages/
│   ├── EncuentrosSlotsPage.tsx       — Tabla de slots + botón nuevo
│   └── SlotDetailPage.tsx            — Detalle de slot + instancias editables
```

### Guardias
```
features/guardias/
├── types/index.ts                    — Guardia, GuardiaCreateRequest, GuardiaFiltros, EstadoGuardia
├── services/guardiasApi.ts           — fetchGuardias, crearGuardia, fetchGuardia, cambiarEstadoGuardia, exportGuardiasCSV
├── hooks/useGuardias.ts             — useQuery hooks
├── hooks/useGuardiaMutations.ts     — useMutation hooks
├── components/
│   ├── GuardiaTable.tsx              — Tabla de guardias con filtros (materia, carrera, cohorte, estado)
│   ├── GuardiaFormDialog.tsx         — Modal de registro de guardia
│   └── GuardiaEstadoBadge.tsx        — Badge de estado (pendiente/realizada/cancelada) con cambio inline
├── pages/
│   └── GuardiasListPage.tsx          — Tabla + filtros + botón nueva guardia + export CSV
```

### Estructura
```
features/estructura/
├── types/index.ts                    — Carrera, Programa, FechaAcademica, CalendarioItem
├── services/estructuraApi.ts        — fetchCarreras, crearCarrera, fetchProgramas, crearPrograma, fetchPrograma, fetchFechas, crearFecha, actualizarFecha, fetchCalendario
├── hooks/useEstructura.ts          — useQuery hooks
├── hooks/useEstructuraMutations.ts — useMutation hooks
├── components/
│   ├── CarreraTable.tsx            — Tabla de carreras
│   ├── ProgramaTable.tsx           — Tabla de programas + upload button
│   ├── ProgramaUploadDialog.tsx    — Modal de upload de PDF
│   ├── FechaTable.tsx              — Tabla de fechas académicas
│   ├── FechaFormDialog.tsx         — Modal de creación/edición
│   └── CalendarioView.tsx          — Vista calendario (lista mensual simple)
├── pages/
│   ├── EstructuraHomePage.tsx      — Menú interno de estructura
│   ├── CarrerasListPage.tsx        — Listado de carreras
│   ├── ProgramasListPage.tsx       — Listado de programas + upload
│   └── FechasAcademicasPage.tsx    — Tabla + calendario toggle
```

## Data Flow

```
Browser → Router (React Router v6)
  → ProtectedRoute (verifica sesión + permiso declarado)
    → AppLayout (QueryClientProvider aquí)
      → Page Component (React.lazy)
        → useQuery hook (llama service module)
          → service module (llama api from shared/)
            → api.ts (Axios con interceptor de token + refresh)
              → Backend API

Mutaciones:
  → useMutation hook (llama service module)
    → onSuccess: invalidateQueries de la lista afectada
    → toast/notificación de resultado
```

### QueryClient configuration
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,       // 30s antes de refetch
      retry: 1,                // 1 reintento en error
      refetchOnWindowFocus: false,
    },
  },
})
```

## Backend Endpoints Reference

| Feature | Método | Endpoint | Permiso | Scope |
|---------|--------|----------|---------|-------|
| Equipos | GET | `/api/v1/equipos/mis-equipos` | authenticated | propio |
| Equipos | GET | `/api/v1/equipos` | equipos:asignar | tenant |
| Equipos | POST | `/api/v1/equipos/asignacion-masiva` | equipos:asignar | tenant |
| Equipos | POST | `/api/v1/equipos/clonar` | equipos:asignar | tenant |
| Equipos | PATCH | `/api/v1/equipos/vigencia` | equipos:asignar | tenant |
| Equipos | GET | `/api/v1/equipos/export` | equipos:asignar | tenant |
| Asignaciones | GET | `/api/v1/asignaciones` | equipos:asignar | tenant |
| Asignaciones | POST | `/api/v1/asignaciones` | equipos:asignar | tenant |
| Asignaciones | DELETE | `/api/v1/asignaciones/{id}` | equipos:asignar | tenant |
| Avisos | GET | `/api/v1/avisos/` | avisos:publicar | tenant |
| Avisos | POST | `/api/v1/avisos/` | avisos:publicar | tenant |
| Avisos | GET | `/api/v1/avisos/{id}` | avisos:publicar | tenant |
| Avisos | PUT | `/api/v1/avisos/{id}` | avisos:publicar | tenant |
| Avisos | DELETE | `/api/v1/avisos/{id}` | avisos:publicar | tenant |
| Tareas | GET | `/api/tareas/mias` | tareas:gestionar | scope propio |
| Tareas | GET | `/api/tareas` | tareas:gestionar | scope global |
| Tareas | POST | `/api/tareas` | tareas:gestionar | tenant |
| Tareas | DELETE | `/api/tareas/{id}` | tareas:gestionar | tenant |
| Tareas | POST | `/api/tareas/{id}/asignar` | tareas:gestionar | tenant |
| Tareas | PATCH | `/api/tareas/{id}/estado` | tareas:gestionar | tenant |
| Tareas | GET | `/api/tareas/{id}/comentarios` | tareas:gestionar | tenant |
| Tareas | POST | `/api/tareas/{id}/comentarios` | tareas:gestionar | tenant |
| Coloquios | GET | `/api/v1/coloquios` | coloquios:gestionar | tenant |
| Coloquios | POST | `/api/v1/coloquios` | coloquios:gestionar | tenant |
| Coloquios | GET | `/api/v1/coloquios/metricas` | coloquios:gestionar | tenant |
| Coloquios | GET | `/api/v1/coloquios/agenda` | coloquios:gestionar | tenant |
| Coloquios | GET | `/api/v1/coloquios/registro-academico` | coloquios:gestionar | tenant |
| Estructura | GET | `/api/v1/estructura/carreras` | estructura:gestionar | tenant |
| Estructura | POST | `/api/v1/estructura/carreras` | estructura:gestionar | tenant |
| Programas | GET | `/api/v1/programas` | estructura:ver | tenant |
| Programas | POST | `/api/v1/programas` | estructura:gestionar | tenant |
| Programas | GET | `/api/v1/programas/{id}` | estructura:ver | tenant |
| Fechas | GET | `/api/v1/fechas-academicas` | estructura:ver | tenant |
| Fechas | POST | `/api/v1/fechas-academicas` | estructura:gestionar | tenant |
| Fechas | PUT | `/api/v1/fechas-academicas/{id}` | estructura:gestionar | tenant |
| Fechas | GET | `/api/v1/fechas-academicas/calendario` | estructura:ver | tenant |
| Encuentros | POST | `/api/encuentros/slots` | encuentros:gestionar | scope global |
| Encuentros | GET | `/api/encuentros/slots` | encuentros:gestionar | scope global |
| Encuentros | GET | `/api/encuentros/slots/{slot_id}` | encuentros:gestionar | scope global |
| Encuentros | DELETE | `/api/encuentros/slots/{slot_id}` | encuentros:gestionar | scope global |
| Encuentros | GET | `/api/encuentros/instancias` | encuentros:gestionar | scope global |
| Encuentros | GET | `/api/encuentros/instancias/{instancia_id}` | encuentros:gestionar | scope global |
| Encuentros | PATCH | `/api/encuentros/instancias/{instancia_id}` | encuentros:gestionar | scope global |
| Encuentros | GET | `/api/encuentros/slots/{slot_id}/html` | encuentros:gestionar | scope global |
| Guardias | POST | `/api/guardias` | guardias:registrar | scope global |
| Guardias | GET | `/api/guardias` | guardias:registrar | scope global |
| Guardias | GET | `/api/guardias/{guardia_id}` | guardias:registrar | scope global |
| Guardias | PATCH | `/api/guardias/{guardia_id}/estado` | guardias:registrar | scope global |
| Guardias | GET | `/api/guardias/export` | guardias:registrar | scope global |

## Risks / Trade-offs

- **[Sidebar hooks violation actual puede romper con React 19]** → Fix inmediato en D-02. El approach de mapeo de permisos por item es mantenible pero requiere actualizar el permiso map cuando se agregan items nuevos.
- **[Estructura /cohortes y /materias son stubs → respuestas [] ]** → Las páginas de estructura muestran mensaje "Sin datos — funcionalidad en implementación" para cohortes y materias, sin errores.
- **[TanStack Query recién introducido en este change]** → Posibles problemas de粗细 configuración de cache. Mitigación: staleTime conservador (30s) y retry: 1. Se monitorea comportamiento en dev.
- **[Multi-tab refresh race condition]** → Misma mitigación que C-21: cookie httpOnly garantiza que el backend maneja el token más reciente.

## Open Questions

- ¿Upload de programas requiere manejo de archivos (multipart) o es solo URL/referencia? → Asumir multipart con FormData.
- ¿La exportación de equipos (GET /export) debe abrirse como descarga directa o generar un link temporario? → Asumir descarga directa con Blob response.
