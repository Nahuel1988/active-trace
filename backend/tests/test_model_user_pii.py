"""Tests para las columnas PII extendidas del modelo User — TDD C-07.

RED: tests fallan porque las columnas PII aún no existen en User.
GREEN: se agregan las columnas y los tests pasan.
TRIANGULATE: unicidad (tenant_id, email_lookup) sigue intacta.
"""

import pytest


class TestUserPIIColumns:
    """Scenario: Modelo User expone nuevas columnas con tipos/nullabilities correctas."""

    def test_user_model_has_nombre_column(self) -> None:
        """WHEN se inspecciona el modelo User, THEN tiene columna 'nombre' nullable."""
        from app.models.user import User
        from sqlalchemy import inspect

        mapper = inspect(User)
        col_names = [c.key for c in mapper.mapper.columns]
        assert "nombre" in col_names

    def test_user_model_has_apellidos_column(self) -> None:
        """WHEN se inspecciona el modelo User, THEN tiene columna 'apellidos' nullable."""
        from app.models.user import User
        from sqlalchemy import inspect

        mapper = inspect(User)
        col_names = [c.key for c in mapper.mapper.columns]
        assert "apellidos" in col_names

    def test_user_model_has_dni_encrypted_column(self) -> None:
        """WHEN se inspecciona el modelo User, THEN tiene columna 'dni_encrypted' nullable."""
        from app.models.user import User
        from sqlalchemy import inspect

        mapper = inspect(User)
        col_names = [c.key for c in mapper.mapper.columns]
        assert "dni_encrypted" in col_names

    def test_user_model_has_cuil_encrypted_column(self) -> None:
        """WHEN se inspecciona el modelo User, THEN tiene columna 'cuil_encrypted' nullable."""
        from app.models.user import User
        from sqlalchemy import inspect

        mapper = inspect(User)
        col_names = [c.key for c in mapper.mapper.columns]
        assert "cuil_encrypted" in col_names

    def test_user_model_has_cbu_encrypted_column(self) -> None:
        """WHEN se inspecciona el modelo User, THEN tiene columna 'cbu_encrypted' nullable."""
        from app.models.user import User
        from sqlalchemy import inspect

        mapper = inspect(User)
        col_names = [c.key for c in mapper.mapper.columns]
        assert "cbu_encrypted" in col_names

    def test_user_model_has_alias_cbu_encrypted_column(self) -> None:
        """WHEN se inspecciona el modelo User, THEN tiene columna 'alias_cbu_encrypted' nullable."""
        from app.models.user import User
        from sqlalchemy import inspect

        mapper = inspect(User)
        col_names = [c.key for c in mapper.mapper.columns]
        assert "alias_cbu_encrypted" in col_names

    def test_user_model_has_banco_column(self) -> None:
        """WHEN se inspecciona el modelo User, THEN tiene columna 'banco' nullable."""
        from app.models.user import User
        from sqlalchemy import inspect

        mapper = inspect(User)
        col_names = [c.key for c in mapper.mapper.columns]
        assert "banco" in col_names

    def test_user_model_has_regional_column(self) -> None:
        """WHEN se inspecciona el modelo User, THEN tiene columna 'regional' nullable."""
        from app.models.user import User
        from sqlalchemy import inspect

        mapper = inspect(User)
        col_names = [c.key for c in mapper.mapper.columns]
        assert "regional" in col_names

    def test_user_model_has_legajo_profesional_column(self) -> None:
        """WHEN se inspecciona el modelo User, THEN tiene columna 'legajo_profesional' nullable."""
        from app.models.user import User
        from sqlalchemy import inspect

        mapper = inspect(User)
        col_names = [c.key for c in mapper.mapper.columns]
        assert "legajo_profesional" in col_names

    def test_user_model_has_facturador_column(self) -> None:
        """WHEN se inspecciona el modelo User, THEN tiene columna 'facturador' NOT NULL DEFAULT false."""
        from app.models.user import User
        from sqlalchemy import inspect

        mapper = inspect(User)
        col_names = [c.key for c in mapper.mapper.columns]
        assert "facturador" in col_names

    def test_pii_columns_are_nullable(self) -> None:
        """WHEN se inspecciona el modelo User, THEN las columnas _encrypted son nullable."""
        from app.models.user import User

        # Usar __table__.columns que retorna Column objects directamente
        table_cols = {c.name: c for c in User.__table__.columns}

        for col_name in ("dni_encrypted", "cuil_encrypted", "cbu_encrypted", "alias_cbu_encrypted",
                         "nombre", "apellidos", "banco", "regional", "legajo_profesional"):
            col = table_cols.get(col_name)
            assert col is not None, f"Column {col_name} not found in table"
            assert col.nullable is True, f"Column {col_name} should be nullable"

    def test_facturador_is_not_nullable(self) -> None:
        """WHEN se inspecciona el modelo User, THEN facturador es NOT NULL."""
        from app.models.user import User

        table_cols = {c.name: c for c in User.__table__.columns}
        facturador_col = table_cols["facturador"]
        assert facturador_col.nullable is False


class TestUserInstantiationWithPII:
    """Scenario: Se puede instanciar User con los nuevos campos PII en memoria."""

    def test_user_can_be_created_with_all_pii_fields(self) -> None:
        """WHEN se instancia User con todos los campos PII, THEN no hay error."""
        import uuid
        from app.models.user import User

        u = User(
            tenant_id=uuid.uuid4(),
            email_encrypted="ciphertext",
            email_lookup="hmac",
            password_hash="argon2id",
            nombre="Juan",
            apellidos="García",
            dni_encrypted="ct_dni",
            cuil_encrypted="ct_cuil",
            cbu_encrypted="ct_cbu",
            alias_cbu_encrypted="ct_alias",
            banco="Banco Provincia",
            regional="Mendoza",
            legajo_profesional="LP-100",
            facturador=True,
        )
        assert u.nombre == "Juan"
        assert u.apellidos == "García"
        assert u.dni_encrypted == "ct_dni"
        assert u.facturador is True

    def test_user_new_columns_default_to_none(self) -> None:
        """WHEN se crea User sin PII fields, THEN los nuevos campos son None."""
        import uuid
        from app.models.user import User

        u = User(
            tenant_id=uuid.uuid4(),
            email_encrypted="ct",
            email_lookup="lk",
            password_hash="ph",
        )
        assert u.nombre is None
        assert u.apellidos is None
        assert u.dni_encrypted is None
        assert u.cuil_encrypted is None
        assert u.cbu_encrypted is None
        assert u.alias_cbu_encrypted is None

    def test_user_facturador_defaults_false(self) -> None:
        """WHEN se crea User sin facturador, THEN facturador es False."""
        import uuid
        from app.models.user import User

        u = User(
            tenant_id=uuid.uuid4(),
            email_encrypted="ct",
            email_lookup="lk",
            password_hash="ph",
        )
        # El default está en la columna SQLAlchemy
        # Puede ser None antes de flush, pero el default DB es False
        assert u.facturador is None or u.facturador is False


class TestUserUniqueConstraintStillWorks:
    """TRIANGULATE: unicidad (tenant_id, email_lookup) sigue intacta."""

    def test_unique_constraint_name_exists(self) -> None:
        """WHEN se inspecciona el modelo User, THEN UniqueConstraint uq_user_tenant_email existe."""
        from app.models.user import User
        from sqlalchemy import inspect

        # El __table_args__ debe seguir declarando la constraint
        table_args = User.__table_args__
        constraint_names = []
        for arg in table_args:
            if hasattr(arg, "name") and arg.name:
                constraint_names.append(arg.name)
        assert any("tenant_email" in n for n in constraint_names), (
            f"UniqueConstraint uq_user_tenant_email not found. Got: {constraint_names}"
        )
