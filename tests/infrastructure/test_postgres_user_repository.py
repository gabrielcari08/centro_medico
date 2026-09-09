from app.domain.entities.user import User, UserRole
from app.infrastructure.db.base import Base
from app.infrastructure.db.models.professional_model import ProfessionalModel  # noqa: F401
from app.infrastructure.db.models.user_model import UserModel  # noqa: F401
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.repositories.postgres_user_repository import PostgresUserRepository


def _clean():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_save_and_exists():
    _clean()
    db = SessionLocal()
    try:
        repo = PostgresUserRepository(db)
        user = User(
            name="Ana",
            last_name="Lopez",
            dni="11111111",
            email="ana@test.com",
            phone="1111111111",
            password_hash="hashed",
            role=UserRole.RECEPTIONIST,
        )
        saved = repo.save(user)
        assert repo.exists_by_email("ana@test.com") is True
        assert repo.exists_by_dni("11111111") is True
        assert repo.exists_by_phone("1111111111") is True
        assert repo.get_by_email("ana@test.com").email == "ana@test.com"
        assert saved.id is not None
    finally:
        db.close()


def test_duplicate_integrity():
    _clean()
    db = SessionLocal()
    try:
        repo = PostgresUserRepository(db)
        u1 = User(name="A", last_name="B", dni="22222222", email="dup@test.com", phone="2222222222", password_hash="h", role=UserRole.RECEPTIONIST)
        repo.save(u1)
        u2 = User(name="C", last_name="D", dni="22222222", email="dup2@test.com", phone="3333333333", password_hash="h", role=UserRole.RECEPTIONIST)
        try:
            repo.save(u2)
            assert False, "should have raised"
        except Exception as e:
            assert "Usuario ya registrado" in str(e)
    finally:
        db.close()



