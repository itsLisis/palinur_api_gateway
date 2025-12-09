from fastapi import APIRouter, HTTPException, Depends
from core.config import settings
from core.security import verify_jwt, require_complete_profile
import httpx

router = APIRouter(prefix="/profile", tags=["Profile"])

