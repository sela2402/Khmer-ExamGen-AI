from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.concurrency import run_in_threadpool
from supabase_auth.errors import AuthApiError, AuthRetryableError

from app.config import settings
from utils.supabase_client import create_supabase_client


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in with Supabase to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication is not configured. Set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY (or SUPABASE_KEY) in backend/.env.",
        )

    try:
        response = await run_in_threadpool(
            create_supabase_client().auth.get_user, credentials.credentials
        )
    except AuthApiError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Supabase access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    except AuthRetryableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach Supabase to verify the access token.",
        ) from error

    user = response.user if response else None
    if user is None or not user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Supabase access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"id": user.id, "sub": user.id, "email": user.email}
