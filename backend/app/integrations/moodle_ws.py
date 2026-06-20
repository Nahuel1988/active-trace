"""MoodleWsClient — cliente HTTP async para Moodle Web Services.

Expone funciones para sincronizar el padrón de alumnos desde una
instancia de Moodle vía su API de Web Services.

Configuración vía entorno:
    MOODLE_URL: URL base de la instancia Moodle (ej: https://moodle.example.com)
    MOODLE_TOKEN: Token de servicio web con permiso ``core_user_get_users``

Errores de red/respuesta se mapean a MoodleWsError.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from app.core.config import Settings


class MoodleWsError(Exception):
    """Error en la comunicación con Moodle Web Services.

    Attributes:
        status_code: Código HTTP (502, 503, 504).
        detail: Mensaje de error descriptivo.
    """

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class MoodleWsClient:
    """Cliente HTTP async para Moodle Web Services.

    Uso::

        client = MoodleWsClient()
        alumnos = await client.get_padron(materia_id="...", cohorte_id="...")
    """

    # Columnas esperadas en la respuesta del WS de Moodle
    CAMPOS_REQUERIDOS = {"nombre", "apellidos", "email", "comision"}
    CAMPOS_OPCIONALES = {"regional"}

    def __init__(
        self,
        moodle_url: str | None = None,
        moodle_token: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Inicializa el cliente con configuración del entorno.

        Args:
            moodle_url: URL base de Moodle. Si es None, se lee de Settings().
            moodle_token: Token WS. Si es None, se lee de Settings().
            http_client: Cliente HTTP opcional (útil para inyectar mocks en tests).
        """
        if moodle_url is None or moodle_token is None:
            settings = Settings()
            moodle_url = moodle_url or getattr(settings, "moodle_url", None) or os.getenv("MOODLE_URL", "")
            moodle_token = moodle_token or getattr(settings, "moodle_token", None) or os.getenv("MOODLE_TOKEN", "")
        self._base_url = moodle_url.rstrip("/") if moodle_url else ""
        self._token = moodle_token or ""
        self._client = http_client or httpx.AsyncClient(timeout=30.0)

    async def get_padron(
        self,
        materia_id: str,
        cohorte_id: str,
    ) -> list[dict[str, Any]]:
        """Obtiene el padrón de alumnos desde Moodle WS.

        Args:
            materia_id: ID de la materia en Moodle (course id).
            cohorte_id: ID de la cohorte/grupo en Moodle (group id).

        Returns:
            Lista de dicts con keys ``nombre``, ``apellidos``, ``email``,
            ``comision``, ``regional``.

        Raises:
            MoodleWsError: Si Moodle no está disponible, timeout, o
                respuesta inválida.
        """
        if not self._base_url or not self._token:
            raise MoodleWsError(
                503,
                "Moodle no está configurado para este tenant",
            )

        try:
            # Llamada al WS core_user_get_users de Moodle
            # Documentación: https://docs.moodle.org/dev/User_related_web_services
            params = {
                "wstoken": self._token,
                "wsfunction": "core_user_get_users",
                "moodlewsrestformat": "json",
                "criteria[0][key]": "courseid",
                "criteria[0][value]": materia_id,
            }
            if cohorte_id:
                params["criteria[1][key]"] = "groupid"
                params["criteria[1][value]"] = cohorte_id

            response = await self._client.get(
                f"{self._base_url}/webservice/rest/server.php",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        except httpx.TimeoutException:
            raise MoodleWsError(504, "Timeout al conectar con Moodle")
        except httpx.HTTPStatusError as e:
            raise MoodleWsError(502, f"Moodle respondió con error HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            raise MoodleWsError(502, f"Error de conexión con Moodle: {e!s}")

        # Parsear respuesta
        usuarios = data.get("users", [])
        resultado: list[dict[str, Any]] = []
        errores_mapeo: list[str] = []

        for u in usuarios:
            alumno = self._mapear_usuario(u)
            if alumno is not None:
                resultado.append(alumno)
            else:
                email = u.get("email", "sin-email")
                errores_mapeo.append(f"Usuario {email}: columnas requeridas faltantes")

        if errores_mapeo and not resultado:
            raise MoodleWsError(502, f"Error de mapeo: {'; '.join(errores_mapeo[:5])}")

        return resultado

    def _mapear_usuario(self, usuario: dict[str, Any]) -> dict[str, Any] | None:
        """Mapea un usuario de Moodle al formato interno del padrón.

        Args:
            usuario: Dict con datos del usuario desde Moodle WS.

        Returns:
            Dict con keys estandarizadas, o None si faltan campos requeridos.
        """
        # Extraer campos del perfil personalizado (custom profile fields)
        perfil = {}
        for field in usuario.get("customfields", []):
            perfil[field.get("shortname", "")] = field.get("value", "")

        nombre = usuario.get("firstname", "").strip()
        apellidos = usuario.get("lastname", "").strip()
        email = usuario.get("email", "").strip()
        # Intentar obtener comisión de custom field o del department
        comision = (
            perfil.get("comision", "")
            or perfil.get("comission", "")
            or usuario.get("department", "")
        ).strip()
        regional = perfil.get("regional", "").strip() or None

        # Validar campos requeridos
        if not all([nombre, apellidos, email, comision]):
            return None

        return {
            "nombre": nombre,
            "apellidos": apellidos,
            "email": email,
            "comision": comision,
            "regional": regional,
        }

    async def close(self) -> None:
        """Cierra el cliente HTTP."""
        await self._client.aclose()
