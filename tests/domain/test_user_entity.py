import pytest
from app.domain.entities.professional import Professional
from app.domain.entities.user import User, UserRole


def test_invariants_receptionist_ok():
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


def test_invariants_professional_ok():
    user = User(
        name="Ana",
        last_name="Lopez",
        dni="12345678",
        email="ana@test.com",
        phone="1234567890",
        password_hash="hashed",
        role=UserRole.PROFESSIONAL,
    )
    assert user.role == UserRole.PROFESSIONAL


def test_professional_cedula_ok():
    prof = Professional(user_id=1, cedula="ABC1234")
    assert prof.cedula == "ABC1234"


def test_professional_cedula_empty_raises():
    with pytest.raises(ValueError, match="Campos faltantes"):
        Professional(user_id=1, cedula="  ")


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
