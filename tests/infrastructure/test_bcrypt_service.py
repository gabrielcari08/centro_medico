from app.infrastructure.services.bcrypt_password_service import BcryptPasswordService


def test_hash_and_verify():
    svc = BcryptPasswordService()
    hashed = svc.hash("gabi12345")
    assert hashed != "gabi12345"
    assert svc.verify("gabi12345", hashed) is True
    assert svc.verify("wrong", hashed) is False
