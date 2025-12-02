from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt

from .config import settings

security = HTTPBearer()

ALGORITHM = "HS256"

def verify_jwt(credentials = Depends(security)):
    
    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_complete_profile(payload: dict = Depends(verify_jwt)):

    if not payload.get("complete_profile", False):
        raise HTTPException(
            status_code=403, 
            detail="Profile not completed. Please complete your profile first."
        )
    return payload


def require_incomplete_profile(payload: dict = Depends(verify_jwt)):

    if payload.get("complete_profile", False):
        raise HTTPException(
            status_code=403,
            detail="Profile already completed. Access denied."
        )
    return payload
