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


def test_exists_exclude_id():
    _clean()
    db = SessionLocal()
    try:
        repo = PostgresUserRepository(db)
        u1 = repo.save(User(name="A", last_name="B", dni="11111111", email="a@test.com", phone="1111111111", password_hash="h", role=UserRole.RECEPTIONIST))
        u2 = repo.save(User(name="C", last_name="D", dni="22222222", email="b@test.com", phone="2222222222", password_hash="h", role=UserRole.RECEPTIONIST))
        assert repo.exists_by_email("a@test.com", exclude_id=u1.id) is False
        assert repo.exists_by_email("a@test.com", exclude_id=u2.id) is True
        assert repo.exists_by_dni("11111111", exclude_id=u1.id) is False
        assert repo.exists_by_dni("11111111", exclude_id=u2.id) is True
        assert repo.exists_by_phone("1111111111", exclude_id=u1.id) is False
        assert repo.exists_by_phone("1111111111", exclude_id=u2.id) is True
    finally:
        db.close()


def test_save_update_touches_updated_at():
    _clean()
    db = SessionLocal()
    try:
        repo = PostgresUserRepository(db)
        saved = repo.save(User(name="Ana", last_name="Lopez", dni="33333333", email="u@test.com", phone="3333333333", password_hash="h", role=UserRole.RECEPTIONIST))
        old_updated = saved.updated_at
        saved.name = "Anita"
        updated = repo.save(saved)
        assert updated.name == "Anita"
        assert updated.id == saved.id
        assert updated.updated_at >= old_updated
    finally:
        db.close()


def test_delete_cascades_professional():
    _clean()
    db = SessionLocal()
    try:
        from app.domain.entities.professional import Professional
        from app.infrastructure.repositories.postgres_professional_repository import PostgresProfessionalRepository

        u_repo = PostgresUserRepository(db)
        p_repo = PostgresProfessionalRepository(db)
        user = u_repo.save(User(name="Pro", last_name="T", dni="44444444", email="p@test.com", phone="4444444444", password_hash="h", role=UserRole.PROFESSIONAL))
        p_repo.save(Professional(user_id=user.id, cedula="ABC1234"))
        assert p_repo.exists_by_cedula("ABC1234") is True
        u_repo.delete(user)
        assert u_repo.get_by_id(user.id) is None
        assert p_repo.exists_by_cedula("ABC1234") is False
    finally:
        db.close()



