"""Catálogo de códigos de acción auditables.

Cada código es un string constante que identifica de forma única una
acción de dominio que puede ser registrada en el audit log.

Uso::

    from app.core.audit_codes import AuditCodes

    @audited(AuditCodes.PADRON_CARGAR)
    async def cargar_padron(...):
        ...

    await audit_action(ctx, AuditCodes.COMUNICACION_ENVIAR, ...)
"""


class _AuditCodes:
    """Contenedor de constantes tipadas para códigos de acción auditables.

    Cada atributo es un ``str`` cuyo valor coincide con el nombre del
    atributo. Esto permite verificación estática de tipos (mypy/pyright
    acepta ``AuditCodes.PADRON_CARGAR`` como ``str``).
    """

    # ── Calificaciones ────────────────────────────────────────────────────
    CALIFICACIONES_IMPORTAR: str = "CALIFICACIONES_IMPORTAR"
    CALIFICACIONES_CONFIGURAR_UMBRAL: str = "CALIFICACIONES_CONFIGURAR_UMBRAL"
    CALIFICACIONES_VACIAR: str = "CALIFICACIONES_VACIAR"

    # ── Padrón ────────────────────────────────────────────────────────────
    PADRON_CARGAR: str = "PADRON_CARGAR"
    PADRON_VACIAR: str = "PADRON_VACIAR"

    # ── Comunicación ──────────────────────────────────────────────────────
    COMUNICACION_ENVIAR: str = "COMUNICACION_ENVIAR"

    # ── Asignaciones ──────────────────────────────────────────────────────
    ASIGNACION_MODIFICAR: str = "ASIGNACION_MODIFICAR"

    # ── Liquidaciones ─────────────────────────────────────────────────────
    LIQUIDACION_CERRAR: str = "LIQUIDACION_CERRAR"

    # ── Tareas internas (C-16) ────────────────────────────────────────────
    TAREA_CREAR: str = "TAREA_CREAR"
    TAREA_DELEGAR: str = "TAREA_DELEGAR"
    TAREA_CAMBIAR_ESTADO: str = "TAREA_CAMBIAR_ESTADO"

    # ── Coloquios / Evaluaciones ──────────────────────────────────────────
    COLOQUIO_MODIFICAR_RESULTADO: str = "COLOQUIO_MODIFICAR_RESULTADO"

    # ── Encuentros (C-13) ──────────────────────────────────────────────────
    ENCUENTRO_SLOT_CREAR: str = "ENCUENTRO_SLOT_CREAR"
    ENCUENTRO_INSTANCIA_EDITAR: str = "ENCUENTRO_INSTANCIA_EDITAR"

    # ── Guardias (C-13) ───────────────────────────────────────────────────
    GUARDIA_REGISTRAR: str = "GUARDIA_REGISTRAR"
    GUARDIA_CAMBIAR_ESTADO: str = "GUARDIA_CAMBIAR_ESTADO"

    # ── Impersonación ─────────────────────────────────────────────────────
    IMPERSONACION_INICIAR: str = "IMPERSONACION_INICIAR"
    IMPERSONACION_FINALIZAR: str = "IMPERSONACION_FINALIZAR"


# Singleton para acceso directo
AuditCodes = _AuditCodes()
