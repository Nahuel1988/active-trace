import uuid

import pytest
from pydantic import ValidationError

from app.schemas.padron import (
    ConfirmarRequest,
    ConfirmarResponse,
    EntradaPadronCreate,
    EntradaPadronPreview,
    MoodleSyncResponse,
    PreviewResponse,
    VaciarRequest,
    VersionPadronListResponse,
    VersionPadronResponse,
)


class TestEntradaPadronCreate:
    def test_valid_data(self):
        data = {
            "nombre": "Juan",
            "apellidos": "Pérez",
            "email": "juan@example.com",
            "comision": "A",
        }
        e = EntradaPadronCreate(**data)
        assert e.nombre == "Juan"
        assert e.apellidos == "Pérez"
        assert e.email == "juan@example.com"
        assert e.comision == "A"
        assert e.regional is None
        assert e.usuario_id is None

    def test_with_all_fields(self):
        uid = uuid.uuid4()
        data = {
            "nombre": "María",
            "apellidos": "García",
            "email": "maria@test.com",
            "comision": "B",
            "regional": "CABA",
            "usuario_id": str(uid),
        }
        e = EntradaPadronCreate(**data)
        assert e.regional == "CABA"
        assert e.usuario_id == uid

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            EntradaPadronCreate(
                nombre="Juan",
                apellidos="Pérez",
                email="juan@example.com",
                comision="A",
                extra="no",
            )

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            EntradaPadronCreate(
                nombre="Juan",
                apellidos="Pérez",
                email="not-an-email",
                comision="A",
            )

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            EntradaPadronCreate(
                apellidos="Pérez",
                email="juan@example.com",
            )


class TestEntradaPadronPreview:
    def test_valid_data(self):
        data = {
            "nombre": "Juan",
            "apellidos": "Pérez",
            "email": "cualquier-cosa",
            "comision": "A",
        }
        e = EntradaPadronPreview(**data)
        assert e.email == "cualquier-cosa"

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            EntradaPadronPreview(
                nombre="Juan",
                apellidos="Pérez",
                email="j@e.com",
                comision="A",
                extra="no",
            )


class TestConfirmarRequest:
    def test_valid(self):
        uid = uuid.uuid4()
        data = {
            "materia_id": str(uid),
            "cohorte_id": str(uid),
            "entradas": [
                {
                    "nombre": "Juan",
                    "apellidos": "Pérez",
                    "email": "juan@example.com",
                    "comision": "A",
                }
            ],
        }
        r = ConfirmarRequest(**data)
        assert r.materia_id == uid
        assert len(r.entradas) == 1

    def test_extra_field_forbidden(self):
        uid = uuid.uuid4()
        with pytest.raises(ValidationError):
            ConfirmarRequest(
                materia_id=uid,
                cohorte_id=uid,
                entradas=[],
                extra="no",
            )


class TestVaciarRequest:
    def test_valid(self):
        uid = uuid.uuid4()
        r = VaciarRequest(materia_id=uid)
        assert r.materia_id == uid

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            VaciarRequest(materia_id=uuid.uuid4(), extra="no")

    def test_missing_field(self):
        with pytest.raises(ValidationError):
            VaciarRequest()


class TestPreviewResponse:
    def test_valid(self):
        r = PreviewResponse(
            total_filas=10,
            columnas_detectadas=["nombre", "email"],
            muestra=[],
            errores=[],
        )
        assert r.total_filas == 10
        assert r.errores == []


class TestVersionPadronResponse:
    def test_valid(self):
        import datetime

        r = VersionPadronResponse(
            id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            activa=True,
            total_entradas=5,
            origen="archivo",
            created_at=datetime.datetime.now(),
        )
        assert r.activa is True


class TestMoodleSyncResponse:
    def test_valid(self):
        r = MoodleSyncResponse(
            version_id=uuid.uuid4(),
            total_sincronizadas=10,
            errores=[],
        )
        assert r.total_sincronizadas == 10


class TestVersionPadronListResponse:
    def test_valid(self):
        import datetime

        v = VersionPadronResponse(
            id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            activa=True,
            total_entradas=0,
            origen="archivo",
            created_at=datetime.datetime.now(),
        )
        r = VersionPadronListResponse(versiones=[v], total=1)
        assert r.total == 1
        assert len(r.versiones) == 1


class TestConfirmarResponse:
    def test_valid(self):
        r = ConfirmarResponse(
            version_id=uuid.uuid4(),
            total_entradas=3,
            origen="archivo",
        )
        assert r.total_entradas == 3
