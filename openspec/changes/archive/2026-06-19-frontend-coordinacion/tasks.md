## 1. Foundation — QueryClient, Sidebar fix, Routes

- [x] 1.1 Add `QueryClientProvider` in `AppLayout.tsx` wrapping `<Outlet />` with configured `QueryClient` (staleTime 30s, retry 1)
- [x] 1.2 Create `shared/hooks/useMenuItems.ts` — custom hook that calls `usePermission()` at top level for each domain permission and filters the sidebar items declaratively
- [x] 1.3 Update `Sidebar.tsx` to use `useMenuItems()` instead of inline `.filter()` with `usePermission`
- [x] 1.4 Add domain menu items to the sidebar array: Equipos docentes (`equipos:asignar`), Avisos (`avisos:publicar`), Tareas internas (`tareas:gestionar`), Coloquios (`coloquios:gestionar`), Estructura académica (`estructura:gestionar`), Encuentros (`encuentros:gestionar`), Guardias (`guardias:registrar`)
- [x] 1.5 Add lazy imports and protected routes in `App.tsx` for all domain features: `/equipos/*`, `/avisos/*`, `/tareas/*`, `/coloquios/*`, `/estructura/*`, `/encuentros/*`, `/guardias/*`
- [x] 1.6 Verify `npm run dev` works without errors and sidebar renders correctly

## 2. Equipos Module — Types, Services, Query Keys

- [x] 2.1 Create `features/equipos/types/index.ts` with `Equipo`, `Asignacion`, `AsignacionMasivaRequest`, `EquipoFilters`, `ClonarRequest`, `VigenciaRequest` types
- [x] 2.2 Create `features/equipos/services/equiposApi.ts` with all API functions: `fetchMisEquipos`, `fetchEquipos`, `crearAsignacionMasiva`, `clonarEquipo`, `actualizarVigencia`, `exportarEquipo`, `fetchAsignaciones`, `crearAsignacion`, `eliminarAsignacion`
- [x] 2.3 Create query key factory `features/equipos/hooks/equiposKeys.ts` with `all`, `lists()`, `list(filters)`, `details()`, `detail(id)`
- [x] 2.4 Create `features/equipos/hooks/useEquipos.ts` with `useMisEquipos()`, `useEquipos(filters)`, `useAsignaciones(equipoFilters)`
- [x] 2.5 Create `features/equipos/hooks/useEquipoMutations.ts` with `useAsignacionMasiva()`, `useClonarEquipo()`, `useActualizarVigencia()`, `useCrearAsignacion()`, `useEliminarAsignacion()`

## 3. Equipos Module — Components and Pages

- [x] 3.1 Create `EquipoCard.tsx` — card component showing materia, carrera, cohorte, cantidad de docentes, vigencia
- [x] 3.2 Create `EquipoTable.tsx` — table with columns (materia, comisiones, docentes, vigencia) and action buttons (asignación masiva, clonar, exportar, ajustar vigencia)
- [x] 3.3 Create `AsignacionMasivaForm.tsx` — step form with materia/carrera/cohorte select, rol select, responsable optional, comisiones, vigencia, and multi-user select with search
- [x] 3.4 Create `ClonarEquipoForm.tsx` — form with origen equipo selector, destino carrera/cohorte selectors, nueva vigencia
- [x] 3.5 Create `VigenciaForm.tsx` — inline form for desde/hasta dates with validation
- [x] 3.6 Create `AsignacionRow.tsx` — editable row for individual assignment with delete action
- [x] 3.7 Create `MisEquiposPage.tsx` — grid of `EquipoCard` using `useMisEquipos()`
- [x] 3.8 Create `EquiposListPage.tsx` — `EquipoTable` with filters + action buttons, using `useEquipos(filters)`
- [x] 3.9 Create `AsignacionMasivaPage.tsx` — wrapper for `AsignacionMasivaForm` showing results (creadas/rechazadas)
- [x] 3.10 Create `ClonarEquipoPage.tsx` — wrapper for `ClonarEquipoForm` showing results (clonadas/omitidas)

## 4. Avisos Module — Types, Services, Hooks

- [x] 4.1 Create `features/avisos/types/index.ts` with `Aviso`, `AvisoFormData`, `Alcance` (enum string), `Severidad` (enum string)
- [x] 4.2 Create `features/avisos/services/avisosApi.ts` — `fetchAvisos`, `crearAviso`, `actualizarAviso`, `eliminarAviso`, `fetchAviso`
- [x] 4.3 Create query key factory and hooks: `useAvisos()`, `useAviso(id)`, `useCrearAviso()`, `useActualizarAviso()`, `useEliminarAviso()`

## 5. Avisos Module — Components and Pages

- [x] 5.1 Create `AvisoFormDialog.tsx` — modal with RHF + Zod form fields: titulo, cuerpo, alcance (conditional fields), severidad, inicio_en, fin_en, orden, requiere_ack
- [x] 5.2 Create `AvisoTable.tsx` — table with columns (título, alcance badge, severidad badge, vigencia, activo toggle, acciones)
- [x] 5.3 Create `AvisosListPage.tsx` — table + "Nuevo aviso" button that opens `AvisoFormDialog` in create or edit mode
- [x] 5.4 Create `AvisoFormPage.tsx` — standalone page for create/edit via /nuevo and /:id/editar routes

## 6. Tareas Module — Types, Services, Hooks

- [x] 6.1 Create `features/tareas/types/index.ts` with `Tarea`, `TareaFormData`, `TareaEstado`, `Comentario`
- [x] 6.2 Create `features/tareas/services/tareasApi.ts` — `fetchMisTareas`, `fetchTareas`, `crearTarea`, `eliminarTarea`, `reasignarTarea`, `cambiarEstado`, `fetchComentarios`, `agregarComentario`
- [x] 6.3 Create query key factory and hooks: `useMisTareas()`, `useTareas(filters)`, `useTarea(id)`, `useComentarios(tareaId)`, plus all mutation hooks

## 7. Tareas Module — Components and Pages

- [x] 7.1 Create `TareaTable.tsx` — table with columns (título, asignado, estado badge, prioridad, vencimiento, acciones)
- [x] 7.2 Create `TareaKanban.tsx` — three-column kanban (Pendiente, En Progreso, Completada) with drag-to-change-state
- [x] 7.3 Create `TareaFormDialog.tsx` — modal with RHF + Zod: título, descripción, prioridad, asignado_a (user select), fecha_vencimiento
- [x] 7.4 Create `ComentarioList.tsx` — timeline of comments with author avatar, date, content
- [x] 7.5 Create `ComentarioForm.tsx` — inline textarea + submit for new comment
- [x] 7.6 Create `TareaDetail.tsx` — full task detail with info + `ComentarioList` + `ComentarioForm`
- [x] 7.7 Create `MisTareasPage.tsx` — table using `useMisTareas()` with action to change state
- [x] 7.8 Create `TareasListPage.tsx` — table + kanban toggle + filter bar + "Nueva tarea" button
- [x] 7.9 Create `TareaDetailPage.tsx` — wrapper for `TareaDetail` with back navigation

## 8. Coloquios Module — Types, Services, Hooks

- [x] 8.1 Create `features/coloquios/types/index.ts` with `Coloquio`, `ColoquioFormData`, `MetricasColoquios`, `AgendaItem`, `RegistroAcademico`
- [x] 8.2 Create `features/coloquios/services/coloquiosApi.ts` — `fetchColoquios`, `crearColoquio`, `fetchMetricas`, `fetchAgenda`, `fetchRegistroAcademico`
- [x] 8.3 Create query key factory and hooks: `useColoquios()`, `useMetricas()`, `useAgenda(filters)`, `useRegistroAcademico()`, `useCrearColoquio()`

## 9. Coloquios Module — Components and Pages

- [x] 9.1 Create `MetricasPanel.tsx` — 4 stat cards showing total_candidatos, instancias_activas, reservas_activas, notas_registradas
- [x] 9.2 Create `ColoquioTable.tsx` — table with columns (materia, instancia, tipo, convocados, reservas, cupos, acciones)
- [x] 9.3 Create `ColoquioFormDialog.tsx` — modal with RHF + Zod: materia_id, cohorte_id, tipo, instancia, dias_disponibles
- [x] 9.4 Create `AgendaTable.tsx` — table with filters (materia, cohorte, rango fechas) showing alumno, materia, fecha_hora
- [x] 9.5 Create `RegistroAcademicoTable.tsx` — table of registered grades
- [x] 9.6 Create `ColoquiosDashboardPage.tsx` — `MetricasPanel` at top + `ColoquioTable` below + "Nueva convocatoria" button
- [x] 9.7 Create `ColoquiosAgendaPage.tsx` — filter bar + `AgendaTable`
- [x] 9.8 Create `RegistroAcademicoPage.tsx` — `RegistroAcademicoTable` with optional filters

## 10. Estructura Module — Types, Services, Hooks

- [x] 10.1 Create `features/estructura/types/index.ts` with `Carrera`, `Programa`, `FechaAcademica`, `CalendarioItem`
- [x] 10.2 Create `features/estructura/services/estructuraApi.ts` — `fetchCarreras`, `crearCarrera`, `fetchProgramas`, `crearPrograma` (FormData), `fetchPrograma`, `fetchFechas`, `crearFecha`, `actualizarFecha`, `fetchCalendario`
- [x] 10.3 Create query key factory and hooks: `useCarreras()`, `useProgramas()`, `useFechas()`, `useCalendario()`, `useCrearCarrera()`, `useCrearPrograma()`, `useCrearFecha()`, `useActualizarFecha()`

## 11. Estructura Module — Components and Pages

- [x] 11.1 Create `CarreraTable.tsx` — simple table of carreras with create button
- [x] 11.2 Create `ProgramaTable.tsx` — table of programas with upload button and download link
- [x] 11.3 Create `ProgramaUploadDialog.tsx` — modal with file input (PDF only) + materia/carrera selectors
- [x] 11.4 Create `FechaTable.tsx` — table of fechas académicas with edit/create actions
- [x] 11.5 Create `FechaFormDialog.tsx` — modal with RHF + Zod: tipo, titulo, fecha, descripcion, materia_id (optional)
- [x] 11.6 Create `CalendarioView.tsx` — simple monthly list view of fechas académicas
- [x] 11.7 Replace `CarrerasListPage.tsx` — `CarreraTable` + create form
- [x] 11.8 Replace `ProgramasListPage.tsx` — `ProgramaTable` + `ProgramaUploadDialog`
- [x] 11.9 Replace `FechasAcademicasPage.tsx` — toggle between `FechaTable` and `CalendarioView`

## 12. Encuentros Module — Types, Services, Hooks

- [x] 12.1 Create `features/encuentros/types/index.ts` with `SlotEncuentro`, `InstanciaEncuentro`, `SlotCreateRequest`, `InstanciaEditRequest`, `EstadoInstancia`
- [x] 12.2 Create `features/encuentros/services/encuentrosApi.ts` — `fetchSlots`, `crearSlot`, `fetchSlot`, `eliminarSlot`, `fetchInstancias`, `fetchInstancia`, `editarInstancia`, `exportarHTML`
- [x] 12.3 Create query key factory and hooks: `useSlots(filters)`, `useSlot(id)`, `useInstancias(filters)`, `useCrearSlot()`, `useEliminarSlot()`, `useEditarInstancia()`

## 13. Encuentros Module — Components and Pages

- [x] 13.1 Create `SlotTable.tsx` — table of slots with columns (materia, título, día, hora, tipo, instancias, acciones: ver/eliminar/export HTML)
- [x] 13.2 Create `SlotDetail.tsx` — detail view showing slot metadata + list of `InstanciaRow` components
- [x] 13.3 Create `InstanciaRow.tsx` — editable row for an instance with inline fields: estado (select), meet_url, video_url, comentario
- [x] 13.4 Create `EncuentroFormDialog.tsx` — modal with RHF + Zod: modo toggle (recurrente/único), conditional fields (cant_semanas vs fecha_unica), dia_semana, hora, materia, titulo, meet_url
- [x] 13.5 Create `EncuentrosSlotsPage.tsx` — `SlotTable` + "Nuevo slot" button + filter by materia
- [x] 13.6 Create `SlotDetailPage.tsx` — `SlotDetail` with back navigation, all instances editable

## 14. Guardias Module — Types, Services, Hooks

- [x] 14.1 Create `features/guardias/types/index.ts` with `Guardia`, `GuardiaCreateRequest`, `GuardiaFiltros`, `EstadoGuardia`
- [x] 14.2 Create `features/guardias/services/guardiasApi.ts` — `fetchGuardias`, `crearGuardia`, `fetchGuardia`, `cambiarEstado`, `exportGuardiasCSV`
- [x] 14.3 Create query key factory and hooks: `useGuardias(filters)`, `useCrearGuardia()`, `useCambiarEstadoGuardia()`

## 15. Guardias Module — Components and Pages

- [x] 15.1 Create `GuardiaTable.tsx` — table with columns (materia, carrera, cohorte, día, horario, estado badge, acciones) and filters bar
- [x] 15.2 Create `GuardiaFormDialog.tsx` — modal with RHF + Zod: materia, carrera, cohorte, día, horario, comentarios
- [x] 15.3 Create `GuardiaEstadoBadge.tsx` — badge component showing estado color-coded with dropdown to change state
- [x] 15.4 Create `GuardiasListPage.tsx` — `GuardiaTable` + "Nueva guardia" button + "Exportar CSV" button

## 16. Tests

- [x] 16.1 Write test for `useMenuItems` hook — verifica filtrado correcto según permisos mock
- [x] 16.2 Write test for `EquiposListPage` — render with mock data, verifica tabla visible
- [x] 16.3 Write test for `AsignacionMasivaForm` — fill form and submit, verifica mutation called
- [x] 16.4 Write test for `AvisosListPage` — render with mock avisos, verifica tabla con badges
- [x] 16.5 Write test for `AvisoFormDialog` — validation: submit vacío muestra errores
- [x] 16.6 Write test for `TareasListPage` — render with mock tareas, verifica filtros funcionan
- [x] 16.7 Write test for `MetricasPanel` — render with mock metrics, verifica 4 cards visibles
- [x] 16.8 Write test for `CarrerasListPage` — render empty state "No hay carreras registradas"
- [x] 16.9 Write test for `EncuentrosSlotsPage` — render with mock slots, verifica tabla visible
- [x] 16.10 Write test for `GuardiasListPage` — render with mock guardias, verifica filtros y export button
- [x] 16.11 Verify all tests pass with `npm run test` — 85 tests pass, 0 regressions
