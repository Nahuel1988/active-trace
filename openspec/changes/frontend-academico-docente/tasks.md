# Tasks — frontend-academico-docente (C-22)

> Todas las tareas siguen Strict TDD: RED (test que falla) → GREEN (mínimo) → TRIANGULATE (2do caso) → REFACTOR.
> Mocks: se mockea la instancia `api` de `@/shared/services/api`; nunca se replica lógica de negocio del backend.
> Convención: feature-based, sin imports cross-feature, sin `any`, componentes <200 LOC, fetch solo vía hooks de TanStack Query.

## 1. Contexto de comisión compartido (shared)

- [ ] 1.1 Test: `comisionApi` (catálogo) llama a `GET /api/materias` y `GET /api/cohortes?materia_id=` con la instancia `api` mockeada (verifica URL y params, sin instancia Axios secundaria)
- [ ] 1.2 Implementar `features/comisiones/types/index.ts` (DTOs `MateriaDTO`, `CohorteDTO`) y `features/comisiones/services/comisionApi.ts`
- [ ] 1.3 Test: hook `useMaterias` / `useCohortes` (TanStack Query) — happy path + error 403 (`ForbiddenError`)
- [ ] 1.4 Implementar `features/comisiones/hooks/useMaterias.ts` y `useCohortes.ts`
- [ ] 1.5 Test: `useComisionContext` lee/escribe `?materia=&cohorte=` en la URL y persiste al recargar; estado vacío cuando no hay selección
- [ ] 1.6 Implementar `shared/comision/ComisionContext.tsx` + `shared/comision/useComisionContext.ts` (provider montado en el layout docente, estado en query params)
- [ ] 1.7 Test: `ComisionSelector` renderiza materias, al elegir materia carga cohortes y actualiza el contexto; triangular con materia sin cohortes
- [ ] 1.8 Implementar `features/comisiones/components/ComisionSelector.tsx`

## 2. Feature padron — importación de padrón

- [ ] 2.1 Test: `padronApi.preview` hace `POST .../padron/preview` multipart y `padronApi.commit` hace `POST .../padron/commit`; verifica que preview no persiste y errores se propagan
- [ ] 2.2 Implementar `features/padron/types/index.ts` (DTOs preview/commit) y `features/padron/services/padronApi.ts`
- [ ] 2.3 Test: `usePadronPreview` / `usePadronCommit` (useMutation) — éxito y error de formato; commit invalida query del padrón
- [ ] 2.4 Implementar `features/padron/hooks/usePadronPreview.ts` y `usePadronCommit.ts`
- [ ] 2.5 Test: `PadronPreviewTable` muestra alumnos detectados y bloquea confirmación si hay `errores`; triangular con 0 errores → confirmación habilitada
- [ ] 2.6 Implementar `features/padron/components/PadronPreviewTable.tsx`
- [ ] 2.7 Test: `ConfirmDestructiveDialog` — commit NO se dispara sin confirmar; al confirmar sí; advierte reemplazo destructivo (RN-05)
- [ ] 2.8 Implementar `features/padron/components/ConfirmDestructiveDialog.tsx`
- [ ] 2.9 Test: `ImportPadronPage` integra upload→preview→confirmación→commit y muestra resultado (importados/reemplazados); requiere comisión seleccionada
- [ ] 2.10 Implementar `features/padron/pages/ImportPadronPage.tsx`

## 3. Feature calificaciones — importación + umbral

- [ ] 3.1 Test: `calificacionesApi.preview/commit` (preview lista actividades con escala; commit envía solo `actividades_seleccionadas`) con `api` mockeada
- [ ] 3.2 Implementar `features/calificaciones/types/index.ts` y `features/calificaciones/services/calificacionesApi.ts`
- [ ] 3.3 Test: `calificacionesApi.getUmbral/putUmbral` — default 60 cuando no configurado; PUT envía el valor
- [ ] 3.4 Implementar funciones de umbral en `calificacionesApi.ts`
- [ ] 3.5 Test: hooks `useCalificacionesPreview`, `useCalificacionesCommit`, `useUmbral` — commit y PUT umbral invalidan queries de atrasados/ranking
- [ ] 3.6 Implementar `features/calificaciones/hooks/*`
- [ ] 3.7 Test: `ActividadesSelector` — seleccionar subconjunto; solo ids elegidos van al commit; sin lógica de detección en cliente (datos ya parseados)
- [ ] 3.8 Implementar `features/calificaciones/components/ActividadesSelector.tsx`
- [ ] 3.9 Test: `UmbralForm` (RHF + Zod) — default 60; valida entero 0–100; valor inválido no dispara PUT; triangular con valor válido
- [ ] 3.10 Implementar `features/calificaciones/components/UmbralForm.tsx`
- [ ] 3.11 Test: `ImportCalificacionesPage` integra upload→preview→selección→commit + sección de umbral
- [ ] 3.12 Implementar `features/calificaciones/pages/ImportCalificacionesPage.tsx`

## 4. Feature atrasados — dashboard, ranking, reportes, entregas

- [ ] 4.1 Test: `atrasadosApi` (atrasados, ranking, resumen, notas-finales, entregas-sin-corregir, export) llaman a sus endpoints acotados por `materia_id`/`cohorte_id`
- [ ] 4.2 Implementar `features/atrasados/types/index.ts` y `features/atrasados/services/atrasadosApi.ts`
- [ ] 4.3 Test: hooks keyed por `(materia_id, cohorte_id)` — cambiar de comisión recarga; 403 → `ForbiddenError`
- [ ] 4.4 Implementar `features/atrasados/hooks/*`
- [ ] 4.5 Test: `AtrasadosTable` muestra motivos (faltantes / nota bajo umbral); estado vacío sin datos; triangular con 2 motivos en una fila
- [ ] 4.6 Implementar `features/atrasados/components/AtrasadosTable.tsx`
- [ ] 4.7 Test: `RankingTable` excluye alumnos con 0 aprobadas y ordena por aprobadas (RN-09)
- [ ] 4.8 Implementar `features/atrasados/components/RankingTable.tsx`
- [ ] 4.9 Test: `ReportesResumen` y `NotasFinalesTable` — render con datos y estado vacío
- [ ] 4.10 Implementar `features/atrasados/components/ReportesResumen.tsx` y `NotasFinalesTable.tsx`
- [ ] 4.11 Test: `EntregasSinCorregir` — render de entregas (solo escala textual) + export dispara descarga de blob (`GET .../export`)
- [ ] 4.12 Implementar `features/atrasados/components/EntregasSinCorregir.tsx`
- [ ] 4.13 Test: selección de alumnos habilita acción "comunicar a seleccionados" solo con `comunicacion:enviar`; navega con la selección codificada (sin import cross-feature)
- [ ] 4.14 Implementar selección en `AtrasadosTable` + `features/atrasados/pages/AtrasadosDashboardPage.tsx`

## 5. Feature comunicaciones — cola, preview, aprobación, tracking

- [ ] 5.1 Test: `comunicacionesApi` (preview, enviar, listar cola, aprobar/cancelar lote y por destinatario) contra `api` mockeada
- [ ] 5.2 Implementar `features/comunicaciones/types/index.ts` (estados `pendiente|enviando|ok|fallido|cancelado`) y `services/comunicacionesApi.ts`
- [ ] 5.3 Test: `useComunicacionPreview` / `useEnviarComunicacion` (mutations) — enviar encola en `pendiente` y expone `requiere_aprobacion`
- [ ] 5.4 Implementar hooks de preview/envío
- [ ] 5.5 Test: `useColaComunicaciones` — `refetchInterval` activo con mensajes no terminales; se detiene cuando todos son terminales (mock con respuestas sucesivas pendiente→ok)
- [ ] 5.6 Implementar `features/comunicaciones/hooks/useColaComunicaciones.ts`
- [ ] 5.7 Test: `ComunicacionPreview` muestra asunto+cuerpo por destinatario; confirmar dispara envío
- [ ] 5.8 Implementar `features/comunicaciones/components/ComunicacionPreview.tsx`
- [ ] 5.9 Test: `ColaTable` — refleja transición de estado por polling; controles de aprobar/cancelar ocultos sin `comunicacion:aprobar`; aprobar lote y cancelar por destinatario invalidan la cola
- [ ] 5.10 Implementar `features/comunicaciones/components/ColaTable.tsx`
- [ ] 5.11 Test: `ComunicacionesQueuePage` integra preview→envío→cola con tracking; recibe la selección de atrasados desde navegación
- [ ] 5.12 Implementar `features/comunicaciones/pages/ComunicacionesQueuePage.tsx`

## 6. Integración con el shell (Sidebar + rutas)

- [ ] 6.1 Test: `Sidebar` muestra ítems "Importar padrón/calificaciones", "Atrasados", "Comunicaciones" solo con el permiso requerido (`calificaciones:importar`, `atrasados:ver`, `comunicacion:enviar`)
- [ ] 6.2 Agregar los ítems de dominio a `shared/components/Sidebar.tsx` (con su `permission`)
- [ ] 6.3 Test: rutas lazy nuevas en `App.tsx` envueltas en `<ProtectedRoute permission=...>` redirigen a `/403` sin permiso y montan la página con permiso
- [ ] 6.4 Agregar rutas lazy de las páginas docentes a `App.tsx` bajo el layout protegido + montar el `ComisionContext` provider en el layout docente

## 7. Cierre de calidad

- [ ] 7.1 Ejecutar la suite Vitest completa de las features nuevas y confirmar verde
- [ ] 7.2 Verificar cobertura ≥80% líneas en las features nuevas (`npm run test -- --coverage`)
- [ ] 7.3 `tsc --noEmit` sin errores y sin `any` en el código nuevo; confirmar ausencia de imports cross-feature de dominio
