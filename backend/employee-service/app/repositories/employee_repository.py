
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.employee import Employee


class EmployeeRepository:
    """Handles database operations for Employee records."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, employee_data: dict) -> Employee:
        employee = Employee(**employee_data)

        self.db.add(employee)
        self.db.flush()
        self.db.refresh(employee)

        return employee

    def get_by_id(self, employee_id: int) -> Employee | None:
        statement = select(Employee).where(
            Employee.id == employee_id
        )

        return self.db.scalar(statement)

    def get_by_user_id(self, user_id: int) -> Employee | None:
        statement = select(Employee).where(
            Employee.user_id == user_id
        )

        return self.db.scalar(statement)

    def get_by_email(self, email: str) -> Employee | None:
        statement = select(Employee).where(
            Employee.email == email
        )

        return self.db.scalar(statement)

    def get_by_employee_code(
        self,
        employee_code: str,
    ) -> Employee | None:
        statement = select(Employee).where(
            Employee.employee_code == employee_code
        )

        return self.db.scalar(statement)

    def get_all(
        self,
        page: int = 1,
        page_size: int = 10,
        include_inactive: bool = False,
    ) -> tuple[list[Employee], int]:

        statement = select(Employee)

        count_statement = select(func.count()).select_from(Employee)

        if not include_inactive:
            statement = statement.where(Employee.is_active.is_(True))
            count_statement = count_statement.where(
                Employee.is_active.is_(True)
            )

        total = self.db.scalar(count_statement) or 0

        statement = (
            statement
            .order_by(Employee.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        employees = list(self.db.scalars(statement).all())

        return employees, total

    def update(
        self,
        employee: Employee,
        update_data: dict,
    ) -> Employee:

        for field, value in update_data.items():
            setattr(employee, field, value)

        self.db.flush()
        self.db.refresh(employee)

        return employee

    def deactivate(self, employee: Employee) -> Employee:
        employee.is_active = False

        self.db.flush()
        self.db.refresh(employee)

        return employee
