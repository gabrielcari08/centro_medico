from unittest.mock import MagicMock

import pytest

from app.application.dtos.user_dtos import CreateReceptionistRequest
from app.application.use_cases.user.create_receptionist import CreateReceptionistUseCase
from app.domain.exceptions.user_exceptions import DuplicateEmailException, DuplicateUserException
from app.domain.entities.user import UserRole


def _make_repo_mock(email=False, dni=False, phone=False):
    repo = MagicMock()
    repo.exists_by_email.return_value = email
    repo.exists_by_dni.return_value = dni
    repo.exists_by_phone.return_value = phone
    def save_side_effect(user):
        user.id = 1
        return user
    repo.save.side_effect = save_side_effect
    return repo


def _make_pwd_mock():
    pwd = MagicMock()
    pwd.hash.return_value = "hashed_pwd"
    return pwd


def test_success_returns_active_user():
    repo = _make_repo_mock()
    pwd = _make_pwd_mock()
    uc = CreateReceptionistUseCase(repo, pwd)
    dto = CreateReceptionistRequest(
        name="Ana",
        last_name="Lopez",
        dni="11111111",
        email="ana@test.com",
        phone="1111111111",
        password="password123",
    )
    result = uc.execute(dto)
    assert result.is_active is True
    assert result.role == UserRole.RECEPTIONIST
    assert result.password_hash == "hashed_pwd"
    assert result.id == 1
    pwd.hash.assert_called_once_with("password123")


def test_duplicate_email_raises():
    repo = _make_repo_mock(email=True)
    pwd = _make_pwd_mock()
    uc = CreateReceptionistUseCase(repo, pwd)
    dto = CreateReceptionistRequest(
        name="Ana", last_name="Lopez", dni="11111111", email="ana@test.com", phone="1111111111", password="password123"
    )
    with pytest.raises(DuplicateEmailException, match="email ya registrado"):
        uc.execute(dto)


def test_duplicate_dni_raises():
    repo = _make_repo_mock(dni=True)
    pwd = _make_pwd_mock()
    uc = CreateReceptionistUseCase(repo, pwd)
    dto = CreateReceptionistRequest(
        name="Ana", last_name="Lopez", dni="11111111", email="ana@test.com", phone="1111111111", password="password123"
    )
    with pytest.raises(DuplicateUserException, match="Usuario ya registrado"):
        uc.execute(dto)


def test_duplicate_phone_raises():
    repo = _make_repo_mock(phone=True)
    pwd = _make_pwd_mock()
    uc = CreateReceptionistUseCase(repo, pwd)
    dto = CreateReceptionistRequest(
        name="Ana", last_name="Lopez", dni="11111111", email="ana@test.com", phone="1111111111", password="password123"
    )
    with pytest.raises(DuplicateUserException, match="Usuario ya registrado"):
        uc.execute(dto)
