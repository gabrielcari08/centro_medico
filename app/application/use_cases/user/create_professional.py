from app.application.dtos.user_dtos import CreateProfessionalRequest
from app.domain.entities.user import User, UserRole
from app.domain.exceptions.user_exceptions import DuplicateEmailException, DuplicateUserException
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_service import PasswordService


class CreateProfessionalUseCase:
    def __init__(self, user_repo: UserRepository, pwd_service: PasswordService):
        self.user_repo = user_repo
        self.pwd_service = pwd_service

    # Receives the already validated DTO: CreateProfessionalRequest.
    # Verifies if the user already exists in the database.
    def execute(self, dto: CreateProfessionalRequest) -> User:
        if self.user_repo.exists_by_email(dto.email):
            raise DuplicateEmailException("email ya registrado")
        if self.user_repo.exists_by_dni(dto.dni):
            raise DuplicateUserException("Usuario ya registrado")
        if self.user_repo.exists_by_phone(dto.phone):
            raise DuplicateUserException("Usuario ya registrado")
        if self.user_repo.exists_by_cedula(dto.cedula):
            raise DuplicateUserException("Usuario ya registrado")

        # Encrypt password.
        hashed = self.pwd_service.hash(dto.password)
        # Create user entity.
        user = User(
            name=dto.name,
            last_name=dto.last_name,
            dni=dto.dni,
            email=dto.email,
            phone=dto.phone,
            password_hash=hashed,
            role=UserRole.PROFESSIONAL,
            cedula=dto.cedula,
            is_active=True,
        )
        # Save user in database.
        return self.user_repo.save(user)
