from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.application.use_cases.user.create_professional import CreateProfessionalUseCase
from app.application.use_cases.user.create_receptionist import CreateReceptionistUseCase
from app.domain.entities.user import UserRole
from app.infrastructure.config.settings import Settings
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.repositories.postgres_professional_repository import PostgresProfessionalRepository
from app.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from app.infrastructure.services.bcrypt_password_service import BcryptPasswordService

settings = Settings()
security = HTTPBearer()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def get_db():
    # Entrega sesion DB y garantiza cierre
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_repository(db: Session = Depends(get_db)):
    return PostgresUserRepository(db)


def get_professional_repository(db: Session = Depends(get_db)):
    return PostgresProfessionalRepository(db)


def get_password_service():
    return BcryptPasswordService()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    # Verifica JWT y que el rol sea administrador
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if email is None or role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if role != UserRole.ADMINISTRATOR.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    repo = PostgresUserRepository(db)
    user = repo.get_by_email(email)
    if not user or user.role != UserRole.ADMINISTRATOR:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user


def get_create_receptionist_use_case(
    repo=Depends(get_user_repository),
    pwd=Depends(get_password_service),
):
    return CreateReceptionistUseCase(repo, pwd)


def get_create_professional_use_case(
    repo=Depends(get_user_repository),
    prof_repo=Depends(get_professional_repository),
    pwd=Depends(get_password_service),
):
    return CreateProfessionalUseCase(repo, prof_repo, pwd)
