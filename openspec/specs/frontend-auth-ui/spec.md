## ADDED Requirements

### Requirement: Pantalla de login
El sistema SHALL proveer una pantalla `/login` con formulario de email y contraseña validado con Zod. Al enviar, llama a `POST /api/auth/login`. Si las credenciales son válidas y el usuario NO tiene 2FA activo, establece sesión y redirige al destino original (`returnTo`) o a `/`. Si el usuario tiene 2FA activo, avanza al gate de 2FA.

#### Scenario: Login exitoso sin 2FA redirige al destino
- **WHEN** el usuario ingresa credenciales válidas y no tiene 2FA
- **THEN** se almacena el access token en AuthContext y se redirige a `/` (o al `returnTo` guardado)

#### Scenario: Login exitoso con 2FA avanza al gate
- **WHEN** el usuario ingresa credenciales válidas y tiene 2FA activo
- **THEN** se muestra el gate de verificación TOTP sin emitir sesión completa

#### Scenario: Credenciales inválidas muestran error
- **WHEN** el usuario ingresa email o contraseña incorrectos
- **THEN** se muestra el mensaje de error devuelto por el backend sin redirigir

#### Scenario: Validación de formulario antes de enviar
- **WHEN** el usuario envía el formulario con email vacío o mal formado
- **THEN** se muestran errores de validación inline y no se realiza la request

### Requirement: Gate de verificación 2FA
El sistema SHALL proveer un componente de gate 2FA que aparece luego de las credenciales válidas si el usuario tiene 2FA activo. Solicita el código TOTP de 6 dígitos y llama a `POST /api/auth/2fa/verify`. Solo si la verificación es exitosa se emite la sesión completa. El AuthContext SHALL distinguir el estado `pendingTwoFactor` (post-credenciales, pre-TOTP) de `isAuthenticated` (sesión completa).

#### Scenario: TOTP correcto completa la sesión
- **WHEN** el usuario ingresa el código TOTP válido
- **THEN** el AuthContext pasa de `pendingTwoFactor` a `isAuthenticated` y se redirige al destino

#### Scenario: TOTP incorrecto muestra error sin limpiar sesión previa
- **WHEN** el usuario ingresa un código TOTP inválido
- **THEN** se muestra error y el estado permanece en `pendingTwoFactor`

### Requirement: Flujo de recuperación de contraseña
El sistema SHALL proveer dos pantallas: `/auth/recovery` (solicitud) y `/auth/reset` (nueva contraseña con token). La pantalla de solicitud llama a `POST /api/auth/forgot` con el email. La pantalla de reset llama a `POST /api/auth/reset` con el token de la URL y la nueva contraseña. Ambos formularios están validados con Zod.

#### Scenario: Solicitud de recuperación muestra confirmación
- **WHEN** el usuario ingresa un email y envía el formulario de recovery
- **THEN** se muestra un mensaje de confirmación ("revisá tu email") independientemente de si el email existe (para no exponer usuarios)

#### Scenario: Reset exitoso redirige a login
- **WHEN** el usuario establece una nueva contraseña con un token válido
- **THEN** la contraseña se actualiza y el usuario es redirigido a `/login`

#### Scenario: Token de reset inválido o expirado muestra error
- **WHEN** el usuario accede a `/auth/reset` con un token inválido o expirado
- **THEN** se muestra un mensaje de error y un enlace para solicitar un nuevo token

### Requirement: Guard de rutas por permiso
El componente `<ProtectedRoute>` SHALL envolver cada ruta privada. Si no hay sesión activa → redirige a `/login` guardando la URL actual en `returnTo`. Si hay sesión pero el usuario no tiene el permiso declarado en la ruta → redirige a `/403`. Si no se declara permiso, solo verifica sesión.

#### Scenario: Ruta privada sin sesión redirige a login
- **WHEN** un usuario no autenticado accede a cualquier ruta privada
- **THEN** es redirigido a `/login` y la URL original queda en `returnTo`

#### Scenario: Ruta con permiso requerido deniega a usuario sin ese permiso
- **WHEN** un usuario autenticado accede a una ruta que requiere `liquidaciones:ver` y no lo tiene
- **THEN** es redirigido a `/403`

#### Scenario: Ruta con permiso requerido permite acceso si lo tiene
- **WHEN** un usuario autenticado accede a una ruta que requiere `estructura:gestionar` y lo tiene
- **THEN** se renderiza el componente de la ruta sin redirección

#### Scenario: Sesión recuperada al recargar la página
- **WHEN** la SPA se carga o recarga y hay un refresh token válido en cookie
- **THEN** el AuthContext realiza un refresh silencioso y el usuario accede a rutas protegidas sin pasar por login

### Requirement: Logout con revocación de sesión
El sistema SHALL proveer una acción de logout que llama a `POST /api/auth/logout` para revocar el refresh token en el backend, limpia el AuthContext (access token en memoria) y redirige a `/login`.

#### Scenario: Logout limpia sesión y redirige
- **WHEN** el usuario hace logout
- **THEN** se llama a `POST /api/auth/logout`, se limpia el AuthContext y se redirige a `/login`

#### Scenario: Logout con error de red igual limpia sesión local
- **WHEN** el usuario hace logout y la request falla por error de red
- **THEN** el AuthContext se limpia igualmente y el usuario es redirigido a `/login`

### Requirement: Tests de pantallas de autenticación
El sistema SHALL incluir tests con Vitest + React Testing Library que cubran: render de LoginPage, flujo de login con mock de API (éxito y error), guard redirige sin sesión, refresh transparente (mock de interceptor).

#### Scenario: LoginPage renderiza sin errores
- **WHEN** se monta `<LoginPage>` en el test
- **THEN** el componente renderiza el formulario sin lanzar errores

#### Scenario: Guard redirige usuario no autenticado
- **WHEN** se renderiza una ruta privada sin AuthContext activo
- **THEN** el test confirma redirección a `/login`
