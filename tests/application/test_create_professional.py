from unittest.mock import MagicMock

import pytest

from app.application.dtos.user_dtos import CreateProfessionalRequest
from app.application.use_cases.user.create_professional import CreateProfessionalUseCase
from app.domain.entities.user import UserRole
from app.domain.exceptions.user_exceptions import DuplicateUserException, DuplicateEmailException


def _make_user_repo(email=False, dni=False, phone=False):
    repo = MagicMock()
    repo.exists_by_email.return_value = email
    repo.exists_by_dni.return_value = dni
    repo.exists_by_phone.return_value = phone
    def save_side_effect(user):
        user.id = 2
        return user
    repo.save.side_effect = save_side_effect
    return repo


def _make_prof_repo(cedula=False):
    repo = MagicMock()
    repo.exists_by_cedula.return_value = cedula
    def save_side_effect(prof):
        prof.id = 1
        return prof
    repo.save.side_effect = save_side_effect
    return repo


def _make_pwd_mock():
    pwd = MagicMock()
    pwd.hash.return_value = "hashed_pwd"
    return pwd


def test_success_cedula_7_chars():
    user_repo = _make_user_repo()
    prof_repo = _make_prof_repo()
    pwd = _make_pwd_mock()
    uc = CreateProfessionalUseCase(user_repo, prof_repo, pwd)
    dto = CreateProfessionalRequest(
        name="Pro", last_name="Test", dni="22222222", email="pro@test.com", phone="2222222222", password="password123", cedula="ABC1234"
    )
    result = uc.execute(dto)
    assert result.role == UserRole.PROFESSIONAL
    assert result.is_active is True
    assert result.id == 2
    prof_repo.save.assert_called_once()
    assert prof_repo.save.call_args[0][0].cedula == "ABC1234"
    assert prof_repo.save.call_args[0][0].user_id == 2


def test_success_cedula_8_chars():
    user_repo = _make_user_repo()
    prof_repo = _make_prof_repo()
    pwd = _make_pwd_mock()
    uc = CreateProfessionalUseCase(user_repo, prof_repo, pwd)
    dto = CreateProfessionalRequest(
        name="Pro", last_name="Test", dni="22222222", email="pro@test.com", phone="2222222222", password="password123", cedula="12345678"
    )
    result = uc.execute(dto)
    assert prof_repo.save.call_args[0][0].cedula == "12345678"


def test_duplicate_cedula_raises():
    user_repo = _make_user_repo()
    prof_repo = _make_prof_repo(cedula=True)
    pwd = _make_pwd_mock()
    uc = CreateProfessionalUseCase(user_repo, prof_repo, pwd)
    dto = CreateProfessionalRequest(
        name="Pro", last_name="Test", dni="22222222", email="pro@test.com", phone="2222222222", password="password123", cedula="ABC1234"
    )
    with pytest.raises(DuplicateUserException, match="Usuario ya registrado"):
        uc.execute(dto)


def test_duplicate_email_raises():
    user_repo = _make_user_repo(email=True)
    prof_repo = _make_prof_repo()
    pwd = _make_pwd_mock()
    uc = CreateProfessionalUseCase(user_repo, prof_repo, pwd)
    dto = CreateProfessionalRequest(
        name="Pro", last_name="Test", dni="22222222", email="pro@test.com", phone="2222222222", password="password123", cedula="ABC1234"
    )
    with pytest.raises(DuplicateEmailException, match="email ya registrado"):
        uc.execute(dto)
