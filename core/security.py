from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt

from config import settings

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
