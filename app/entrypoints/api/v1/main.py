from contextlib import asynccontextmanager

from fastapi import FastAPI

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


@app.get("/health")
def health():
    return {"status": "ok"}
