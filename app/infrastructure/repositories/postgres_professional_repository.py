from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities.professional import Professional
from app.domain.entities.user import User, UserRole
from app.domain.exceptions.user_exceptions import DuplicateUserException
from app.domain.repositories.professional_repository import ProfessionalRepository
from app.infrastructure.db.models.professional_model import ProfessionalModel
from app.infrastructure.db.models.user_model import UserModel


def _to_entity(model: ProfessionalModel) -> Professional:
    return Professional(
        id=model.id,
        user_id=model.user_id,
        cedula=model.cedula,
    )


def _to_user_entity(model: UserModel) -> User:
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


def _to_model(entity: Professional) -> ProfessionalModel:
    data = dict(user_id=entity.user_id, cedula=entity.cedula)
    if entity.id is not None:
        data["id"] = entity.id
    return ProfessionalModel(**data)


class PostgresProfessionalRepository(ProfessionalRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, professional_id: int):
        model = self.db.query(ProfessionalModel).filter(ProfessionalModel.id == professional_id).first()
        return _to_entity(model) if model else None

    def get_by_cedula(self, cedula: str):
        model = self.db.query(ProfessionalModel).filter(ProfessionalModel.cedula == cedula).first()
        return _to_entity(model) if model else None

    def get_by_user_id(self, user_id: int):
        model = self.db.query(ProfessionalModel).filter(ProfessionalModel.user_id == user_id).first()
        return _to_entity(model) if model else None

    def exists_by_cedula(self, cedula: str, exclude_user_id: int | None = None) -> bool:
        query = self.db.query(ProfessionalModel).filter(ProfessionalModel.cedula == cedula)
        if exclude_user_id is not None:
            query = query.filter(ProfessionalModel.user_id != exclude_user_id)
        return query.first() is not None

    def _base_query(self, is_active: bool):
        return (
            self.db.query(UserModel, ProfessionalModel)
            .join(ProfessionalModel, ProfessionalModel.user_id == UserModel.id)
            .filter(UserModel.role == UserRole.PROFESSIONAL.value, UserModel.is_active == is_active)
        )

    def list_active(self, search: str | None = None) -> list[tuple[User, Professional]]:
        query = self._base_query(True)
        if search is not None and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(UserModel.name).like(term),
                    func.lower(UserModel.last_name).like(term),
                    func.lower(func.concat(UserModel.name, " ", UserModel.last_name)).like(term),
                    func.lower(ProfessionalModel.cedula).like(term),
                )
            )
        query = query.order_by(func.lower(UserModel.name).asc(), func.lower(UserModel.last_name).asc())
        return [(_to_user_entity(u), _to_entity(p)) for u, p in query.all()]

    def list_deactivated(self) -> list[tuple[User, Professional]]:
        query = self._base_query(False).order_by(func.lower(UserModel.name).asc(), func.lower(UserModel.last_name).asc())
        return [(_to_user_entity(u), _to_entity(p)) for u, p in query.all()]

    def save(self, professional: Professional) -> Professional:
        try:
            model = _to_model(professional)
            self.db.add(model)
            self.db.commit()
            self.db.refresh(model)
            return _to_entity(model)
        except IntegrityError as e:
            self.db.rollback()
            raise DuplicateUserException("Usuario ya registrado") from e

    def delete(self, professional: Professional) -> None:
        if professional.id is None:
            return
        model = self.db.query(ProfessionalModel).filter(ProfessionalModel.id == professional.id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
