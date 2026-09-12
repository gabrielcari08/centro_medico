import pytest
from pydantic import ValidationError

from app.application.dtos.professional_dtos import UpdateProfessionalRequest


def test_missing_field():
    with pytest.raises(ValidationError) as exc:
        UpdateProfessionalRequest(name="Ana", last_name="Lopez", dni="12345678", email="a@test.com", phone="1234567890")
    # missing cedula should be reported; at API level maps to Campos faltantes
    assert "Field required" in str(exc.value) or "Campos faltantes" in str(exc.value)


def test_empty_field_campos_faltantes():
    with pytest.raises(ValidationError) as exc:
        UpdateProfessionalRequest(name=" ", last_name="Lopez", dni="12345678", email="a@test.com", phone="1234567890", cedula="ABC1234")
    assert "Campos faltantes" in str(exc.value)


def test_invalid_email():
    with pytest.raises(ValidationError) as exc:
        UpdateProfessionalRequest(name="Ana", last_name="Lopez", dni="12345678", email="ana-at-test.com", phone="1234567890", cedula="ABC1234")
    assert "email invalido" in str(exc.value)


def test_invalid_dni():
    with pytest.raises(ValidationError) as exc:
        UpdateProfessionalRequest(name="Ana", last_name="Lopez", dni="123", email="a@test.com", phone="1234567890", cedula="ABC1234")
    assert "Formato inválido, debe tener 8 caracteres" in str(exc.value)


def test_invalid_phone():
    with pytest.raises(ValidationError) as exc:
        UpdateProfessionalRequest(name="Ana", last_name="Lopez", dni="12345678", email="a@test.com", phone="123", cedula="ABC1234")
    assert "Formato inválido, debe tener 10 caracteres" in str(exc.value)


def test_invalid_cedula():
    with pytest.raises(ValidationError) as exc:
        UpdateProfessionalRequest(name="Ana", last_name="Lopez", dni="12345678", email="a@test.com", phone="1234567890", cedula="abc")
    assert "Formato inválido, debe tener 7 u 8 caracteres" in str(exc.value)


def test_valid_payload():
    dto = UpdateProfessionalRequest(name="Ana", last_name="Lopez", dni="12345678", email="A@TEST.COM", phone="1234567890", cedula="ABC1234")
    assert dto.email == "a@test.com"
    assert dto.cedula == "ABC1234"


def test_password_field_forbidden():
    with pytest.raises(ValidationError) as exc:
        UpdateProfessionalRequest(name="Ana", last_name="Lopez", dni="12345678", email="a@test.com", phone="1234567890", cedula="ABC1234", password="shouldfail")
    assert "extra" in str(exc.value).lower() or "not permitted" in str(exc.value).lower() or "password" in str(exc.value).lower()


def test_detail_response_mapping():
    from datetime import datetime
    from app.domain.entities.user import User, UserRole
    from app.domain.entities.professional import Professional
    from app.application.dtos.professional_dtos import ProfessionalDetailResponse

    user = User(name="Ana", last_name="Lopez", dni="12345678", email="a@test.com", phone="1234567890", password_hash="h", role=UserRole.PROFESSIONAL, id=1, is_active=True, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    prof = Professional(user_id=1, cedula="ABC1234", id=10)
    resp = ProfessionalDetailResponse.from_entities(user, prof)
    assert resp.id == 10
    assert resp.user_id == 1
    assert resp.cedula == "ABC1234"


def test_list_response():
    from app.application.dtos.professional_dtos import ProfessionalListResponse, ProfessionalDetailResponse
    from datetime import datetime
    from app.domain.entities.user import User, UserRole
    from app.domain.entities.professional import Professional

    user = User(name="Ana", last_name="Lopez", dni="12345678", email="a@test.com", phone="1234567890", password_hash="h", role=UserRole.PROFESSIONAL, id=1, is_active=True, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    prof = Professional(user_id=1, cedula="ABC1234", id=10)
    detail = ProfessionalDetailResponse.from_entities(user, prof)
    lst = ProfessionalListResponse(items=[detail], count=1)
    assert lst.count == 1
