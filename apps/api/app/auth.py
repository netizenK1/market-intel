"""Supabase JWT verification. The user id is taken ONLY from the verified token (`sub`)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Header

from .config import Settings, get_settings
from .errors import AppError


@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: UUID
    email: str | None


def _unauthorized(detail: str) -> AppError:
    return AppError(401, "UNAUTHORIZED", "Avtorizatsiya talab qilinadi", detail)


@lru_cache(maxsize=4)
def _jwks_client(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url, cache_keys=True, lifespan=3600)


def verify_token(token: str, settings: Settings) -> CurrentUser:
    options: jwt.types.Options = {"require": ["exp", "sub", "aud"]}
    try:
        if settings.supabase_jwt_secret is not None:
            claims = jwt.decode(
                token,
                settings.supabase_jwt_secret.get_secret_value(),
                algorithms=["HS256"],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
                options=options,
            )
        else:
            jwks_url = settings.resolved_jwks_url
            if not jwks_url:
                raise AppError(500, "AUTH_NOT_CONFIGURED", "Autentifikatsiya sozlanmagan")
            signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
                options=options,
            )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Sessiya muddati tugagan. Qayta kiring.") from None
    except jwt.PyJWTError:
        raise _unauthorized("Token yaroqsiz.") from None

    try:
        user_id = UUID(str(claims["sub"]))
    except ValueError:
        raise _unauthorized("Token yaroqsiz.") from None
    email = claims.get("email")
    return CurrentUser(id=user_id, email=email if isinstance(email, str) else None)


def get_current_user(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    # sync dependency => FastAPI runs it in a thread pool (JWKS fetch is blocking)
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Authorization: Bearer <token> sarlavhasi yo‘q.")
    return verify_token(authorization[7:].strip(), settings)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
