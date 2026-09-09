from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMINISTRATOR = "administrator"
    RECEPTIONIST = "receptionist"
    PROFESSIONAL = "professional"


@dataclass
class User:
    name: str
    last_name: str
    dni: str
    email: str
    phone: str
    password_hash: str
    role: UserRole
    id: int | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        # Normalizacion basica de strings
        self.name = self.name.strip()
        self.last_name = self.last_name.strip()
        self.email = self.email.strip()
        self.dni = self.dni.strip()
        self.phone = self.phone.strip()

        # Campos obligatorios no vacios
        if not self.name:
            raise ValueError("Campos faltantes")
        if not self.last_name:
            raise ValueError("Campos faltantes")
        if not self.dni:
            raise ValueError("Campos faltantes")
        if not self.email:
            raise ValueError("Campos faltantes")
        if not self.phone:
            raise ValueError("Campos faltantes")
        if not self.password_hash:
            raise ValueError("Campos faltantes")
