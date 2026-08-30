from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.config.settings import Settings

# Motor de conexion usando DATABASE_URL del .env
_settings = Settings()
engine = create_engine(_settings.DATABASE_URL, pool_pre_ping=True)

# Fabrica de sesiones sincronas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    # Dependencia para FastAPI - entrega sesion y garantiza cierre
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
