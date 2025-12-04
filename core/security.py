from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt

from .config import settings

security = HTTPBearer()

ALGORITHM = "HS256"

def verify_jwt(credentials = Depends(security)):
    
    token = credentials.credentials
    print(f"[API_GATEWAY] verify_jwt - Token received: {token[:50]}...")
    print(f"[API_GATEWAY] verify_jwt - SECRET_KEY: {settings.SECRET_KEY}")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        print(f"[API_GATEWAY] verify_jwt - Token verified successfully: {payload}")
        return payload

    except jwt.ExpiredSignatureError:
        print(f"[API_GATEWAY] verify_jwt - Token expired")
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError as e:
        print(f"[API_GATEWAY] verify_jwt - Invalid token: {str(e)}")
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
