"""
Auth API — 카카오/구글 OAuth 2.0 + JWT 발급.

플로우:
  1. GET /api/auth/kakao        → 카카오 인증 URL로 리다이렉트
  2. GET /api/auth/kakao/callback → 코드 교환 → user 조회/생성 → JWT 발급
                                 → 프론트로 리다이렉트 (?token=...&user_id=...&is_new=true/false)
  3. GET /api/auth/google       → 구글 인증 URL로 리다이렉트
  4. GET /api/auth/google/callback → 동일 흐름
  5. GET /api/auth/me           → JWT 검증 → 사용자 정보 반환
"""

import uuid
from urllib.parse import urlencode

import httpx
import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserMeResponse
from app.services.jwt import create_token, verify_token

router = APIRouter()

# ── OAuth 상수 ───────────────────────────────────────────────────────────────

_KAKAO_AUTH_URL     = "https://kauth.kakao.com/oauth/authorize"
_KAKAO_TOKEN_URL    = "https://kauth.kakao.com/oauth/token"
_KAKAO_PROFILE_URL  = "https://kapi.kakao.com/v2/user/me"

_GOOGLE_AUTH_URL    = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL   = "https://oauth2.googleapis.com/token"
_GOOGLE_PROFILE_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def _kakao_redirect_uri(request: Request) -> str:
    return str(request.base_url).rstrip("/") + "/api/auth/kakao/callback"


def _google_redirect_uri(request: Request) -> str:
    return str(request.base_url).rstrip("/") + "/api/auth/google/callback"


# ── 공통: user 조회 or 생성 ──────────────────────────────────────────────────

async def _get_or_create_user(
    db: AsyncSession,
    email: str,
    provider: str,
) -> tuple[User, bool]:
    """
    이메일로 사용자를 찾거나 새로 생성한다.

    Returns:
        (user, is_new_user)
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        return user, False

    user = User(id=uuid.uuid4(), email=email, provider=provider)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, True


def _make_frontend_redirect(token: str, user_id: uuid.UUID, is_new: bool) -> str:
    """OAuth 완료 후 프론트엔드 리다이렉트 URL을 만든다."""
    params = urlencode({
        "token": token,
        "user_id": str(user_id),
        "is_new": "true" if is_new else "false",
    })
    return f"{settings.frontend_url}/auth/callback?{params}"


# ── 카카오 ────────────────────────────────────────────────────────────────────

@router.get("/api/auth/kakao")
async def kakao_login(request: Request) -> RedirectResponse:
    """카카오 인증 페이지로 리다이렉트."""
    if not settings.kakao_client_id:
        raise HTTPException(status_code=501, detail="카카오 OAuth가 설정되지 않았어요.")

    params = urlencode({
        "client_id": settings.kakao_client_id,
        "redirect_uri": _kakao_redirect_uri(request),
        "response_type": "code",
    })
    return RedirectResponse(f"{_KAKAO_AUTH_URL}?{params}")


@router.get("/api/auth/kakao/callback")
async def kakao_callback(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """카카오 인증 코드를 받아 JWT를 발급한다."""
    async with httpx.AsyncClient() as client:
        # 1. 액세스 토큰 교환
        token_res = await client.post(_KAKAO_TOKEN_URL, data={
            "grant_type":    "authorization_code",
            "client_id":     settings.kakao_client_id,
            "client_secret": settings.kakao_client_secret,
            "redirect_uri":  _kakao_redirect_uri(request),
            "code":          code,
        })
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="카카오 토큰 교환 실패")
        kakao_token = token_res.json()["access_token"]

        # 2. 사용자 정보 조회
        profile_res = await client.get(
            _KAKAO_PROFILE_URL,
            headers={"Authorization": f"Bearer {kakao_token}"},
        )
        if profile_res.status_code != 200:
            raise HTTPException(status_code=400, detail="카카오 프로필 조회 실패")
        profile = profile_res.json()

    email: str | None = (
        profile.get("kakao_account", {}).get("email")
    )
    if not email:
        # 이메일 미동의 → kakao_id로 대체 이메일 생성
        email = f"kakao_{profile['id']}@colorfit.app"

    user, is_new = await _get_or_create_user(db, email, "kakao")
    token = create_token(user.id, email)
    return RedirectResponse(_make_frontend_redirect(token, user.id, is_new))


# ── 구글 ──────────────────────────────────────────────────────────────────────

@router.get("/api/auth/google")
async def google_login(request: Request) -> RedirectResponse:
    """구글 인증 페이지로 리다이렉트."""
    if not settings.google_client_id:
        raise HTTPException(status_code=501, detail="구글 OAuth가 설정되지 않았어요.")

    params = urlencode({
        "client_id":     settings.google_client_id,
        "redirect_uri":  _google_redirect_uri(request),
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "online",
    })
    return RedirectResponse(f"{_GOOGLE_AUTH_URL}?{params}")


@router.get("/api/auth/google/callback")
async def google_callback(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """구글 인증 코드를 받아 JWT를 발급한다."""
    async with httpx.AsyncClient() as client:
        # 1. 액세스 토큰 교환
        token_res = await client.post(_GOOGLE_TOKEN_URL, data={
            "grant_type":    "authorization_code",
            "client_id":     settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri":  _google_redirect_uri(request),
            "code":          code,
        })
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="구글 토큰 교환 실패")
        access_token = token_res.json()["access_token"]

        # 2. 사용자 정보 조회
        profile_res = await client.get(
            _GOOGLE_PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_res.status_code != 200:
            raise HTTPException(status_code=400, detail="구글 프로필 조회 실패")
        profile = profile_res.json()

    email: str = profile.get("email", f"google_{profile['id']}@colorfit.app")
    user, is_new = await _get_or_create_user(db, email, "google")
    token = create_token(user.id, email)
    return RedirectResponse(_make_frontend_redirect(token, user.id, is_new))


# ── 내 정보 조회 ──────────────────────────────────────────────────────────────

@router.get("/api/auth/me", response_model=UserMeResponse)
async def get_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserMeResponse:
    """
    Authorization: Bearer <token> 헤더로 현재 사용자 정보를 반환한다.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 필요해요.")

    token = auth_header[7:]
    try:
        payload = verify_token(token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료됐어요. 다시 로그인해주세요.")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰이에요.")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="토큰 형식이 올바르지 않아요.")

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없어요.")

    return UserMeResponse(
        user_id=user.id,
        email=user.email,
        provider=user.provider,
        has_onboarding=bool(user.tone_id),
    )
