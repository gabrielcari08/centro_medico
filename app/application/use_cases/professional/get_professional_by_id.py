from app.application.dtos.professional_dtos import ProfessionalDetailResponse
from app.domain.exceptions.professional_exceptions import (
    ProfessionalNotFoundException,
)
from app.domain.repositories.professional_repository import ProfessionalRepository
from app.domain.repositories.user_repository import UserRepository


class GetProfessionalByIdUseCase:
    def __init__(
        self,
        professional_repo: ProfessionalRepository,
        user_repo: UserRepository,
    ):
        self.professional_repo = professional_repo
        self.user_repo = user_repo

    def execute(self, professional_id: int) -> ProfessionalDetailResponse:
        # Busca profesional, 404 si no existe
        professional = self.professional_repo.get_by_id(professional_id)
        if professional is None:
            raise ProfessionalNotFoundException("Professional Not Found")
        # Busca usuario vinculado, 404 si huerfano
        user = self.user_repo.get_by_id(professional.user_id)
        if user is None:
            raise ProfessionalNotFoundException("Professional Not Found")
        # Endpoint publico solo expone activos
        if not user.is_active:
            raise ProfessionalNotFoundException("Professional Not Found")
        return ProfessionalDetailResponse.from_entities(user, professional)
