from app.models.base import TenantScopedMixin
from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role, UserRole
from app.models.permiso import Permiso, RolPermiso
from app.models.refresh_token import RefreshToken
from app.models.totp_secret import TotpSecret
from app.models.password_reset_token import PasswordResetToken
from app.models.audit_log import AuditLog
from app.models.carrera import Carrera, EstadoCarrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia, EstadoMateria
from app.models.programa_materia import ProgramaMateria
from app.models.fecha_academica import FechaAcademica, TipoFechaAcademica
from app.models.asignacion import Asignacion, ROLES_EN_ASIGNACION, ESTADO_VIGENTE, ESTADO_VENCIDA
from app.models.tarea import Tarea, EstadoTarea
from app.models.comentario_tarea import ComentarioTarea
from app.models.aviso import Aviso, AlcanceAviso, SeveridadAviso
from app.models.acknowledgment import AcknowledgmentAviso
from app.models.hilo_mensaje import HiloMensaje
from app.models.mensaje_interno import MensajeInterno
from app.models.evaluacion import Evaluacion, ReservaEvaluacion, ResultadoEvaluacion, TipoEvaluacion, EstadoReserva
from app.models.slot_encuentro import SlotEncuentro, DiaSemana
from app.models.instancia_encuentro import InstanciaEncuentro, EstadoInstancia
from app.models.guardia import Guardia, EstadoGuardia

__all__ = [
    "Tenant",
    "TenantScopedMixin",
    "User",
    "Role",
    "UserRole",
    "Permiso",
    "RolPermiso",
    "RefreshToken",
    "TotpSecret",
    "PasswordResetToken",
    "AuditLog",
    "Carrera",
    "EstadoCarrera",
    "Cohorte",
    "Materia",
    "EstadoMateria",
    "ProgramaMateria",
    "FechaAcademica",
    "TipoFechaAcademica",
    "Asignacion",
    "ROLES_EN_ASIGNACION",
    "ESTADO_VIGENTE",
    "ESTADO_VENCIDA",
    "Tarea",
    "EstadoTarea",
    "ComentarioTarea",
    "Aviso",
    "AlcanceAviso",
    "SeveridadAviso",
    "AcknowledgmentAviso",
    "HiloMensaje",
    "MensajeInterno",
    "Evaluacion",
    "ReservaEvaluacion",
    "ResultadoEvaluacion",
    "TipoEvaluacion",
    "EstadoReserva",
    "SlotEncuentro",
    "DiaSemana",
    "InstanciaEncuentro",
    "EstadoInstancia",
    "Guardia",
    "EstadoGuardia",
]
