from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from app.core.config import settings
from app.core.security import (
    create_session_token,
    decode_session_token,
    generate_csrf_token,
    generate_pkce_pair,
    get_current_user,
    SESSION_COOKIE_NAME,
    CSRF_COOKIE_NAME,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

class DemoLoginBody(BaseModel):
    role: str = "analyst"  # "viewer", "analyst", "admin"

@router.get("/session")
async def get_session(
    request: Request,
    response: Response,
    arena_session: Optional[str] = None,
):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    auth_header = request.headers.get("Authorization")
    if not token and auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]

    payload = decode_session_token(token) if token else None

    # Ensure CSRF cookie is present
    csrf_token = request.cookies.get(CSRF_COOKIE_NAME)
    if not csrf_token:
        csrf_token = generate_csrf_token()
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_token,
            httponly=False,  # Client JS needs to read it and send in X-CSRF-Token header
            samesite="lax",
            secure=settings.cookie_secure,
        )

    if not payload:
        return {
            "authenticated": False,
            "user": None,
            "csrf_token": csrf_token,
            "demo_mode": settings.demo_mode,
            "environment": settings.app_env,
        }

    return {
        "authenticated": True,
        "user": {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
        },
        "csrf_token": csrf_token,
        "demo_mode": settings.demo_mode,
        "environment": settings.app_env,
    }

@router.post("/demo-login")
async def demo_login(
    body: DemoLoginBody,
    request: Request,
    response: Response,
):
    if not settings.demo_mode or settings.app_env.lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login is disabled in production environments.",
        )

    role = body.role.lower()
    if role not in ["viewer", "analyst", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid demo role: {role}. Must be 'viewer', 'analyst', or 'admin'.",
        )

    user_id = f"demo-{role}-001"
    username = f"demo_{role}"
    email = f"{role}@demo.local"
    roles = [role]

    session_token = create_session_token(user_id, username, email, roles)
    csrf_token = generate_csrf_token()

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=86400 * 7,
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=86400 * 7,
    )

    return {
        "status": "success",
        "user": {
            "user_id": user_id,
            "username": username,
            "email": email,
            "roles": roles,
        },
        "token": session_token,
        "csrf_token": csrf_token,
    }

@router.get("/login")
async def oidc_login():
    """Initiates Keycloak OIDC Authorization Code Flow with PKCE."""
    verifier, challenge = generate_pkce_pair()
    auth_url = (
        f"{settings.oidc_issuer_url}/protocol/openid-connect/auth"
        f"?client_id={settings.oidc_client_id}"
        f"&response_type=code"
        f"&scope=openid profile email"
        f"&redirect_uri={settings.oidc_redirect_uri}"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
    )
    return {"authorization_url": auth_url, "code_verifier": verifier}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME)
    response.delete_cookie(CSRF_COOKIE_NAME)
    return {"status": "logged_out"}
