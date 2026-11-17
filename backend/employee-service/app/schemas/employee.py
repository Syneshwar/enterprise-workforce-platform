
from datetime import date, datetime
from typing import Literal

from pydantic import (
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.common import ORMBaseSchema


EmploymentType = Literal[
    "full_time",
    "part_time",
    "contract",
    "intern",
]


class EmployeeBase(ORMBaseSchema):
    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=1,
        max_length=100,
    )

    email: EmailStr

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    department: str = Field(
        min_length=2,
        max_length=100,
    )

    designation: str = Field(
        min_length=2,
        max_length=100,
    )

    date_of_joining: date

    employment_type: EmploymentType = "full_time"

    manager_id: int | None = Field(
        default=None,
        gt=0,
    )

    @field_validator(
        "first_name",
        "last_name",
        "department",
        "designation",
        mode="before",
    )
    @classmethod
    def strip_text_fields(cls, value):
        if isinstance(value, str):
            value = value.strip()

            if not value:
                raise ValueError("This field cannot be empty.")

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            return value

        value = value.strip()

        if not value:
            return None

        allowed_characters = set("0123456789+-() ")

        if not all(char in allowed_characters for char in value):
            raise ValueError("Phone number contains invalid characters.")

        digits = [char for char in value if char.isdigit()]

        if not 7 <= len(digits) <= 15:
            raise ValueError("Phone number must contain 7 to 15 digits.")

        return value

    @field_validator("date_of_joining")
    @classmethod
    def validate_joining_date(cls, value):
        if value > date.today():
            raise ValueError("Joining date cannot be in the future.")

        return value


class EmployeeCreate(EmployeeBase):
    """
    Request schema for creating an employee.

    user_id and employee_code are supplied by
    the application/service layer, not the public request.
    """

    pass


class EmployeeUpdate(ORMBaseSchema):
    """
    Partial update schema.

    All fields are optional because clients may update
    only selected employee attributes.
    """

    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    department: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    designation: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    date_of_joining: date | None = None

    employment_type: EmploymentType | None = None

    manager_id: int | None = Field(
        default=None,
        gt=0,
    )

    is_active: bool | None = None

    @field_validator(
        "first_name",
        "last_name",
        "department",
        "designation",
        mode="before",
    )
    @classmethod
    def strip_update_text_fields(cls, value):
        if isinstance(value, str):
            value = value.strip()

            if not value:
                raise ValueError("This field cannot be empty.")

        return value

    @field_validator("phone")
    @classmethod
    def validate_update_phone(cls, value):
        if value is None:
            return value

        value = value.strip()

        if not value:
            return None

        allowed_characters = set("0123456789+-() ")

        if not all(char in allowed_characters for char in value):
            raise ValueError("Phone number contains invalid characters.")

        digits = [char for char in value if char.isdigit()]

        if not 7 <= len(digits) <= 15:
            raise ValueError("Phone number must contain 7 to 15 digits.")

        return value

    @field_validator("date_of_joining")
    @classmethod
    def validate_update_joining_date(cls, value):
        if value is not None and value > date.today():
            raise ValueError("Joining date cannot be in the future.")

        return value

    @model_validator(mode="after")
    def validate_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        return self


class EmployeeResponse(ORMBaseSchema):
    """
    Employee details returned by the API.
    """

    id: int
    user_id: int
    employee_code: str

    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None

    department: str
    designation: str

    date_of_joining: date
    employment_type: EmploymentType

    manager_id: int | None
    is_active: bool

    created_at: datetime
    updated_at: datetime


class EmployeeListResponse(ORMBaseSchema):
    """
    Paginated employee listing response.
    """

    items: list[EmployeeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
