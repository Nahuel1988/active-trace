from app.models.materia import Materia, EstadoMateria


def test_materia_fields_and_enum():
    m = Materia()
    assert hasattr(m, "codigo")
    assert hasattr(m, "nombre")
    assert hasattr(m, "estado")
    assert EstadoMateria.Activa.value == "activa"
