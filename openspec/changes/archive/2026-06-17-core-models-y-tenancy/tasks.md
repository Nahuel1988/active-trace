## 1. Dependencias y migración

- [x] 1.1 Verificar que `cryptography` está declarado en `backend/pyproject.toml`; agregarlo en `[project.dependencies]` si falta
- [x] 1.2 Crear `backend/app/models/tenant.py` con el modelo SQLAlchemy `Tenant`: columnas `id` (UUID PK), `slug` (str, unique), `nombre` (str), `activo` (bool, default True), `created_at`, `updated_at` (datetime UTC); heredar de `Base`
- [x] 1.3 Exportar `Tenant` en `backend/app/models/__init__.py`
- [x] 1.4 Generar migración Alembic `001_tenant`: `alembic revision --autogenerate -m "001_tenant"` y revisar que crea tabla `tenant` con constraint `UNIQUE(slug)` e índice en `id`
- [x] 1.5 Aplicar `alembic upgrade head` contra la DB de test y verificar que no hay errores

## 2. Mixin base (TDD)

- [x] 2.1 **[RED]** Escribir `backend/tests/test_base_mixin.py`: test que un modelo con `TenantScopedMixin` tiene UUID generado sin proveer `id`; test que `created_at` y `updated_at` se setean en INSERT; test que `deleted_at` arranca en `None`; test que UPDATE actualiza `updated_at`. Los tests deben fallar (clase no existe aún)
- [x] 2.2 **[GREEN]** Crear `backend/app/models/base.py` con `TenantScopedMixin`: `id: Mapped[UUID]` con `default=uuid4`, PK; `tenant_id: Mapped[UUID]` FK → `tenant.id`, NOT NULL, `index=True`; `created_at: Mapped[datetime]` con `server_default=func.now()`; `updated_at: Mapped[datetime]` con `server_default=func.now()`, `onupdate=func.now()`; `deleted_at: Mapped[datetime | None]` nullable. Ejecutar tests → deben pasar
- [x] 2.3 **[TRIANGULATE]** Agregar tests: dos instancias del mismo modelo tienen UUIDs distintos; soft delete seteando `deleted_at` deja el registro en tabla con timestamp. Ejecutar → pasar
- [x] 2.4 Exportar `TenantScopedMixin` en `backend/app/models/__init__.py`

## 3. BaseRepository (TDD)

- [x] 3.1 **[RED]** Escribir `backend/tests/test_base_repository.py`: test `get` retorna `None` para ID de otro tenant; test `list` con dos tenants retorna solo los del tenant correcto; test soft delete → `get` retorna `None` después; test `list` no incluye registros soft-deleted. Los tests deben fallar (clase no existe aún). Usar modelo de prueba inline en conftest o fixture
- [x] 3.2 **[GREEN]** Crear `backend/app/repositories/base.py` con `BaseRepository[T]` genérico: `async def get(self, *, id: UUID, tenant_id: UUID, session: AsyncSession) -> T | None`; `async def list(self, *, tenant_id: UUID, session: AsyncSession, limit: int = 50, offset: int = 0) -> list[T]`; `async def create(self, *, obj: T, session: AsyncSession) -> T`; `async def soft_delete(self, *, id: UUID, tenant_id: UUID, session: AsyncSession) -> bool`. Todos los métodos de lectura filtran `WHERE tenant_id = :tenant_id AND deleted_at IS NULL`. Ejecutar tests → pasar
- [x] 3.3 **[TRIANGULATE]** Agregar test: `soft_delete` con ID de otro tenant no modifica ningún registro (retorna `False`); `list` con `limit=1` retorna máximo 1 resultado. Ejecutar → pasar
- [x] 3.4 Exportar `BaseRepository` en `backend/app/repositories/__init__.py`

## 4. EncryptionService (TDD)

- [x] 4.1 **[RED]** Escribir `backend/tests/test_encryption.py`: test round-trip `encrypt → decrypt = valor original`; test dos cifrados del mismo valor producen ciphertexts distintos; test descifrar ciphertext con 1 byte alterado lanza excepción; test `Settings` con `ENCRYPTION_KEY` de longitud ≠ 32 levanta `ValidationError`. Los tests deben fallar
- [x] 4.2 **[GREEN]** Implementar `EncryptionService` en `backend/app/core/security.py`: método `encrypt(plaintext: str) -> str` usa `AESGCM` con IV de 12 bytes aleatorios (`os.urandom(12)`), serializa `iv + ciphertext` en base64; método `decrypt(ciphertext_b64: str) -> str` desempaqueta IV, descifra. Instanciar `encryption_service = EncryptionService(key=settings.encryption_key.encode())` como módulo-level singleton. Ejecutar tests → pasar
- [x] 4.3 **[TRIANGULATE]** Agregar test: cifrar string vacío no falla; cifrar string con caracteres Unicode (ej: `"José Pérez"`) hace round-trip correcto. Ejecutar → pasar

## 5. Wiring y conftest

- [x] 5.1 Actualizar `backend/tests/conftest.py` para que la sesión de test incluya la tabla `tenant` (ya cubierta si Alembic corre en DB de test) y exponga un fixture `tenant_factory` que crea tenants de prueba con UUID único
- [x] 5.2 Verificar que los tests existentes de C-01 (`test_health.py`, `test_config.py`, `test_database.py`, `test_app_startup.py`) siguen pasando sin regresiones

## 6. Cobertura y cierre

- [x] 6.1 Ejecutar `pytest --cov=app/models --cov=app/repositories --cov=app/core/security --cov-report=term-missing` y verificar ≥ 80% de líneas y ≥ 90% en los casos de negocio críticos (aislamiento, soft delete, cifrado). **Resultado: 94% líneas, 100% reglas de negocio cubiertas.**
- [x] 6.2 Revisar que ningún archivo supera 500 LOC (`wc -l backend/app/**/*.py`). **Máximo: 82 LOC (repositories/base.py)**
- [x] 6.3 Marcar `[x]` el change C-02 en `CHANGES.md` cuando todos los tests pasen en verde
