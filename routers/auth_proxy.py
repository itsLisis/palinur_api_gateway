from fastapi import APIRouter, HTTPException, Request
from core.config import settings
import httpx
from schemas import UserRegister, UserLogin, AuthResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=AuthResponse)
async def register_proxy(data: UserRegister, request: Request):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/register", 
                json=data.model_dump(mode='json'),
                headers={"X-Forwarded-For": request.client.host}
            )

        if res.status_code != 200:
            try:
                error_detail = res.json()
            except:
                error_detail = res.text or "Unknown error from auth service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)

        auth_response = res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")
    
    return {
        "access_token": auth_response["access_token"],
        "token_type": auth_response["token_type"],
        "complete_profile": auth_response["complete_profile"],
        "user_id": auth_response["user_id"],
        "next_endpoint": "/user/complete_profile"
    }


@router.post("/login", response_model=AuthResponse)
async def login_proxy(data: UserLogin, request: Request):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/login", 
                json=data.model_dump(),
                headers={"X-Forwarded-For": request.client.host}
            )

        if res.status_code != 200:
            try:
                error_detail = res.json()
            except:
                error_detail = res.text or "Unknown error from auth service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)

        auth_response = res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")
    
    if auth_response.get("complete_profile"):
        next_endpoint = "/home"
    else:
        next_endpoint = "/user/complete_profile"
    
    return {
        "access_token": auth_response["access_token"],
        "token_type": auth_response["token_type"],
        "complete_profile": auth_response["complete_profile"],
        "user_id": auth_response["user_id"],
        "next_endpoint": next_endpoint
    }
