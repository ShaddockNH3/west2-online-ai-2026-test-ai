"""密码哈希与双 Token。"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.errors import TokenExpiredError, ValidationError

_hasher = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)

ACCESS = "access"
REFRESH = "refresh"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def validate_password_strength(password: str) -> None:
    if len(password) < 8 or len(password) > 64:
        raise ValidationError("密码长度需在 8 到 64 位之间")
    if password.isdigit() or password.isalpha():
        raise ValidationError("密码需同时包含字母和数字")


def encode_token(
    *, user_id: int, role: str, session_id: str, token_type: str, ttl: int, secret: str
) -> tuple[str, str, int]:
    """返回 (token, jti, expires_in_seconds)。"""
    jti = secrets.token_urlsafe(16)
    # 注意用带时区的当前时间取时间戳：naive UTC 的 .timestamp() 会按本地时区解释，
    # 在 +08:00 机器上会让 token 立刻过期。
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "sid": session_id,
        "typ": token_type,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token, jti, ttl


def decode_token(token: str, *, expected_type: str, secret: str) -> dict[str, Any]:
    try:
        claims = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("登录凭证已过期") from exc
    except jwt.PyJWTError as exc:
        raise TokenExpiredError("登录凭证无效") from exc
    if claims.get("typ") != expected_type:
        raise TokenExpiredError("登录凭证类型不正确")
    return claims
