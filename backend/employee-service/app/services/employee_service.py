
from math import ceil

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.repositories.employee_repository import EmployeeRepository
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdate,
)


class EmployeeService:
    """Contains employee management business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = EmployeeRepository(db)

    def create_employee(
        self,
        employee_data: EmployeeCreate,
        user_id: int,
        employee_code: str,
    ) -> EmployeeResponse:

        if self.repository.get_by_user_id(user_id):
            raise ValueError("An employee profile already exists for this user.")

        if self.repository.get_by_email(str(employee_data.email)):
            raise ValueError("An employee with this email already exists.")

        if self.repository.get_by_employee_code(employee_code):
            raise ValueError("Employee code already exists.")

        data = employee_data.model_dump()

        data.update({
            "user_id": user_id,
            "employee_code": employee_code,
        })

        try:
            employee = self.repository.create(data)
            self.db.commit()
            self.db.refresh(employee)

        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError(
                "Employee creation failed due to a duplicate or invalid reference."
            ) from exc

        return EmployeeResponse.model_validate(employee)

    def get_employee(self, employee_id: int) -> EmployeeResponse:
        employee = self.repository.get_by_id(employee_id)

        if employee is None:
            raise ValueError("Employee not found.")

        return EmployeeResponse.model_validate(employee)

    def get_my_profile(self, user_id: int) -> EmployeeResponse:
        employee = self.repository.get_by_user_id(user_id)

        if employee is None:
            raise ValueError("Employee profile not found.")

        return EmployeeResponse.model_validate(employee)

    def list_employees(
        self,
        page: int = 1,
        page_size: int = 10,
        include_inactive: bool = False,
    ) -> EmployeeListResponse:

        if page < 1:
            raise ValueError("Page must be greater than zero.")

        if not 1 <= page_size <= 100:
            raise ValueError("Page size must be between 1 and 100.")

        employees, total = self.repository.get_all(
            page=page,
            page_size=page_size,
            include_inactive=include_inactive,
        )

        return EmployeeListResponse(
            items=[
                EmployeeResponse.model_validate(employee)
                for employee in employees
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total else 0,
        )

    def update_employee(
        self,
        employee_id: int,
        update_data: EmployeeUpdate,
    ) -> EmployeeResponse:

        employee = self.repository.get_by_id(employee_id)

        if employee is None:
            raise ValueError("Employee not found.")

        if not employee.is_active:
            raise ValueError("Inactive employees cannot be updated.")

        data = update_data.model_dump(exclude_unset=True)

        if "email" in data and data["email"] is not None:
            existing = self.repository.get_by_email(str(data["email"]))

            if existing and existing.id != employee_id:
                raise ValueError("Email already belongs to another employee.")

            data["email"] = str(data["email"])

        try:
            employee = self.repository.update(employee, data)
            self.db.commit()
            self.db.refresh(employee)

        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Employee update failed due to a database constraint.") from exc

        return EmployeeResponse.model_validate(employee)

    def deactivate_employee(self, employee_id: int) -> EmployeeResponse:
        employee = self.repository.get_by_id(employee_id)

        if employee is None:
            raise ValueError("Employee not found.")

        if not employee.is_active:
            raise ValueError("Employee is already inactive.")

        employee = self.repository.deactivate(employee)
        self.db.commit()
        self.db.refresh(employee)

        return EmployeeResponse.model_validate(employee)
