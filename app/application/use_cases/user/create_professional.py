from app.application.dtos.user_dtos import CreateProfessionalRequest
from app.domain.entities.professional import Professional
from app.domain.entities.user import User, UserRole
from app.domain.exceptions.user_exceptions import DuplicateEmailException, DuplicateUserException
from app.domain.repositories.professional_repository import ProfessionalRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_service import PasswordService


class CreateProfessionalUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        professional_repo: ProfessionalRepository,
        pwd_service: PasswordService,
    ):
        self.user_repo = user_repo
        self.professional_repo = professional_repo
        self.pwd_service = pwd_service

    def execute(self, dto: CreateProfessionalRequest) -> User:
        # Validaciones de unicidad
        if self.user_repo.exists_by_email(dto.email):
            raise DuplicateEmailException("email ya registrado")
        if self.user_repo.exists_by_dni(dto.dni):
            raise DuplicateUserException("Usuario ya registrado")
        if self.user_repo.exists_by_phone(dto.phone):
            raise DuplicateUserException("Usuario ya registrado")
        if self.professional_repo.exists_by_cedula(dto.cedula):
            raise DuplicateUserException("Usuario ya registrado")

        hashed = self.pwd_service.hash(dto.password)
        user = User(
            name=dto.name,
            last_name=dto.last_name,
            dni=dto.dni,
            email=dto.email,
            phone=dto.phone,
            password_hash=hashed,
            role=UserRole.PROFESSIONAL,
            is_active=True,
        )
        saved_user = self.user_repo.save(user)

        # Crear registro profesional enlazado
        try:
            professional = Professional(user_id=saved_user.id, cedula=dto.cedula)
            self.professional_repo.save(professional)
        except Exception:
            # Si falla cedula, el usuario ya quedo creado; en flujo real se haria rollback transaccional
            # Por ahora dejamos el usuario y propagamos el error
            raise
        return saved_user
