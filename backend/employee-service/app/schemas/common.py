
from pydantic import BaseModel, ConfigDict


class ORMBaseSchema(BaseModel):
    """
    Base schema for converting SQLAlchemy models
    into Pydantic response objects.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )
