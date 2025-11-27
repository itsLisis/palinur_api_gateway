from fastapi import APIRouter, HTTPException
from core.config import settings
import httpx

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
async def register_proxy(data: dict):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.AUTH_SERVICE_URL}/auth/register", json=data)

    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail=res.json())

    return res.json()


@router.post("/login")
async def login_proxy(data: dict):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.AUTH_SERVICE_URL}/auth/login", json=data)

    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail=res.json())

    return res.json()
