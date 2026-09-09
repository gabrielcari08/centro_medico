from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities.professional import Professional
from app.domain.exceptions.user_exceptions import DuplicateUserException
from app.domain.repositories.professional_repository import ProfessionalRepository
from app.infrastructure.db.models.professional_model import ProfessionalModel


def _to_entity(model: ProfessionalModel) -> Professional:
    return Professional(
        id=model.id,
        user_id=model.user_id,
        cedula=model.cedula,
    )


def _to_model(entity: Professional) -> ProfessionalModel:
    data = dict(user_id=entity.user_id, cedula=entity.cedula)
    if entity.id is not None:
        data["id"] = entity.id
    return ProfessionalModel(**data)


class PostgresProfessionalRepository(ProfessionalRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_cedula(self, cedula: str):
        model = self.db.query(ProfessionalModel).filter(ProfessionalModel.cedula == cedula).first()
        return _to_entity(model) if model else None

    def get_by_user_id(self, user_id: int):
        model = self.db.query(ProfessionalModel).filter(ProfessionalModel.user_id == user_id).first()
        return _to_entity(model) if model else None

    def exists_by_cedula(self, cedula: str) -> bool:
        return self.db.query(ProfessionalModel).filter(ProfessionalModel.cedula == cedula).first() is not None

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
