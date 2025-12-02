from fastapi import APIRouter, Depends
from core.security import require_complete_profile

router = APIRouter(prefix="/home", tags=["Home"])

@router.get("/", dependencies=[Depends(require_complete_profile)])
async def get_home(payload: dict = Depends(require_complete_profile)):

    return {
        "message": "Welcome to home!",
        "user_id": payload["user_id"],
        "complete_profile": payload["complete_profile"]
    }

