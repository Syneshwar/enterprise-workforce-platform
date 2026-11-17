
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import (
    CurrentUser,
    get_current_user,
    require_hr_or_admin,
)
from app.db.session import get_db
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.services.employee_service import EmployeeService

from fastapi import Path

from app.clients.auth_service_client import (
    AuthServiceClient,
    AuthServiceError,
    AuthServiceUserNotFound,
)


router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


def generate_employee_code() -> str:
    """Generate a unique employee reference code."""
    return f"EMP-{uuid4().hex[:12].upper()}"



@router.post(
    "/{auth_user_id}",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    employee_data: EmployeeCreate,
    auth_user_id: int = Path(
        gt=0,
        description="User ID to verify with Auth Service",
    ),
    current_user: CurrentUser = Depends(require_hr_or_admin),
    db: Session = Depends(get_db),
):
    auth_client = AuthServiceClient()

    try:
        verified_user = auth_client.get_active_user(auth_user_id)

    except AuthServiceUserNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except AuthServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    # Ensure the employee profile email matches the verified account.
    if (
        str(employee_data.email).strip().lower()
        != verified_user["email"].strip().lower()
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee email does not match the verified Auth Service account.",
        )

    service = EmployeeService(db)

    try:
        return service.create_employee(
            employee_data=employee_data,
            user_id=verified_user["id"],
            employee_code=generate_employee_code(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc



@router.get(
    "/me",
    response_model=EmployeeResponse,
)
def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's own employee profile."""

    service = EmployeeService(db)

    try:
        return service.get_my_profile(current_user.user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=EmployeeListResponse,
)
def list_employees(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    include_inactive: bool = Query(default=False),
    current_user: CurrentUser = Depends(require_hr_or_admin),
    db: Session = Depends(get_db),
):
    """List employee profiles. HR/Admin only."""

    service = EmployeeService(db)

    return service.list_employees(
        page=page,
        page_size=page_size,
        include_inactive=include_inactive,
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def get_employee(
    employee_id: int,
    current_user: CurrentUser = Depends(require_hr_or_admin),
    db: Session = Depends(get_db),
):
    """Retrieve an employee by ID. HR/Admin only."""

    service = EmployeeService(db)

    try:
        return service.get_employee(employee_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: CurrentUser = Depends(require_hr_or_admin),
    db: Session = Depends(get_db),
):
    """Update an employee profile. HR/Admin only."""

    service = EmployeeService(db)

    try:
        return service.update_employee(
            employee_id=employee_id,
            update_data=employee_data,
        )
    except ValueError as exc:
        message = str(exc)

        if "not found" in message.lower():
            error_status = status.HTTP_404_NOT_FOUND
        else:
            error_status = status.HTTP_409_CONFLICT

        raise HTTPException(
            status_code=error_status,
            detail=message,
        ) from exc


@router.delete(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def deactivate_employee(
    employee_id: int,
    current_user: CurrentUser = Depends(require_hr_or_admin),
    db: Session = Depends(get_db),
):
    """Soft-deactivate an employee. HR/Admin only."""

    service = EmployeeService(db)

    try:
        return service.deactivate_employee(employee_id)
    except ValueError as exc:
        message = str(exc)

        if "not found" in message.lower():
            error_status = status.HTTP_404_NOT_FOUND
        else:
            error_status = status.HTTP_409_CONFLICT

        raise HTTPException(
            status_code=error_status,
            detail=message,
        ) from exc
