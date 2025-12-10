from fastapi import APIRouter, HTTPException, Depends
from core.config import settings
from core.security import require_incomplete_profile, get_current_user
from schemas import ProfileComplete, ProfileCompleteResponse
import httpx

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/complete_profile", dependencies=[Depends(require_incomplete_profile)])
async def get_profile_options():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{settings.USER_SERVICE_URL}/user/complete_profile")

        if res.status_code != 200:
            try:
                error_detail = res.json()
            except:
                error_detail = res.text or "Unknown error from user service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)

        return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"User service unavailable: {str(e)}")

@router.post("/complete_profile", response_model=ProfileCompleteResponse)
async def complete_profile(data: ProfileComplete, payload: dict = Depends(require_incomplete_profile)):
    user_id = payload["user_id"]
    
    profile_data = data.model_dump(mode='json')
    profile_data["user_id"] = user_id
    
    try:
        async with httpx.AsyncClient() as client:

            user_response = await client.post(
                f"{settings.USER_SERVICE_URL}/user/complete_profile",
                params={"user_id": user_id},
                json=profile_data
            )

            if user_response.status_code != 200:
                try:
                    error_detail = user_response.json()
                except:
                    error_detail = user_response.text or "Unknown error from user service"
                raise HTTPException(
                    status_code=user_response.status_code, 
                    detail=error_detail
                )

            profile_result = user_response.json()
            
            auth_response = await client.patch(
                f"{settings.AUTH_SERVICE_URL}/auth/users/{user_id}/complete_profile"
            )
            
            if auth_response.status_code != 200:
                return {
                    **profile_result,
                    "warning": "Profile created but token not updated. Please login again.",
                    "token_updated": False
                }
            
            auth_result = auth_response.json()
            
            return {
                "message": profile_result["message"],
                "profile_id": profile_result["profile_id"],
                "access_token": auth_result["access_token"],
                "token_type": auth_result["token_type"],
                "complete_profile": auth_result["complete_profile"],
                "user_id": auth_result["user_id"],
                "next_endpoint": "/home"
            }
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@router.get("/profile")
async def get_user_profile(payload: dict = Depends(get_current_user)):
    """Get the profile of the authenticated user."""
    user_id = payload["user_id"]
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{settings.USER_SERVICE_URL}/user/profile",
                params={"user_id": user_id}
            )

        if res.status_code != 200:
            try:
                error_detail = res.json()
            except:
                error_detail = res.text or "Unknown error from user service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)

        return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"User service unavailable: {str(e)}")