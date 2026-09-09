from fastapi.testclient import TestClient

from app.entrypoints.api.v1.main import app
from app.infrastructure.db.base import Base
from app.infrastructure.db.models.professional_model import ProfessionalModel  # noqa: F401
from app.infrastructure.db.models.user_model import UserModel  # noqa: F401
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from app.infrastructure.services.bcrypt_password_service import BcryptPasswordService
from app.infrastructure.config.settings import Settings
from app.infrastructure.db.seed.admin_seed import ensure_admin_exists

client = TestClient(app)


def _clean_and_login():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        repo = PostgresUserRepository(db)
        pwd = BcryptPasswordService()
        ensure_admin_exists(repo, pwd, Settings())
    finally:
        db.close()
    r = client.post("/api/v1/auth/login", json={"name": "Gabriel Cari", "password": "gabi12345"})
    assert r.status_code == 200
    return r.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_receptionist_success():
    token = _clean_and_login()
    payload = {"name": "Ana", "last_name": "Lopez", "dni": "11111111", "email": "ana@test.com", "phone": "1111111111", "password": "password123"}
    r = client.post("/api/v1/users/receptionists", json=payload, headers=_auth(token))
    assert r.status_code == 201
    assert r.json()["email"] == "ana@test.com"


def test_create_professional_success():
    token = _clean_and_login()
    payload = {"name": "Pro", "last_name": "Test", "dni": "22222222", "email": "pro@test.com", "phone": "2222222222", "password": "password123", "cedula": "ABC1234"}
    r = client.post("/api/v1/users/professionals", json=payload, headers=_auth(token))
    assert r.status_code == 201
    assert r.json()["cedula"] == "ABC1234"


def test_duplicate_email():
    token = _clean_and_login()
    payload = {"name": "Ana", "last_name": "L", "dni": "11111111", "email": "dup@test.com", "phone": "1111111111", "password": "password123"}
    client.post("/api/v1/users/receptionists", json=payload, headers=_auth(token))
    payload2 = {"name": "Bob", "last_name": "T", "dni": "22222222", "email": "dup@test.com", "phone": "2222222222", "password": "password123"}
    r = client.post("/api/v1/users/receptionists", json=payload2, headers=_auth(token))
    assert r.status_code == 409
    assert r.json()["detail"] == "email ya registrado"


def test_duplicate_dni():
    token = _clean_and_login()
    p1 = {"name": "Ana", "last_name": "L", "dni": "11111111", "email": "a1@test.com", "phone": "1111111111", "password": "password123"}
    client.post("/api/v1/users/receptionists", json=p1, headers=_auth(token))
    p2 = {"name": "Bob", "last_name": "T", "dni": "11111111", "email": "b2@test.com", "phone": "2222222222", "password": "password123"}
    r = client.post("/api/v1/users/receptionists", json=p2, headers=_auth(token))
    assert r.status_code == 409
    assert r.json()["detail"] == "Usuario ya registrado"


def test_duplicate_phone():
    token = _clean_and_login()
    p1 = {"name": "Ana", "last_name": "L", "dni": "11111111", "email": "a1@test.com", "phone": "1111111111", "password": "password123"}
    client.post("/api/v1/users/receptionists", json=p1, headers=_auth(token))
    p2 = {"name": "Bob", "last_name": "T", "dni": "22222222", "email": "b2@test.com", "phone": "1111111111", "password": "password123"}
    r = client.post("/api/v1/users/receptionists", json=p2, headers=_auth(token))
    assert r.status_code == 409
    assert "Usuario ya registrado" in r.json()["detail"]


def test_duplicate_cedula():
    token = _clean_and_login()
    p1 = {"name": "Pro1", "last_name": "T", "dni": "11111111", "email": "p1@test.com", "phone": "1111111111", "password": "password123", "cedula": "ABC1234"}
    client.post("/api/v1/users/professionals", json=p1, headers=_auth(token))
    p2 = {"name": "Pro2", "last_name": "T", "dni": "22222222", "email": "p2@test.com", "phone": "2222222222", "password": "password123", "cedula": "ABC1234"}
    r = client.post("/api/v1/users/professionals", json=p2, headers=_auth(token))
    assert r.status_code == 409


def test_missing_fields():
    token = _clean_and_login()
    r = client.post("/api/v1/users/receptionists", json={"name": "Ana"}, headers=_auth(token))
    assert r.status_code == 400
    assert r.json()["detail"] == "Campos faltantes"


def test_invalid_email():
    token = _clean_and_login()
    payload = {"name": "Ana", "last_name": "L", "dni": "11111111", "email": "ana-at-test.com", "phone": "1111111111", "password": "password123"}
    r = client.post("/api/v1/users/receptionists", json=payload, headers=_auth(token))
    assert r.status_code == 422
    assert r.json()["detail"] == "email invalido"


def test_invalid_dni():
    token = _clean_and_login()
    payload = {"name": "Ana", "last_name": "L", "dni": "123", "email": "ana@test.com", "phone": "1111111111", "password": "password123"}
    r = client.post("/api/v1/users/receptionists", json=payload, headers=_auth(token))
    assert r.status_code == 422
    assert "Formato inválido, debe tener 8 caracteres" in r.json()["detail"]


def test_invalid_phone():
    token = _clean_and_login()
    payload = {"name": "Ana", "last_name": "L", "dni": "11111111", "email": "ana@test.com", "phone": "123", "password": "password123"}
    r = client.post("/api/v1/users/receptionists", json=payload, headers=_auth(token))
    assert r.status_code == 422
    assert "Formato inválido, debe tener 10 caracteres" in r.json()["detail"]


def test_invalid_cedula():
    token = _clean_and_login()
    payload = {"name": "Pro", "last_name": "T", "dni": "11111111", "email": "pro@test.com", "phone": "1111111111", "password": "password123", "cedula": "abc"}
    r = client.post("/api/v1/users/professionals", json=payload, headers=_auth(token))
    assert r.status_code == 422
    assert "Formato inválido, debe tener 7 u 8 caracteres" in r.json()["detail"]


def test_password_too_short():
    token = _clean_and_login()
    payload = {"name": "Ana", "last_name": "L", "dni": "11111111", "email": "ana@test.com", "phone": "1111111111", "password": "short"}
    r = client.post("/api/v1/users/receptionists", json=payload, headers=_auth(token))
    assert r.status_code == 422
    assert "La contraseña debe tener al menos 8 caracteres" in r.json()["detail"]


def test_non_admin_forbidden():
    token = _clean_and_login()
    # crear receptionist y sacar token receptionist
    client.post("/api/v1/users/receptionists", json={"name": "Ana", "last_name": "L", "dni": "11111111", "email": "ana@test.com", "phone": "1111111111", "password": "password123"}, headers=_auth(token))
    from app.entrypoints.api.v1.dependencies import create_access_token
    recep_token = create_access_token({"sub": "ana@test.com", "role": "receptionist"})
    r = client.post("/api/v1/users/receptionists", json={"name": "Bob", "last_name": "T", "dni": "22222222", "email": "bob@test.com", "phone": "2222222222", "password": "password123"}, headers=_auth(recep_token))
    assert r.status_code == 403


def test_no_token_unauthorized():
    payload = {"name": "Ana", "last_name": "L", "dni": "11111111", "email": "ana@test.com", "phone": "1111111111", "password": "password123"}
    r = client.post("/api/v1/users/receptionists", json=payload)
    assert r.status_code in (401, 403)
