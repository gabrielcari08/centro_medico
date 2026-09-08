from app.application.dtos.user_dtos import CreateReceptionistRequest
from app.domain.entities.user import User, UserRole
from app.domain.exceptions.user_exceptions import DuplicateEmailException, DuplicateUserException
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_service import PasswordService


class CreateReceptionistUseCase:
    def __init__(self, user_repo: UserRepository, pwd_service: PasswordService):
        self.user_repo = user_repo
        self.pwd_service = pwd_service

    def execute(self, dto: CreateReceptionistRequest) -> User:
        # Validaciones de unicidad en orden especifico para mensajes correctos
        if self.user_repo.exists_by_email(dto.email):
            raise DuplicateEmailException("email ya registrado")
        if self.user_repo.exists_by_dni(dto.dni):
            raise DuplicateUserException("Usuario ya registrado")
        if self.user_repo.exists_by_phone(dto.phone):
            raise DuplicateUserException("Usuario ya registrado")

        hashed = self.pwd_service.hash(dto.password)
        user = User(
            name=dto.name,
            last_name=dto.last_name,
            dni=dto.dni,
            email=dto.email,
            phone=dto.phone,
            password_hash=hashed,
            role=UserRole.RECEPTIONIST,
            cedula=None,
            is_active=True,
        )
        return self.user_repo.save(user)
