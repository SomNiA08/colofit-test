"""
JWT 토큰 발급/검증 서비스.

토큰 페이로드:
  sub  : user_id (UUID 문자열)
  email: 이메일 (옵션)
  exp  : 만료 일시
"""

import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings


def create_token(user_id: uuid.UUID, email: str | None = None) -> str:
    """
    JWT 액세스 토큰을 발급한다.

    Args:
        user_id: 사용자 UUID
        email:   이메일 (소셜 로그인에서 수집)

    Returns:
        서명된 JWT 문자열
    """
    now = datetime.now(tz=timezone.utc)
    payload: dict = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_expire_days),
    }
    if email:
        payload["email"] = email

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict:
    """
    JWT 토큰을 검증하고 페이로드를 반환한다.

    Args:
        token: JWT 문자열 (Bearer 접두사 없이)

    Returns:
        디코딩된 페이로드 dict

    Raises:
        jwt.ExpiredSignatureError: 만료된 토큰
        jwt.InvalidTokenError:     유효하지 않은 토큰
    """
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )


def get_user_id_from_token(token: str) -> uuid.UUID:
    """
    토큰에서 user_id를 추출한다.

    Raises:
        jwt.InvalidTokenError: 검증 실패
        ValueError:            sub 필드 누락 또는 UUID 변환 실패
    """
    payload = verify_token(token)
    sub = payload.get("sub")
    if not sub:
        raise ValueError("토큰에 sub 필드가 없어요.")
    return uuid.UUID(sub)
