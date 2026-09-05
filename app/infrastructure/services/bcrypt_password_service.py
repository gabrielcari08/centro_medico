from passlib.context import CryptContext

from app.domain.services.password_service import PasswordService


class BcryptPasswordService(PasswordService):
    def __init__(self):
        # Contexto bcrypt con manejo automatico de salt
        self._ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, plain: str) -> str:
        return self._ctx.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        return self._ctx.verify(plain, hashed)
