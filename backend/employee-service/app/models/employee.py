
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Employee(Base):
    """
    Employee database model.

    Stores employee profile and employment information.
    Authentication credentials remain owned by Auth Service.
    """

    __tablename__ = "employees"

    # Primary key
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    # Logical reference to Auth Service user
    user_id: Mapped[int] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
    )

    # Employee identification
    employee_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    # Personal information
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Employment information
    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    designation: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    date_of_joining: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    employment_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="full_time",
    )

    # Self-referencing reporting manager
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Employee status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Audit timestamps (UTC)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_employees_department", "department"),
        Index("ix_employees_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<Employee(id={self.id}, "
            f"employee_code='{self.employee_code}', "
            f"email='{self.email}')>"
        )
