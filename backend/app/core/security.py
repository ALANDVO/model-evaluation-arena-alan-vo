import base64
import hashlib
import hmac
import os
import secrets
import time
from typing import Dict, List, Optional
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
import jwt
from app.core.config import settings

ALGORITHM = "HS256"
SESSION_COOKIE_NAME = "arena_session"
CSRF_COOKIE_NAME = "arena_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"

def generate_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return verifier, challenge

def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)

def create_session_token(user_id: str, username: str, email: str, roles: List[str]) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "email": email,
        "roles": roles,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 7,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def decode_session_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None

async def get_current_user(
    request: Request,
    arena_session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = None
    if arena_session:
        token = arena_session
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in or supply a valid session token.",
        )

    payload = decode_session_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
        )
    return payload

def require_role(allowed_roles: List[str]):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        # 'admin' has superuser access to all viewer/analyst routes
        if "admin" in user_roles:
            return current_user
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}",
            )
        return current_user
    return role_checker

async def verify_csrf(
    request: Request,
    arena_csrf: Optional[str] = Cookie(default=None, alias=CSRF_COOKIE_NAME),
    x_csrf_token: Optional[str] = Header(default=None, alias=CSRF_HEADER_NAME),
) -> None:
    # Only verify CSRF on mutating HTTP methods
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        # If authenticated via Authorization Bearer header, CSRF cookie is not strictly needed
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return
        if not arena_csrf or not x_csrf_token or not hmac.compare_digest(arena_csrf, x_csrf_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token validation failed or header missing.",
            )
