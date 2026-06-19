## ADDED Requirements

### Requirement: Instancia Axios centralizada
El sistema SHALL proveer una única instancia Axios en `src/shared/services/api.ts` con `baseURL` configurada desde variables de entorno (`VITE_API_URL`). Todos los módulos de la aplicación SHALL usar esta instancia para las requests HTTP; no SHALL crearse instancias Axios adicionales.

#### Scenario: Request usa baseURL configurada
- **WHEN** cualquier servicio llama a `api.get('/health')`
- **THEN** la request se dirige a `${VITE_API_URL}/health`

#### Scenario: No existen instancias Axios secundarias
- **WHEN** se analiza el código fuente
- **THEN** no hay `axios.create()` fuera de `shared/services/api.ts`

### Requirement: Interceptor de autenticación
La instancia Axios SHALL incluir un request interceptor que adjunte el header `Authorization: Bearer <access_token>` en cada request, tomando el token del AuthContext (memoria de React). Si no hay token activo, la request procede sin header (el backend devolverá 401).

#### Scenario: Request autenticada lleva header Authorization
- **WHEN** el usuario tiene sesión activa y se realiza cualquier request
- **THEN** el header `Authorization: Bearer <token>` está presente en la request

#### Scenario: Request sin sesión no lleva header Authorization
- **WHEN** el usuario no tiene sesión activa
- **THEN** el header `Authorization` no está presente en la request

### Requirement: Refresh transparente de access token
Cuando el servidor retorna 401, el cliente HTTP SHALL:
1. Pausar todas las requests en vuelo (cola de promesas).
2. Intentar un único `POST /api/auth/refresh` (con la cookie httpOnly de refresh).
3. Si el refresh es exitoso: actualizar el access token en AuthContext, reintentar todas las requests de la cola con el nuevo token.
4. Si el refresh falla: limpiar la sesión en AuthContext y redirigir al usuario a `/login`.
El mecanismo SHALL garantizar que solo se emite un único request de refresh simultáneamente, sin importar cuántas requests hayan fallado con 401.

#### Scenario: 401 dispara refresh y reintento exitoso
- **WHEN** una request retorna 401 y el refresh es exitoso
- **THEN** la request original se reintenta con el nuevo access token y devuelve la respuesta correcta

#### Scenario: Múltiples 401 simultáneos producen un único refresh
- **WHEN** tres requests concurrentes retornan 401 al mismo tiempo
- **THEN** se emite exactamente un `POST /api/auth/refresh` y las tres requests se reintentan

#### Scenario: 401 con refresh fallido redirige a login
- **WHEN** una request retorna 401 y el `POST /api/auth/refresh` también retorna 401
- **THEN** la sesión se limpia y el usuario es redirigido a `/login`

### Requirement: Propagación de 403 a la UI
Cuando el servidor retorna 403, el cliente HTTP SHALL rechazar la promesa con un error tipado `ForbiddenError` que la UI puede capturar para mostrar un mensaje apropiado. No SHALL redirigir automáticamente — la UI decide cómo manejarlo.

#### Scenario: 403 produce error tipado en la capa de UI
- **WHEN** el servidor retorna 403 para una request
- **THEN** la promesa rechaza con una instancia de `ForbiddenError` y la UI puede mostrar "Sin permiso"

### Requirement: Cookies de refresh con credentials
La instancia Axios SHALL tener `withCredentials: true` para que las cookies httpOnly (refresh token) sean enviadas automáticamente en el request de refresh.

#### Scenario: Cookie de refresh enviada en POST refresh
- **WHEN** el interceptor llama a `POST /api/auth/refresh`
- **THEN** la cookie httpOnly `refresh_token` se incluye en la request
