from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.entrypoints.api.v1.routes import auth_router, user_router
from app.infrastructure.config.settings import Settings
from app.infrastructure.db.base import Base
from app.infrastructure.db.seed.admin_seed import ensure_admin_exists
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from app.infrastructure.services.bcrypt_password_service import BcryptPasswordService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas y seed del administrador al iniciar
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        repo = PostgresUserRepository(db)
        pwd = BcryptPasswordService()
        ensure_admin_exists(repo, pwd, Settings())
    finally:
        db.close()
    yield


app = FastAPI(title="Centro Médico", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Mapear errores de validacion a mensajes del spec
    errors = exc.errors()
    for err in errors:
        msg = err.get("msg", "")
        err_type = err.get("type", "")
        # Campos faltantes -> 400
        if err_type == "missing":
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Campos faltantes"})
        # Mensajes custom de Pydantic ya contienen literales del spec
        if "Campos faltantes" in msg:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Campos faltantes"})
        if "email invalido" in msg:
            return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": "email invalido"})
        if "Formato inválido" in msg:
            return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": msg.replace("Value error, ", "")})
        if "La contraseña" in msg:
            return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": msg.replace("Value error, ", "")})
    # Fallback generico 422 con primer mensaje limpio
    first = errors[0].get("msg", "Validation error").replace("Value error, ", "")
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": first})


app.include_router(auth_router.router)
app.include_router(user_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}
