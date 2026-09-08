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
    # Autenticacion solo para administrador pre-provisionado
    settings = Settings()
    # Buscar admin por email sintetico
    admin = repo.get_by_email("admin@centro.local")
    if not admin or admin.role != UserRole.ADMINISTRATOR:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    # Verificar que el nombre coincida con .env NAME y password con hash
    if payload.name.strip() != settings.NAME:
        # tambien aceptar email del admin como alias
        if payload.name.strip().lower() != admin.email.lower():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if not pwd.verify(payload.password, admin.password_hash):
        # Fallback directo a Settings.PASSWORD en caso de desincronizacion de hash
        if payload.password != settings.PASSWORD:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    token = create_access_token({"sub": admin.email, "role": admin.role.value})
    return LoginResponse(access_token=token)
