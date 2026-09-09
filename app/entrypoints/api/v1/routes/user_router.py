from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dtos.user_dtos import CreateProfessionalRequest, CreateReceptionistRequest, ProfessionalUserResponse, UserResponse
from app.domain.exceptions.user_exceptions import DuplicateEmailException, DuplicateUserException
from app.entrypoints.api.v1.dependencies import get_create_professional_use_case, get_create_receptionist_use_case, get_current_admin, get_professional_repository

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/receptionists", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_receptionist(
    dto: CreateReceptionistRequest,
    admin=Depends(get_current_admin),
    use_case=Depends(get_create_receptionist_use_case),
):
    try:
        user = use_case.execute(dto)
        return UserResponse.from_entity(user)
    except DuplicateEmailException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DuplicateUserException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/professionals", response_model=ProfessionalUserResponse, status_code=status.HTTP_201_CREATED)
def create_professional(
    dto: CreateProfessionalRequest,
    admin=Depends(get_current_admin),
    use_case=Depends(get_create_professional_use_case),
    prof_repo=Depends(get_professional_repository),
):
    try:
        user = use_case.execute(dto)
        # Obtener cedula desde tabla professionals para la respuesta
        prof = prof_repo.get_by_user_id(user.id)
        cedula = prof.cedula if prof else dto.cedula
        return ProfessionalUserResponse.from_entities(user, cedula)
    except DuplicateEmailException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DuplicateUserException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
