from fastapi import APIRouter, HTTPException, Depends
from core.config import settings
from core.security import require_incomplete_profile
from schemas import ProfileComplete, ProfileCompleteResponse
import httpx

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/complete_profile")
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
    print(f"[USER_PROXY] POST /complete_profile - user_id: {user_id}")
    print(f"[USER_PROXY] POST /complete_profile - payload: {payload}")
    
    profile_data = data.model_dump()
    profile_data["user_id"] = user_id
    # Convert date to string for JSON serialization
    if isinstance(profile_data.get("birthday"), str):
        profile_data["birthday"] = profile_data["birthday"]
    else:
        profile_data["birthday"] = profile_data["birthday"].isoformat() if profile_data.get("birthday") else None
    print(f"[USER_PROXY] POST /complete_profile - profile_data: {profile_data}")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"[USER_PROXY] Calling user service at {settings.USER_SERVICE_URL}/user/complete_profile")
            user_response = await client.post(
                f"{settings.USER_SERVICE_URL}/user/complete_profile",
                json=profile_data
            )
            print(f"[USER_PROXY] User service response status: {user_response.status_code}")

            if user_response.status_code != 200:
                try:
                    error_detail = user_response.json()
                except:
                    error_detail = user_response.text or "Unknown error from user service"
                print(f"[USER_PROXY] User service error: {error_detail}")
                raise HTTPException(
                    status_code=user_response.status_code, 
                    detail=error_detail
                )

            profile_result = user_response.json()
            print(f"[USER_PROXY] Profile result: {profile_result}")
            
            print(f"[USER_PROXY] Calling auth service to mark profile complete")
            auth_response = await client.patch(
                f"{settings.AUTH_SERVICE_URL}/auth/users/{user_id}/complete_profile"
            )
            print(f"[USER_PROXY] Auth service response status: {auth_response.status_code}")
            
            if auth_response.status_code != 200:
                try:
                    error_detail = auth_response.json()
                except:
                    error_detail = auth_response.text or "Unknown error from auth service"
                print(f"[USER_PROXY] Auth service error: {error_detail}")
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=error_detail
                )
            
            auth_result = auth_response.json()
            print(f"[USER_PROXY] Auth result: {auth_result}")

            return {
                "message": "Profile completed successfully",
                "profile_id": profile_result.get("profile_id", user_id),
                "access_token": auth_result.get("access_token", ""),
                "token_type": auth_result.get("token_type", "bearer"),
                "complete_profile": auth_result.get("complete_profile", True)
            }
    except HTTPException:
        raise
    except httpx.RequestError as e:
        print(f"[USER_PROXY] Request error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
    except Exception as e:
        print(f"[USER_PROXY] Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")