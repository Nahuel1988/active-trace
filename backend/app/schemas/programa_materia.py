from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProgramaMateriaCreate(BaseModel):
    materia_id: str
    carrera_id: str
    cohorte_id: str
    titulo: str
    referencia_archivo: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ProgramaMateriaUpdate(BaseModel):
    titulo: Optional[str] = None
    referencia_archivo: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ProgramaMateriaResponse(BaseModel):
    id: str
    tenant_id: str
    materia_id: str
    carrera_id: str
    cohorte_id: str
    titulo: str
    referencia_archivo: Optional[str] = None
    cargado_at: str
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True, extra="forbid")
