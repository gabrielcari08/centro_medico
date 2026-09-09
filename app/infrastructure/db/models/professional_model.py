from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.infrastructure.db.base import Base


class ProfessionalModel(Base):
    # Tabla exclusiva para profesionales - relacionada 1:1 con users
    __tablename__ = "professionals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    cedula = Column(String(8), unique=True, nullable=False)

    user = relationship("UserModel", backref="professional", passive_deletes=True)

    __table_args__ = (
        CheckConstraint("cedula ~ '^[A-Za-z0-9]{7,8}$'", name="ck_professionals_cedula_format"),
    )
