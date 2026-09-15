from app.domain.entities.professional import Professional
from app.domain.entities.user import User, UserRole
from app.infrastructure.db.base import Base
from app.infrastructure.db.models.professional_model import ProfessionalModel  # noqa: F401
from app.infrastructure.db.models.user_model import UserModel  # noqa: F401
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.repositories.postgres_professional_repository import PostgresProfessionalRepository
from app.infrastructure.repositories.postgres_user_repository import PostgresUserRepository


def _clean():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _make_user(repo, name="Ana", last_name="Lopez", dni="11111111", email="ana@test.com", phone="1111111111", active=True):
    user = User(
        name=name,
        last_name=last_name,
        dni=dni,
        email=email,
        phone=phone,
        password_hash="hashed",
        role=UserRole.PROFESSIONAL,
        is_active=active,
    )
    return repo.save(user)


def test_save_and_exists_by_cedula():
    _clean()
    db = SessionLocal()
    try:
        u_repo = PostgresUserRepository(db)
        p_repo = PostgresProfessionalRepository(db)
        user = _make_user(u_repo)
        prof = p_repo.save(Professional(user_id=user.id, cedula="ABC1234"))
        assert prof.id is not None
        assert p_repo.exists_by_cedula("ABC1234") is True
        assert p_repo.exists_by_cedula("ZZZ9999") is False
        assert p_repo.exists_by_cedula("ABC1234", exclude_user_id=user.id) is False
        assert p_repo.get_by_cedula("ABC1234").id == prof.id
        assert p_repo.get_by_user_id(user.id).cedula == "ABC1234"
    finally:
        db.close()


def test_list_active_returns_only_active_ordered():
    _clean()
    db = SessionLocal()
    try:
        u_repo = PostgresUserRepository(db)
        p_repo = PostgresProfessionalRepository(db)
        u_carlos = _make_user(u_repo, name="Carlos", dni="11111111", email="c@test.com", phone="1111111111")
        p_repo.save(Professional(user_id=u_carlos.id, cedula="CCC1111"))
        u_ana = _make_user(u_repo, name="Ana", dni="22222222", email="a@test.com", phone="2222222222")
        p_repo.save(Professional(user_id=u_ana.id, cedula="AAA1111"))
        u_bea = _make_user(u_repo, name="Beatriz", dni="33333333", email="b@test.com", phone="3333333333")
        p_repo.save(Professional(user_id=u_bea.id, cedula="BBB1111"))
        u_inactive = _make_user(u_repo, name="Zed", dni="44444444", email="z@test.com", phone="4444444444", active=False)
        p_repo.save(Professional(user_id=u_inactive.id, cedula="ZZZ1111"))

        rows = p_repo.list_active()
        names = [u.name for u, _ in rows]
        assert names == ["Ana", "Beatriz", "Carlos"]
    finally:
        db.close()


def test_list_active_search_case_insensitive():
    _clean()
    db = SessionLocal()
    try:
        u_repo = PostgresUserRepository(db)
        p_repo = PostgresProfessionalRepository(db)
        u1 = _make_user(u_repo, name="Ana", last_name="Lopez", dni="11111111", email="a1@test.com", phone="1111111111")
        p_repo.save(Professional(user_id=u1.id, cedula="ABC1234"))
        u2 = _make_user(u_repo, name="ANA", last_name="Garcia", dni="22222222", email="a2@test.com", phone="2222222222")
        p_repo.save(Professional(user_id=u2.id, cedula="XYZ9999"))
        u3 = _make_user(u_repo, name="Carlos", dni="33333333", email="c@test.com", phone="3333333333")
        p_repo.save(Professional(user_id=u3.id, cedula="CCC1111"))

        rows = p_repo.list_active(search="ana")
        assert len(rows) == 2
        rows_full = p_repo.list_active(search="Ana Lopez")
        assert len(rows_full) == 1
        rows_ced = p_repo.list_active(search="xyz9999")
        assert len(rows_ced) == 1
    finally:
        db.close()


def test_list_deactivated():
    _clean()
    db = SessionLocal()
    try:
        u_repo = PostgresUserRepository(db)
        p_repo = PostgresProfessionalRepository(db)
        u_active = _make_user(u_repo, name="Ana", dni="11111111", email="a@test.com", phone="1111111111", active=True)
        p_repo.save(Professional(user_id=u_active.id, cedula="AAA1111"))
        u_off = _make_user(u_repo, name="Bea", dni="22222222", email="b@test.com", phone="2222222222", active=False)
        p_repo.save(Professional(user_id=u_off.id, cedula="BBB1111"))

        rows = p_repo.list_deactivated()
        assert len(rows) == 1
        assert rows[0][0].name == "Bea"
    finally:
        db.close()


def test_get_by_id_not_found():
    _clean()
    db = SessionLocal()
    try:
        p_repo = PostgresProfessionalRepository(db)
        assert p_repo.get_by_id(999999) is None
    finally:
        db.close()


def test_delete_removes_row():
    _clean()
    db = SessionLocal()
    try:
        u_repo = PostgresUserRepository(db)
        p_repo = PostgresProfessionalRepository(db)
        user = _make_user(u_repo)
        prof = p_repo.save(Professional(user_id=user.id, cedula="DEL1234"))
        assert p_repo.exists_by_cedula("DEL1234") is True
        p_repo.delete(prof)
        assert p_repo.exists_by_cedula("DEL1234") is False
    finally:
        db.close()
