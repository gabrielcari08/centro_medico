from app.application.dtos.professional_dtos import ProfessionalDetailResponse
from app.domain.entities.user import User, UserRole
from app.domain.exceptions.user_exceptions import ForbiddenException
from app.domain.repositories.professional_repository import ProfessionalRepository
from app.domain.repositories.user_repository import UserRepository


class ListDeactivatedProfessionalsUseCase:
    def __init__(
        self,
        professional_repo: ProfessionalRepository,
        user_repo: UserRepository,
    ):
        self.professional_repo = professional_repo
        self.user_repo = user_repo

    def execute(self, current_admin: User) -> list[ProfessionalDetailResponse]:
        # Solo administradores pueden ver desactivados
        if current_admin.role != UserRole.ADMINISTRATOR:
            raise ForbiddenException("Forbidden")
        pairs = self.professional_repo.list_deactivated()
        return [
            ProfessionalDetailResponse.from_entities(user, professional)
            for user, professional in pairs
        ]
