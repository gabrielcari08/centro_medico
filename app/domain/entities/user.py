from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


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
    id: UUID | None = None
    cedula: str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        # Normalizacion basica de strings
        self.name = self.name.strip()
        self.last_name = self.last_name.strip()
        self.email = self.email.strip()
        self.dni = self.dni.strip()
        self.phone = self.phone.strip()
        if self.cedula is not None:
            self.cedula = self.cedula.strip()

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

        # Invariante de rol y cedula
        if self.role == UserRole.PROFESSIONAL and self.cedula is None:
            raise ValueError("Campos faltantes")
        if self.role != UserRole.PROFESSIONAL and self.cedula is not None:
            raise ValueError("cedula only allowed for professional")

        # Generar id si no se proporciona
        if self.id is None:
            self.id = uuid4()
