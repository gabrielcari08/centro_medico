from app.domain.entities.user import User, UserRole
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_service import PasswordService
from app.infrastructure.config.settings import Settings


def ensure_admin_exists(
    user_repo: UserRepository,
    pwd_service: PasswordService,
    settings: Settings | None = None,
) -> User | None:
    # Usa .env NAME y PASSWORD para crear el unico administrador
    cfg = settings or Settings()
    if not cfg.NAME or not cfg.PASSWORD:
        return None

    if user_repo.exists_by_role(UserRole.ADMINISTRATOR):
        return None

    # Split NAME en nombre y apellido
    parts = cfg.NAME.strip().split()
    name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else name

    # Datos sinteticos unicos para admin (no provistos por .env)
    admin = User(
        name=name,
        last_name=last_name,
        dni="00000000",
        email="admin@centro.local",
        phone="0000000000",
        password_hash=pwd_service.hash(cfg.PASSWORD),
        role=UserRole.ADMINISTRATOR,
        is_active=True,
    )
    return user_repo.save(admin)
