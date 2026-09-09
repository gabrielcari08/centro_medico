from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities.user import User, UserRole
from app.domain.exceptions.user_exceptions import DuplicateEmailException, DuplicateUserException
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.db.models.user_model import UserModel


def _to_entity(model: UserModel) -> User:
    # Mapeo ORM -> entidad de dominio
    return User(
        id=model.id,
        name=model.name,
        last_name=model.last_name,
        dni=model.dni,
        email=model.email,
        phone=model.phone,
        password_hash=model.password_hash,
        role=UserRole(model.role),
        is_active=model.is_active,
        created_at=model.created_at,
    )


def _to_model(entity: User) -> UserModel:
    data = dict(
        name=entity.name,
        last_name=entity.last_name,
        dni=entity.dni,
        email=entity.email,
        phone=entity.phone,
        password_hash=entity.password_hash,
        role=entity.role.value,
        is_active=entity.is_active,
        created_at=entity.created_at,
    )
    if entity.id is not None:
        data["id"] = entity.id
    return UserModel(**data)


class PostgresUserRepository(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str):
        model = self.db.query(UserModel).filter(UserModel.email == email.lower()).first()
        return _to_entity(model) if model else None

    def get_by_dni(self, dni: str):
        model = self.db.query(UserModel).filter(UserModel.dni == dni).first()
        return _to_entity(model) if model else None

    def get_by_phone(self, phone: str):
        model = self.db.query(UserModel).filter(UserModel.phone == phone).first()
        return _to_entity(model) if model else None

    def get_by_id(self, user_id: int):
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return _to_entity(model) if model else None

    def exists_by_email(self, email: str) -> bool:
        return self.db.query(UserModel).filter(UserModel.email == email.lower()).first() is not None

    def exists_by_dni(self, dni: str) -> bool:
        return self.db.query(UserModel).filter(UserModel.dni == dni).first() is not None

    def exists_by_phone(self, phone: str) -> bool:
        return self.db.query(UserModel).filter(UserModel.phone == phone).first() is not None

    def exists_by_role(self, role: UserRole) -> bool:
        return self.db.query(UserModel).filter(UserModel.role == role.value).first() is not None

    def save(self, user: User) -> User:
        # Defensa en profundidad: captura violaciones de unicidad a nivel DB
        try:
            model = _to_model(user)
            self.db.add(model)
            self.db.commit()
            self.db.refresh(model)
            return _to_entity(model)
        except IntegrityError as e:
            self.db.rollback()
            msg = str(e.orig) if hasattr(e, "orig") else str(e)
            if "email" in msg.lower():
                raise DuplicateEmailException("email ya registrado") from e
            raise DuplicateUserException("Usuario ya registrado") from e
