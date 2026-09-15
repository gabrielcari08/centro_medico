from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities.user import User, UserRole
from app.domain.exceptions.user_exceptions import DuplicateEmailException, DuplicateUserException
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.db.models.user_model import UserModel


def _to_entity(model: UserModel) -> User:
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
        updated_at=model.updated_at,
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
        updated_at=entity.updated_at,
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

    # Implements exclude_id
    def exists_by_email(self, email: str, exclude_id: int | None = None) -> bool:
        query = self.db.query(UserModel).filter(UserModel.email == email.lower())
        if exclude_id is not None:
            query = query.filter(UserModel.id != exclude_id)
        return query.first() is not None

    def exists_by_dni(self, dni: str, exclude_id: int | None = None) -> bool:
        query = self.db.query(UserModel).filter(UserModel.dni == dni)
        if exclude_id is not None:
            query = query.filter(UserModel.id != exclude_id)
        return query.first() is not None

    def exists_by_phone(self, phone: str, exclude_id: int | None = None) -> bool:
        query = self.db.query(UserModel).filter(UserModel.phone == phone)
        if exclude_id is not None:
            query = query.filter(UserModel.id != exclude_id)
        return query.first() is not None

    def exists_by_role(self, role: UserRole) -> bool:
        return self.db.query(UserModel).filter(UserModel.role == role.value).first() is not None

    def save(self, user: User) -> User:
        try:
            if user.id is not None:
                existing = self.db.query(UserModel).filter(UserModel.id == user.id).first()
                if existing is not None:
                    existing.name = user.name
                    existing.last_name = user.last_name
                    existing.dni = user.dni
                    existing.email = user.email.lower()
                    existing.phone = user.phone
                    existing.password_hash = user.password_hash
                    existing.role = user.role.value
                    existing.is_active = user.is_active
                    existing.updated_at = datetime.now(timezone.utc)
                    self.db.commit()
                    self.db.refresh(existing)
                    return _to_entity(existing)
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

    # Implements delete method
    def delete(self, user: User) -> None:
        if user.id is None:
            return
        from app.infrastructure.db.models.professional_model import ProfessionalModel

        self.db.query(ProfessionalModel).filter(ProfessionalModel.user_id == user.id).delete(synchronize_session=False)
        model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if model:
            self.db.delete(model)
            self.db.commit()