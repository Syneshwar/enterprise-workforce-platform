
from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
)


def valid_employee_data():
    return {
        "first_name": "Eshwar",
        "last_name": "Gurram",
        "email": "eshwar@example.com",
        "phone": "+91 9876543210",
        "department": "Engineering",
        "designation": "Python Developer",
        "date_of_joining": date.today() - timedelta(days=30),
        "employment_type": "full_time",
    }


def test_employee_create_success():
    employee = EmployeeCreate(**valid_employee_data())

    assert employee.first_name == "Eshwar"
    assert employee.email == "eshwar@example.com"
    assert employee.employment_type == "full_time"


def test_employee_create_rejects_invalid_email():
    data = valid_employee_data()
    data["email"] = "invalid-email"

    with pytest.raises(ValidationError):
        EmployeeCreate(**data)


def test_employee_create_rejects_future_joining_date():
    data = valid_employee_data()
    data["date_of_joining"] = date.today() + timedelta(days=10)

    with pytest.raises(ValidationError):
        EmployeeCreate(**data)


def test_employee_create_rejects_invalid_employment_type():
    data = valid_employee_data()
    data["employment_type"] = "temporary"

    with pytest.raises(ValidationError):
        EmployeeCreate(**data)


def test_employee_update_supports_partial_update():
    employee = EmployeeUpdate(
        designation="Senior Python Developer"
    )

    assert employee.designation == "Senior Python Developer"
    assert employee.model_dump(exclude_unset=True) == {
        "designation": "Senior Python Developer"
    }


def test_employee_update_rejects_empty_payload():
    with pytest.raises(ValidationError):
        EmployeeUpdate()


def test_employee_create_rejects_invalid_phone():
    data = valid_employee_data()
    data["phone"] = "abc123"

    with pytest.raises(ValidationError):
        EmployeeCreate(**data)


def test_employee_create_strips_whitespace():
    data = valid_employee_data()
    data["first_name"] = "  Eshwar  "

    employee = EmployeeCreate(**data)

    assert employee.first_name == "Eshwar"
