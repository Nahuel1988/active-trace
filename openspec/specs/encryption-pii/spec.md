## ADDED Requirements

### Requirement: EncryptionService cifra y descifra valores con AES-256-GCM
El sistema SHALL proveer un `EncryptionService` que use AES-256-GCM con la `ENCRYPTION_KEY` de 32 bytes definida en Settings. El servicio MUST exponer: `encrypt(plaintext: str) -> str` y `decrypt(ciphertext: str) -> str`. El IV (12 bytes) es generado aleatoriamente en cada cifrado y se antepone al ciphertext antes de codificar en base64.

#### Scenario: Cifrado y descifrado round-trip
- **WHEN** se cifra un valor con `encrypt(value)` y luego se descifra con `decrypt(result)`
- **THEN** el valor descifrado es idéntico al original

#### Scenario: Distintos cifrados del mismo valor son distintos ciphertexts
- **WHEN** se cifra el mismo valor dos veces
- **THEN** los dos ciphertexts resultantes son distintos (IV aleatorio diferente cada vez)

#### Scenario: Descifrado de ciphertext manipulado falla con excepción
- **WHEN** se intenta descifrar un ciphertext modificado (1 bit alterado)
- **THEN** el servicio lanza una excepción (autenticación GCM falla)

### Requirement: Valores PII nunca se exponen en logs ni en texto plano en persistencia
El sistema SHALL garantizar que los atributos marcados `[cifrado]` en el modelo de datos se almacenen en la columna DB como ciphertext base64, nunca como texto plano.

#### Scenario: Valor cifrado en DB
- **WHEN** se persiste un modelo con un campo cifrado (ej: email `test@ejemplo.com`)
- **THEN** la columna en la base de datos contiene el ciphertext base64, no el email en claro

#### Scenario: Valor descifrado en memoria
- **WHEN** se lee el modelo desde la base de datos y se accede al campo cifrado
- **THEN** el valor en Python es el texto original descifrado (no el ciphertext)

### Requirement: `ENCRYPTION_KEY` validada al arranque
El sistema SHALL rechazar el arranque de la aplicación si `ENCRYPTION_KEY` no tiene exactamente 32 caracteres (ya validado en C-01 Settings, confirmado en este change).

#### Scenario: Arranque con clave válida
- **WHEN** `ENCRYPTION_KEY` tiene exactamente 32 caracteres
- **THEN** la aplicación arranca sin errores de configuración

#### Scenario: Arranque con clave inválida
- **WHEN** `ENCRYPTION_KEY` tiene longitud distinta de 32 caracteres
- **THEN** `Settings` lanza `ValidationError` y la aplicación no arranca
