import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.entities.professional import Professional
from app.domain.entities.user import User, UserRole


class UpdateProfessionalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    last_name: str
    dni: str
    email: str
    phone: str
    cedula: str

    @field_validator("name", "last_name", mode="before")
    @classmethod
    def check_not_empty(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Campos faltantes")
        return v.strip() if isinstance(v, str) else v

    @field_validator("dni")
    @classmethod
    def validate_dni(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Campos faltantes")
        if not re.fullmatch(r"^\d{8}$", v.strip()):
            raise ValueError("Formato inválido, debe tener 8 caracteres")
        return v.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Campos faltantes")
        if "@" not in v:
            raise ValueError("email invalido")
        return v.strip().lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Campos faltantes")
        if not re.fullmatch(r"^\d{10}$", v.strip()):
            raise ValueError("Formato inválido, debe tener 10 caracteres")
        return v.strip()

    @field_validator("cedula")
    @classmethod
    def validate_cedula(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Campos faltantes")
        if not re.fullmatch(r"^[A-Za-z0-9]{7,8}$", v.strip()):
            raise ValueError("Formato inválido, debe tener 7 u 8 caracteres")
        return v.strip()


class ProfessionalDetailResponse(BaseModel):
    id: int
    user_id: int
    cedula: str
    name: str
    last_name: str
    dni: str
    email: str
    phone: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entities(cls, user: User, professional: Professional) -> "ProfessionalDetailResponse":
        return cls(
            id=professional.id,
            user_id=user.id,
            cedula=professional.cedula,
            name=user.name,
            last_name=user.last_name,
            dni=user.dni,
            email=user.email,
            phone=user.phone,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at if hasattr(user, "updated_at") else user.created_at,
        )


class ProfessionalListResponse(BaseModel):
    items: list[ProfessionalDetailResponse]
    count: int
