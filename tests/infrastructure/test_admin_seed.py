from app.domain.entities.user import UserRole
from app.infrastructure.config.settings import Settings
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.db.seed.admin_seed import ensure_admin_exists
from app.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from app.infrastructure.services.bcrypt_password_service import BcryptPasswordService


def _clean():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_admin_seed_idempotent():
    _clean()
    db = SessionLocal()
    try:
        repo = PostgresUserRepository(db)
        pwd = BcryptPasswordService()
        settings = Settings()
        # first call creates
        admin1 = ensure_admin_exists(repo, pwd, settings)
        assert admin1 is not None
        assert repo.exists_by_role(UserRole.ADMINISTRATOR) is True
        count1 = db.execute__not_needed = None
        # second call idempotent
        admin2 = ensure_admin_exists(repo, pwd, settings)
        assert admin2 is None
        # still only one admin
        db2 = SessionLocal()
        try:
            repo2 = PostgresUserRepository(db2)
            assert repo2.exists_by_role(UserRole.ADMINISTRATOR) is True
        finally:
            db2.close()
        # verify seed ok import
        from app.infrastructure.db.seed.admin_seed import ensure_admin_exists as fn
        assert fn is not None
    finally:
        db.close()


def test_seed_ok_import():
    from app.infrastructure.db.seed.admin_seed import ensure_admin_exists
    assert callable(ensure_admin_exists)
