"""CalificacionService — calificaciones, umbral y trazabilidad de aprobación.

Reglas de negocio cubiertas:
- RN-01: columna numérica si header termina en "(Real)"
- RN-02: columna textual si NO termina en "(Real)"
- RN-03: umbral_pct default = 60
- RN-04: vaciado scoped al usuario (soft-delete con deleted_by)
- RN-08: reporte de finalización SOLO para actividades textuales
- D-01: ``aprobado`` se deriva en read-time (no se almacena)
"""

from __future__ import annotations

import csv
import io
import os
import re
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext, audit_action
from app.models.calificacion import Calificacion, OrigenCalificacionDB, UmbralMateria
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.umbral_repository import UmbralRepository
from app.schemas.calificacion import (
    CalificacionResponse,
    PreviewResponse,
    ReporteFinalizacionItem,
    ReporteFinalizacionResponse,
    UmbralMateriaResponse,
)

# Límite máximo de filas por importación
_MAX_CALIFICACIONES_IMPORT = int(os.getenv("MAX_CALIFICACIONES_IMPORT", "5000"))
# Default global de umbral si no hay configuración
_DEFAULT_UMBRAL_PCT = 60


class CalificacionError(Exception):
    """Error de dominio en operaciones de calificaciones.

    Attributes:
        status_code: Código HTTP (400, 403, 404, 409, 413, 422).
        detail: Descripción del error.
    """

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class CalificacionService:
    """Servicio de calificaciones con preview, importación, reporte y vaciado.

    Dependencias:
        - CalificacionRepository: persistencia de calificaciones.
        - UmbralRepository: persistencia de umbrales (opcional).
    """

    PATRON_NUMERICA = re.compile(r"\(Real\)\s*$", re.IGNORECASE)
    PATRON_TEXTUAL = re.compile(
        r"(aprobado|estado|condicion|resultado|calificacion_cualitativa)",
        re.IGNORECASE,
    )
    COLUMNAS_IGNORADAS = {
        "nombre", "apellidos", "email", "comision", "legajo", "dni",
        "entrada_padron_id", "id_alumno", "alumno_id", "uuid",
    }

    COLUMNAS_REQUERIDAS_ALUMNO = {"nombre", "apellidos"}

    def __init__(
        self,
        calificacion_repo: CalificacionRepository | None = None,
        umbral_repo: UmbralRepository | None = None,
    ) -> None:
        self._calificacion_repo = calificacion_repo or CalificacionRepository()
        self._umbral_repo = umbral_repo or UmbralRepository()

    # ------------------------------------------------------------------
    # Group 7 — Preview archivo
    # ------------------------------------------------------------------

    async def preview_archivo(
        self,
        contenido: bytes,
        nombre_archivo: str,
    ) -> PreviewResponse:
        """Parsea un archivo .csv de calificaciones y devuelve preview.

        Args:
            contenido: Contenido del archivo en bytes.
            nombre_archivo: Nombre del archivo (para detectar extensión).

        Returns:
            PreviewResponse con columnas clasificadas, filas y errores.
        """
        filas_raw, errores = self._parse_archivo(contenido, nombre_archivo)

        if not filas_raw:
            return PreviewResponse(
                columnas_detectadas=[],
                total_filas=0,
                muestra_primeras_3=[],
                errores=errores,
            )

        # Clasificar columnas desde la primera fila
        headers = list(filas_raw[0].keys())
        columnas_detectadas = self._clasificar_columnas(headers)
        columnas_relevantes = [c["nombre"] for c in columnas_detectadas
                              if c["tipo"] in ("numerica", "textual")]

        # Construir filas de muestra (solo columnas relevantes)
        muestra = []
        for fila in filas_raw[:3]:
            muestra.append({
                k: v for k, v in fila.items()
                if k in columnas_relevantes or k in self.COLUMNAS_REQUERIDAS_ALUMNO
            })

        return PreviewResponse(
            columnas_detectadas=columnas_detectadas,
            total_filas=len(filas_raw),
            muestra_primeras_3=muestra,
            errores=errores,
        )

    def _clasificar_columnas(self, headers: list[str]) -> list[dict[str, str]]:
        """Clasifica columnas del archivo en numéricas, textuales o ignoradas.

        RN-01: header que termina en "(Real)" → numérica.
        RN-02: header que NO termina en "(Real)" y es texto → textual.
        Columnas ``COLUMNAS_IGNORADAS`` → ignoradas.

        Args:
            headers: Lista de nombres de columna.

        Returns:
            Lista de dicts con ``nombre`` y ``tipo``.
        """
        resultado: list[dict[str, str]] = []
        for h in headers:
            h_lower = h.strip().lower()
            if h_lower in self.COLUMNAS_IGNORADAS:
                resultado.append({"nombre": h, "tipo": "ignorada"})
            elif self.PATRON_NUMERICA.search(h):
                resultado.append({"nombre": h, "tipo": "numerica"})
            elif self.PATRON_TEXTUAL.search(h_lower):
                resultado.append({"nombre": h, "tipo": "textual"})
            else:
                # Por defecto: si no coincide con ningún patrón, asumir textual
                resultado.append({"nombre": h, "tipo": "textual"})
        return resultado

    def _parse_archivo(
        self,
        contenido: bytes,
        nombre_archivo: str,
    ) -> tuple[list[dict[str, str]], list[str]]:
        """Parsea un archivo .csv a lista de dicts.

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
    ) -> tuple[list[dict[str, str]], list[str]]:
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

        # Validar columnas identificatorias
        columnas_archivo = {c.strip().lower() for c in reader.fieldnames}
        faltantes = self.COLUMNAS_REQUERIDAS_ALUMNO - columnas_archivo
        if faltantes:
            errores.append(
                f"Faltan columnas requeridas: {', '.join(sorted(faltantes))}"
            )
            return [], errores

        filas: list[dict[str, str]] = []
        for i, row in enumerate(reader, start=1):
            fila = {
                k.strip(): v.strip()
                for k, v in row.items()
                if v is not None and v.strip()
            }
            # Verificar columnas requeridas
            if all(fila.get(c) for c in self.COLUMNAS_REQUERIDAS_ALUMNO):
                filas.append(fila)
            else:
                nombre = fila.get("nombre", f"fila {i}")
                errores.append(f"Fila {i} ({nombre}): datos incompletos, se omite")

        if not filas:
            errores.append("No se encontraron filas válidas en el archivo.")

        return filas, errores

    # ------------------------------------------------------------------
    # Group 8 — Confirmar importación
    # ------------------------------------------------------------------

    async def confirmar_importacion(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        archivo_parseado: list[dict[str, str]],
        columnas_detectadas: list[dict[str, str]],
        actividades_seleccionadas: list[str],
        actor_id: UUID,
        audit_ctx: AuditContext,
        session: AsyncSession,
    ) -> int:
        """Confirma la importación de calificaciones desde archivo parseado.

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            archivo_parseado: Filas parseadas del archivo.
            columnas_detectadas: Columnas clasificadas del preview.
            actividades_seleccionadas: Actividades a importar (headers).
            actor_id: UUID del usuario que importa.
            audit_ctx: Contexto de auditoría.
            session: Sesión async.

        Returns:
            Cantidad de calificaciones creadas.

        Raises:
            CalificacionError: si validaciones fallan.
        """
        # Validar actividades seleccionadas
        self._validar_actividades_en_columnas(
            actividades_seleccionadas, columnas_detectadas
        )

        # Validar límite
        total_estimado = len(archivo_parseado) * len(actividades_seleccionadas)
        if total_estimado > _MAX_CALIFICACIONES_IMPORT:
            raise CalificacionError(
                413,
                f"Demasiadas calificaciones: ~{total_estimado}. "
                f"Máximo permitido: {_MAX_CALIFICACIONES_IMPORT}",
            )

        # Construir calificaciones
        calificaciones: list[Calificacion] = []
        entrada_padron_id_map = self._extraer_entradas(archivo_parseado)
        if not entrada_padron_id_map:
            raise CalificacionError(422, "No se pudieron identificar alumnos en el archivo")

        columnas_por_actividad = {
            c["nombre"]: c["tipo"] for c in columnas_detectadas
        }

        for entrada_id_str, fila in entrada_padron_id_map:
            for actividad in actividades_seleccionadas:
                valor = fila.get(actividad, "").strip()
                if not valor:
                    continue

                nota_numerica = None
                nota_textual = None
                tipo = columnas_por_actividad.get(actividad, "textual")

                if tipo == "numerica":
                    try:
                        nota_numerica = float(valor.replace(",", "."))
                    except ValueError:
                        nota_textual = valor
                else:
                    nota_textual = valor

                calificaciones.append(
                    Calificacion(
                        tenant_id=tenant_id,
                        entrada_padron_id=UUID(entrada_id_str),
                        materia_id=materia_id,
                        actividad=actividad,
                        nota_numerica=nota_numerica,
                        nota_textual=nota_textual,
                        origen=OrigenCalificacionDB.IMPORTADO,
                        creado_por=actor_id,
                    )
                )

        if not calificaciones:
            raise CalificacionError(422, "No hay datos para importar (todas las celdas están vacías)")

        await self._calificacion_repo.bulk_create(
            calificaciones=calificaciones,
            session=session,
        )

        # Auditar
        await audit_action(
            ctx=audit_ctx,
            accion=AuditCodes.CALIFICACIONES_IMPORTAR,
            session=session,
            detalle={
                "materia_id": str(materia_id),
                "actividades": actividades_seleccionadas,
                "total_calificaciones": len(calificaciones),
            },
            filas_afectadas=len(calificaciones),
            materia_id=materia_id,
        )

        return len(calificaciones)

    def _extraer_entradas(
        self,
        filas: list[dict[str, str]],
    ) -> list[tuple[str, dict[str, str]]]:
        """Extrae pares (entrada_padron_id, fila) de las filas parseadas.

        Busca columna 'entrada_padron_id' o la primera columna que parezca UUID.
        """
        if not filas:
            return []

        headers = list(filas[0].keys())
        # Buscar columna explícita de ID
        id_col = None
        for h in headers:
            if h.strip().lower() in ("entrada_padron_id", "id_alumno", "alumno_id", "uuid"):
                id_col = h
                break

        # Si no hay columna explícita, usar índice de fila como fallback
        if id_col is None:
            return []

        resultado: list[tuple[str, dict[str, str]]] = []
        for fila in filas:
            raw_id = fila.get(id_col, "").strip()
            if raw_id:
                resultado.append((raw_id, fila))
        return resultado

    def _validar_actividades_en_columnas(
        self,
        actividades: list[str],
        columnas: list[dict[str, str]],
    ) -> None:
        """Valida que las actividades seleccionadas existan en las columnas."""
        nombres_columna = {c["nombre"] for c in columnas}
        for act in actividades:
            if act not in nombres_columna:
                raise CalificacionError(
                    422,
                    f"Actividad '{act}' no encontrada en las columnas del archivo",
                )

    # ------------------------------------------------------------------
    # Group 9 — Reporte de finalización
    # ------------------------------------------------------------------

    async def reporte_finalizacion(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        archivo_contenido: bytes,
        nombre_archivo: str,
        session: AsyncSession,
    ) -> ReporteFinalizacionResponse:
        """Genera reporte de entregas finalizadas sin calificar.

        RN-08: solo se consideran actividades textuales (no numéricas).

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            archivo_contenido: Contenido del archivo de finalización.
            nombre_archivo: Nombre del archivo.
            session: Sesión async.

        Returns:
            ReporteFinalizacionResponse con items no calificados.
        """
        filas, errores = self._parse_archivo(archivo_contenido, nombre_archivo)
        if errores and not filas:
            return ReporteFinalizacionResponse(items=[])

        if not filas:
            return ReporteFinalizacionResponse(items=[])

        # Clasificar columnas y filtrar solo textuales
        headers = list(filas[0].keys())
        columnas = self._clasificar_columnas(headers)
        columnas_textuales = [c["nombre"] for c in columnas if c["tipo"] == "textual"]

        # También incluir columna de identificación del alumno
        entrada_padron_id_map = self._extraer_entradas(filas)
        nombre_col = "nombre"
        apellido_col = "apellidos"

        items: list[ReporteFinalizacionItem] = []
        for entrada_id_str, fila in entrada_padron_id_map:
            entrada_id = UUID(entrada_id_str) if self._es_uuid(entrada_id_str) else None
            if entrada_id is None:
                continue

            # Obtener calificaciones existentes del alumno para esta materia
            existing = await self._calificacion_repo.get_by_entrada_padron(
                tenant_id=tenant_id,
                entrada_padron_id=entrada_id,
                materia_id=materia_id,
                session=session,
            )
            actividades_existentes = {c.actividad for c in existing}

            # Para cada actividad textual, si no tiene calificación → reportar
            alumno_nombre = fila.get(nombre_col, "")
            alumno_apellido = fila.get(apellido_col, "")
            nombre_completo = f"{alumno_nombre} {alumno_apellido}".strip()

            for actividad in columnas_textuales:
                if actividad in actividades_existentes:
                    continue

                # Verificar que la actividad esté "finalizada" (tiene valor)
                valor = fila.get(actividad, "").strip()
                if not valor:
                    continue

                items.append(ReporteFinalizacionItem(
                    entrada_padron_id=entrada_id,
                    alumno=nombre_completo,
                    actividad=actividad,
                    fecha_finalizacion=valor,
                ))

        return ReporteFinalizacionResponse(items=items)

    def _es_uuid(self, valor: str) -> bool:
        """Verifica si un string es un UUID válido."""
        try:
            UUID(valor)
            return True
        except ValueError:
            return False

    # ------------------------------------------------------------------
    # Group 10 — aprobado derivado (D-01)
    # ------------------------------------------------------------------

    def _compute_aprobado(
        self,
        calificacion: Calificacion,
        umbral: UmbralMateria | None = None,
    ) -> bool:
        """Determina si una calificación está aprobada.

        RN-01: ``nota_numerica >= umbral_pct`` → True.
        RN-02: ``nota_textual in valores_aprobatorios`` → True.
        D-01: sin umbral configurado → usa defaults (_DEFAULT_UMBRAL_PCT).

        Args:
            calificacion: Calificación a evaluar.
            umbral: Umbral configurado (opcional).

        Returns:
            True si está aprobada, False en caso contrario.
        """
        if umbral is not None and umbral.deleted_at is not None:
            umbral = None

        if calificacion.nota_numerica is not None:
            threshold = umbral.umbral_pct if umbral else _DEFAULT_UMBRAL_PCT
            return calificacion.nota_numerica >= threshold

        if calificacion.nota_textual is not None:
            if umbral and umbral.valores_aprobatorios:
                return calificacion.nota_textual in umbral.valores_aprobatorios
            # Sin valores_aprobatorios configurados, asumir false
            return False

        return False

    async def get_calificaciones(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        creado_por: UUID,
        session: AsyncSession,
    ) -> list[CalificacionResponse]:
        """Retorna calificaciones con ``aprobado`` derivado en read-time.

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            creado_por: UUID del usuario.
            session: Sesión async.

        Returns:
            Lista de CalificacionResponse con aprobado computado.
        """
        calificaciones = await self._calificacion_repo.get_by_materia_y_usuario(
            tenant_id=tenant_id,
            materia_id=materia_id,
            creado_por=creado_por,
            session=session,
        )

        if not calificaciones:
            return []

        # Obtener umbral del usuario para la materia
        umbral = await self._get_umbral_para_materia(
            tenant_id=tenant_id,
            creado_por=creado_por,
            materia_id=materia_id,
            session=session,
        )

        return [
            CalificacionResponse(
                id=c.id,
                entrada_padron_id=c.entrada_padron_id,
                materia_id=c.materia_id,
                actividad=c.actividad,
                nota_numerica=c.nota_numerica,
                nota_textual=c.nota_textual,
                aprobado=self._compute_aprobado(c, umbral),
                origen=c.origen.value,
                creado_por=c.creado_por,
                creada_at=c.created_at.isoformat() if c.created_at else "",
            )
            for c in calificaciones
        ]

    async def _get_umbral_para_materia(
        self,
        *,
        tenant_id: UUID,
        creado_por: UUID,
        materia_id: UUID,
        session: AsyncSession,
    ) -> UmbralMateria | None:
        """Obtiene el umbral del usuario para una materia.

        Busca la asignación del usuario para la materia y luego el umbral
        correspondiente. Si no hay umbral configurado, retorna None.
        """
        from app.models.asignacion import Asignacion
        from sqlalchemy import select

        stmt = (
            select(Asignacion.id)
            .where(
                Asignacion.tenant_id == tenant_id,
                Asignacion.usuario_id == creado_por,
                Asignacion.materia_id == materia_id,
                Asignacion.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        asignacion_id = result.scalar_one_or_none()
        if asignacion_id is None:
            return None

        return await self._umbral_repo.get_by_asignacion(
            tenant_id=tenant_id,
            asignacion_id=asignacion_id,
            session=session,
        )

    # ------------------------------------------------------------------
    # Group 11 — Vaciar (F1.5, RN-04)
    # ------------------------------------------------------------------

    async def vaciar_materia(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        actor_id: UUID,
        audit_ctx: AuditContext,
        session: AsyncSession,
    ) -> int:
        """Vacía las calificaciones de un usuario para una materia.

        RN-04: soft-delete scoped al usuario (creado_por=actor_id).
        Preserva calificaciones de otros docentes.

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            actor_id: UUID del usuario que vacía.
            audit_ctx: Contexto de auditoría.
            session: Sesión async.

        Returns:
            Cantidad de registros eliminados (soft-delete).

        Raises:
            CalificacionError: si validaciones fallan.
        """
        affected = await self._calificacion_repo.soft_delete_by_materia_y_usuario(
            tenant_id=tenant_id,
            materia_id=materia_id,
            creado_por=actor_id,
            deleted_by=actor_id,
            session=session,
        )

        await audit_action(
            ctx=audit_ctx,
            accion=AuditCodes.CALIFICACIONES_VACIAR,
            session=session,
            detalle={
                "materia_id": str(materia_id),
                "total_vaciadas": affected,
            },
            filas_afectadas=affected,
            materia_id=materia_id,
        )

        return affected


# ---------------------------------------------------------------------------
# UmbralService
# ---------------------------------------------------------------------------


class UmbralService:
    """Servicio de umbral de aprobación (Grupo 12).

    Dependencias: UmbralRepository.
    """

    def __init__(
        self,
        umbral_repo: UmbralRepository | None = None,
    ) -> None:
        self._umbral_repo = umbral_repo or UmbralRepository()

    async def get_umbral(
        self,
        *,
        tenant_id: UUID,
        asignacion_id: UUID,
        session: AsyncSession,
    ) -> UmbralMateriaResponse | None:
        """Retorna el umbral configurado, o defaults si no existe.

        Args:
            tenant_id: UUID del tenant.
            asignacion_id: UUID de la asignación.
            session: Sesión async.

        Returns:
            UmbralMateriaResponse con valores reales o defaults.
        """
        umbral = await self._umbral_repo.get_by_asignacion(
            tenant_id=tenant_id,
            asignacion_id=asignacion_id,
            session=session,
        )
        if umbral is None:
            return None

        return UmbralMateriaResponse(
            id=umbral.id,
            asignacion_id=umbral.asignacion_id,
            materia_id=umbral.materia_id,
            umbral_pct=umbral.umbral_pct,
            valores_aprobatorios=umbral.valores_aprobatorios,
        )

    async def configurar_umbral(
        self,
        *,
        tenant_id: UUID,
        asignacion_id: UUID,
        materia_id: UUID,
        umbral_pct: int,
        valores_aprobatorios: list[str] | None = None,
        audit_ctx: AuditContext,
        session: AsyncSession,
    ) -> UmbralMateriaResponse:
        """Crea o actualiza el umbral para una asignación.

        Args:
            tenant_id: UUID del tenant.
            asignacion_id: UUID de la asignación.
            materia_id: UUID de la materia.
            umbral_pct: Porcentaje mínimo (0-100).
            valores_aprobatorios: Valores textuales aprobatorios (opcional).
            audit_ctx: Contexto de auditoría.
            session: Sesión async.

        Returns:
            UmbralMateriaResponse actualizado.

        Raises:
            CalificacionError: si el umbral está fuera de rango.
        """
        if not 0 <= umbral_pct <= 100:
            raise CalificacionError(422, "umbral_pct debe estar entre 0 y 100")

        umbral = await self._umbral_repo.upsert(
            tenant_id=tenant_id,
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprobatorios,
            session=session,
        )

        await audit_action(
            ctx=audit_ctx,
            accion=AuditCodes.CALIFICACIONES_CONFIGURAR_UMBRAL,
            session=session,
            detalle={
                "materia_id": str(materia_id),
                "asignacion_id": str(asignacion_id),
                "umbral_pct": umbral_pct,
                "valores_aprobatorios": valores_aprobatorios,
            },
            materia_id=materia_id,
        )

        return UmbralMateriaResponse(
            id=umbral.id,
            asignacion_id=umbral.asignacion_id,
            materia_id=umbral.materia_id,
            umbral_pct=umbral.umbral_pct,
            valores_aprobatorios=umbral.valores_aprobatorios,
        )
