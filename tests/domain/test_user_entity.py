import pytest
from app.domain.entities.user import User, UserRole


def test_invariants_receptionist_with_cedula_raises():
    with pytest.raises(ValueError):
        User(
            name="Ana",
            last_name="Lopez",
            dni="12345678",
            email="ana@test.com",
            phone="1234567890",
            password_hash="hashed",
            role=UserRole.RECEPTIONIST,
            cedula="ABC1234",
        )


def test_invariants_professional_without_cedula_raises():
    with pytest.raises(ValueError):
        User(
            name="Ana",
            last_name="Lopez",
            dni="12345678",
            email="ana@test.com",
            phone="1234567890",
            password_hash="hashed",
            role=UserRole.PROFESSIONAL,
            cedula=None,
        )


def test_invariants_professional_with_cedula_ok():
    user = User(
        name="Ana",
        last_name="Lopez",
        dni="12345678",
        email="ana@test.com",
        phone="1234567890",
        password_hash="hashed",
        role=UserRole.PROFESSIONAL,
        cedula="ABC1234",
    )
    assert user.cedula == "ABC1234"
    assert user.is_active is True


def test_invariants_is_active_default_true():
    user = User(
        name="Ana",
        last_name="Lopez",
        dni="12345678",
        email="ana@test.com",
        phone="1234567890",
        password_hash="hashed",
        role=UserRole.RECEPTIONIST,
    )
    assert user.is_active is True


def test_invariants_missing_name_raises():
    with pytest.raises(ValueError, match="Campos faltantes"):
        User(
            name="  ",
            last_name="Lopez",
            dni="12345678",
            email="ana@test.com",
            phone="1234567890",
            password_hash="hashed",
            role=UserRole.RECEPTIONIST,
        )
