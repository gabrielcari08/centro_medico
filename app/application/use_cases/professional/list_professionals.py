from app.application.dtos.professional_dtos import ProfessionalDetailResponse
from app.domain.repositories.professional_repository import ProfessionalRepository
from app.domain.repositories.user_repository import UserRepository


class ListProfessionalsUseCase:
    def __init__(
        self,
        professional_repo: ProfessionalRepository,
        user_repo: UserRepository,
    ):
        self.professional_repo = professional_repo
        self.user_repo = user_repo

    def execute(self, search: str | None = None) -> list[ProfessionalDetailResponse]:
        # Lista publica de activos, delega filtrado y orden al repositorio
        pairs = self.professional_repo.list_active(search)
        return [
            ProfessionalDetailResponse.from_entities(user, professional)
            for user, professional in pairs
        ]
