from __future__ import annotations

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    low_stock_threshold: int = Field(default=5, ge=0, le=1_000_000)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    low_stock_threshold: int | None = Field(default=None, ge=0, le=1_000_000)


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    low_stock_threshold: int
    current_stock: int

