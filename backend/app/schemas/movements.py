from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class MovementCreate(BaseModel):
    type: str = Field(pattern="^(receive|ship|adjust)$")
    direction: str | None = Field(default=None, pattern="^(increase|decrease)$")
    quantity: int = Field(ge=1, le=1_000_000)
    note: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _validate_adjust_direction(self):
        if self.type == "adjust" and not self.direction:
            raise ValueError("direction is required when type=adjust")
        if self.type != "adjust" and self.direction is not None:
            raise ValueError("direction is only allowed when type=adjust")
        return self


class MovementOut(BaseModel):
    id: int
    product_id: int
    type: str
    direction: str | None
    quantity: int
    note: str | None
    created_at: str

