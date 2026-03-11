"""OAuth login routes — GitHub and Google."""

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.crud import user as user_crud
from app.db.session import get_db
from app.schemas.user import TokenResponse

router = APIRouter(prefix="/oauth", tags=["oauth"])


# --- GitHub ---

@router.get("/github/authorize")
async def github_authorize() -> dict[str, str]:
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="GitHub OAuth not configured")
    return {
        "authorize_url": (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&scope=user:email"
            f"&redirect_uri={settings.OAUTH_REDIRECT_BASE}/api/v1/oauth/github/callback"
        )
    }


@router.get("/github/callback", response_model=TokenResponse)
async def github_callback(code: str, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="GitHub OAuth not configured")

    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()
        gh_token = token_data.get("access_token")
        if not gh_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get GitHub access token")

        # Get user info
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {gh_token}"},
        )
        gh_user = user_resp.json()
        gh_id = str(gh_user["id"])

        # Get primary email
        email_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {gh_token}"},
        )
        emails = email_resp.json()
        primary_email = next((e["email"] for e in emails if e.get("primary")), None)
        if not primary_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No primary email on GitHub account")

    return await _oauth_login_or_register(db, "github", gh_id, primary_email, gh_user.get("login"))


# --- Google ---

@router.get("/google/authorize")
async def google_authorize() -> dict[str, str]:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth not configured")
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/api/v1/oauth/google/callback"
    return {
        "authorize_url": (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope=openid+email+profile"
        )
    }


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(code: str, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth not configured")

    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/api/v1/oauth/google/callback"
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        token_data = token_resp.json()
        id_token = token_data.get("access_token")
        if not id_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get Google access token")

        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {id_token}"},
        )
        google_user = userinfo_resp.json()
        google_id = str(google_user["id"])
        email = google_user.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No email on Google account")

    return await _oauth_login_or_register(db, "google", google_id, email, google_user.get("name"))


# --- Shared ---

async def _oauth_login_or_register(
    db: AsyncSession, provider: str, oauth_id: str, email: str, nickname: str | None
) -> TokenResponse:
    """Find existing OAuth user or create a new one, then return tokens."""
    user = await user_crud.get_by_oauth(db, provider, oauth_id)
    if not user:
        # Check if email is already registered (link accounts)
        user = await user_crud.get_by_email(db, email)
        if user:
            await user_crud.update(db, user, oauth_provider=provider, oauth_id=oauth_id)
        else:
            user = await user_crud.create(
                db, email=email, oauth_provider=provider, oauth_id=oauth_id, nickname=nickname
            )
        await db.commit()
        await db.refresh(user)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )
