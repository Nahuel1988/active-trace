from app.models.cohorte import Cohorte


def test_cohorte_model_fields():
    c = Cohorte()
    assert hasattr(c, "carrera_id")
    assert hasattr(c, "nombre")
    assert hasattr(c, "anio")
    assert hasattr(c, "vig_desde")
    assert hasattr(c, "vig_hasta")
    assert hasattr(c, "estado")
