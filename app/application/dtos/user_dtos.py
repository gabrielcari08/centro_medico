import re
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.domain.entities.user import User, UserRole

# Define which fields the user must submit to register a receptionist.
class CreateReceptionistRequest(BaseModel):
    name: str
    last_name: str
    dni: str
    email: str
    phone: str
    password: str

    # Validations of the fields.
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

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Campos faltantes")
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v

# Define which fields the user must submit to register a professional.
# Extends from CreateReceptionistRequest because it has the same fields + cedula.
class CreateProfessionalRequest(CreateReceptionistRequest):
    cedula: str

    # Validations of the field.
    @field_validator("cedula")
    @classmethod
    def validate_cedula(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Campos faltantes")
        if not re.fullmatch(r"^[A-Za-z0-9]{7,8}$", v.strip()):
            raise ValueError("Formato inválido, debe tener 7 u 8 caracteres")
        return v.strip()

# Define which fields must be returned from a user.
class UserResponse(BaseModel):
    id: int
    name: str
    last_name: str
    dni: str
    email: str
    phone: str
    role: UserRole
    is_active: bool
    created_at: datetime

    @classmethod
    def from_entity(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            name=user.name,
            last_name=user.last_name,
            dni=user.dni,
            email=user.email,
            phone=user.phone,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )


class ProfessionalResponse(BaseModel):
    id: int
    user_id: int
    cedula: str

    @classmethod
    def from_entity(cls, professional) -> "ProfessionalResponse":
        return cls(id=professional.id, user_id=professional.user_id, cedula=professional.cedula)
