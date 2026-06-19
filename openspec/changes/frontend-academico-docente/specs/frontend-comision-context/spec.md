## ADDED Requirements

### Requirement: Contrato de API de catálogo de comisiones
El sistema SHALL definir los contratos de API esperados (endpoints + DTOs tipados en TypeScript) que el frontend consume para poblar el selector de comisión, sin acoplar a la implementación interna del backend. Los DTOs SHALL usar `snake_case` en los campos que cruzan la red para coincidir con los schemas Pydantic del backend.

El contrato esperado SHALL incluir:
- `GET /api/materias` → `200` con `{ materias: Array<{ materia_id: string; nombre: string }> }`, filtrado por tenant y por las asignaciones vigentes del usuario (el backend resuelve el scope desde el JWT).
- `GET /api/cohortes?materia_id=<id>` → `200` con `{ cohortes: Array<{ cohorte_id: string; etiqueta: string }> }`.

#### Scenario: Servicio de materias usa la instancia Axios centralizada
- **WHEN** el hook de catálogo solicita las materias del usuario
- **THEN** la request se realiza con la instancia `api` de `@/shared/services/api` (no con una instancia Axios secundaria) hacia `GET /api/materias`

#### Scenario: Cohortes se piden acotadas por materia
- **WHEN** el usuario selecciona una materia en el selector
- **THEN** se realiza `GET /api/cohortes?materia_id=<id>` y solo se muestran las cohortes de esa materia

#### Scenario: Tipos de los DTOs sin `any`
- **WHEN** se inspeccionan los tipos del servicio de catálogo
- **THEN** los DTOs de request y response están tipados explícitamente y ningún campo usa el tipo `any`

### Requirement: Selector de comisión como contexto compartido
El sistema SHALL proveer un selector de comisión (materia + cohorte) y un hook `useComisionContext` accesible desde `shared/` por todas las features docentes. El contexto seleccionado SHALL persistirse en query params de la URL (`?materia=&cohorte=`) para ser linkeable y sobrevivir a un refresh de página. Ninguna feature de dominio SHALL importar el selector de otra feature de dominio: el acceso al contexto es siempre vía el hook compartido.

#### Scenario: Contexto persistido en la URL
- **WHEN** el usuario selecciona materia y cohorte
- **THEN** la URL refleja `?materia=<id>&cohorte=<id>` y al recargar la página la selección se restaura desde la URL

#### Scenario: Features consumen el contexto desde shared
- **WHEN** una feature docente (padron, calificaciones, atrasados, comunicaciones) necesita la comisión activa
- **THEN** la obtiene mediante `useComisionContext()` sin importar nada de otra feature de dominio

#### Scenario: Sin contexto seleccionado las páginas muestran estado vacío
- **WHEN** no hay materia/cohorte seleccionada
- **THEN** la página de dominio muestra un estado informativo pidiendo seleccionar una comisión, en lugar de disparar requests sin scope
