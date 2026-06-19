from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.fecha_academica_repository import FechaAcademicaRepository
from app.repositories.materia_repository import MateriaRepository
from app.repositories.cohorte_repository import CohorteRepository
from app.models.fecha_academica import FechaAcademica, TipoFechaAcademica


class FechaAcademicaError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def build_lms_fragment(fechas: list[FechaAcademica]) -> str:
    """Genera un fragmento de texto con las evaluaciones ordenadas por fecha.

    Args:
        fechas: Lista de FechaAcademica (puede estar desordenada).

    Returns:
        Texto con el listado de evaluaciones, o "Sin evaluaciones registradas"
        si la lista está vacía.
    """
    if not fechas:
        return "Sin evaluaciones registradas"

    sorted_fechas = sorted(fechas, key=lambda f: f.fecha)
    lines: list[str] = []
    for f in sorted_fechas:
        fecha_str = f.fecha.strftime("%d/%m/%Y") if hasattr(f.fecha, "strftime") else str(f.fecha)
        tipo_val = f.tipo.value if hasattr(f.tipo, 'value') else f.tipo
        lines.append(f"- [{tipo_val} #{f.numero}] {f.titulo} — {fecha_str}")
    return "\n".join(lines)


class FechaAcademicaService:
    def __init__(
        self,
        repo: FechaAcademicaRepository | None = None,
        materia_repo: MateriaRepository | None = None,
        cohorte_repo: CohorteRepository | None = None,
    ) -> None:
        self._repo = repo or FechaAcademicaRepository()
        self._materia_repo = materia_repo or MateriaRepository()
        self._cohorte_repo = cohorte_repo or CohorteRepository()

    async def _validate_entities(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID,
        session: AsyncSession,
    ) -> None:
        materia = await self._materia_repo.get(id=materia_id, tenant_id=tenant_id, session=session)
        if materia is None:
            raise FechaAcademicaError(status_code=404, detail="materia not found")
        cohorte = await self._cohorte_repo.get(id=cohorte_id, tenant_id=tenant_id, session=session)
        if cohorte is None:
            raise FechaAcademicaError(status_code=404, detail="cohorte not found")

    async def create(
        self,
        *,
        tenant_id: UUID,
        data: dict,
        session: AsyncSession,
    ) -> FechaAcademica:
        materia_id = UUID(data["materia_id"])
        cohorte_id = UUID(data["cohorte_id"])
        tipo_str = data["tipo"]

        # Validate enum
        try:
            tipo = TipoFechaAcademica(tipo_str)
        except ValueError as exc:
            raise FechaAcademicaError(status_code=422, detail=f"invalid tipo: {tipo_str}") from exc

        await self._validate_entities(
            tenant_id=tenant_id, materia_id=materia_id, cohorte_id=cohorte_id, session=session,
        )

        # Check duplicate
        existente = await self._repo.get_by_instance(
            tenant_id=tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            tipo=tipo_str,
            numero=data["numero"],
            session=session,
        )
        if existente is not None:
            raise FechaAcademicaError(status_code=409, detail="fecha already exists for this tipo+numero")

        fecha_str = data["fecha"]
        if isinstance(fecha_str, str):
            fecha_dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
        else:
            fecha_dt = fecha_str

        obj = FechaAcademica(
            tenant_id=tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            tipo=tipo,
            numero=data["numero"],
            periodo=data["periodo"],
            fecha=fecha_dt,
            titulo=data["titulo"],
        )
        return await self._repo.create(obj=obj, session=session)

    async def get(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        session: AsyncSession,
    ) -> FechaAcademica | None:
        return await self._repo.get(id=id, tenant_id=tenant_id, session=session)

    async def update(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        data: dict,
        session: AsyncSession,
    ) -> FechaAcademica:
        obj = await self._repo.get(id=id, tenant_id=tenant_id, session=session)
        if obj is None:
            raise FechaAcademicaError(status_code=404, detail="not found")

        if "periodo" in data:
            obj.periodo = data["periodo"]
        if "fecha" in data:
            fecha_val = data["fecha"]
            if isinstance(fecha_val, str):
                obj.fecha = datetime.fromisoformat(fecha_val.replace("Z", "+00:00"))
            else:
                obj.fecha = fecha_val
        if "titulo" in data:
            obj.titulo = data["titulo"]
        await session.flush()
        await session.refresh(obj)
        return obj

    async def delete(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        session: AsyncSession,
    ) -> bool:
        return await self._repo.soft_delete(id=id, tenant_id=tenant_id, session=session)

    async def list_tabular(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        periodo: str | None = None,
        tipo: str | None = None,
    ) -> list[FechaAcademica]:
        return await self._repo.list(
            tenant_id=tenant_id,
            session=session,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            periodo=periodo,
            tipo=tipo,
        )

    async def list_calendario(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
    ) -> list[dict]:
        fechas = await self._repo.list(
            tenant_id=tenant_id,
            session=session,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            limit=200,
        )
        grouped: dict[str, list[FechaAcademica]] = {}
        for f in fechas:
            grouped.setdefault(f.periodo, []).append(f)
        result = [
            {"periodo": periodo, "fechas": sorted(fs, key=lambda x: x.fecha)}
            for periodo, fs in sorted(grouped.items())
        ]
        return result
