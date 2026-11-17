"""API tests with in-memory repositories (no network, no database)."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Settings, get_settings
from app.main import create_app
from app.repositories import get_product_repo, get_profile_repo, get_reference_repo

SECRET = "test-secret-at-least-32-bytes-long-xxxx"
SUPABASE_URL = "https://proj.supabase.test"
ALICE = uuid.UUID("00000000-0000-0000-0000-00000000000a")
BOB = uuid.UUID("00000000-0000-0000-0000-00000000000b")


def token(sub: UUID, *, exp_in: int = 3600, aud: str = "authenticated", secret: str = SECRET) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": str(sub),
            "aud": aud,
            "exp": now + exp_in,
            "iat": now,
            "iss": f"{SUPABASE_URL}/auth/v1",
            "email": "user@example.test",
        },
        secret,
        algorithm="HS256",
    )


def auth(sub: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(sub)}"}


class FakeProducts:
    def __init__(self) -> None:
        self.rows: dict[UUID, dict[str, Any]] = {}

    async def list(self, owner_id: UUID) -> list[dict[str, Any]]:
        return [self._pub(r) for r in self.rows.values() if r["owner_id"] == owner_id]

    async def get(self, owner_id: UUID, product_id: UUID) -> dict[str, Any] | None:
        r = self.rows.get(product_id)
        return self._pub(r) if r and r["owner_id"] == owner_id else None

    async def create(self, owner_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC)
        pid = uuid.uuid4()
        self.rows[pid] = {"id": pid, "owner_id": owner_id, "created_at": now, "updated_at": now, **data}
        return self._pub(self.rows[pid])

    async def update(self, owner_id: UUID, product_id: UUID, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self.rows.get(product_id)
        if not r or r["owner_id"] != owner_id:
            return None
        r.update(data)
        return self._pub(r)

    async def delete(self, owner_id: UUID, product_id: UUID) -> bool:
        r = self.rows.get(product_id)
        if not r or r["owner_id"] != owner_id:
            return False
        del self.rows[product_id]
        return True

    @staticmethod
    def _pub(r: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in r.items() if k != "owner_id"}


class FakeProfiles:
    def __init__(self) -> None:
        self.rows = {
            ALICE: {"id": ALICE, "full_name": "Alice", "locale": "uz", "home_country": None, "role": "user"},
        }

    async def get(self, user_id: UUID) -> dict[str, Any] | None:
        return self.rows.get(user_id)

    async def update(self, user_id: UUID, data: dict[str, Any]) -> dict[str, Any] | None:
        if user_id not in self.rows:
            return None
        self.rows[user_id].update(data)
        return self.rows[user_id]


class FakeReference:
    async def enabled_countries(self) -> list[dict[str, Any]]:
        return [
            {
                "code": "AE",
                "name_en": "United Arab Emirates",
                "name_uz": "BAA",
                "currency": "AED",
                "customs_union": "GCC",
            },
            {"code": "DE", "name_en": "Germany", "name_uz": "Germaniya", "currency": "EUR", "customs_union": "EU"},
        ]


@pytest.fixture
def client() -> TestClient:
    settings = Settings(
        app_env="test",
        supabase_url=SUPABASE_URL,
        supabase_jwt_secret=SecretStr(SECRET),
        cors_origins=["http://localhost:5173"],
    )
    app = create_app(settings)
    products, profiles, ref = FakeProducts(), FakeProfiles(), FakeReference()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_product_repo] = lambda: products
    app.dependency_overrides[get_profile_repo] = lambda: profiles
    app.dependency_overrides[get_reference_repo] = lambda: ref
    return TestClient(app)


def test_health_is_public(client: TestClient) -> None:
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.headers["x-request-id"].startswith("req_")


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Basic abc"},
        {"Authorization": "Bearer not-a-jwt"},
        {"Authorization": f"Bearer {token(ALICE, exp_in=-10)}"},
        {"Authorization": f"Bearer {token(ALICE, aud='anon')}"},
        {"Authorization": f"Bearer {token(ALICE, secret='wrong-secret-at-least-32-bytes-long-x')}"},
    ],
)
def test_protected_endpoints_reject_bad_tokens(client: TestClient, headers: dict[str, str]) -> None:
    r = client.get("/v1/me", headers=headers)
    assert r.status_code == 401
    body = r.json()
    assert body["code"] == "UNAUTHORIZED"
    assert r.headers["content-type"].startswith("application/problem+json")


def test_me_and_update(client: TestClient) -> None:
    r = client.get("/v1/me", headers=auth(ALICE))
    assert r.status_code == 200
    assert r.json()["email"] == "user@example.test"
    r = client.patch("/v1/me", headers=auth(ALICE), json={"locale": "en", "home_country": "UZ"})
    assert r.status_code == 200 and r.json()["locale"] == "en"
    r = client.patch("/v1/me", headers=auth(ALICE), json={"role": "admin"})  # cannot self-promote
    assert r.status_code == 422


def test_me_without_profile(client: TestClient) -> None:
    assert client.get("/v1/me", headers=auth(BOB)).json()["code"] == "PROFILE_NOT_FOUND"


def test_countries(client: TestClient) -> None:
    r = client.get("/v1/countries", headers=auth(ALICE))
    assert [c["code"] for c in r.json()] == ["AE", "DE"]


def test_product_crud_and_isolation(client: TestClient) -> None:
    body = {"name": "Charm sumka", "origin_country": "UZ", "unit_cost": "15.00", "unit_cost_currency": "USD"}
    r = client.post("/v1/products", headers=auth(ALICE), json=body)
    assert r.status_code == 201, r.text
    product = r.json()
    pid = product["id"]
    assert product["unit_cost"] == "15.00"  # decimals travel as strings

    assert len(client.get("/v1/products", headers=auth(ALICE)).json()) == 1
    # Bob cannot see, change or delete Alice's product
    assert client.get("/v1/products", headers=auth(BOB)).json() == []
    assert client.get(f"/v1/products/{pid}", headers=auth(BOB)).status_code == 404
    assert client.patch(f"/v1/products/{pid}", headers=auth(BOB), json={"name": "x"}).status_code == 404
    assert client.delete(f"/v1/products/{pid}", headers=auth(BOB)).status_code == 404

    r = client.patch(f"/v1/products/{pid}", headers=auth(ALICE), json={"material": "natural leather"})
    assert r.status_code == 200 and r.json()["material"] == "natural leather"
    assert client.delete(f"/v1/products/{pid}", headers=auth(ALICE)).status_code == 204
    assert client.get(f"/v1/products/{pid}", headers=auth(ALICE)).status_code == 404


@pytest.mark.parametrize(
    "body,field",
    [
        ({"name": ""}, "name"),
        ({"name": "x", "unit_cost": "-1", "unit_cost_currency": "USD"}, "unit_cost"),
        ({"name": "x", "unit_cost": "10"}, ""),  # currency required with cost
        ({"name": "x", "origin_country": "uzb"}, "origin_country"),
        ({"name": "x", "owner_id": str(BOB)}, "owner_id"),  # extra fields are forbidden
    ],
)
def test_product_validation(client: TestClient, body: dict[str, Any], field: str) -> None:
    r = client.post("/v1/products", headers=auth(ALICE), json=body)
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"
    assert any(field in k for k in r.json()["fields"])


def test_patch_cannot_leave_cost_without_currency(client: TestClient) -> None:
    pid = client.post("/v1/products", headers=auth(ALICE), json={"name": "x"}).json()["id"]
    r = client.patch(f"/v1/products/{pid}", headers=auth(ALICE), json={"unit_cost": "5"})
    assert r.status_code == 422


def test_db_not_configured_returns_503() -> None:
    settings = Settings(app_env="test", supabase_url=SUPABASE_URL, supabase_jwt_secret=SecretStr(SECRET))
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    r = TestClient(app).get("/v1/products", headers=auth(ALICE))
    assert r.status_code == 503
    assert r.json()["code"] == "DB_NOT_CONFIGURED"
