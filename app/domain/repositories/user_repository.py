from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.user import User, UserRole


class UserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_dni(self, dni: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_phone(self, phone: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_cedula(self, cedula: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        pass

    @abstractmethod
    def exists_by_dni(self, dni: str) -> bool:
        pass

    @abstractmethod
    def exists_by_phone(self, phone: str) -> bool:
        pass

    @abstractmethod
    def exists_by_cedula(self, cedula: str) -> bool:
        pass

    @abstractmethod
    def exists_by_role(self, role: UserRole) -> bool:
        pass

    @abstractmethod
    def save(self, user: User) -> User:
        pass
