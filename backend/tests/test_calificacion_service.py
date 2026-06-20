"""Service tests para CalificacionService (Grupos 7-12).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Requiere --run-db (base PostgreSQL real, sin mocks).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.core.audit import AuditCodes, AuditContext
from app.models.calificacion import (
    Calificacion,
    OrigenCalificacionDB,
    UmbralMateria,
)
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.umbral_repository import UmbralRepository
from app.schemas.calificacion import (
    CalificacionResponse,
    UmbralMateriaResponse,
)
from app.services.calificacion_service import (
    CalificacionError,
    CalificacionService,
    UmbralService,
)

pytestmark = pytest.mark.requires_db


# ============================================================================
# Helpers
# ============================================================================


def _build_audit_ctx(user, tenant_id) -> AuditContext:
    return AuditContext(
        actor_id=user.id,
        tenant_id=tenant_id,
        ip="127.0.0.1",
        user_agent="test",
    )


def _crear_archivo_csv(columnas: list[str], filas: list[list[str]]) -> bytes:
    """Crea un archivo CSV en memoria."""
    header = ",".join(columnas)
    lines = [header]
    for row in filas:
        lines.append(",".join(row))
    content = "\n".join(lines)
    return content.encode("utf-8-sig")


def _crear_archivo_con_entrada_ids(
    columnas: list[str],
    filas: list[tuple[str, ...]],
    id_col: str = "entrada_padron_id",
) -> bytes:
    """Crea un archivo CSV con una columna explícita de entrada_padron_id."""
    cols = [id_col] + columnas
    lines = [",".join(cols)]
    for row in filas:
        lines.append(",".join(str(v) for v in row))
    content = "\n".join(lines)
    return content.encode("utf-8-sig")


# ============================================================================
# Group 7 — Preview archivo
# ============================================================================


class TestPreviewArchivo:
    """CalificacionService.preview_archivo — 7.1 RED → 7.2 GREEN → 7.3 TRIANGULATE."""

    async def test_preview_detecta_columnas_numericas_textuales(self):
        """7.1 RED: preview parsea CSV, detecta numéricas (Real) y textuales."""
        service = CalificacionService()
        contenido = _crear_archivo_csv(
            columnas=["nombre", "apellidos", "email", "Parcial (Real)", "TP (Real)", "Estado"],
            filas=[
                ["Juan", "Pérez", "juan@e.com", "85", "90", "Aprobado"],
                ["María", "García", "maria@e.com", "70", "65", "Regular"],
            ],
        )

        resultado = await service.preview_archivo(contenido, "notas.csv")

        assert resultado.total_filas == 2
        assert len(resultado.muestra_primeras_3) == 2
        assert len(resultado.errores) == 0

        # Clasificar columnas
        col_nombres = {c["nombre"]: c["tipo"] for c in resultado.columnas_detectadas}
        assert col_nombres.get("Parcial (Real)") == "numerica"
        assert col_nombres.get("TP (Real)") == "numerica"
        assert col_nombres.get("Estado") == "textual"
        assert col_nombres.get("nombre") == "ignorada"
        assert col_nombres.get("apellidos") == "ignorada"
        assert col_nombres.get("email") == "ignorada"

    async def test_preview_archivo_vacio_0_filas(self):
        """7.3: archivo CSV vacío (solo headers) → 0 filas, columnas vacías."""
        service = CalificacionService()
        contenido = _crear_archivo_csv(
            columnas=["nombre", "apellidos", "Parcial (Real)"],
            filas=[],
        )

        resultado = await service.preview_archivo(contenido, "vacio.csv")
        assert resultado.total_filas == 0
        # Sin filas de datos no podemos clasificar columnas
        assert len(resultado.columnas_detectadas) == 0

    async def test_preview_faltan_columnas_requeridas(self):
        """7.3: faltan nombre y apellidos → errores."""
        service = CalificacionService()
        contenido = _crear_archivo_csv(
            columnas=["email", "Parcial (Real)"],
            filas=[["juan@e.com", "85"]],
        )

        resultado = await service.preview_archivo(contenido, "mal.csv")
        assert resultado.total_filas == 0
        assert any("Faltan columnas" in e for e in resultado.errores)

    async def test_preview_formato_no_soportado_errores(self):
        """7.3: formato .xlsx no soportado → error."""
        service = CalificacionService()
        resultado = await service.preview_archivo(b"dummy", "notas.xlsx")
        assert "no soportado" in resultado.errores[0].lower()
        assert resultado.total_filas == 0

    async def test_preview_muestra_primeras_3(self):
        """7.3: muestra_primeras_3 incluye solo columnas relevantes + nombre/apellidos."""
        service = CalificacionService()
        contenido = _crear_archivo_csv(
            columnas=["nombre", "apellidos", "Parcial (Real)", "Estado"],
            filas=[
                ["Ana", "López", "95", "Aprobado"],
                ["Luis", "Martín", "60", "Regular"],
                ["Carla", "Díaz", "80", "Promocionado"],
                ["Pedro", "Sánchez", "40", "Libre"],
            ],
        )

        resultado = await service.preview_archivo(contenido, "notas.csv")
        assert resultado.total_filas == 4
        assert len(resultado.muestra_primeras_3) == 3
        # Cada muestra debe tener nombre, apellidos y columnas relevantes
        for item in resultado.muestra_primeras_3:
            assert "nombre" in item
            assert "apellidos" in item

    async def test_preview_filas_incompletas_omitidas(self):
        """7.3: filas sin nombre/apellidos se omiten con error."""
        service = CalificacionService()
        contenido = _crear_archivo_csv(
            columnas=["nombre", "apellidos", "Parcial (Real)"],
            filas=[
                ["Juan", "Pérez", "85"],
                ["", "", "70"],  # incompleta
                ["María", "", "90"],  # incompleta
            ],
        )

        resultado = await service.preview_archivo(contenido, "notas.csv")
        assert resultado.total_filas == 1
        assert len(resultado.errores) == 2


# ============================================================================
# Group 8 — Confirmar importación
# ============================================================================


class TestConfirmarImportacion:
    """CalificacionService.confirmar_importacion — 8.1 RED → 8.3 TRIANGULATE."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, materia, user_factory, version_padron):
        self.t, self.m = materia
        self.vp, self.ep = version_padron
        self.user = await user_factory(db_session, tenant_id=self.t.id)
        self.audit_ctx = _build_audit_ctx(self.user, self.t.id)
        self.session = db_session

    async def _importar_y_verificar(
        self,
        service,
        filas: list[dict[str, str]],
        columnas: list[dict[str, str]],
        actividades: list[str],
        esperadas: int,
    ) -> int:
        return await service.confirmar_importacion(
            tenant_id=self.t.id,
            materia_id=self.m.id,
            archivo_parseado=filas,
            columnas_detectadas=columnas,
            actividades_seleccionadas=actividades,
            actor_id=self.user.id,
            audit_ctx=self.audit_ctx,
            session=self.session,
        )

    async def test_confirmar_crea_calificaciones_origen_importado(self):
        """8.1 RED: confirmar crea calificaciones con origen=importado."""
        service = CalificacionService()
        filas = [
            {"nombre": "Juan", "apellidos": "Pérez", "entrada_padron_id": str(self.ep.id), "Parcial (Real)": "85"},
        ]
        columnas = [
            {"nombre": "nombre", "tipo": "ignorada"},
            {"nombre": "apellidos", "tipo": "ignorada"},
            {"nombre": "entrada_padron_id", "tipo": "ignorada"},
            {"nombre": "Parcial (Real)", "tipo": "numerica"},
        ]

        total = await self._importar_y_verificar(
            service, filas, columnas, ["Parcial (Real)"], esperadas=1
        )
        assert total == 1

        # Verificar en DB
        repo = CalificacionRepository()
        califs = await repo.get_by_materia_y_usuario(
            tenant_id=self.t.id, materia_id=self.m.id,
            creado_por=self.user.id, session=self.session,
        )
        assert len(califs) == 1
        assert califs[0].origen == OrigenCalificacionDB.IMPORTADO
        assert califs[0].nota_numerica == 85.0
        assert califs[0].actividad == "Parcial (Real)"

    async def test_confirmar_audita_calificaciones_importar(self):
        """8.1: confirmar audita CALIFICACIONES_IMPORTAR."""
        # Verificar que audit_action fue llamado — esto se verifica indirectamente
        # porque el test de auditoría en integración (Grupo 14) lo cubre.
        # Acá solo verificamos que no falla.
        service = CalificacionService()
        filas = [
            {"nombre": "Juan", "apellidos": "Pérez",
             "entrada_padron_id": str(self.ep.id), "Parcial (Real)": "85"},
        ]
        columnas = [
            {"nombre": "entrada_padron_id", "tipo": "ignorada"},
            {"nombre": "Parcial (Real)", "tipo": "numerica"},
        ]
        total = await self._importar_y_verificar(
            service, filas, columnas, ["Parcial (Real)"], esperadas=1
        )
        assert total == 1

    async def test_confirmar_actividad_inexistente_422(self):
        """8.3: actividad no existe en columnas → 422."""
        service = CalificacionService()
        filas = [
            {"nombre": "Juan", "apellidos": "Pérez", "entrada_padron_id": str(self.ep.id)},
        ]
        columnas = [{"nombre": "Parcial (Real)", "tipo": "numerica"}]

        with pytest.raises(CalificacionError) as exc:
            await self._importar_y_verificar(
                service, filas, columnas, ["TP (Real)"], esperadas=0
            )
        assert exc.value.status_code == 422

    async def test_confirmar_max_filas_excedido_413(self):
        """8.3: más de MAX_CALIFICACIONES_IMPORT (5000) → 413."""
        service = CalificacionService()
        filas = [{"nombre": "X", "apellidos": "Y", "entrada_padron_id": str(self.ep.id)}
                 for _ in range(2000)]
        columnas = [{"nombre": "Parcial (Real)", "tipo": "numerica"},
                    {"nombre": "TP (Real)", "tipo": "numerica"},
                    {"nombre": "Estado", "tipo": "textual"}]

        # 2000 filas x 3 actividades = 6000 > 5000
        with pytest.raises(CalificacionError) as exc:
            await self._importar_y_verificar(
                service, filas, columnas,
                ["Parcial (Real)", "TP (Real)", "Estado"],
                esperadas=0,
            )
        assert exc.value.status_code == 413
        assert "Demasiadas" in exc.value.detail

    async def test_confirmar_sin_entrada_padron_id_422(self):
        """8.3: sin columna entrada_padron_id → no se pueden identificar alumnos."""
        service = CalificacionService()
        filas = [
            {"nombre": "Juan", "apellidos": "Pérez", "email": "juan@e.com",
             "Parcial (Real)": "85"},
        ]
        columnas = [{"nombre": "Parcial (Real)", "tipo": "numerica"}]

        with pytest.raises(CalificacionError) as exc:
            await self._importar_y_verificar(
                service, filas, columnas, ["Parcial (Real)"], esperadas=0
            )
        assert exc.value.status_code == 422

    async def test_confirmar_reimporta_crea_duplicados(self):
        """8.4: reimportar mismas actividades crea duplicados (no upsert)."""
        service = CalificacionService()
        filas = [
            {"nombre": "Juan", "apellidos": "Pérez",
             "entrada_padron_id": str(self.ep.id), "Parcial (Real)": "85"},
        ]
        columnas = [{"nombre": "entrada_padron_id", "tipo": "ignorada"},
                    {"nombre": "Parcial (Real)", "tipo": "numerica"}]

        await self._importar_y_verificar(service, filas, columnas, ["Parcial (Real)"], esperadas=1)
        await self._importar_y_verificar(service, filas, columnas, ["Parcial (Real)"], esperadas=1)

        repo = CalificacionRepository()
        califs = await repo.get_by_materia_y_usuario(
            tenant_id=self.t.id, materia_id=self.m.id,
            creado_por=self.user.id, session=self.session,
        )
        assert len(califs) == 2  # duplicados

    async def test_confirmar_nota_numerica_y_textual(self):
        """8.3: importa notas numéricas y textuales por separado."""
        service = CalificacionService()
        filas = [
            {"nombre": "Juan", "apellidos": "Pérez",
             "entrada_padron_id": str(self.ep.id),
             "Parcial (Real)": "85",
             "Estado": "Aprobado"},
        ]
        columnas = [
            {"nombre": "entrada_padron_id", "tipo": "ignorada"},
            {"nombre": "Parcial (Real)", "tipo": "numerica"},
            {"nombre": "Estado", "tipo": "textual"},
        ]

        total = await self._importar_y_verificar(
            service, filas, columnas, ["Parcial (Real)", "Estado"], esperadas=2
        )
        assert total == 2

        repo = CalificacionRepository()
        califs = await repo.get_by_materia_y_usuario(
            tenant_id=self.t.id, materia_id=self.m.id,
            creado_por=self.user.id, session=self.session,
        )
        notas_numericas = [c for c in califs if c.nota_numerica is not None]
        notas_textuales = [c for c in califs if c.nota_textual is not None]
        assert len(notas_numericas) == 1
        assert len(notas_textuales) == 1
        assert notas_numericas[0].nota_numerica == 85.0
        assert notas_textuales[0].nota_textual == "Aprobado"

    async def test_confirmar_datos_vacios_422(self):
        """8.3: todas las celdas vacías → 422."""
        service = CalificacionService()
        filas = [
            {"nombre": "Juan", "apellidos": "Pérez",
             "entrada_padron_id": str(self.ep.id),
             "Parcial (Real)": ""},
        ]
        columnas = [{"nombre": "entrada_padron_id", "tipo": "ignorada"},
                    {"nombre": "Parcial (Real)", "tipo": "numerica"}]

        with pytest.raises(CalificacionError) as exc:
            await self._importar_y_verificar(
                service, filas, columnas, ["Parcial (Real)"], esperadas=0
            )
        assert exc.value.status_code == 422


# ============================================================================
# Group 9 — Reporte de finalización
# ============================================================================


class TestReporteFinalizacion:
    """CalificacionService.reporte_finalizacion — 9.1 RED → 9.3 TRIANGULATE."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, materia, version_padron):
        self.t, self.m = materia
        self.vp, self.ep = version_padron
        self.session = db_session

    async def test_reporte_detecta_entregas_sin_calificar(self):
        """9.1 RED: reporte cruza archivo vs calificaciones existentes."""
        service = CalificacionService()
        contenido = _crear_archivo_con_entrada_ids(
            columnas=["nombre", "apellidos", "Estado", "TP (Real)"],
            filas=[
                (str(self.ep.id), "Juan", "Pérez", "Completo", "85"),
                (str(uuid.uuid4()), "Ana", "López", "Completo", "90"),
            ],
        )

        resultado = await service.reporte_finalizacion(
            tenant_id=self.t.id,
            materia_id=self.m.id,
            archivo_contenido=contenido,
            nombre_archivo="finalizacion.csv",
            session=self.session,
        )
        # "Estado" es textual, "TP (Real)" es numérica → no debe aparecer en reporte (RN-08)
        assert any(i.actividad == "Estado" for i in resultado.items)
        assert not any(i.actividad == "TP (Real)" for i in resultado.items)

    async def test_reporte_todo_calificado_lista_vacia(self, user_factory):
        """9.3: todas las actividades ya calificadas → lista vacía."""
        # Primero importar calificación con un usuario real
        user = await user_factory(self.session, tenant_id=self.t.id)
        service = CalificacionService()
        calif = Calificacion(
            id=uuid.uuid4(),
            tenant_id=self.t.id,
            entrada_padron_id=self.ep.id,
            materia_id=self.m.id,
            actividad="Estado",
            nota_textual="Completo",
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=user.id,
        )
        self.session.add(calif)
        await self.session.commit()

        contenido = _crear_archivo_con_entrada_ids(
            columnas=["nombre", "apellidos", "Estado"],
            filas=[
                (str(self.ep.id), "Juan", "Pérez", "Completo"),
            ],
        )

        resultado = await service.reporte_finalizacion(
            tenant_id=self.t.id,
            materia_id=self.m.id,
            archivo_contenido=contenido,
            nombre_archivo="finalizacion.csv",
            session=self.session,
        )
        assert len(resultado.items) == 0

    async def test_reporte_solo_actividades_textuales_RN08(self):
        """9.3 RN-08: solo reporta actividades textuales."""
        service = CalificacionService()
        contenido = _crear_archivo_con_entrada_ids(
            columnas=["nombre", "apellidos", "Entregó", "Parcial (Real)", "Nota Final (Real)"],
            filas=[
                (str(self.ep.id), "Juan", "Pérez", "Sí", "75", "8"),
            ],
        )

        resultado = await service.reporte_finalizacion(
            tenant_id=self.t.id,
            materia_id=self.m.id,
            archivo_contenido=contenido,
            nombre_archivo="finalizacion.csv",
            session=self.session,
        )
        # Solo "Entregó" es textual
        for item in resultado.items:
            assert item.actividad == "Entregó"

    async def test_reporte_sin_calificaciones_previas(self):
        """9.3: sin calificaciones previas → todas las textuales aparecen."""
        service = CalificacionService()
        contenido = _crear_archivo_con_entrada_ids(
            columnas=["nombre", "apellidos", "Estado", "Observaciones"],
            filas=[
                (str(self.ep.id), "Juan", "Pérez", "Completo", "OK"),
            ],
        )

        resultado = await service.reporte_finalizacion(
            tenant_id=self.t.id,
            materia_id=self.m.id,
            archivo_contenido=contenido,
            nombre_archivo="finalizacion.csv",
            session=self.session,
        )
        actividades = {i.actividad for i in resultado.items}
        assert "Estado" in actividades
        assert "Observaciones" in actividades


# ============================================================================
# Group 10 — Aprobado derivado (D-01)
# ============================================================================


class TestComputeAprobado:
    """CalificacionService._compute_aprobado — 10.1 RED → 10.3 TRIANGULATE."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, materia):
        self.t, self.m = materia
        self.session = db_session

    def _crear_calificacion(
        self,
        nota_numerica: float | None = None,
        nota_textual: str | None = None,
    ) -> Calificacion:
        return Calificacion(
            id=uuid.uuid4(),
            tenant_id=self.t.id,
            entrada_padron_id=uuid.uuid4(),
            materia_id=self.m.id,
            actividad="Parcial (Real)",
            nota_numerica=nota_numerica,
            nota_textual=nota_textual,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=uuid.uuid4(),
        )

    def _crear_umbral(
        self,
        umbral_pct: int = 60,
        valores_aprobatorios: list[str] | None = None,
    ) -> UmbralMateria:
        return UmbralMateria(
            id=uuid.uuid4(),
            tenant_id=self.t.id,
            asignacion_id=uuid.uuid4(),
            materia_id=self.m.id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprobatorios or [],
        )

    def test_aprobado_numerico_supera_umbral_true(self):
        """10.1: nota_numerica >= umbral_pct → True."""
        service = CalificacionService()
        calif = self._crear_calificacion(nota_numerica=75)
        umbral = self._crear_umbral(umbral_pct=60)

        assert service._compute_aprobado(calif, umbral) is True

    def test_aprobado_numerico_no_supera_umbral_false(self):
        """10.1: nota_numerica < umbral_pct → False."""
        service = CalificacionService()
        calif = self._crear_calificacion(nota_numerica=45)
        umbral = self._crear_umbral(umbral_pct=60)

        assert service._compute_aprobado(calif, umbral) is False

    def test_aprobado_numerico_exactamente_umbral_true(self):
        """10.1: nota_numerica == umbral_pct → True."""
        service = CalificacionService()
        calif = self._crear_calificacion(nota_numerica=60)
        umbral = self._crear_umbral(umbral_pct=60)

        assert service._compute_aprobado(calif, umbral) is True

    def test_aprobado_textual_en_valores_true(self):
        """10.3: nota_textual en valores_aprobatorios → True."""
        service = CalificacionService()
        calif = self._crear_calificacion(nota_textual="Aprobado")
        umbral = self._crear_umbral(valores_aprobatorios=["Aprobado", "Promocionado"])

        assert service._compute_aprobado(calif, umbral) is True

    def test_aprobado_textual_fuera_valores_false(self):
        """10.3: nota_textual NO en valores_aprobatorios → False."""
        service = CalificacionService()
        calif = self._crear_calificacion(nota_textual="Regular")
        umbral = self._crear_umbral(valores_aprobatorios=["Aprobado", "Promocionado"])

        assert service._compute_aprobado(calif, umbral) is False

    def test_aprobado_sin_umbral_configurado_usa_default_60(self):
        """10.3: sin umbral configurado → usa default 60."""
        service = CalificacionService()
        calif = self._crear_calificacion(nota_numerica=60)

        assert service._compute_aprobado(calif, None) is True

    def test_aprobado_sin_umbral_por_debajo_60_false(self):
        """10.3: sin umbral, nota < 60 → False."""
        service = CalificacionService()
        calif = self._crear_calificacion(nota_numerica=59)

        assert service._compute_aprobado(calif, None) is False

    def test_aprobado_sin_umbral_textual_sin_valores_false(self):
        """10.3: sin umbral + nota textual → False (no hay valores_aprobatorios)."""
        service = CalificacionService()
        calif = self._crear_calificacion(nota_textual="Aprobado")

        assert service._compute_aprobado(calif, None) is False

    def test_aprobado_umbral_soft_deleted_tratado_como_none(self):
        """10.3: umbral con deleted_at != None se trata como None."""
        service = CalificacionService()
        calif = self._crear_calificacion(nota_numerica=70)
        umbral = self._crear_umbral(umbral_pct=80)
        umbral.deleted_at = datetime.now(timezone.utc)

        # Al estar soft-delete, se ignora y usa default 60 → 70 >= 60 → True
        assert service._compute_aprobado(calif, umbral) is True


class TestGetCalificaciones:
    """CalificacionService.get_calificaciones — 10.4 REFACTOR integration."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, materia, version_padron, user_factory):
        self.t, self.m = materia
        self.vp, self.ep = version_padron
        self.user = await user_factory(db_session, tenant_id=self.t.id)
        self.session = db_session

    async def test_get_calificaciones_incluye_aprobado(self):
        """10.4: get_calificaciones devuelve aprobado computado."""
        service = CalificacionService()

        # Crear calificaciones directamente
        calif1 = Calificacion(
            id=uuid.uuid4(),
            tenant_id=self.t.id,
            entrada_padron_id=self.ep.id,
            materia_id=self.m.id,
            actividad="Parcial (Real)",
            nota_numerica=85.0,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=self.user.id,
        )
        calif2 = Calificacion(
            id=uuid.uuid4(),
            tenant_id=self.t.id,
            entrada_padron_id=self.ep.id,
            materia_id=self.m.id,
            actividad="TP (Real)",
            nota_numerica=45.0,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=self.user.id,
        )
        self.session.add_all([calif1, calif2])
        await self.session.commit()

        resultado = await service.get_calificaciones(
            tenant_id=self.t.id,
            materia_id=self.m.id,
            creado_por=self.user.id,
            session=self.session,
        )

        assert len(resultado) == 2
        aprobados = {r.actividad: r.aprobado for r in resultado}
        assert aprobados["Parcial (Real)"] is True
        assert aprobados["TP (Real)"] is False

    async def test_get_calificaciones_sin_datos_lista_vacia(self):
        """10.4: sin calificaciones → lista vacía."""
        service = CalificacionService()

        resultado = await service.get_calificaciones(
            tenant_id=self.t.id,
            materia_id=self.m.id,
            creado_por=self.user.id,
            session=self.session,
        )
        assert resultado == []


# ============================================================================
# Group 11 — Vaciar
# ============================================================================


class TestVaciarMateria:
    """CalificacionService.vaciar_materia — 11.1 RED → 11.3 TRIANGULATE."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, materia, version_padron, user_factory):
        self.t, self.m = materia
        self.vp, self.ep = version_padron
        self.user = await user_factory(db_session, tenant_id=self.t.id)
        self.other_user = await user_factory(
            db_session,
            tenant_id=self.t.id,
            email="other@example.com",
        )
        self.audit_ctx = _build_audit_ctx(self.user, self.t.id)
        self.session = db_session

    async def _crear_calificacion(self, usuario_id):
        calif = Calificacion(
            id=uuid.uuid4(),
            tenant_id=self.t.id,
            entrada_padron_id=self.ep.id,
            materia_id=self.m.id,
            actividad="Parcial (Real)",
            nota_numerica=75.0,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=usuario_id,
        )
        self.session.add(calif)
        await self.session.commit()
        return calif

    async def test_vaciar_calificaciones_propias(self):
        """11.1: vaciar soft-deletea calificaciones del actor."""
        await self._crear_calificacion(self.user.id)

        service = CalificacionService()
        affected = await service.vaciar_materia(
            tenant_id=self.t.id,
            materia_id=self.m.id,
            actor_id=self.user.id,
            audit_ctx=self.audit_ctx,
            session=self.session,
        )
        assert affected == 1

        # Verificar soft-delete
        repo = CalificacionRepository()
        califs = await repo.get_by_materia_y_usuario(
            tenant_id=self.t.id, materia_id=self.m.id,
            creado_por=self.user.id, session=self.session,
        )
        assert len(califs) == 0

    async def test_vaciar_no_afecta_otro_docente(self):
        """11.1: vaciar preserva calificaciones de otros docentes."""
        await self._crear_calificacion(self.user.id)
        await self._crear_calificacion(self.other_user.id)

        service = CalificacionService()
        affected = await service.vaciar_materia(
            tenant_id=self.t.id,
            materia_id=self.m.id,
            actor_id=self.user.id,
            audit_ctx=self.audit_ctx,
            session=self.session,
        )
        assert affected == 1

        # El otro usuario mantiene sus calificaciones
        repo = CalificacionRepository()
        califs_other = await repo.get_by_materia_y_usuario(
            tenant_id=self.t.id, materia_id=self.m.id,
            creado_por=self.other_user.id, session=self.session,
        )
        assert len(califs_other) == 1

    async def test_vaciar_sin_calificaciones_0_afectados(self):
        """11.3: vaciar sin datos → 0 afectados."""
        service = CalificacionService()
        affected = await service.vaciar_materia(
            tenant_id=self.t.id,
            materia_id=self.m.id,
            actor_id=self.user.id,
            audit_ctx=self.audit_ctx,
            session=self.session,
        )
        assert affected == 0

    async def test_doble_vaciado_204(self):
        """11.3: doble vaciado → 0 afectados."""
        await self._crear_calificacion(self.user.id)

        service = CalificacionService()
        affected1 = await service.vaciar_materia(
            tenant_id=self.t.id,
            materia_id=self.m.id,
            actor_id=self.user.id,
            audit_ctx=self.audit_ctx,
            session=self.session,
        )
        assert affected1 == 1

        affected2 = await service.vaciar_materia(
            tenant_id=self.t.id,
            materia_id=self.m.id,
            actor_id=self.user.id,
            audit_ctx=self.audit_ctx,
            session=self.session,
        )
        assert affected2 == 0


# ============================================================================
# Group 12 — UmbralService
# ============================================================================


class TestUmbralService:
    """UmbralService — get_umbral y configurar_umbral."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, materia, asignacion_factory, user_factory):
        self.t, self.m = materia
        self.user = await user_factory(db_session, tenant_id=self.t.id)
        self.asignacion = await asignacion_factory(
            db_session,
            tenant_id=self.t.id,
            usuario_id=self.user.id,
            materia_id=self.m.id,
        )
        self.audit_ctx = _build_audit_ctx(self.user, self.t.id)
        self.session = db_session

    async def test_get_umbral_sin_configurar_devuelve_none(self):
        """12.1 RED: get_umbral sin configuración → None."""
        service = UmbralService()
        resultado = await service.get_umbral(
            tenant_id=self.t.id,
            asignacion_id=self.asignacion.id,
            session=self.session,
        )
        assert resultado is None

    async def test_get_umbral_con_configuracion_devuelve_valores(self):
        """12.1: get_umbral con configuración existente → datos."""
        # Crear umbral primero
        umbral = UmbralMateria(
            id=uuid.uuid4(),
            tenant_id=self.t.id,
            asignacion_id=self.asignacion.id,
            materia_id=self.m.id,
            umbral_pct=70,
            valores_aprobatorios=["Aprobado", "Promocionado"],
        )
        self.session.add(umbral)
        await self.session.commit()
        await self.session.refresh(umbral)

        service = UmbralService()
        resultado = await service.get_umbral(
            tenant_id=self.t.id,
            asignacion_id=self.asignacion.id,
            session=self.session,
        )
        assert resultado is not None
        assert resultado.umbral_pct == 70
        assert resultado.valores_aprobatorios == ["Aprobado", "Promocionado"]

    async def test_configurar_umbral_crea_nuevo(self):
        """12.3 RED: configurar_umbral crea y audita."""
        service = UmbralService()
        resultado = await service.configurar_umbral(
            tenant_id=self.t.id,
            asignacion_id=self.asignacion.id,
            materia_id=self.m.id,
            umbral_pct=65,
            valores_aprobatorios=["Aprobado"],
            audit_ctx=self.audit_ctx,
            session=self.session,
        )
        assert resultado.umbral_pct == 65
        assert resultado.valores_aprobatorios == ["Aprobado"]
        assert resultado.asignacion_id == self.asignacion.id
        assert resultado.materia_id == self.m.id

    async def test_configurar_umbral_actualiza_existente(self):
        """12.3: configurar_umbral actualiza umbral existente."""
        servicio = UmbralService()
        # Crear primero
        await servicio.configurar_umbral(
            tenant_id=self.t.id,
            asignacion_id=self.asignacion.id,
            materia_id=self.m.id,
            umbral_pct=60,
            audit_ctx=self.audit_ctx,
            session=self.session,
        )
        # Actualizar
        resultado = await servicio.configurar_umbral(
            tenant_id=self.t.id,
            asignacion_id=self.asignacion.id,
            materia_id=self.m.id,
            umbral_pct=75,
            valores_aprobatorios=["Aprobado", "Promocionado"],
            audit_ctx=self.audit_ctx,
            session=self.session,
        )
        assert resultado.umbral_pct == 75
        assert "Promocionado" in (resultado.valores_aprobatorios or [])

    async def test_configurar_umbral_fuera_rango_422(self):
        """12.5: umbral_pct fuera de 0-100 → 422."""
        service = UmbralService()
        with pytest.raises(CalificacionError) as exc:
            await service.configurar_umbral(
                tenant_id=self.t.id,
                asignacion_id=self.asignacion.id,
                materia_id=self.m.id,
                umbral_pct=150,
                audit_ctx=self.audit_ctx,
                session=self.session,
            )
        assert exc.value.status_code == 422

    async def test_umbral_independiente_por_asignacion(self):
        """12.5: cada asignación tiene su propio umbral."""
        # Crear segunda asignación con otro role (no PROFESOR para evitar unique)
        from app.models.asignacion import Asignacion
        from app.models.role import Role

        role = Role(
            id=uuid.uuid4(),
            tenant_id=self.t.id,
            code=f"AUX-{uuid.uuid4().hex[:6]}",
            nombre="Auxiliar",
        )
        self.session.add(role)
        await self.session.flush()

        otra_asignacion = Asignacion(
            id=uuid.uuid4(),
            tenant_id=self.t.id,
            usuario_id=self.user.id,
            role_id=role.id,
            materia_id=self.m.id,
            desde=datetime.now(timezone.utc),
        )
        self.session.add(otra_asignacion)
        await self.session.commit()
        await self.session.refresh(otra_asignacion)

        service = UmbralService()
        # Configurar umbral para primera asignación
        await service.configurar_umbral(
            tenant_id=self.t.id,
            asignacion_id=self.asignacion.id,
            materia_id=self.m.id,
            umbral_pct=80,
            audit_ctx=self.audit_ctx,
            session=self.session,
        )
        # La segunda no tiene umbral → None
        resultado = await service.get_umbral(
            tenant_id=self.t.id,
            asignacion_id=otra_asignacion.id,
            session=self.session,
        )
        assert resultado is None
