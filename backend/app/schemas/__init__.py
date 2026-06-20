"""Pydantic v2 schemas for API request/response validation."""

from app.schemas.salario_base import SalarioBaseCreate, SalarioBaseUpdate, SalarioBaseResponse
from app.schemas.salario_plus import SalarioPlusCreate, SalarioPlusUpdate, SalarioPlusResponse
from app.schemas.liquidacion import (
    LiquidacionResponse,
    LiquidacionResumen,
    CalculoRequest,
    SegmentoLiquidaciones,
    KpisLiquidacion,
    LiquidacionSegmentadaResponse,
)
from app.schemas.factura import FacturaCreate, FacturaUpdate, FacturaResponse
from app.schemas.auth import (
    CurrentUserResponse,
    ForgotRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    ResetRequest,
    TokenPair,
    TwoFAChallenge,
    TwoFAConfirmRequest,
    TwoFAEnrollResponse,
    TwoFAVerifyRequest,
)

__all__ = [
    "SalarioBaseCreate",
    "SalarioBaseUpdate",
    "SalarioBaseResponse",
    "SalarioPlusCreate",
    "SalarioPlusUpdate",
    "SalarioPlusResponse",
    "LiquidacionResponse",
    "LiquidacionResumen",
    "CalculoRequest",
    "SegmentoLiquidaciones",
    "KpisLiquidacion",
    "LiquidacionSegmentadaResponse",
    "FacturaCreate",
    "FacturaUpdate",
    "FacturaResponse",
    "CurrentUserResponse",
    "ForgotRequest",
    "LoginRequest",
    "LogoutRequest",
    "MessageResponse",
    "RefreshRequest",
    "ResetRequest",
    "TokenPair",
    "TwoFAChallenge",
    "TwoFAConfirmRequest",
    "TwoFAEnrollResponse",
    "TwoFAVerifyRequest",
]
