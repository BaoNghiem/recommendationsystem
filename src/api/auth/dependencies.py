"""
FastAPI Dependencies: JWT token extraction + role checks
=========================================================
Usage:
  current_user = Depends(get_current_user)
  admin_user   = Depends(require_admin)
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.api.auth.utils import decode_token
from src.database.db_config import DatabaseConnector

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    """
    Parse Bearer token -> return user dict from DB.
    Raises 401 if token is invalid or user does not exist.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token missing user info.")

    conn = DatabaseConnector.get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT user_id, email, role, account_type, is_active FROM users WHERE user_id = %s",
            (int(user_id),)
        )
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="User does not exist.")

    user_id_db, email, role, account_type, is_active = row

    if not is_active:
        raise HTTPException(status_code=403, detail="Account has been disabled.")

    return {
        "user_id":      user_id_db,
        "email":        email,
        "role":         role,
        "account_type": account_type,
    }


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Only allow admin role to access."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return current_user
