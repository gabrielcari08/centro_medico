from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.domain.entities.user import UserRole
from app.entrypoints.api.v1.dependencies import create_access_token, get_password_service, get_user_repository
from app.infrastructure.config.settings import Settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    name: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, repo=Depends(get_user_repository), pwd=Depends(get_password_service)):
    settings = Settings()
    login_name = payload.name.strip()
    # Buscar admin por email sintetico
    admin = repo.get_by_email("admin@centro.local")

    is_admin_login = False
    if admin and admin.role == UserRole.ADMINISTRATOR:
        if login_name == settings.NAME or login_name.lower() == admin.email.lower():
            is_admin_login = True

    if is_admin_login:
        if not admin.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        if not pwd.verify(payload.password, admin.password_hash):
            if payload.password != settings.PASSWORD:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        token = create_access_token({"sub": admin.email, "role": admin.role.value})
        return LoginResponse(access_token=token)

    # Login general para cualquier usuario (profesionales, recepcionistas) por email
    user = repo.get_by_email(login_name.lower())
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if not pwd.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token = create_access_token({"sub": user.email, "role": user.role.value})
    return LoginResponse(access_token=token)
