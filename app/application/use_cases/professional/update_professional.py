from datetime import datetime, timezone

from app.application.dtos.professional_dtos import (
    ProfessionalDetailResponse,
    UpdateProfessionalRequest,
)
from app.domain.entities.user import User, UserRole
from app.domain.exceptions.professional_exceptions import (
    ProfessionalNotFoundException,
)
from app.domain.exceptions.user_exceptions import (
    DuplicateEmailException,
    DuplicateUserException,
    ForbiddenException,
)
from app.domain.repositories.professional_repository import ProfessionalRepository
from app.domain.repositories.user_repository import UserRepository


class UpdateProfessionalUseCase:
    def __init__(
        self,
        professional_repo: ProfessionalRepository,
        user_repo: UserRepository,
    ):
        self.professional_repo = professional_repo
        self.user_repo = user_repo

    def execute(
        self,
        professional_id: int,
        dto: UpdateProfessionalRequest,
        current_admin: User,
    ) -> ProfessionalDetailResponse:
        # Solo administradores pueden actualizar
        if current_admin.role != UserRole.ADMINISTRATOR:
            raise ForbiddenException("Forbidden")
        # Busca profesional y usuario vinculado
        professional = self.professional_repo.get_by_id(professional_id)
        if professional is None:
            raise ProfessionalNotFoundException("Professional Not Found")
        user = self.user_repo.get_by_id(professional.user_id)
        if user is None:
            raise ProfessionalNotFoundException("Professional Not Found")
        # Unicidad excluyendo al propio usuario
        if self.user_repo.exists_by_email(dto.email, exclude_id=user.id):
            raise DuplicateEmailException("email ya registrado")
        if self.user_repo.exists_by_dni(dto.dni, exclude_id=user.id):
            raise DuplicateUserException("Usuario ya registrado")
        if self.user_repo.exists_by_phone(dto.phone, exclude_id=user.id):
            raise DuplicateUserException("Usuario ya registrado")
        if self.professional_repo.exists_by_cedula(dto.cedula, exclude_user_id=user.id):
            raise DuplicateUserException("Usuario ya registrado")
        # Actualiza campos editables, password no editable
        user.name = dto.name.strip()
        user.last_name = dto.last_name.strip()
        user.dni = dto.dni
        user.email = dto.email.lower()
        user.phone = dto.phone
        user.updated_at = datetime.now(timezone.utc)
        professional.cedula = dto.cedula
        # Persiste ambos en la misma sesion
        saved_user = self.user_repo.save(user)
        saved_professional = self.professional_repo.save(professional)
        return ProfessionalDetailResponse.from_entities(saved_user, saved_professional)
