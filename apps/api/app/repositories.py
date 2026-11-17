"""Data access. Every user-scoped method REQUIRES owner_id — RLS is the second line of defence, not the first."""

from __future__ import annotations

import json
from typing import Annotated, Any, Protocol
from uuid import UUID

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .db import SessionDep

Row = dict[str, Any]

PRODUCT_COLUMNS = (
    "id, name, description, category_id, origin_country, material, unit_weight_kg, unit_volume_m3, "
    "unit_cost, unit_cost_currency, attributes, created_at, updated_at"
)
# Whitelist of writable product columns (never interpolate user-supplied names into SQL).
PRODUCT_WRITABLE = (
    "name",
    "description",
    "category_id",
    "origin_country",
    "material",
    "unit_weight_kg",
    "unit_volume_m3",
    "unit_cost",
    "unit_cost_currency",
    "attributes",
)


class ProductRepo(Protocol):
    async def list(self, owner_id: UUID) -> list[Row]: ...
    async def get(self, owner_id: UUID, product_id: UUID) -> Row | None: ...
    async def create(self, owner_id: UUID, data: Row) -> Row: ...
    async def update(self, owner_id: UUID, product_id: UUID, data: Row) -> Row | None: ...
    async def delete(self, owner_id: UUID, product_id: UUID) -> bool: ...


class ProfileRepo(Protocol):
    async def get(self, user_id: UUID) -> Row | None: ...
    async def update(self, user_id: UUID, data: Row) -> Row | None: ...


class ReferenceRepo(Protocol):
    async def enabled_countries(self) -> list[Row]: ...


def _params(data: Row) -> Row:
    out = {k: v for k, v in data.items() if k in PRODUCT_WRITABLE}
    if "attributes" in out:
        out["attributes"] = json.dumps(out["attributes"] or {})
    return out


def _cast(col: str) -> str:
    return f"CAST(:{col} AS jsonb)" if col == "attributes" else f":{col}"


class SqlProductRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def list(self, owner_id: UUID) -> list[Row]:
        res = await self.s.execute(
            text(f"SELECT {PRODUCT_COLUMNS} FROM public.products WHERE owner_id = :owner ORDER BY created_at DESC"),
            {"owner": owner_id},
        )
        return [dict(r) for r in res.mappings()]

    async def get(self, owner_id: UUID, product_id: UUID) -> Row | None:
        res = await self.s.execute(
            text(f"SELECT {PRODUCT_COLUMNS} FROM public.products WHERE owner_id = :owner AND id = :id"),
            {"owner": owner_id, "id": product_id},
        )
        row = res.mappings().first()
        return dict(row) if row else None

    async def create(self, owner_id: UUID, data: Row) -> Row:
        p = _params(data)
        cols = list(p)
        sql = (
            f"INSERT INTO public.products (owner_id, {', '.join(cols)}) "
            f"VALUES (:owner, {', '.join(_cast(c) for c in cols)}) RETURNING {PRODUCT_COLUMNS}"
        )
        res = await self.s.execute(text(sql), {"owner": owner_id, **p})
        return dict(res.mappings().one())

    async def update(self, owner_id: UUID, product_id: UUID, data: Row) -> Row | None:
        p = _params(data)
        if not p:
            return await self.get(owner_id, product_id)
        sets = ", ".join(f"{c} = {_cast(c)}" for c in p)
        sql = f"UPDATE public.products SET {sets} WHERE owner_id = :owner AND id = :id RETURNING {PRODUCT_COLUMNS}"
        res = await self.s.execute(text(sql), {"owner": owner_id, "id": product_id, **p})
        row = res.mappings().first()
        return dict(row) if row else None

    async def delete(self, owner_id: UUID, product_id: UUID) -> bool:
        res = await self.s.execute(
            text("DELETE FROM public.products WHERE owner_id = :owner AND id = :id RETURNING id"),
            {"owner": owner_id, "id": product_id},
        )
        return res.first() is not None


class SqlProfileRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get(self, user_id: UUID) -> Row | None:
        res = await self.s.execute(
            text(
                "SELECT id, full_name, locale, home_country, role::text AS role FROM public.user_profiles WHERE id = :id"
            ),
            {"id": user_id},
        )
        row = res.mappings().first()
        return dict(row) if row else None

    async def update(self, user_id: UUID, data: Row) -> Row | None:
        allowed = {k: v for k, v in data.items() if k in ("full_name", "locale", "home_country")}
        if allowed:
            sets = ", ".join(f"{c} = :{c}" for c in allowed)
            await self.s.execute(
                text(f"UPDATE public.user_profiles SET {sets} WHERE id = :id"), {"id": user_id, **allowed}
            )
        return await self.get(user_id)


class SqlReferenceRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def enabled_countries(self) -> list[Row]:
        res = await self.s.execute(
            text(
                "SELECT code, name_en, name_uz, currency, customs_union FROM public.countries WHERE is_enabled ORDER BY code"
            )
        )
        return [dict(r) for r in res.mappings()]


def get_product_repo(session: SessionDep) -> ProductRepo:
    return SqlProductRepo(session)


def get_profile_repo(session: SessionDep) -> ProfileRepo:
    return SqlProfileRepo(session)


def get_reference_repo(session: SessionDep) -> ReferenceRepo:
    return SqlReferenceRepo(session)


ProductRepoDep = Annotated[ProductRepo, Depends(get_product_repo)]
ProfileRepoDep = Annotated[ProfileRepo, Depends(get_profile_repo)]
ReferenceRepoDep = Annotated[ReferenceRepo, Depends(get_reference_repo)]
