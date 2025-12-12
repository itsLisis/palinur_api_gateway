from fastapi import APIRouter, HTTPException, Depends, Query
from core.config import settings
from core.security import get_current_user
import httpx
import random

router = APIRouter(prefix="/matching", tags=["Matching"])

# httpx default timeout is quite small for endpoints that may do heavier DB work
HTTP_TIMEOUT = httpx.Timeout(20.0)


@router.get("/potential")
async def get_potential_matches(
    payload: dict = Depends(get_current_user)
):
    """Gets potential profiles for matching."""
    user_id = payload["user_id"]
    
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
           
            current_user_response = await client.get(
                f"{settings.USER_SERVICE_URL}/user/profile",
                params={"user_id": user_id}
            )
            
            if current_user_response.status_code != 200:
                raise HTTPException(status_code=current_user_response.status_code, detail="Error getting current user profile")
            
            current_user = current_user_response.json()
            
           
            excluded_response = await client.get(
                f"{settings.MATCHING_SERVICE_URL}/matching/excluded-users/{user_id}"
            )
            
            if excluded_response.status_code != 200:
                raise HTTPException(status_code=excluded_response.status_code, detail="Error getting excluded users")
            
            excluded_data = excluded_response.json()
            excluded_ids = excluded_data.get("excluded_ids", [])
            
          
            profiles_response = await client.get(
                f"{settings.USER_SERVICE_URL}/user/profiles"
            )
            
            if profiles_response.status_code != 200:
                raise HTTPException(status_code=profiles_response.status_code, detail="Error getting profiles")
            
            all_profiles = profiles_response.json()
            
         
            filter_response = await client.post(
                f"{settings.MATCHING_SERVICE_URL}/matching/filter-compatible",
                json={
                    "current_user": current_user,
                    "profiles": all_profiles,
                    "excluded_ids": excluded_ids
                }
            )
            
            if filter_response.status_code != 200:
                raise HTTPException(status_code=filter_response.status_code, detail="Error filtering compatible profiles")
            
            filtered_data = filter_response.json()
            filtered_profiles = filtered_data.get("profiles", [])
            
           
            if filtered_profiles:
                
                top_n = min(5, len(filtered_profiles))
                chosen = random.choice(filtered_profiles[:top_n])
                return {
                    "profiles": [chosen],
                    "count": filtered_data.get("count", len(filtered_profiles))
                }
            else:
                return {
                    "profiles": [],
                    "count": 0
                }
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@router.post("/swipe")
async def swipe_user(
    swipe_data: dict,
    payload: dict = Depends(get_current_user)
):

    user_id = payload["user_id"]
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{settings.MATCHING_SERVICE_URL}/matching/swipe",
                params={"current_user_id": user_id},
                json=swipe_data
            )
        
        if res.status_code not in [200, 201]:
            try:
                error_detail = res.json()
            except:
                error_detail = res.text or "Unknown error from matching service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)
        
        return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Matching service unavailable: {str(e)}")


@router.get("/relationships/check")
async def check_relationship(
    user1_id: int = Query(..., description="ID del primer usuario"),
    user2_id: int = Query(..., description="ID del segundo usuario")
):

    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{settings.MATCHING_SERVICE_URL}/matching/relationships/check",
                params={"user1_id": user1_id, "user2_id": user2_id}
            )
        
        if res.status_code != 200:
            try:
                error_detail = res.json()
            except:
                error_detail = res.text or "Unknown error from matching service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)
        
        return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Matching service unavailable: {str(e)}")


@router.get("/relationships/user/{user_id}/active")
async def get_active_relationship(user_id: int):
    """
    Obtiene la relación activa (match) de un usuario.
    """
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{settings.MATCHING_SERVICE_URL}/matching/relationships/user/{user_id}/active"
            )
        
        if res.status_code != 200:
            try:
                error_detail = res.json()
            except:
                error_detail = res.text or "Unknown error from matching service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)
        
        return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Matching service unavailable: {str(e)}")


@router.post("/dismatch")
async def dismatch(
    relationship_id: int,
    payload: dict = Depends(get_current_user),
):

    user_id = payload["user_id"]
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            res = await client.post(
                f"{settings.MATCHING_SERVICE_URL}/matching/relationships/{relationship_id}/dismatch",
                params={"current_user_id": user_id},
            )

            if res.status_code != 200:
                try:
                    error_detail = res.json()
                except Exception:
                    error_detail = res.text or "Unknown error from matching service"
                raise HTTPException(status_code=res.status_code, detail=error_detail)

            # Deactivate chat best-effort
            try:
                await client.post(
                    f"{settings.CHAT_SERVICE_URL}/internal/chats/deactivate",
                    params={"relationship_id": relationship_id},
                )
            except Exception:
                pass

            return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@router.get("/connections")
async def connections(payload: dict = Depends(get_current_user)):
 
    user_id = payload["user_id"]
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            rel_res = await client.get(
                f"{settings.MATCHING_SERVICE_URL}/matching/connections/{user_id}"
            )
            if rel_res.status_code != 200:
                raise HTTPException(status_code=rel_res.status_code, detail="Error getting connections")
            partner_ids = rel_res.json().get("partners", [])

            profiles_res = await client.get(f"{settings.USER_SERVICE_URL}/user/profiles")
            if profiles_res.status_code != 200:
                raise HTTPException(status_code=profiles_res.status_code, detail="Error getting profiles")
            profiles = profiles_res.json()
            by_id = {p["id"]: p for p in profiles}

            connections = []
            for pid in partner_ids:
                p = by_id.get(pid)
                if not p:
                    continue
                photo = None
                imgs = p.get("images") or []
                if imgs:
                    photo = imgs[0]
                connections.append(
                    {"user_id": pid, "username": p.get("username"), "photo_url": photo}
                )

            return {"connections": connections, "count": len(connections)}
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

