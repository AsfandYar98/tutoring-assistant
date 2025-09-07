"""API dependencies for authentication and database access."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_id, get_tenant_id

# Security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """Get current authenticated user."""
    token = credentials.credentials
    user_id = get_current_user_id(token)
    tenant_id = get_tenant_id(token)
    
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "token": token
    }


def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get current tenant ID from token."""
    token = credentials.credentials
    return get_tenant_id(token)
