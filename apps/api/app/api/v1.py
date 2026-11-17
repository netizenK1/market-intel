from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from .. import __version__
from ..auth import CurrentUserDep
from ..config import Settings, get_settings
from ..errors import AppError, not_found
from ..repositories import ProductRepoDep, ProfileRepoDep, ReferenceRepoDep
from ..schemas import Country, Health, Product, ProductCreate, ProductUpdate, Profile, ProfileUpdate

router = APIRouter(prefix="/v1")


@router.get("/health", response_model=Health, tags=["system"])
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> Health:
    return Health(status="ok", env=settings.app_env, version=__version__)


# ---------------------------------------------------------------- profile


@router.get("/me", response_model=Profile, tags=["profile"])
async def get_me(user: CurrentUserDep, profiles: ProfileRepoDep) -> Profile:
    row = await profiles.get(user.id)
    if row is None:
        # the DB trigger creates a profile on sign-up; a missing row means the account is not set up
        raise AppError(404, "PROFILE_NOT_FOUND", "Profil topilmadi")
    return Profile(email=user.email, **row)


@router.patch("/me", response_model=Profile, tags=["profile"])
async def update_me(body: ProfileUpdate, user: CurrentUserDep, profiles: ProfileRepoDep) -> Profile:
    row = await profiles.update(user.id, body.model_dump(exclude_unset=True))
    if row is None:
        raise AppError(404, "PROFILE_NOT_FOUND", "Profil topilmadi")
    return Profile(email=user.email, **row)


# ---------------------------------------------------------------- reference


@router.get("/countries", response_model=list[Country], tags=["reference"])
async def list_countries(_: CurrentUserDep, ref: ReferenceRepoDep) -> list[Country]:
    return [Country(**r) for r in await ref.enabled_countries()]


# ---------------------------------------------------------------- products


@router.get("/products", response_model=list[Product], tags=["products"])
async def list_products(user: CurrentUserDep, repo: ProductRepoDep) -> list[Product]:
    return [Product(**r) for r in await repo.list(user.id)]


@router.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED, tags=["products"])
async def create_product(body: ProductCreate, user: CurrentUserDep, repo: ProductRepoDep) -> Product:
    return Product(**await repo.create(user.id, body.model_dump()))


@router.get("/products/{product_id}", response_model=Product, tags=["products"])
async def get_product(product_id: UUID, user: CurrentUserDep, repo: ProductRepoDep) -> Product:
    row = await repo.get(user.id, product_id)
    if row is None:
        raise not_found("Mahsulot")
    return Product(**row)


@router.patch("/products/{product_id}", response_model=Product, tags=["products"])
async def update_product(product_id: UUID, body: ProductUpdate, user: CurrentUserDep, repo: ProductRepoDep) -> Product:
    changes = body.model_dump(exclude_unset=True)
    current = await repo.get(user.id, product_id)
    if current is None:
        raise not_found("Mahsulot")
    merged_cost = changes.get("unit_cost", current["unit_cost"])
    merged_cur = changes.get("unit_cost_currency", current["unit_cost_currency"])
    if merged_cost is not None and merged_cur is None:
        raise AppError(
            422, "VALIDATION_ERROR", "Kiritilgan ma’lumot noto‘g‘ri", fields={"unit_cost_currency": "required"}
        )
    row = await repo.update(user.id, product_id, changes)
    if row is None:
        raise not_found("Mahsulot")
    return Product(**row)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["products"])
async def delete_product(product_id: UUID, user: CurrentUserDep, repo: ProductRepoDep) -> Response:
    if not await repo.delete(user.id, product_id):
        raise not_found("Mahsulot")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
