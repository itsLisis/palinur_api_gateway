from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
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


@router.get("/options")
async def get_profile_options_any(payload: dict = Depends(get_current_user)):

    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{settings.USER_SERVICE_URL}/user/complete_profile")

        if res.status_code != 200:
            try:
                error_detail = res.json()
            except Exception:
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


@router.patch("/profile")
async def update_own_profile(data: dict, payload: dict = Depends(get_current_user)):
    """
    Update the authenticated user's profile (introduction, interests, etc.).
    """
    user_id = payload["user_id"]
    try:
        async with httpx.AsyncClient() as client:
            res = await client.patch(
                f"{settings.USER_SERVICE_URL}/user/profile",
                params={"user_id": user_id},
                json=data,
            )

        if res.status_code != 200:
            try:
                error_detail = res.json()
            except Exception:
                error_detail = res.text or "Unknown error from user service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)

        return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"User service unavailable: {str(e)}")


@router.delete("/account")
async def delete_account(payload: dict = Depends(get_current_user)):
    """
    Delete the authenticated user's account and ALL related data across services:
    - matching (swipes + relationships)
    - chat (chats + messages)
    - user profile (profile + images + interests)
    - auth user record
    """
    user_id = payload["user_id"]
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        results = {}

        # 1) matching cleanup
        try:
            r = await client.delete(
                f"{settings.MATCHING_SERVICE_URL}/matching/internal/users/delete",
                params={"user_id": user_id},
            )
            results["matching"] = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"status_code": r.status_code}
        except Exception as e:
            results["matching"] = {"success": False, "error": str(e)}

        # 2) chat cleanup
        try:
            r = await client.delete(
                f"{settings.CHAT_SERVICE_URL}/internal/users/delete",
                params={"user_id": user_id},
            )
            results["chat"] = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"status_code": r.status_code}
        except Exception as e:
            results["chat"] = {"success": False, "error": str(e)}

        # 3) user profile cleanup
        try:
            r = await client.delete(
                f"{settings.USER_SERVICE_URL}/user/profile",
                params={"user_id": user_id},
            )
            results["profile"] = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"status_code": r.status_code}
        except Exception as e:
            results["profile"] = {"success": False, "error": str(e)}

        # 4) auth user cleanup
        try:
            r = await client.delete(f"{settings.AUTH_SERVICE_URL}/auth/users/{user_id}")
            results["auth"] = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"status_code": r.status_code}
        except Exception as e:
            results["auth"] = {"success": False, "error": str(e)}

    # If auth deletion succeeded, consider account deleted even if other services had partial errors.
    if results.get("auth", {}).get("success") is True:
        return {"success": True, "user_id": user_id, "results": results}

    raise HTTPException(status_code=500, detail={"success": False, "user_id": user_id, "results": results})


@router.get("/profile/{user_id}")
async def get_profile_by_id(
    user_id: int,
    _payload: dict = Depends(get_current_user),
):
    """
    Get any user's profile by id (used for showing chat partner name).
    Requires authentication, but does NOT force user_id to match the token.
    """
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{settings.USER_SERVICE_URL}/user/profile",
                params={"user_id": user_id},
            )

        if res.status_code != 200:
            try:
                error_detail = res.json()
            except Exception:
                error_detail = res.text or "Unknown error from user service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)

        return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"User service unavailable: {str(e)}")

@router.post("/profile/upload-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    payload: dict = Depends(get_current_user)
):
    """Upload a profile image."""
    user_id = payload["user_id"]
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Create multipart form data
        files = {"file": (file.filename, file_content, file.content_type)}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{settings.USER_SERVICE_URL}/user/profile/upload-image",
                params={"user_id": user_id},
                files=files
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

@router.delete("/profile/image/{image_id}")
async def delete_profile_image(
    image_id: int,
    payload: dict = Depends(get_current_user)
):
    """Delete a profile image."""
    user_id = payload["user_id"]
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.delete(
                f"{settings.USER_SERVICE_URL}/user/profile/image/{image_id}",
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

@router.get("/profiles")
async def get_all_profiles():
    """Get all user profiles (for matching service)."""
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{settings.USER_SERVICE_URL}/user/profiles")

        if res.status_code != 200:
            try:
                error_detail = res.json()
            except:
                error_detail = res.text or "Unknown error from user service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)

        return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"User service unavailable: {str(e)}")


@router.get("/profiles/random")
async def get_random_profile(payload: dict = Depends(get_current_user)):
    """Get a random profile for the authenticated user."""
    user_id = payload["user_id"]
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{settings.USER_SERVICE_URL}/user/profiles/random",
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