## Context

La SPA (C-21) provee shell, auth, cliente HTTP centralizado (`@/shared/services/api`) y, desde C-23, TanStack Query en uso con el patrón query key factory por módulo, formularios RHF + Zod en modales, y el selector de comisión compartido `useComisionContext` (C-22, `shared/comision/`). El backend de C-18 (liquidaciones, grilla, facturas), C-19 (auditoría/métricas) y C-07/C-06 (usuarios, estructura) está completo. La feature `estructura` ya existe (carreras/programas/fechas), pero cohortes y materias quedaron como stubs `[]`. Este change agrega los dos perfiles administrativos/financieros que faltan para cerrar el roadmap frontend.

## Goals / Non-Goals

**Goals:**
- 2 features nuevas (`finanzas`, `admin`) + extensión de `estructura`, todas con TanStack Query y query key factory por módulo (patrón C-23).
- Vista de liquidación segmentada en tres bloques con KPIs de cabecera, reutilizando `useComisionContext` para cohorte + un selector de período.
- Cierre de liquidación con confirmación e invalidación de cache (refleja inmutabilidad del backend RN-22).
- ABM de grilla salarial con manejo del 409 de solapamiento como feedback de formulario, no como crash.
- Gestión de facturas con selector de docentes facturantes (`facturador=true`) y transición unidireccional Pendiente → Abonada.
- ABM de usuarios con PII descifrada solo en el detalle (nunca en logs ni en listados), paginación por cursor/total.
- Panel de auditoría con 4 visualizaciones agregadas + log filtrable, respetando el scope por rol que el backend ya aplica.
- ABM real de cohortes y materias (cierra los stubs de C-23) + mapeo materia → clave de Plus.
- Tests unitarios de hooks y componentes críticos por módulo.

**Non-Goals:**
- Modificaciones al backend o a la base de datos.
- El **cálculo** de liquidaciones (`POST /api/v1/liquidaciones/calcular`) — el frontend lo dispara como acción pero la lógica vive en el backend; ADMIN no puede calcular (403). Se modela como botón de acción que invalida la vista.
- Gráficos avanzados (librería de charts): el panel de auditoría usa tablas y barras CSS simples con Tailwind, sin nueva dependencia.
- SSR, i18n, tema oscuro.
- Resolución de PA-22/PA-23 (claves de Plus / acumulación): el frontend consume el contrato de grilla tal como lo expone el backend C-18; el mapeo materia→clave es un ABM simple sobre la config del tenant.

## Decisions

### D-01 — `useComisionContext` para el scope cohorte, selector de período propio del feature finanzas

La vista de liquidaciones se acota por `cohorte_id` + `periodo` (AAAA-MM). El `cohorte_id` se obtiene del `useComisionContext` compartido (ya persiste en la URL `?materia=&cohorte=`). El `periodo` es específico de finanzas, así que se modela como estado local del feature con un `<PeriodoSelector>` (input `month`) que también se refleja en query param `?periodo=`. No se importa nada de otra feature de dominio; el contexto se consume vía el hook compartido.

*Alternativa descartada*: un selector cohorte propio de finanzas — duplicaría el catálogo de cohortes ya resuelto por `useComisionContext`.

### D-02 — Query key factory por módulo (patrón C-23)

Cada feature define su factory:

```
liquidacionesKeys.all = ['liquidaciones'] as const
liquidacionesKeys.vista = (cohorteId: string, periodo: string, usuarioId?: string) =>
  [...liquidacionesKeys.all, 'vista', cohorteId, periodo, usuarioId ?? null] as const
liquidacionesKeys.historial = (filters: HistorialFilters) =>
  [...liquidacionesKeys.all, 'historial', filters] as const

grillaKeys.base = (rol?: string) => ['grilla', 'base', rol ?? null] as const
grillaKeys.plus = (grupo?: string) => ['grilla', 'plus', grupo ?? null] as const

facturasKeys.list = (filters: FacturaFilters) => ['facturas', 'list', filters] as const
facturasKeys.detail = (id: string) => ['facturas', 'detail', id] as const

usuariosKeys.list = (filters: UsuarioFilters) => ['admin-usuarios', 'list', filters] as const
usuariosKeys.detail = (id: string) => ['admin-usuarios', 'detail', id] as const

auditoriaKeys.metricas = (filters: AuditFilters) => ['auditoria', 'metricas', filters] as const
auditoriaKeys.log = (filters: AuditLogFilters) => ['auditoria', 'log', filters] as const
```

Cada mutación invalida la(s) lista(s) afectada(s) con `queryClient.invalidateQueries()`. El cierre de liquidación invalida `liquidacionesKeys.vista(...)` Y `liquidacionesKeys.historial(...)`.

### D-03 — El 409 de solapamiento/conflicto se traduce a error de formulario, no a toast genérico

Grilla salarial (solapamiento de vigencia), facturas (editar/abonar ya abonada) y cierre (liquidación ya cerrada) devuelven 409. El interceptor de `api` ya normaliza errores; en estos formularios se captura el 409 en `onError` de la mutación y se muestra como mensaje a nivel de formulario (`setError` de RHF cuando aplica al campo de vigencia, o banner de error inline cuando es de estado). Esto evita que el usuario pierda lo cargado.

*Alternativa descartada*: dejar que el 409 caiga al error boundary global — rompería el formulario y perdería el input.

### D-04 — PII descifrada solo en el detalle admin, nunca en el listado ni en logs

El listado de usuarios (`UsuarioTable`) muestra solo `{nombre, apellidos, legajo, regional, facturador, is_active}` — sin PII. El detalle (`UsuarioDetailPage`) consume `GET /api/v1/admin/usuarios/{id}` que devuelve `dni`, `cuil`, `cbu`, `alias_cbu` en claro. Estos campos NUNCA se pasan a `console.log` ni a estado global; viven solo en el componente de detalle. El formulario de edición los carga en campos enmascarables.

### D-05 — Panel de auditoría: tablas + barras CSS Tailwind, sin librería de charts

Las 4 agregaciones (acciones por día, comunicaciones por docente, interacciones docente×materia, últimas acciones) se renderizan con tablas y barras horizontales construidas con `div` + `width` dinámico Tailwind (el ancho es valor dinámico → inline style permitido por la regla dura). No se agrega `recharts`/`chart.js`. El log completo es una tabla paginada con barra de filtros (rango de fechas, materia, usuario, código de acción) keyed por los filtros.

*Alternativa descartada*: agregar `recharts` — viola "sin nuevas dependencias" para un MVP de métricas; las barras CSS son suficientes.

### D-06 — Cohortes y materias extienden la feature `estructura` existente, no una feature nueva

C-23 ya creó `features/estructura/` con carreras/programas/fechas y dejó cohortes/materias como stubs. C-24 agrega `types`, `services` (`cohortesApi`, `materiasApi` o extensión de `estructuraApi`), `hooks` y `pages` (`CohortesListPage`, `MateriasListPage`) en esa misma feature, y el mapeo materia→clave de Plus como sub-form de la página de materias. El item `Estructura` del sidebar gana sub-rutas. Esto respeta el principio de no duplicar features de dominio.

### D-07 — Acción "calcular liquidación" como botón con guard de permiso

El cálculo (`POST /api/v1/liquidaciones/calcular`) requiere permiso de FINANZAS; ADMIN recibe 403. El botón "Calcular período" en `LiquidacionesPage` se renderiza solo si el usuario tiene el permiso (vía `usePermission('liquidaciones:calcular')` o el permiso que exponga el backend); al ejecutar, invalida `liquidacionesKeys.vista(...)`. ADMIN ve la vista en modo solo-lectura (sin botones de calcular/cerrar/exportar).

### D-08 — API service modules por feature (patrón C-21/C-23)

Cada feature define su `services/<feature>Api.ts` que importa la instancia `api` de `@/shared/services/api`. Funciones tipadas sin `any`, DTOs en `snake_case` para coincidir con Pydantic.

## Route Structure

```
/finanzas                              — LiquidacionesPage         (liquidaciones:ver)
/finanzas/historial                    — HistorialLiquidacionesPage(liquidaciones:ver)
/finanzas/grilla                       — GrillaSalarialPage        (liquidaciones:configurar-salarios)
/finanzas/facturas                     — FacturasListPage          (facturas:gestionar)
/admin/usuarios                        — UsuariosListPage          (usuarios:gestionar)
/admin/usuarios/nuevo                  — UsuarioFormPage           (usuarios:gestionar)
/admin/usuarios/:id                    — UsuarioDetailPage         (usuarios:gestionar)
/admin/usuarios/:id/editar             — UsuarioFormPage           (usuarios:gestionar)
/admin/auditoria                       — AuditoriaPanelPage        (auditoria:ver)
/admin/auditoria/log                   — AuditoriaLogPage          (auditoria:ver)
/estructura/cohortes                   — CohortesListPage          (estructura:gestionar)
/estructura/materias                   — MateriasListPage          (estructura:gestionar)
```

## Component Tree per Module

### Finanzas
```
features/finanzas/
├── types/index.ts                    — LiquidacionVista, SegmentoLiquidacion, LiquidacionItem, KpisLiquidacion,
│                                        HistorialFilters, SalarioBase, SalarioPlus, SalarioBaseFormData,
│                                        SalarioPlusFormData, Factura, FacturaFormData, FacturaFilters, EstadoFactura
├── services/
│   ├── liquidacionesApi.ts           — fetchLiquidaciones, cerrarLiquidacion, fetchHistorial, calcularPeriodo
│   ├── grillaApi.ts                  — fetchSalariosBase, crearSalarioBase, actualizarSalarioBase, eliminarSalarioBase,
│   │                                    fetchSalariosPlus, crearSalarioPlus, actualizarSalarioPlus, eliminarSalarioPlus
│   └── facturasApi.ts                — fetchFacturas, fetchFactura, crearFactura, actualizarFactura, abonarFactura
├── hooks/
│   ├── liquidacionesKeys.ts          — query key factory
│   ├── useLiquidaciones.ts           — useLiquidaciones(cohorteId, periodo, usuarioId?), useHistorial(filters)
│   ├── useLiquidacionMutations.ts    — useCerrarLiquidacion(), useCalcularPeriodo()
│   ├── grillaKeys.ts                 — query key factory
│   ├── useGrilla.ts                  — useSalariosBase(rol?), useSalariosPlus(grupo?)
│   ├── useGrillaMutations.ts         — crear/actualizar/eliminar base y plus
│   ├── facturasKeys.ts               — query key factory
│   ├── useFacturas.ts                — useFacturas(filters), useFactura(id)
│   └── useFacturaMutations.ts        — useCrearFactura(), useActualizarFactura(), useAbonarFactura()
├── components/
│   ├── PeriodoSelector.tsx           — input month sincronizado con query param ?periodo=
│   ├── KpisCabecera.tsx              — 2 stat cards: total_sin_factura, total_con_factura
│   ├── SegmentoTable.tsx             — tabla reutilizable de un segmento (docente, rol, monto)
│   ├── LiquidacionSegmentada.tsx     — orquesta KpisCabecera + 3 SegmentoTable (general/nexo/facturantes)
│   ├── CerrarLiquidacionDialog.tsx   — modal de confirmación de cierre
│   ├── HistorialTable.tsx            — tabla de cerradas con filtros (cohorte, período, docente)
│   ├── SalarioBaseTable.tsx          — tabla ABM de SalarioBase
│   ├── SalarioBaseFormDialog.tsx     — modal RHF+Zod: rol, monto, desde, hasta; maneja 409 solapamiento
│   ├── SalarioPlusTable.tsx          — tabla ABM de SalarioPlus
│   ├── SalarioPlusFormDialog.tsx     — modal RHF+Zod: grupo, rol, descripcion, monto, desde, hasta
│   ├── FacturaTable.tsx              — tabla con filtros (período, estado) y badges
│   ├── FacturaFormDialog.tsx         — modal RHF+Zod: usuario_id (solo facturadores), periodo, detalle, referencia_archivo, tamano_kb
│   └── AbonarFacturaButton.tsx       — botón con confirmación de transición Pendiente→Abonada
├── pages/
│   ├── LiquidacionesPage.tsx         — PeriodoSelector + LiquidacionSegmentada + acciones (calcular/cerrar/exportar según permiso)
│   ├── HistorialLiquidacionesPage.tsx— HistorialTable con filtros
│   ├── GrillaSalarialPage.tsx        — tabs Base / Plus, cada uno con su tabla + form
│   └── FacturasListPage.tsx          — FacturaTable + "Nueva factura" + abonar inline
```

### Admin
```
features/admin/
├── types/index.ts                    — Usuario, UsuarioDetalle (con PII), UsuarioFormData, UsuarioFilters,
│                                        AccionesPorDia, ComunicacionPorDocente, InteraccionDocenteMateria,
│                                        AuditLogItem, AuditFilters, AuditLogFilters, MetricasAuditoria
├── services/
│   ├── usuariosApi.ts                — fetchUsuarios, fetchUsuario, crearUsuario, actualizarUsuario, eliminarUsuario
│   └── auditoriaApi.ts               — fetchMetricas (panel), fetchAuditLog (query)
├── hooks/
│   ├── usuariosKeys.ts               — query key factory
│   ├── useUsuarios.ts                — useUsuarios(filters), useUsuario(id)
│   ├── useUsuarioMutations.ts        — useCrearUsuario(), useActualizarUsuario(), useEliminarUsuario()
│   ├── auditoriaKeys.ts              — query key factory
│   ├── useAuditoria.ts               — useMetricasAuditoria(filters), useAuditLog(filters)
├── components/
│   ├── UsuarioTable.tsx              — tabla paginada SIN PII: nombre, apellidos, legajo, regional, facturador, activo
│   ├── UsuarioFilters.tsx            — barra de filtros (regional, facturador, búsqueda)
│   ├── UsuarioFormDialog.tsx         — (o página) RHF+Zod con campos PII enmascarables
│   ├── UsuarioDetail.tsx             — detalle con PII descifrada (DNI/CUIL/CBU/alias)
│   ├── AccionesPorDiaChart.tsx       — barras CSS de serie temporal
│   ├── ComunicacionesPorDocente.tsx  — tabla distribución de estados por docente
│   ├── InteraccionesTable.tsx        — tabla docente×materia×acción
│   ├── UltimasAccionesTable.tsx      — log de últimas N acciones (default 200)
│   ├── AuditLogFilters.tsx           — barra de filtros (rango fechas, materia, usuario, código acción)
│   └── AuditLogTable.tsx             — tabla paginada del log completo
├── pages/
│   ├── UsuariosListPage.tsx          — UsuarioFilters + UsuarioTable paginada + "Nuevo usuario"
│   ├── UsuarioFormPage.tsx           — alta/edición vía /nuevo y /:id/editar
│   ├── UsuarioDetailPage.tsx         — UsuarioDetail con PII + acciones editar/baja
│   ├── AuditoriaPanelPage.tsx        — 4 visualizaciones agregadas (panel C-19)
│   └── AuditoriaLogPage.tsx          — AuditLogFilters + AuditLogTable
```

### Estructura (extensión)
```
features/estructura/  (+ nuevos archivos)
├── types/index.ts                    — (+) Cohorte, CohorteFormData, Materia, MateriaFormData, ClavePlus
├── services/estructuraApi.ts         — (+) fetchCohortes, crearCohorte, actualizarCohorte, eliminarCohorte,
│                                        fetchMaterias, crearMateria, actualizarMateria, asignarClavePlus
├── hooks/useEstructura.ts            — (+) useCohortes(), useMaterias(), + mutation hooks
├── components/
│   ├── CohorteTable.tsx              — (+) tabla ABM de cohortes
│   ├── CohorteFormDialog.tsx         — (+) modal RHF+Zod: etiqueta, carrera_id, fechas
│   ├── MateriaTable.tsx              — (+) tabla ABM de materias con columna clave de Plus
│   └── MateriaFormDialog.tsx         — (+) modal RHF+Zod: nombre, clave_plus (PROG|BD|ARQ|MAT|MET, obligatoria)
├── pages/
│   ├── CohortesListPage.tsx          — (+) CohorteTable + form
│   └── MateriasListPage.tsx          — (+) MateriaTable + form (con clave de Plus obligatoria)
```

## Data Flow

```
Browser → Router (React Router v6)
  → ProtectedRoute (verifica sesión + permiso declarado)
    → AppLayout (QueryClientProvider — ya existe desde C-23)
      → Page Component (React.lazy)
        → useComisionContext() para cohorte (finanzas) + estado local periodo
        → useQuery hook (llama service module, keyed por scope/filtros)
          → service module → api (Axios con interceptor token+refresh) → Backend

Mutaciones:
  → useMutation hook
    → onSuccess: invalidateQueries de la(s) lista(s) afectada(s)
    → onError: 409 → mensaje de formulario (D-03); otro → toast/banner
```

## Backend Endpoints Reference

| Feature | Método | Endpoint | Permiso |
|---------|--------|----------|---------|
| Liquidaciones | GET | `/api/v1/liquidaciones?cohorte_id=&periodo=&usuario_id=` | liquidaciones:ver |
| Liquidaciones | POST | `/api/v1/liquidaciones/calcular` | liquidaciones:calcular (FINANZAS) |
| Liquidaciones | POST | `/api/v1/liquidaciones/{id}/cerrar` | liquidaciones:cerrar |
| Liquidaciones | GET | `/api/v1/liquidaciones/historial?cohorte_id=&periodo=&usuario_id=` | liquidaciones:ver |
| Grilla | GET | `/api/v1/grilla/salarios-base?rol=` | liquidaciones:configurar-salarios |
| Grilla | POST | `/api/v1/grilla/salarios-base` | liquidaciones:configurar-salarios |
| Grilla | PUT | `/api/v1/grilla/salarios-base/{id}` | liquidaciones:configurar-salarios |
| Grilla | DELETE | `/api/v1/grilla/salarios-base/{id}` | liquidaciones:configurar-salarios |
| Grilla | GET | `/api/v1/grilla/salarios-plus?grupo=&vigente=` | liquidaciones:configurar-salarios |
| Grilla | POST | `/api/v1/grilla/salarios-plus` | liquidaciones:configurar-salarios |
| Grilla | PUT | `/api/v1/grilla/salarios-plus/{id}` | liquidaciones:configurar-salarios |
| Grilla | DELETE | `/api/v1/grilla/salarios-plus/{id}` | liquidaciones:configurar-salarios |
| Facturas | GET | `/api/v1/facturas?periodo=&estado=` | facturas:gestionar |
| Facturas | GET | `/api/v1/facturas/{id}` | facturas:gestionar |
| Facturas | POST | `/api/v1/facturas` | facturas:gestionar |
| Facturas | PUT | `/api/v1/facturas/{id}` | facturas:gestionar |
| Facturas | POST | `/api/v1/facturas/{id}/abonar` | facturas:gestionar |
| Usuarios | GET | `/api/v1/admin/usuarios?regional=&facturador=` | usuarios:gestionar |
| Usuarios | GET | `/api/v1/admin/usuarios/{id}` | usuarios:gestionar |
| Usuarios | POST | `/api/v1/admin/usuarios` | usuarios:gestionar |
| Usuarios | PUT | `/api/v1/admin/usuarios/{id}` | usuarios:gestionar |
| Usuarios | DELETE | `/api/v1/admin/usuarios/{id}` | usuarios:gestionar |
| Auditoría | GET | `/api/v1/auditoria/metricas/*` (panel C-19) | auditoria:ver |
| Auditoría | GET | `/api/v1/auditoria/log?desde=&hasta=&materia_id=&actor_id=&accion=` | auditoria:ver |
| Estructura | GET/POST/PUT/DELETE | `/api/v1/cohortes`, `/api/v1/materias` | estructura:gestionar |

> Los paths exactos de las agregaciones del panel (`/api/v1/auditoria/...`) se confirman contra C-19 al implementar; los DTOs están tipados según `audit-panel`/`audit-query`.

## Risks / Trade-offs

- **[Paths exactos del panel de auditoría C-19]** → El spec describe las agregaciones por contrato; los paths concretos se verifican contra los routers de C-19 en la fase de apply. Mitigación: `auditoriaApi.ts` centraliza los paths, fácil de ajustar.
- **[PII descifrada en el detalle admin]** → Riesgo de exposición accidental. Mitigación D-04: PII solo en `UsuarioDetail`, nunca en estado global, listados ni logs; campos enmascarables.
- **[Acción calcular puede ser pesada en backend]** → El botón muestra estado de carga y deshabilita reintentos hasta resolver; invalida la vista al terminar.
- **[Solapamiento de vigencia en grilla]** → 409 traducido a error de formulario (D-03) en el campo de vigencia, no crash.
- **[Doble fuente de cohorte: useComisionContext vs filtros de historial]** → El historial usa sus propios filtros independientes; la vista del período usa `useComisionContext`. Documentado para evitar confusión.

## Open Questions

- ¿La exportación de liquidaciones (si existe en C-18) es descarga directa Blob o link temporario? → Asumir descarga directa Blob, consistente con C-23 (equipos/guardias export). Confirmar endpoint al implementar.
- ¿El mapeo materia→clave de Plus es endpoint propio o atributo de la materia? → Asumir atributo `clave_plus` obligatorio en el ABM de materia (consistente con `grilla-salarial-abm`: "no SHALL existir materias sin clave"). Confirmar contra C-06/C-18 al implementar.
