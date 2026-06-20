## ADDED Requirements

### Requirement: TanStack Query integration for server state

El sistema SHALL integrar TanStack Query (`@tanstack/react-query`) como capa de server state para todas las features de dominio. Se configura un `QueryClient` con defaults conservadores y un `QueryClientProvider` envuelve las rutas protegidas.

#### Scenario: QueryClient configurado correctamente
- **WHEN** la aplicación monta las rutas protegidas
- **THEN** el `QueryClientProvider` está disponible con staleTime de 30s y retry: 1

#### Scenario: Error de query no propaga al root
- **WHEN** una query falla (ej. 500 del backend)
- **THEN** el error se maneja localmente en el componente, no se propaga como error no controlado

### Requirement: Query key factory pattern por módulo

Cada feature module SHALL definir un objeto factory de query keys con la estructura `moduleKeys.{all,lists,list(filters),details,detail(id)}`.

#### Scenario: Equipos query keys
- **GIVEN** el módulo equipos
- **WHEN** se llama `equiposKeys.list({materia_id: 'x'})`
- **THEN** retorna `['equipos', 'list', {materia_id: 'x'}]`

#### Scenario: Invalidation al mutar
- **WHEN** una mutación de equipos es exitosa
- **THEN** el `onSuccess` invalida `equiposKeys.lists()` para refrescar listados

### Requirement: Custom hooks por feature module

Cada feature module SHALL exportar custom hooks que encapsulan `useQuery` y `useMutation` con tipos correctos y manejo de errores básico.

#### Scenario: Hook useEquipos
- **GIVEN** el hook `useEquipos(filters)`
- **WHEN** se invoca
- **THEN** retorna `{ data, isLoading, isError, error, refetch }` tipado a `Equipo[]`

#### Scenario: Hook useCrearEquipo
- **GIVEN** el hook `useCrearEquipo()`
- **WHEN** se invoca `mutate(data)`
- **THEN** ejecuta mutación, invalida listas de equipos en `onSuccess`
