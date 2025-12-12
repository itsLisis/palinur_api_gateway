from fastapi import APIRouter, HTTPException, Depends, Query
from core.config import settings
from core.security import get_current_user
import httpx

router = APIRouter(prefix="/matching", tags=["Matching"])


@router.get("/potential")
async def get_potential_matches(
    payload: dict = Depends(get_current_user)
):
    """
    Obtiene perfiles potenciales para hacer match.
    El gateway orquesta las llamadas entre user_service y matching_service.
    """
    user_id = payload["user_id"]
    
    try:
        async with httpx.AsyncClient() as client:
            # 1. Obtener usuarios excluidos del matching service
            excluded_response = await client.get(
                f"{settings.MATCHING_SERVICE_URL}/matching/excluded-users/{user_id}"
            )
            
            if excluded_response.status_code != 200:
                raise HTTPException(status_code=excluded_response.status_code, detail="Error getting excluded users")
            
            excluded_data = excluded_response.json()
            excluded_ids = excluded_data.get("excluded_ids", [])
            
            # 2. Obtener todos los perfiles del user service
            profiles_response = await client.get(
                f"{settings.USER_SERVICE_URL}/user/profiles"
            )
            
            if profiles_response.status_code != 200:
                raise HTTPException(status_code=profiles_response.status_code, detail="Error getting profiles")
            
            all_profiles = profiles_response.json()
            
            # 3. Filtrar perfiles excluidos
            filtered_profiles = [
                profile for profile in all_profiles 
                if profile["id"] not in excluded_ids
            ]
            
            # 4. Retornar el primer perfil como recomendación
            if filtered_profiles:
                return {
                    "profiles": [filtered_profiles[0]],
                    "count": len(filtered_profiles)
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
    """
    Hace swipe (like/dislike) a un usuario.
    """
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
    """
    Verifica si existe un match/relación entre dos usuarios.
    """
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

