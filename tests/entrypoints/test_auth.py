from fastapi.testclient import TestClient

from app.domain.entities.user import User, UserRole
from app.entrypoints.api.v1.main import app
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from app.infrastructure.services.bcrypt_password_service import BcryptPasswordService

client = TestClient(app)


def _clean():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # re-seed admin via lifespan logic
    from app.infrastructure.config.settings import Settings
    from app.infrastructure.db.seed.admin_seed import ensure_admin_exists

    db = SessionLocal()
    try:
        repo = PostgresUserRepository(db)
        pwd = BcryptPasswordService()
        ensure_admin_exists(repo, pwd, Settings())
    finally:
        db.close()


def test_login_success():
    _clean()
    r = client.post("/api/v1/auth/login", json={"name": "Gabriel Cari", "password": "gabi12345"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password():
    _clean()
    r = client.post("/api/v1/auth/login", json={"name": "Gabriel Cari", "password": "wrongpass"})
    assert r.status_code == 401


def test_get_current_admin_forbidden_for_receptionist():
    _clean()
    # crear receptionist y generar token
    from app.entrypoints.api.v1.dependencies import create_access_token

    db = SessionLocal()
    try:
        repo = PostgresUserRepository(db)
        pwd = BcryptPasswordService()
        user = User(name="Ana", last_name="Lopez", dni="11111111", email="ana@test.com", phone="1111111111", password_hash=pwd.hash("password123"), role=UserRole.RECEPTIONIST)
        repo.save(user)
    finally:
        db.close()

    token = create_access_token({"sub": "ana@test.com", "role": "receptionist"})
    r = client.post(
        "/api/v1/users/receptionists",
        json={"name": "Bob", "last_name": "Test", "dni": "22222222", "email": "bob@test.com", "phone": "2222222222", "password": "password123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
