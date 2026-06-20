"""PadronService — núcleo de reglas de negocio del módulo de padrón.

Carga versionada de padrón por archivo o sync Moodle, preview de archivo,
confirmación de carga, vaciado y auditoría de operaciones.
"""

from __future__ import annotations

import csv
import io
import os
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext, audit_action
from app.core.security import encryption_service
from app.integrations.moodle_ws import MoodleWsClient, MoodleWsError
from app.models.padron import EntradaPadron, VersionPadron
from app.repositories.padron_repository import (
    EntradaPadronRepository,
    VersionPadronRepository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.padron import (
    ConfirmarRequest,
    ConfirmarResponse,
    EntradaPadronCreate,
    EntradaPadronPreview,
    MoodleSyncResponse,
    PreviewResponse,
    VersionPadronResponse,
)

# Límite máximo de filas por carga de padrón
_MAX_PADRON_ROWS = int(os.getenv("MAX_PADRON_ROWS", "2000"))


class PadronError(Exception):
    """Error de dominio en operaciones de padrón.

    Attributes:
        status_code: Código HTTP (400, 403, 404, 409, 413).
        detail: Descripción del error.
    """

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class PadronService:
    """Servicio de padrón versionado con ingesta por archivo y sync Moodle.

    Dependencias:
        - VersionPadronRepository: persistencia de versiones.
        - EntradaPadronRepository: persistencia de entradas.
        - MoodleWsClient: integración con Moodle WS (opcional).
    """

    COLUMNAS_REQUERIDAS = {"nombre", "apellidos", "email", "comision"}
    COLUMNAS_OPCIONALES = {"regional"}

    def __init__(
        self,
        version_repo: VersionPadronRepository | None = None,
        entrada_repo: EntradaPadronRepository | None = None,
        user_repo: UserRepository | None = None,
        moodle_client: MoodleWsClient | None = None,
    ) -> None:
        self._version_repo = version_repo or VersionPadronRepository()
        self._entrada_repo = entrada_repo or EntradaPadronRepository()
        self._user_repo = user_repo or UserRepository()
        self._moodle_client = moodle_client

    # ------------------------------------------------------------------
    # Preview de archivo
    # ------------------------------------------------------------------

    async def preview_archivo(
        self,
        contenido: bytes,
        nombre_archivo: str,
    ) -> PreviewResponse:
        """Procesa un archivo de padrón y devuelve un preview.

        Args:
            contenido: Contenido del archivo en bytes.
            nombre_archivo: Nombre del archivo (para detectar extensión).

        Returns:
            PreviewResponse con filas detectadas, columnas y muestra.

        Raises:
            PadronError: si el formato no es válido o faltan columnas.
        """
        filas, errores = self._parse_archivo(contenido, nombre_archivo)

        if errores and not filas:
            return PreviewResponse(
                total_filas=0,
                columnas_detectadas=[],
                muestra=[],
                errores=errores,
            )

        columnas = list(self.COLUMNAS_REQUERIDAS | self.COLUMNAS_OPCIONALES)
        # Las columnas reales son las que existen en los datos parseados
        if filas:
            columnas = list(filas[0].keys())

        muestra = [
            EntradaPadronPreview(**f) for f in filas[:5]
        ]

        return PreviewResponse(
            total_filas=len(filas),
            columnas_detectadas=columnas,
            muestra=muestra,
            errores=errores,
        )

    def _parse_archivo(
        self,
        contenido: bytes,
        nombre_archivo: str,
    ) -> tuple[list[dict], list[str]]:
        """Parsea un archivo .csv o .xlsx a lista de dicts.

        Args:
            contenido: Contenido del archivo en bytes.
            nombre_archivo: Nombre del archivo.

        Returns:
            Tupla (filas_parseadas, errores_de_validacion).
        """
        errores: list[str] = []
        lower = nombre_archivo.lower()

        if lower.endswith(".csv"):
            return self._parse_csv(contenido, errores)
        elif lower.endswith(".xlsx"):
            errores.append("Formato .xlsx no soportado aún. Usá .csv")
            return [], errores
        else:
            errores.append(f"Formato no soportado: {nombre_archivo}. Usá .csv")
            return [], errores

    def _parse_csv(
        self,
        contenido: bytes,
        errores: list[str],
    ) -> tuple[list[dict], list[str]]:
        """Parsea un archivo CSV a lista de dicts."""
        try:
            text = contenido.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = contenido.decode("latin-1")
            except UnicodeDecodeError:
                errores.append("No se pudo decodificar el archivo. Usá UTF-8.")
                return [], errores

        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            errores.append("El archivo CSV está vacío o no tiene encabezados.")
            return [], errores

        columnas_archivo = {c.strip().lower() for c in reader.fieldnames}
        faltantes = self.COLUMNAS_REQUERIDAS - columnas_archivo
        if faltantes:
            errores.append(
                f"Faltan columnas requeridas: {', '.join(sorted(faltantes))}"
            )
            return [], errores

        filas: list[dict] = []
        for i, row in enumerate(reader, start=1):
            fila = {
                k.strip().lower(): v.strip()
                for k, v in row.items()
                if v is not None
            }
            # Verificar que tenga las columnas requeridas con datos
            if all(fila.get(c) for c in self.COLUMNAS_REQUERIDAS):
                filas.append(fila)
            else:
                email = fila.get("email", f"fila {i}")
                errores.append(f"Fila {i} ({email}): datos incompletos, se omite")

        return filas, errores

    # ------------------------------------------------------------------
    # Confirmar carga
    # ------------------------------------------------------------------

    async def confirmar_carga(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID,
        entradas: list[EntradaPadronCreate],
        audit_ctx: AuditContext,
        session: AsyncSession,
        origen: str = "archivo",
    ) -> ConfirmarResponse:
        """Confirma la carga de un padrón: crea versión e inserta entradas.

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            cohorte_id: UUID de la cohorte.
            entradas: Lista de entradas a insertar.
            audit_ctx: Contexto de auditoría.
            session: Sesión async.
            origen: Origen de la carga ('archivo', 'moodle', 'manual').

        Returns:
            ConfirmarResponse con datos de la versión creada.

        Raises:
            PadronError: si validaciones fallan o límite excedido.
        """
        if len(entradas) > _MAX_PADRON_ROWS:
            raise PadronError(
                413,
                f"Demasiadas filas: {len(entradas)}. Máximo permitido: {_MAX_PADRON_ROWS}",
            )

        validar_materia_cohorte = await self._validar_materia_cohorte(
            tenant_id=tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            session=session,
        )
        if not validar_materia_cohorte:
            raise PadronError(404, "Materia o cohorte no encontrada")

        # Crear nueva versión activa (desactiva anterior automáticamente)
        version = await self._version_repo.activar_version(
            tenant_id=tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            origen=origen,
            total_entradas=len(entradas),
            session=session,
        )

        # Crear y cifrar entradas
        entradas_orm = []
        for e in entradas:
            email_cifrado = encryption_service.encrypt(e.email)
            entrada = EntradaPadron(
                tenant_id=tenant_id,
                version_padron_id=version.id,
                nombre=e.nombre,
                apellidos=e.apellidos,
                email_encrypted=email_cifrado,
                comision=e.comision,
                regional=e.regional,
                usuario_id=e.usuario_id,
            )
            entradas_orm.append(entrada)

        await self._entrada_repo.bulk_insert(
            entradas=entradas_orm,
            session=session,
        )

        # Auditar
        await audit_action(
            ctx=audit_ctx,
            accion=AuditCodes.PADRON_CARGAR,
            session=session,
            detalle={
                "version_id": str(version.id),
                "materia_id": str(materia_id),
                "cohorte_id": str(cohorte_id),
                "origen": origen,
                "total_entradas": len(entradas),
            },
            filas_afectadas=len(entradas),
            materia_id=materia_id,
        )

        return ConfirmarResponse(
            version_id=version.id,
            total_entradas=len(entradas),
            origen=origen,
        )

    # ------------------------------------------------------------------
    # Sync Moodle
    # ------------------------------------------------------------------

    async def sync_moodle(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID,
        audit_ctx: AuditContext,
        session: AsyncSession,
    ) -> MoodleSyncResponse:
        """Sincroniza el padrón desde Moodle Web Services.

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia (course id en Moodle).
            cohorte_id: UUID de la cohorte (group id en Moodle).
            audit_ctx: Contexto de auditoría.
            session: Sesión async.

        Returns:
            MoodleSyncResponse con resultado de la sincronización.

        Raises:
            PadronError: si Moodle no está disponible o error de sync.
        """
        if self._moodle_client is None:
            self._moodle_client = MoodleWsClient()

        try:
            alumnos = await self._moodle_client.get_padron(
                materia_id=str(materia_id),
                cohorte_id=str(cohorte_id),
            )
        except MoodleWsError as e:
            raise PadronError(e.status_code, e.detail)

        if not alumnos:
            # Crear versión vacía igualmente (para tracking)
            entradas: list[EntradaPadronCreate] = []
        else:
            entradas = [
                EntradaPadronCreate(
                    nombre=a["nombre"],
                    apellidos=a["apellidos"],
                    email=a["email"],
                    comision=a["comision"],
                    regional=a.get("regional"),
                )
                for a in alumnos
            ]

        resultado = await self.confirmar_carga(
            tenant_id=tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            entradas=entradas,
            audit_ctx=audit_ctx,
            session=session,
            origen="moodle",
        )

        return MoodleSyncResponse(
            version_id=resultado.version_id,
            total_sincronizadas=resultado.total_entradas,
        )

    # ------------------------------------------------------------------
    # Vaciar padrón
    # ------------------------------------------------------------------

    async def vaciar_materia(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        actor_id: UUID,
        scope_global: bool,
        audit_ctx: AuditContext,
        session: AsyncSession,
    ) -> None:
        """Vacía el padrón de una materia (soft-delete de la versión activa).

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            actor_id: UUID del usuario que ejecuta la operación.
            scope_global: True si el usuario tiene alcance global (COORDINADOR).
            audit_ctx: Contexto de auditoría.
            session: Sesión async.

        Raises:
            PadronError: si no hay versión activa, o no tiene permiso.
        """
        # Si no tiene scope global, validar asignación a la materia
        if not scope_global:
            tiene_asignacion = await self._validar_asignacion_materia(
                tenant_id=tenant_id,
                usuario_id=actor_id,
                materia_id=materia_id,
                session=session,
            )
            if not tiene_asignacion:
                raise PadronError(403, "No tenés asignación vigente a esta materia")

        # Buscar versión activa específica de la materia (cualquier cohorte)
        versiones = await self._version_repo.list_versiones(
            tenant_id=tenant_id,
            session=session,
            materia_id=materia_id,
        )
        version_activa = next(
            (v for v in versiones if v.activa and v.deleted_at is None),
            None,
        )

        if version_activa is None:
            raise PadronError(404, "No hay padrón activo para esta materia")

        if version_activa.deleted_at is not None:
            raise PadronError(409, "El padrón de esta materia ya fue vaciado")

        ok = await self._version_repo.soft_delete_version(
            version_id=version_activa.id,
            tenant_id=tenant_id,
            session=session,
        )

        if not ok:
            raise PadronError(404, "No se encontró la versión activa")

        await audit_action(
            ctx=audit_ctx,
            accion=AuditCodes.PADRON_VACIAR,
            session=session,
            detalle={
                "version_id": str(version_activa.id),
                "materia_id": str(materia_id),
            },
            filas_afectadas=version_activa.total_entradas,
            materia_id=materia_id,
        )

    # ------------------------------------------------------------------
    # Listar versiones
    # ------------------------------------------------------------------

    async def list_versiones(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
    ) -> list[VersionPadronResponse]:
        """Lista versiones de padrón del tenant.

        Args:
            tenant_id: UUID del tenant.
            session: Sesión async.
            materia_id: Filtrar por materia (opcional).
            cohorte_id: Filtrar por cohorte (opcional).

        Returns:
            Lista de VersionPadronResponse.
        """
        versiones = await self._version_repo.list_versiones(
            tenant_id=tenant_id,
            session=session,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
        )
        return [
            VersionPadronResponse(
                id=v.id,
                materia_id=v.materia_id,
                cohorte_id=v.cohorte_id,
                activa=v.activa,
                total_entradas=v.total_entradas,
                origen=v.origen,
                created_at=v.created_at,
            )
            for v in versiones
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _validar_materia_cohorte(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Valida que materia y cohorte existan y pertenezcan al tenant."""
        from app.models.cohorte import Cohorte
        from app.models.materia import Materia
        from sqlalchemy import select

        stmt_m = select(Materia.id).where(
            Materia.id == materia_id,
            Materia.tenant_id == tenant_id,
            Materia.deleted_at.is_(None),
        )
        stmt_c = select(Cohorte.id).where(
            Cohorte.id == cohorte_id,
            Cohorte.tenant_id == tenant_id,
            Cohorte.deleted_at.is_(None),
        )
        result_m = await session.execute(stmt_m)
        result_c = await session.execute(stmt_c)
        return result_m.scalar_one_or_none() is not None and result_c.scalar_one_or_none() is not None

    async def _validar_asignacion_materia(
        self,
        *,
        tenant_id: UUID,
        usuario_id: UUID,
        materia_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Valida que el usuario tenga asignación vigente a la materia."""
        from app.models.asignacion import Asignacion
        from sqlalchemy import select

        stmt = select(Asignacion.id).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.usuario_id == usuario_id,
            Asignacion.materia_id == materia_id,
            Asignacion.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None
