from datetime import date
from pydantic import BaseModel, Field, field_validator, ConfigDict


class EmployeeData(BaseModel):
    tg: str
    rate: float = Field(default=1.0, ge=0.0, le=1.0)  # ставка от 0 до 1
    vacation_range: list[date] | None = None

    @field_validator("vacation_range")
    def check_vacation_range(cls, v):
        if v is not None and len(v) != 2:
            raise ValueError("vacation_range must have exactly 2 dates")
        return v


class ConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employees: dict[str, EmployeeData]
