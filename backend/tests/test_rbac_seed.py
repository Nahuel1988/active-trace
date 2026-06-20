"""Tests de approval para el catálogo de permisos y matriz base.

Estos tests capturan el comportamiento actual de rbac_seed.py para
garantizar que las modificaciones no rompan lo existente.
"""

from app.core.rbac_seed import MATRIZ_BASE, PERMISOS, CODIGOS_PERMISOS


class TestPermisosCatalogo:
    """Approval: el catálogo de permisos contiene los esperados."""

    def test_calificaciones_importar_existe(self):
        codes = [c for c, *_ in PERMISOS]
        assert "calificaciones:importar" in codes

    def test_calificaciones_configurar_umbral_existe(self):
        codes = [c for c, *_ in PERMISOS]
        assert "calificaciones:configurar-umbral" in codes

    def test_calificaciones_vaciar_existe(self):
        codes = [c for c, *_ in PERMISOS]
        assert "calificaciones:vaciar" in codes

    def test_calificaciones_configurar_umbral_descripcion(self):
        entry = next(
            (p for p in PERMISOS if p[0] == "calificaciones:configurar-umbral"),
            None,
        )
        assert entry is not None
        assert entry[1] == "calificaciones"
        assert entry[2] == "configurar-umbral"

    def test_calificaciones_vaciar_descripcion(self):
        entry = next(
            (p for p in PERMISOS if p[0] == "calificaciones:vaciar"),
            None,
        )
        assert entry is not None
        assert entry[1] == "calificaciones"
        assert entry[2] == "vaciar"

    def test_codigos_permisos_dict_consistente(self):
        """CODIGOS_PERMISOS debe tener todos los codes de PERMISOS."""
        codes = {c for c, *_ in PERMISOS}
        assert set(CODIGOS_PERMISOS.keys()) == codes

    def test_calificaciones_importar_descripcion(self):
        entry = next(
            (p for p in PERMISOS if p[0] == "calificaciones:importar"),
            None,
        )
        assert entry is not None
        assert entry[1] == "calificaciones"
        assert entry[2] == "importar"
        assert entry[3] == "Importar calificaciones"


class TestMatrizBase:
    """Approval: la matriz base tiene las asignaciones esperadas."""

    def test_profesor_tiene_calificaciones_importar(self):
        assert ("profesor", "calificaciones:importar", "propio") in MATRIZ_BASE

    def test_profesor_tiene_calificaciones_configurar_umbral(self):
        assert ("profesor", "calificaciones:configurar-umbral", "propio") in MATRIZ_BASE

    def test_profesor_tiene_calificaciones_vaciar(self):
        assert ("profesor", "calificaciones:vaciar", "propio") in MATRIZ_BASE

    def test_coordinador_tiene_calificaciones_importar(self):
        assert ("coordinador", "calificaciones:importar", "global") in MATRIZ_BASE

    def test_coordinador_tiene_calificaciones_configurar_umbral(self):
        assert ("coordinador", "calificaciones:configurar-umbral", "global") in MATRIZ_BASE

    def test_coordinador_tiene_calificaciones_vaciar(self):
        assert ("coordinador", "calificaciones:vaciar", "global") in MATRIZ_BASE

    def test_admin_tiene_calificaciones_importar(self):
        assert ("admin", "calificaciones:importar", "global") in MATRIZ_BASE

    def test_matriz_rol_permiso_validacion_pasa(self):
        """La validación interna de MATRIZ_BASE no debe lanzar ValueError."""
        # Re-ejecutar la validación que está al final del módulo
        codes = {c for c, *_ in PERMISOS}
        for role_code, permiso_code, scope in MATRIZ_BASE:
            assert permiso_code in codes, (
                f"Matriz refiere permiso '{permiso_code}' para rol "
                f"'{role_code}', pero no está en el catálogo PERMISOS"
            )
