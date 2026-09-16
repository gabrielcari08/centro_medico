from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.application.dtos.professional_dtos import (
    ProfessionalDetailResponse,
    ProfessionalListResponse,
    UpdateProfessionalRequest,
)
from app.domain.exceptions.professional_exceptions import (
    AlreadyActiveException,
    AlreadyInactiveException,
    ProfessionalNotFoundException,
)
from app.domain.exceptions.user_exceptions import (
    DuplicateEmailException,
    DuplicateUserException,
    ForbiddenException,
)
from app.entrypoints.api.v1.dependencies import (
    get_activate_professional_use_case,
    get_current_admin,
    get_deactivate_professional_use_case,
    get_delete_professional_use_case,
    get_get_professional_use_case,
    get_list_deactivated_use_case,
    get_list_professionals_use_case,
    get_update_professional_use_case,
)

router = APIRouter(prefix="/api/v1/professionals", tags=["professionals"])


@router.get("", response_model=ProfessionalListResponse)
def list_professionals(
    search: str | None = None,
    use_case=Depends(get_list_professionals_use_case),
):
    # Endpoint publico, sin auth, solo activos ordenados A-Z
    items = use_case.execute(search)
    return ProfessionalListResponse(items=items, count=len(items))


@router.get("/deactivated", response_model=ProfessionalListResponse)
def list_deactivated_professionals(
    admin=Depends(get_current_admin),
    use_case=Depends(get_list_deactivated_use_case),
):
    # Solo administradores, solo inactivos ordenados A-Z
    try:
        items = use_case.execute(admin)
        return ProfessionalListResponse(items=items, count=len(items))
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{professional_id}", response_model=ProfessionalDetailResponse)
def get_professional_by_id(
    professional_id: int,
    use_case=Depends(get_get_professional_use_case),
):
    # Endpoint publico, solo activos, 404 si inactivo o inexistente
    try:
        return use_case.execute(professional_id)
    except ProfessionalNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{professional_id}", response_model=ProfessionalDetailResponse)
def update_professional(
    professional_id: int,
    dto: UpdateProfessionalRequest,
    admin=Depends(get_current_admin),
    use_case=Depends(get_update_professional_use_case),
):
    # Solo administradores, password no editable por DTO
    try:
        return use_case.execute(professional_id, dto, admin)
    except ProfessionalNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateEmailException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DuplicateUserException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{professional_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_professional(
    professional_id: int,
    admin=Depends(get_current_admin),
    use_case=Depends(get_delete_professional_use_case),
):
    # Borrado fisico, solo administradores
    try:
        use_case.execute(professional_id, admin)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ProfessionalNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/{professional_id}/activate", response_model=ProfessionalDetailResponse)
def activate_professional(
    professional_id: int,
    admin=Depends(get_current_admin),
    use_case=Depends(get_activate_professional_use_case),
):
    try:
        return use_case.execute(professional_id, admin)
    except ProfessionalNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AlreadyActiveException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch(
    "/{professional_id}/deactivate", response_model=ProfessionalDetailResponse
)
def deactivate_professional(
    professional_id: int,
    admin=Depends(get_current_admin),
    use_case=Depends(get_deactivate_professional_use_case),
):
    try:
        return use_case.execute(professional_id, admin)
    except ProfessionalNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AlreadyInactiveException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
