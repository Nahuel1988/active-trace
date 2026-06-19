## Why

El sistema necesita un tablón de avisos institucionales (F3.5) para que COORDINADOR y ADMIN puedan comunicar novedades a grupos específicos de usuarios (global, por materia, por cohorte, por rol), con ventana de vigencia, severidad, orden de prioridad y opción de requerir acuse de recibo. Actualmente no existe mecanismo de comunicación interna salvo la mensajería uno-a-uno.

## What Changes

- Nuevos modelos `Aviso` y `AcknowledgmentAviso` con migración
- CRUD de avisos (`avisos:publicar`) — alta, modificación, activación/desactivación
- Listado de avisos visibles para el usuario autenticado (filtrado por alcance/rol/cohorte/vigencia)
- Endpoint de confirmación de lectura (acknowledgment)
- Contadores derivados desde `AcknowledgmentAviso` (sin denormalizar)
- Permiso `avisos:publicar` ya existente en `rbac_seed.py`

## Capabilities

### New Capabilities
- `aviso-management`: CRUD de avisos con alcance (Global/PorMateria/PorCohorte/PorRol), severidad (Info/Advertencia/Crítico), ventana de vigencia, orden de prioridad, y flag requiere_ack
- `acknowledgment`: Confirmación de lectura por usuario, contadores (vistos/confirmados) derivados desde la tabla de acknowledgments

### Modified Capabilities
- (ninguna)

## Impact

- **Backend**: nuevo modelo `Aviso` + `AcknowledgmentAviso`, migración 006, repositorios, schemas Pydantic, service con lógica de filtrado por audiencia, router bajo `/api/avisos`
- **Permisos**: el permiso `avisos:publicar` ya existe en `rbac_seed.py` — se reusa
- **Tests**: ~20 tests nuevos (modelo, repositorio, service, endpoints, filtrado por alcance, acknowledgment, vigencia)
