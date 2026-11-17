"""API contract (request/response models). The frontend types are generated from the OpenAPI schema."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, model_validator

# Money/amounts travel as strings to avoid float rounding in JSON.
DecimalStr = Annotated[Decimal, PlainSerializer(lambda v: str(v), return_type=str, when_used="json")]
CountryCode = Annotated[str, Field(pattern=r"^[A-Z]{2}$")]
CurrencyCode = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Health(BaseModel):
    status: Literal["ok"]
    env: str
    version: str


class Country(BaseModel):
    code: str
    name_en: str
    name_uz: str
    currency: str
    customs_union: str | None


class Profile(BaseModel):
    id: UUID
    email: str | None
    full_name: str | None
    locale: Literal["uz", "en", "ru"]
    home_country: str | None
    role: Literal["user", "admin"]


class ProfileUpdate(StrictModel):
    full_name: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    locale: Literal["uz", "en", "ru"] | None = None
    home_country: CountryCode | None = None


class ProductBase(StrictModel):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(max_length=4000)] | None = None
    category_id: UUID | None = None
    origin_country: CountryCode | None = None
    material: Annotated[str, Field(max_length=200)] | None = None
    unit_weight_kg: Annotated[Decimal, Field(ge=0, max_digits=16, decimal_places=4)] | None = None
    unit_volume_m3: Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=6)] | None = None
    unit_cost: Annotated[Decimal, Field(ge=0, max_digits=22, decimal_places=4)] | None = None
    unit_cost_currency: CurrencyCode | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _cost_needs_currency(self) -> ProductBase:
        if self.unit_cost is not None and self.unit_cost_currency is None:
            raise ValueError("unit_cost_currency is required when unit_cost is set")
        return self


class ProductCreate(ProductBase):
    pass


class ProductUpdate(StrictModel):
    name: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    description: Annotated[str, Field(max_length=4000)] | None = None
    category_id: UUID | None = None
    origin_country: CountryCode | None = None
    material: Annotated[str, Field(max_length=200)] | None = None
    unit_weight_kg: Annotated[Decimal, Field(ge=0, max_digits=16, decimal_places=4)] | None = None
    unit_volume_m3: Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=6)] | None = None
    unit_cost: Annotated[Decimal, Field(ge=0, max_digits=22, decimal_places=4)] | None = None
    unit_cost_currency: CurrencyCode | None = None
    attributes: dict[str, Any] | None = None


class Product(BaseModel):
    id: UUID
    name: str
    description: str | None
    category_id: UUID | None
    origin_country: str | None
    material: str | None
    unit_weight_kg: DecimalStr | None
    unit_volume_m3: DecimalStr | None
    unit_cost: DecimalStr | None
    unit_cost_currency: str | None
    attributes: dict[str, Any]
    created_at: datetime
    updated_at: datetime
