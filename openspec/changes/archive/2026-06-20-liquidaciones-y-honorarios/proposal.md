## Why

activia-trace necesita un módulo de **liquidaciones y honorarios** que permita al equipo de FINANZAS calcular, cerrar y auditar los pagos a docentes de forma estructurada y trazable. Sin este cambio, no existe un registro sistematizado de cuánto se le paga a cada docente, bajo qué concepto, y si el pago corresponde a liquidación directa o facturación independiente. Las preguntas abiertas PA-22 (claves de Plus: PROG, BD, ARQ, MAT, MET) y PA-23 (Plus se aplica una sola vez por clave sin tope de acumulación) ya están resueltas, desbloqueando la arquitectura del cálculo.

## What Changes

- Nuevos modelos `SalarioBase`, `SalarioPlus`, `Liquidacion` y `Factura` con sus respectivas migraciones Alembic.
- **Grilla salarial ABM** (`F10.4`): endpoints CRUD para `SalarioBase` (por rol, con vigencia desde/hasta) y `SalarioPlus` (por grupo × rol, con vigencia desde/hasta). Permiso `liquidaciones:configurar-salarios`.
- **Cálculo de liquidación del período** (`FL-08`, `F10.1`): endpoint `POST /api/liquidaciones/calcular` que, dado un período (AAAA-MM) y cohorte, genera registros `Liquidacion` para cada docente activo. El cálculo respeta RN-21 (Base + ΣPlus), RN-31 (vigencia temporal), RN-33/PA-23 (Plus una vez por clave), RN-34 (Base vigente al mes + Plus por categoría×rol).
- **Vista de liquidaciones** (`F10.1`): GET con segmentación NEXO/general/factura y KPIs de cabecera (total sin factura / total con factura) según RN-36/RN-38.
- **Cierre de liquidación** (`F10.2`): `POST /api/liquidaciones/{id}/cerrar` que inmutabiliza el registro (RN-22). Auditoría con código `LIQUIDACION_CERRAR`.
- **Historial de liquidaciones** (`F10.3`): GET de liquidaciones cerradas con filtros por período, cohorte, docente.
- **Gestión de facturas** (`F10.5`): CRUD de `Factura` con transición Pendiente → Abonada (RN-39). Los docentes facturantes (usuario.facturador=true) se excluyen de la liquidación general (RN-35).
- **Separación contable** (`F10.6`): tres segmentos en la respuesta de liquidación (general, NEXO, facturantes) + KPIs.

## Capabilities

### New Capabilities
- `grilla-salarial-abm`: CRUD versionado de SalarioBase y SalarioPlus con vigencia temporal (desde/hasta). Permiso `liquidaciones:configurar-salarios` para FINANZAS. RN-31, RN-32, RN-33.
- `liquidacion-calculo`: Motor de cálculo que, dado (cohorte, período), genera Liquidacion para cada docente activo. Base por rol vigente al mes + Plus por (grupo × rol) una sola vez por clave. RN-21, RN-34, PA-22, PA-23.
- `liquidacion-vista`: GET de liquidaciones del período con segmentación (general / NEXO / facturantes) y KPIs de cabecera (total sin factura, total con factura). Permiso `liquidaciones:ver`. RN-36, RN-37, RN-38.
- `liquidacion-cierre`: Cierre de liquidación que inmutabiliza el registro. Permiso `liquidaciones:cerrar`. Audit `LIQUIDACION_CERRAR`. RN-22.
- `liquidacion-historial`: GET de liquidaciones cerradas con filtros (período, cohorte, docente). Permiso `liquidaciones:ver`. F10.3.
- `factura-gestion`: CRUD de Factura para docentes facturantes con transición Pendiente→Abonada. Permiso `facturas:gestionar`. RN-35, RN-39, RN-40.

### Modified Capabilities
- *(ninguna — este es el primer módulo de liquidaciones/facturas)*

## Impact

- **Modelos nuevos**: `SalarioBase`, `SalarioPlus`, `Liquidacion`, `Factura` con sus respectivos repositorios y esquemas Pydantic.
- **Routers nuevos**: `/api/liquidaciones/*`, `/api/facturas/*`.
- **Services nuevos**: `liquidacion_service.py`, `factura_service.py`, `grilla_service.py`.
- **Permissions nuevas**: `liquidaciones:calcular`, `liquidaciones:cerrar`, `liquidaciones:ver`, `liquidaciones:exportar`, `liquidaciones:configurar-salarios`, `facturas:gestionar`.
- **Audit code nuevo**: `LIQUIDACION_CERRAR`.
- **Migración Alembic**: `0NN_liquidaciones_y_honorarios` con tablas `salario_base`, `salario_plus`, `liquidacion`, `factura`.
- **Tests**: cobertura ≥90% en reglas de negocio (selección de base vigente, suma de plus por clave única, total, cierre inmutable, exclusión por factura, segmentación NEXO/general/facturantes, KPIs).
- **Dependencia**: requiere `C-07` (usuarios con asignaciones y flag `facturador`).
