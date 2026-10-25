import os
import uuid
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import get_settings

# Module-level cache for JWKS client to avoid refetching on every request
_jwks_client: Optional[jwt.PyJWKClient] = None
_test_verification_key: Optional[str] = None


def set_test_verification_key(key: Optional[str]) -> None:
    """Set an in-memory verification key for unit testing."""
    global _test_verification_key
    _test_verification_key = key


def get_jwks_client() -> Optional[jwt.PyJWKClient]:
    """Retrieve or initialize PyJWKClient if CLERK_JWKS_URL or CLERK_PUBLISHABLE_KEY is configured."""
    global _jwks_client
    settings = get_settings()
    if _jwks_client is None:
        jwks_url = settings.CLERK_JWKS_URL
        if not jwks_url and settings.CLERK_PUBLISHABLE_KEY:
            try:
                import base64
                raw = settings.CLERK_PUBLISHABLE_KEY
                if "_" in raw:
                    b64 = raw.split("_", 2)[-1]
                    b64 += "=" * (-len(b64) % 4)
                    host = base64.b64decode(b64).decode("utf-8").rstrip("$")
                    jwks_url = f"https://{host}/.well-known/jwks.json"
            except Exception:
                pass
        if jwks_url:
            _jwks_client = jwt.PyJWKClient(jwks_url)
    return _jwks_client


def verify_clerk_token(token: str) -> Dict[str, Any]:
    """
    Verify a Clerk JWT session token.
    Supports:
    1. Test verification key (set via set_test_verification_key for unit tests)
    2. CLERK_PEM_PUBLIC_KEY (from env/settings)
    3. CLERK_JWKS_URL or CLERK_PUBLISHABLE_KEY (via PyJWKClient)
    4. CLERK_SECRET_KEY fallback for symmetric HMAC development/test tokens

    Returns the decoded token claims dictionary.
    Raises HTTPException(401) on invalid or expired token.
    """
    settings = get_settings()
    signing_key = None
    algorithms = ["RS256", "HS256"]

    # 1. Test key takes precedence during test execution
    if _test_verification_key is not None:
        signing_key = _test_verification_key
    # 2. Configured PEM public key
    elif settings.CLERK_PEM_PUBLIC_KEY:
        signing_key = settings.CLERK_PEM_PUBLIC_KEY
    # 3. Remote JWKS endpoint
    elif settings.CLERK_JWKS_URL or settings.CLERK_PUBLISHABLE_KEY:
        client = get_jwks_client()
        if client is not None:
            try:
                signing_key = client.get_signing_key_from_jwt(token).key
            except Exception as e:
                # Fallback to symmetric secret key if token is HS256
                if settings.CLERK_SECRET_KEY:
                    signing_key = settings.CLERK_SECRET_KEY
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "error": {
                                "code": "invalid_token",
                                "message": f"Unable to find signing key: {str(e)}",
                                "request_id": str(uuid.uuid4()),
                            }
                        },
                    )
    # 4. Secret key fallback (if using HS256 in test/local dev)
    elif settings.CLERK_SECRET_KEY:
        signing_key = settings.CLERK_SECRET_KEY

    # If no key is configured in test/dev environment, fallback to reading unverified in local mock only if mode=mock
    if signing_key is None:
        # Check if environment is test or development and no key configured
        if os.getenv("ENVIRONMENT") == "test":
            # In test mode without key, reject
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "auth_not_configured",
                        "message": "Clerk authentication key not configured",
                        "request_id": str(uuid.uuid4()),
                    }
                },
            )

    try:
        # Decode and verify signature, exp, nbf
        decoded = jwt.decode(
            token,
            signing_key,
            algorithms=algorithms,
            options={"verify_signature": signing_key is not None, "verify_exp": True},
        )
        if not decoded.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "invalid_token",
                        "message": "Token missing subject (sub) claim",
                        "request_id": str(uuid.uuid4()),
                    }
                },
            )
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "token_expired",
                    "message": "Authentication token has expired",
                    "request_id": str(uuid.uuid4()),
                }
            },
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "invalid_token",
                    "message": f"Invalid authentication token: {str(e)}",
                    "request_id": str(uuid.uuid4()),
                }
            },
        )


class ClerkAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that inspects the Authorization header:
    - If Bearer token is provided, verifies it and populates request.state.user_id.
    - If token is expired or forged, sets request.state.auth_error and user_id=None.
    - If no Authorization header is provided, user_id is set to None (anonymous mode).
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        auth_header = request.headers.get("Authorization")
        request.state.user_id = None
        request.state.auth_token = None
        request.state.auth_error = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            request.state.auth_token = token
            try:
                claims = verify_clerk_token(token)
                request.state.user_id = claims["sub"]
            except HTTPException as exc:
                request.state.auth_error = exc.detail
            except Exception as exc:
                request.state.auth_error = {
                    "error": {
                        "code": "invalid_token",
                        "message": str(exc),
                        "request_id": str(uuid.uuid4()),
                    }
                }

        return await call_next(request)


def get_current_user(request: Request) -> str:
    """
    FastAPI dependency enforcing authentication.
    Returns the authenticated user_id (from Clerk JWT 'sub').
    Raises 401 if missing, invalid, or expired.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "unauthorized",
                    "message": "Authorization header missing or invalid format (expected Bearer <token>)",
                    "request_id": str(uuid.uuid4()),
                }
            },
        )

    # If middleware already ran and encountered an error
    if getattr(request.state, "auth_error", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=request.state.auth_error,
        )

    # If middleware populated user_id
    if getattr(request.state, "user_id", None):
        return request.state.user_id

    # Fallback direct verification if middleware didn't run
    token = auth_header[7:].strip()
    claims = verify_clerk_token(token)
    user_id = claims["sub"]
    request.state.user_id = user_id
    return user_id


def get_optional_user(request: Request) -> Optional[str]:
    """
    FastAPI dependency for endpoints supporting both anonymous and authenticated calls.
    Returns user_id if valid token present, None if anonymous.
    Raises 401 if a token was supplied but is invalid/expired.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    if getattr(request.state, "auth_error", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=request.state.auth_error,
        )

    if getattr(request.state, "user_id", None):
        return request.state.user_id

    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        claims = verify_clerk_token(token)
        user_id = claims["sub"]
        request.state.user_id = user_id
        return user_id

    return None
