from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.infrastructure.db.base import Base


class UserModel(Base):
    # Tabla base para todos los roles - cedula ya no vive aqui
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dni = Column(String(8), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(10), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("dni ~ '^\\d{8}$'", name="ck_users_dni_8digits"),
        CheckConstraint("phone ~ '^\\d{10}$'", name="ck_users_phone_10digits"),
        CheckConstraint("role IN ('administrator','receptionist','professional')", name="ck_users_role"),
    )
