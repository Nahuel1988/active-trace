## ADDED Requirements

### Requirement: Rate limiting de login por IP y email
El sistema SHALL limitar los intentos de `POST /api/auth/login` a un máximo de 5 intentos por 60 segundos por combinación de IP de origen + email. Superado el límite, el sistema MUST responder 429 (fail-closed) antes de validar credenciales. El límite MUST aplicarse detrás de una interfaz que permita migrar de backend in-memory a Redis.

#### Scenario: Intentos dentro del límite se procesan
- **WHEN** se realizan 5 intentos de login o menos en 60s desde la misma IP y email
- **THEN** cada intento se procesa normalmente (200 o 401 según credenciales)

#### Scenario: Sexto intento bloqueado
- **WHEN** se realiza un sexto intento de login dentro de la misma ventana de 60s desde la misma IP y email
- **THEN** el sistema responde 429 sin validar las credenciales

#### Scenario: Límite separado por email distinto
- **WHEN** desde la misma IP se intenta login con un email diferente
- **THEN** ese email tiene su propio contador independiente (la clave es IP + email)

#### Scenario: Ventana se reinicia tras 60s
- **WHEN** transcurren más de 60 segundos desde el primer intento
- **THEN** el contador para esa clave IP+email se reinicia y se permiten nuevos intentos
