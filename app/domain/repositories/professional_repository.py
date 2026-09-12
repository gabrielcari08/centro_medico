from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.professional import Professional
from app.domain.entities.user import User


class ProfessionalRepository(ABC):
    @abstractmethod
    def get_by_id(self, professional_id: int) -> Optional[Professional]:
        pass

    @abstractmethod
    def get_by_cedula(self, cedula: str) -> Optional[Professional]:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[Professional]:
        pass

    @abstractmethod
    def exists_by_cedula(self, cedula: str, exclude_user_id: int | None = None) -> bool:
        pass

    @abstractmethod
    def list_active(self, search: str | None = None) -> list[tuple[User, Professional]]:
        pass

    @abstractmethod
    def list_deactivated(self) -> list[tuple[User, Professional]]:
        pass

    @abstractmethod
    def save(self, professional: Professional) -> Professional:
        pass

    @abstractmethod
    def delete(self, professional: Professional) -> None:
        pass
