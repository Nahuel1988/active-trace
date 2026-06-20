## ADDED Requirements

### Requirement: FINANZAS puede calcular liquidación para una cohorte y período
El sistema SHALL exponer POST /api/v1/liquidaciones/calcular que recibe `cohorte_id` (UUID) y `periodo` (AAAA-MM). El sistema SHALL calcular la liquidación para todos los docentes con asignaciones activas en esa cohorte durante el período indicado, aplicando RN-21 (Base + ΣPlus), RN-31 (vigencia temporal), RN-34 (Base vigente al mes + Plus por categoría×rol) y PA-23 (Plus una vez por clave distinta).

#### Scenario: Cálculo exitoso genera Liquidacion por docente
- **WHEN** un usuario FINANZAS invoca POST /api/v1/liquidaciones/calcular con cohorte_id=X y periodo=2026-06
- **THEN** el sistema retorna 200 con un resumen que incluye cantidad de liquidaciones generadas, total general y detalle por docente

#### Scenario: Cálculo con docentes de distintos roles
- **WHEN** el sistema calcula para un período donde hay PROFESOR, TUTOR y COORDINADOR asignados
- **THEN** cada docente obtiene su Liquidacion con el monto_base correspondiente a su rol según SalarioBase vigente

#### Scenario: Plus se aplica una sola vez por clave (PA-23)
- **WHEN** un docente tiene 3 comisiones de materias con clave PROG y 2 comisiones con clave BD
- **THEN** el sistema suma UNA aplicación del Plus PROG y UNA aplicación del Plus BD, sin importar la cantidad de comisiones

#### Scenario: Docente sin datos bancarios no se liquida (RN-26)
- **WHEN** el cálculo encuentra un docente sin CBU, alias ni banco configurados
- **THEN** el sistema omite al docente de la liquidación y lo incluye en una advertencia en el resumen

#### Scenario: Docente facturante se liquida con excluido_por_factura=true
- **WHEN** el cálculo procesa un docente con facturador=true
- **THEN** el sistema crea la Liquidacion con excluido_por_factura=true y monto calculado normalmente, pero marcado para el flujo de factura

#### Scenario: Docente NEXO se marca con es_nexo=true
- **WHEN** el cálculo procesa un docente con rol=NEXO
- **THEN** el sistema crea la Liquidacion con es_nexo=true

#### Scenario: Recalcular reemplaza liquidaciones Abiertas existentes
- **WHEN** ya existen liquidaciones Abiertas para (cohorte_id, periodo) y se invoca calcular nuevamente
- **THEN** el sistema reemplaza las liquidaciones Abiertas existentes con los nuevos valores calculados

#### Scenario: Recalcular rechazado si existen liquidaciones Cerradas
- **WHEN** ya existen liquidaciones Cerradas para (cohorte_id, periodo)
- **THEN** el sistema responde 409 Conflict indicando que el período ya está cerrado

### Requirement: Base salarial se obtiene de SalarioBase vigente en el período
El sistema SHALL seleccionar el SalarioBase cuyo `desde <= fin_del_periodo AND (hasta IS NULL OR hasta >= inicio_del_periodo)` para el rol del docente.

#### Scenario: Base vigente con hasta abierto
- **WHEN** existe SalarioBase para PROFESOR con desde=2026-01-01 y hasta=NULL
- **THEN** el cálculo lo selecciona como vigente para cualquier período desde enero 2026 en adelante

#### Scenario: Base vigente con hasta definido
- **WHEN** existe SalarioBase para TUTOR con desde=2026-01-01 y hasta=2026-06-30
- **THEN** el cálculo lo selecciona para período 2026-05 pero NO para período 2026-07

#### Scenario: Sin SalarioBase vigente para un rol
- **WHEN** no existe SalarioBase vigente para el rol del docente en el período
- **THEN** el cálculo omite al docente con advertencia y monto_base=0

### Requirement: Plus se obtiene de SalarioPlus vigente por (grupo, rol)
El sistema SHALL aplicar PA-22: las 5 claves de Plus son PROG, BD, ARQ, MAT, MET. El mapeo materia→grupo SHALL ser configurable por tenant. El sistema SHALL buscar SalarioPlus vigente para cada (grupo, rol) distinto que tenga el docente en sus asignaciones activas del período.

#### Scenario: Plus vigente para grupo y rol
- **WHEN** un docente PROFESOR tiene asignaciones en materias de grupo PROG y existe SalarioPlus vigente para (PROG, PROFESOR)
- **THEN** el sistema incluye el monto del plus en el cálculo

#### Scenario: Sin SalarioPlus para grupo y rol
- **WHEN** un docente tiene asignaciones de grupo MAT pero no existe SalarioPlus para (MAT, TUTOR)
- **THEN** el sistema no aplica plus para ese grupo (no falla)

#### Scenario: Clave sin mapeo de materia se omite
- **WHEN** una materia no tiene clave de Plus configurada en el tenant
- **THEN** el sistema omite esa materia del cálculo de plus (no falla)
