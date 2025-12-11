from fastapi import APIRouter, HTTPException, Depends, Query
from core.config import settings
from core.security import get_current_user
import httpx

router = APIRouter(prefix="/matching", tags=["Matching"])


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
                f"{settings.MATCHING_SERVICE_URL}/relationships/check",
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
                f"{settings.MATCHING_SERVICE_URL}/relationships/user/{user_id}/active"
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


@router.get("/relationships/user/{user_id}/all")
async def get_all_relationships(
    user_id: int,
    payload: dict = Depends(get_current_user)
):
    """
    Obtiene todas las relaciones de un usuario (requiere autenticación).
    """
    # Verificar que el usuario solo puede ver sus propias relaciones
    if payload["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver las relaciones de otro usuario")
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{settings.MATCHING_SERVICE_URL}/relationships/user/{user_id}/all"
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

