from app.application.dtos.professional_dtos import ProfessionalDetailResponse
from app.domain.entities.user import User, UserRole
from app.domain.exceptions.professional_exceptions import (
    AlreadyInactiveException,
    ProfessionalNotFoundException,
)
from app.domain.exceptions.user_exceptions import ForbiddenException
from app.domain.repositories.professional_repository import ProfessionalRepository
from app.domain.repositories.user_repository import UserRepository


class DeactivateProfessionalUseCase:
    def __init__(
        self,
        professional_repo: ProfessionalRepository,
        user_repo: UserRepository,
    ):
        self.professional_repo = professional_repo
        self.user_repo = user_repo

    def execute(
        self, professional_id: int, current_admin: User
    ) -> ProfessionalDetailResponse:
        # Solo administradores pueden desactivar
        if current_admin.role != UserRole.ADMINISTRATOR:
            raise ForbiddenException("Forbidden")
        # Busca profesional y usuario vinculado
        professional = self.professional_repo.get_by_id(professional_id)
        if professional is None:
            raise ProfessionalNotFoundException("Professional Not Found")
        user = self.user_repo.get_by_id(professional.user_id)
        if user is None:
            raise ProfessionalNotFoundException("Professional Not Found")
        # Idempotencia: ya inactivo
        if not user.is_active:
            raise AlreadyInactiveException("Profesional ya desactivado")
        user.is_active = False
        saved_user = self.user_repo.save(user)
        return ProfessionalDetailResponse.from_entities(saved_user, professional)
