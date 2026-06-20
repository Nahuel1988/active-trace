## ADDED Requirements

### Requirement: ABM de SalarioBase con vigencia temporal

El sistema SHALL renderizar un ABM de `SalarioBase` (permiso `liquidaciones:configurar-salarios`) consumiendo `GET/POST/PUT/DELETE /api/v1/grilla/salarios-base`. El formulario SHALL capturar `rol` (PROFESOR|TUTOR|NEXO|COORDINADOR), `monto` (decimal), `desde` (fecha) y `hasta` (fecha nullable), validado con React Hook Form + Zod. La tabla SHALL listar los registros con filtro opcional por `rol`. Los DTOs SHALL estar tipados sin `any`, en `snake_case`.

#### Scenario: Crear SalarioBase exitosamente
- **WHEN** un usuario FINANZAS completa el formulario con `rol`, `monto` y `desde` válidos y envía
- **THEN** la mutación llama `POST /api/v1/grilla/salarios-base`, y al responder 201 invalida la lista y cierra el modal

#### Scenario: Filtrar SalarioBase por rol
- **WHEN** el usuario selecciona el filtro `rol=PROFESOR`
- **THEN** la query se invalida y recarga, mostrando solo los SalarioBase de ese rol

#### Scenario: Editar el campo hasta
- **WHEN** el usuario edita `hasta` de un registro y guarda
- **THEN** la mutación llama `PUT /api/v1/grilla/salarios-base/{id}` y refresca la tabla al responder 200

#### Scenario: Eliminar SalarioBase (soft delete)
- **WHEN** el usuario elimina un registro y confirma
- **THEN** la mutación llama `DELETE /api/v1/grilla/salarios-base/{id}` y la fila desaparece de la tabla al responder 204

### Requirement: El solapamiento de vigencia (409) se muestra como error de formulario

El sistema SHALL capturar el `409 Conflict` de solapamiento de vigencia devuelto por el backend al crear o actualizar un SalarioBase o SalarioPlus, y SHALL mostrarlo como mensaje de error a nivel del formulario (asociado al campo de vigencia cuando aplique), preservando los datos cargados. NO SHALL propagarse al error boundary global ni perder el input del usuario.

#### Scenario: Solapamiento de vigencia muestra error inline
- **WHEN** el backend responde 409 por solapamiento al crear un SalarioBase
- **THEN** el formulario muestra un mensaje de error indicando el solapamiento de vigencia y mantiene los valores cargados

#### Scenario: El formulario no se cierra ante 409
- **WHEN** ocurre un 409 de solapamiento
- **THEN** el modal permanece abierto con los datos del usuario intactos para corrección

### Requirement: ABM de SalarioPlus con grupo y rol

El sistema SHALL renderizar un ABM de `SalarioPlus` (permiso `liquidaciones:configurar-salarios`) consumiendo `GET/POST/PUT/DELETE /api/v1/grilla/salarios-plus`. El formulario SHALL capturar `grupo` (PROG|BD|ARQ|MAT|MET), `rol`, `descripcion`, `monto`, `desde` y `hasta` (nullable). La tabla SHALL ofrecer filtro por `grupo`.

#### Scenario: Crear SalarioPlus exitosamente
- **WHEN** un usuario FINANZAS completa `grupo=PROG`, `rol=PROFESOR`, `monto`, `descripcion` y `desde` y envía
- **THEN** la mutación llama `POST /api/v1/grilla/salarios-plus` e invalida la lista al responder 201

#### Scenario: Filtrar SalarioPlus por grupo
- **WHEN** el usuario filtra por `grupo=PROG`
- **THEN** la query recarga mostrando solo los SalarioPlus de ese grupo

#### Scenario: Rechazo de duplicado (grupo, rol) muestra error inline
- **WHEN** el backend responde 409 por solapamiento de `(grupo, rol)` vigente
- **THEN** el formulario muestra el error inline y conserva los datos

### Requirement: Grilla salarial organizada en pestañas Base / Plus

El sistema SHALL presentar el ABM de grilla en una página con dos secciones (pestañas o bloques) — SalarioBase y SalarioPlus — cada una con su tabla y su formulario modal independientes.

#### Scenario: Navegación entre Base y Plus
- **WHEN** el usuario abre la página de grilla salarial
- **THEN** ve dos secciones (Base y Plus), cada una con su propia tabla y botón de alta

### Requirement: Fetch de grilla vía hooks de TanStack Query

El sistema SHALL realizar todo acceso de datos de grilla mediante hooks de TanStack Query con query keys keyed por el filtro aplicado (`rol` para base, `grupo` para plus). Cada mutación SHALL invalidar la lista correspondiente.

#### Scenario: Mutación invalida la lista correcta
- **WHEN** se crea, actualiza o elimina un SalarioBase
- **THEN** se invalida únicamente la query de SalarioBase (no la de SalarioPlus)
