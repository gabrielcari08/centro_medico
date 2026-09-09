from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.professional import Professional


class ProfessionalRepository(ABC):
    @abstractmethod
    def get_by_cedula(self, cedula: str) -> Optional[Professional]:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[Professional]:
        pass

    @abstractmethod
    def exists_by_cedula(self, cedula: str) -> bool:
        pass

    @abstractmethod
    def save(self, professional: Professional) -> Professional:
        pass
