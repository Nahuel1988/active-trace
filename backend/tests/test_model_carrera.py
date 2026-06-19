import pytest

from app.models.carrera import Carrera, EstadoCarrera


def test_carrera_model_has_attributes():
    c = Carrera()
    # attributes should exist on the model class
    assert hasattr(c, "codigo")
    assert hasattr(c, "nombre")
    assert hasattr(c, "estado")


def test_estado_carrera_enum_values():
    assert EstadoCarrera.Activa.value == "activa"
    assert EstadoCarrera.Inactiva.value == "inactiva"
