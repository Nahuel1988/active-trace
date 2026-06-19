import pytest
from pydantic import ValidationError

from app.schemas.estructura import CarreraCreate, MateriaCreate, CohorteCreate


def test_carrera_create_forbids_extra():
    with pytest.raises(ValidationError):
        CarreraCreate(codigo='C1', nombre='Carrera 1', extra_field='no')


def test_materia_create_forbids_extra():
    with pytest.raises(ValidationError):
        MateriaCreate(codigo='M1', nombre='Materia', unknown=1)


def test_cohorte_create_fields_required():
    with pytest.raises(ValidationError):
        CohorteCreate(carrera_id='x', nombre='A')
