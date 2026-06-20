> Strict TDD: para cada módulo, escribir el test que falla ANTES del código (RED → GREEN → TRIANGULATE → REFACTOR). Sin mocks de la lógica de negocio; los tests de UI usan datos mock de respuesta y verifican comportamiento, no tautologías.

## 1. Finanzas — Types, Services, Query Keys

- [ ] 1.1 Create `features/finanzas/types/index.ts` with `LiquidacionVista`, `SegmentoLiquidacion`, `LiquidacionItem`, `KpisLiquidacion`, `HistorialFilters`, `SalarioBase`, `SalarioPlus`, `SalarioBaseFormData`, `SalarioPlusFormData`, `Factura`, `FacturaFormData`, `FacturaFilters`, `EstadoFactura` — sin `any`, en `snake_case`
- [ ] 1.2 Create `features/finanzas/services/liquidacionesApi.ts` — `fetchLiquidaciones(cohorteId, periodo, usuarioId?)`, `cerrarLiquidacion(id)`, `fetchHistorial(filters)`, `calcularPeriodo(cohorteId, periodo)`
- [ ] 1.3 Create `features/finanzas/services/grillaApi.ts` — `fetchSalariosBase(rol?)`, `crearSalarioBase`, `actualizarSalarioBase`, `eliminarSalarioBase`, `fetchSalariosPlus(grupo?)`, `crearSalarioPlus`, `actualizarSalarioPlus`, `eliminarSalarioPlus`
- [ ] 1.4 Create `features/finanzas/services/facturasApi.ts` — `fetchFacturas(filters)`, `fetchFactura(id)`, `crearFactura`, `actualizarFactura`, `abonarFactura(id)`
- [ ] 1.5 Create query key factories: `liquidacionesKeys.ts`, `grillaKeys.ts`, `facturasKeys.ts` (D-02)

## 2. Finanzas — Liquidaciones (vista, cierre, historial)

- [ ] 2.1 Create `hooks/useLiquidaciones.ts` — `useLiquidaciones(cohorteId, periodo, usuarioId?)`, `useHistorial(filters)` keyed por scope/filtros
- [ ] 2.2 Create `hooks/useLiquidacionMutations.ts` — `useCerrarLiquidacion()` (invalida vista + historial), `useCalcularPeriodo()` (invalida vista)
- [ ] 2.3 Create `components/PeriodoSelector.tsx` — input month sincronizado con query param `?periodo=` (D-01)
- [ ] 2.4 Create `components/KpisCabecera.tsx` — 2 stat cards: `total_sin_factura`, `total_con_factura`
- [ ] 2.5 Create `components/SegmentoTable.tsx` — tabla reutilizable de un segmento (docente, rol, monto)
- [ ] 2.6 Create `components/LiquidacionSegmentada.tsx` — orquesta `KpisCabecera` + 3 `SegmentoTable` (general/nexo/facturantes) + estado vacío
- [ ] 2.7 Create `components/CerrarLiquidacionDialog.tsx` — modal de confirmación; maneja 409 (ya cerrada) como error inline (D-03)
- [ ] 2.8 Create `components/HistorialTable.tsx` — tabla de cerradas con filtros independientes (cohorte, período, docente)
- [ ] 2.9 Create `pages/LiquidacionesPage.tsx` — `PeriodoSelector` + `LiquidacionSegmentada` + acciones calcular/cerrar/exportar condicionadas por permiso (D-07); usa `useComisionContext` para cohorte
- [ ] 2.10 Create `pages/HistorialLiquidacionesPage.tsx` — `HistorialTable` con filtros

## 3. Finanzas — Grilla salarial (Base + Plus)

- [ ] 3.1 Create `hooks/useGrilla.ts` — `useSalariosBase(rol?)`, `useSalariosPlus(grupo?)`
- [ ] 3.2 Create `hooks/useGrillaMutations.ts` — crear/actualizar/eliminar base y plus; cada mutación invalida su lista
- [ ] 3.3 Create `components/SalarioBaseTable.tsx` — tabla ABM con filtro por rol y acciones
- [ ] 3.4 Create `components/SalarioBaseFormDialog.tsx` — modal RHF+Zod (rol, monto, desde, hasta); 409 solapamiento → error inline en campo vigencia (D-03)
- [ ] 3.5 Create `components/SalarioPlusTable.tsx` — tabla ABM con filtro por grupo
- [ ] 3.6 Create `components/SalarioPlusFormDialog.tsx` — modal RHF+Zod (grupo, rol, descripcion, monto, desde, hasta); 409 → error inline
- [ ] 3.7 Create `pages/GrillaSalarialPage.tsx` — pestañas/bloques Base y Plus, cada uno con tabla + form

## 4. Finanzas — Facturas

- [ ] 4.1 Create `hooks/useFacturas.ts` — `useFacturas(filters)`, `useFactura(id)`
- [ ] 4.2 Create `hooks/useFacturaMutations.ts` — `useCrearFactura()`, `useActualizarFactura()`, `useAbonarFactura()`; invalidan el listado
- [ ] 4.3 Create `components/FacturaTable.tsx` — tabla con filtros (período, estado) y badges de estado
- [ ] 4.4 Create `components/FacturaFormDialog.tsx` — modal RHF+Zod; selector `usuario_id` limitado a `facturador=true`; 422 (no facturador) → error inline
- [ ] 4.5 Create `components/AbonarFacturaButton.tsx` — botón con confirmación de transición Pendiente→Abonada; 409 → mensaje sin crash
- [ ] 4.6 Create `pages/FacturasListPage.tsx` — `FacturaTable` + "Nueva factura" + abonar inline

## 5. Finanzas — Tests

- [ ] 5.1 Test `LiquidacionSegmentada` — render con mock de 3 segmentos + KPIs; verifica 3 tablas y 2 KPIs visibles
- [ ] 5.2 Test `LiquidacionesPage` — estado vacío sin período seleccionado; acciones ocultas sin permiso (modo solo-lectura ADMIN)
- [ ] 5.3 Test `CerrarLiquidacionDialog` — confirma → llama mutación; 409 → muestra error inline sin cerrar
- [ ] 5.4 Test `SalarioBaseFormDialog` — submit válido llama mutación; 409 solapamiento → error inline conserva datos
- [ ] 5.5 Test `GrillaSalarialPage` — render con mock; verifica secciones Base y Plus visibles
- [ ] 5.6 Test `FacturaFormDialog` — selector solo facturadores; 422 → error inline
- [ ] 5.7 Test `AbonarFacturaButton` — confirma → llama abonar; 409 → mensaje sin crash

## 6. Admin — Types, Services, Query Keys

- [ ] 6.1 Create `features/admin/types/index.ts` with `Usuario`, `UsuarioDetalle` (con PII), `UsuarioFormData`, `UsuarioFilters`, `AccionesPorDia`, `ComunicacionPorDocente`, `InteraccionDocenteMateria`, `AuditLogItem`, `AuditFilters`, `AuditLogFilters`, `MetricasAuditoria` — sin `any`, `snake_case`
- [ ] 6.2 Create `features/admin/services/usuariosApi.ts` — `fetchUsuarios(filters)`, `fetchUsuario(id)`, `crearUsuario`, `actualizarUsuario`, `eliminarUsuario`
- [ ] 6.3 Create `features/admin/services/auditoriaApi.ts` — `fetchMetricas(filters)` (panel C-19), `fetchAuditLog(filters)` (query); centraliza los paths `/api/v1/auditoria/*`
- [ ] 6.4 Create query key factories: `usuariosKeys.ts`, `auditoriaKeys.ts`

## 7. Admin — Usuarios (ABM)

- [ ] 7.1 Create `hooks/useUsuarios.ts` — `useUsuarios(filters)`, `useUsuario(id)`
- [ ] 7.2 Create `hooks/useUsuarioMutations.ts` — `useCrearUsuario()`, `useActualizarUsuario()`, `useEliminarUsuario()`; invalidan listado
- [ ] 7.3 Create `components/UsuarioTable.tsx` — tabla paginada SIN PII (nombre, apellidos, legajo, regional, facturador, activo) (D-04)
- [ ] 7.4 Create `components/UsuarioFilters.tsx` — barra de filtros (regional, facturador, búsqueda)
- [ ] 7.5 Create `components/UsuarioFormDialog.tsx` (o form de página) — RHF+Zod con PII enmascarable; 422 campo extra → error inline
- [ ] 7.6 Create `components/UsuarioDetail.tsx` — detalle con PII descifrada (DNI/CUIL/CBU/alias), aislada (sin logs/estado global) (D-04)
- [ ] 7.7 Create `pages/UsuariosListPage.tsx` — `UsuarioFilters` + `UsuarioTable` paginada + "Nuevo usuario"
- [ ] 7.8 Create `pages/UsuarioFormPage.tsx` — alta/edición vía `/nuevo` y `/:id/editar`
- [ ] 7.9 Create `pages/UsuarioDetailPage.tsx` — `UsuarioDetail` + acciones editar/baja (confirmación)

## 8. Admin — Auditoría (panel + log)

- [ ] 8.1 Create `hooks/useAuditoria.ts` — `useMetricasAuditoria(filters)`, `useAuditLog(filters)` keyed por filtros
- [ ] 8.2 Create `components/AccionesPorDiaChart.tsx` — barras CSS Tailwind de serie temporal (ancho dinámico = inline permitido) (D-05)
- [ ] 8.3 Create `components/ComunicacionesPorDocente.tsx` — tabla distribución de estados por docente
- [ ] 8.4 Create `components/InteraccionesTable.tsx` — tabla docente×materia×acción; agrupa "sin materia"
- [ ] 8.5 Create `components/UltimasAccionesTable.tsx` — log de últimas N acciones (default 200), orden descendente
- [ ] 8.6 Create `components/AuditLogFilters.tsx` — barra de filtros (rango fechas, materia, usuario, código acción)
- [ ] 8.7 Create `components/AuditLogTable.tsx` — tabla paginada solo lectura; expone fecha_hora, actor, materia, accion, filas_afectadas, ip, user_agent
- [ ] 8.8 Create `pages/AuditoriaPanelPage.tsx` — 4 visualizaciones agregadas
- [ ] 8.9 Create `pages/AuditoriaLogPage.tsx` — `AuditLogFilters` + `AuditLogTable`

## 9. Admin — Tests

- [ ] 9.1 Test `UsuarioTable` — render con mock; verifica que NO se muestran columnas de PII (dni/cuil/cbu)
- [ ] 9.2 Test `UsuariosListPage` — filtros combinados invalidan/recargan la query
- [ ] 9.3 Test `UsuarioFormDialog` — submit válido llama mutación; 422 campo extra → error inline
- [ ] 9.4 Test `AuditoriaPanelPage` — render con mock de 4 agregaciones; verifica las 4 visualizaciones visibles
- [ ] 9.5 Test `AuditLogTable` — render con mock; verifica los 7 campos por registro
- [ ] 9.6 Test `AuditLogFilters` — aplicar rango + materia + código invalida/recarga el log

## 10. Estructura — Cohortes y Materias (extensión C-23)

- [ ] 10.1 SAFETY NET: correr tests existentes de `features/estructura/` y registrar baseline (no romper carreras/programas/fechas)
- [ ] 10.2 Extend `features/estructura/types/index.ts` — agregar `Cohorte`, `CohorteFormData`, `Materia`, `MateriaFormData`, `ClavePlus` (PROG|BD|ARQ|MAT|MET)
- [ ] 10.3 Extend `features/estructura/services/estructuraApi.ts` — `fetchCohortes`, `crearCohorte`, `actualizarCohorte`, `eliminarCohorte`, `fetchMaterias`, `crearMateria`, `actualizarMateria`
- [ ] 10.4 Extend `features/estructura/hooks/useEstructura.ts` — `useCohortes()`, `useMaterias()` + mutation hooks; invalidan su lista
- [ ] 10.5 Create `components/CohorteTable.tsx` + `components/CohorteFormDialog.tsx` (RHF+Zod: etiqueta, carrera_id, fechas)
- [ ] 10.6 Create `components/MateriaTable.tsx` (columna clave de Plus) + `components/MateriaFormDialog.tsx` (RHF+Zod: nombre, clave_plus OBLIGATORIA)
- [ ] 10.7 Create `pages/CohortesListPage.tsx` — `CohorteTable` + form (reemplaza stub `[]`)
- [ ] 10.8 Create `pages/MateriasListPage.tsx` — `MateriaTable` + form con clave de Plus obligatoria (reemplaza stub `[]`)

## 11. Estructura — Tests

- [ ] 11.1 Test `CohortesListPage` — render con mock; estado vacío "No hay cohortes registradas"
- [ ] 11.2 Test `MateriaFormDialog` — submit sin `clave_plus` → validación Zod bloquea y muestra error obligatorio
- [ ] 11.3 Test `MateriaTable` — render con mock; verifica columna de clave de Plus por materia

## 12. Shell — Sidebar y Rutas

- [ ] 12.1 SAFETY NET: correr test existente de `useMenuItems` y registrar baseline
- [ ] 12.2 Update `shared/hooks/useMenuItems.ts` — agregar items `Finanzas` (`liquidaciones:ver`), `Usuarios` (`usuarios:gestionar`), `Auditoría` (`auditoria:ver`) con `usePermission` en posición fija (sin hooks violation)
- [ ] 12.3 Update `App.tsx` — lazy imports + rutas protegidas: `/finanzas`, `/finanzas/historial`, `/finanzas/grilla`, `/finanzas/facturas`, `/admin/usuarios(/nuevo|/:id|/:id/editar)`, `/admin/auditoria(/log)`, `/estructura/cohortes`, `/estructura/materias` — cada una con su permiso vía `ProtectedRoute`
- [ ] 12.4 Update menú interno de estructura (`EstructuraHomePage` o sidebar) para enlazar cohortes y materias

## 13. Shell — Tests

- [ ] 13.1 Test `useMenuItems` — verifica que los nuevos items aparecen/desaparecen según permisos mock (Finanzas, Usuarios, Auditoría)
- [ ] 13.2 Verify `npm run test` — todos los tests pasan, 0 regresiones sobre el baseline de C-23
