from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from core.config import settings
from core.security import get_current_user
from schemas import ChatListResponse, MessageListResponse
import httpx
import websockets
import asyncio
import json
import jwt

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/chats", response_model=ChatListResponse)
async def get_user_chats(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    payload: dict = Depends(get_current_user)
):
    """
    Obtiene todos los chats del usuario autenticado.
    """
    user_id = payload["user_id"]
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{settings.CHAT_SERVICE_URL}/chats",
                params={"user_id": user_id, "skip": skip, "limit": limit}
            )
        
        if res.status_code != 200:
            try:
                error_detail = res.json()
            except:
                error_detail = res.text or "Unknown error from chat service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)
        
        return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Chat service unavailable: {str(e)}")


@router.get("/chats/{chat_id}/messages", response_model=MessageListResponse)
async def get_messages(
    chat_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    payload: dict = Depends(get_current_user)
):
    """
    Obtiene el historial de mensajes de un chat.
    """
    user_id = payload["user_id"]
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{settings.CHAT_SERVICE_URL}/chats/{chat_id}/messages",
                params={"user_id": user_id, "page": page, "page_size": page_size}
            )
        
        if res.status_code != 200:
            try:
                error_detail = res.json()
            except:
                error_detail = res.text or "Unknown error from chat service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)
        
        return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Chat service unavailable: {str(e)}")


@router.post("/chats/{chat_id}/read")
async def mark_messages_read(
    chat_id: int,
    payload: dict = Depends(get_current_user)
):
    """
    Marca todos los mensajes de un chat como leídos.
    """
    user_id = payload["user_id"]
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{settings.CHAT_SERVICE_URL}/chats/{chat_id}/read",
                params={"user_id": user_id}
            )
        
        if res.status_code != 200:
            try:
                error_detail = res.json()
            except:
                error_detail = res.text or "Unknown error from chat service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)
        
        return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Chat service unavailable: {str(e)}")


@router.get("/chats/by-relationship/{relationship_id}")
async def get_chat_by_relationship(
    relationship_id: int,
    payload: dict = Depends(get_current_user)
):
    """
    Obtiene un chat por su relationship_id.
    """
    user_id = payload["user_id"]
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{settings.CHAT_SERVICE_URL}/chats/by-relationship/{relationship_id}",
                params={"user_id": user_id}
            )
        
        if res.status_code != 200:
            try:
                error_detail = res.json()
            except:
                error_detail = res.text or "Unknown error from chat service"
            raise HTTPException(status_code=res.status_code, detail=error_detail)
        
        return res.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Chat service unavailable: {str(e)}")


@router.websocket("/ws/{token}")
async def websocket_proxy(websocket: WebSocket, token: str):
    """
    Proxy WebSocket que redirige al chat service.
    El gateway desencripta el token y pasa solo el user_id al chat service.
    """
    await websocket.accept()
    
    # Desencriptar el token en el gateway (igual que en REST endpoints)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub") or payload.get("user_id")
        
        if not user_id:
            error_msg = json.dumps({"type": "error", "error": "Token inválido"})
            await websocket.send_text(error_msg)
            await websocket.close(code=4001)
            return
            
    except jwt.ExpiredSignatureError:
        error_msg = json.dumps({"type": "error", "error": "Token expirado"})
        await websocket.send_text(error_msg)
        await websocket.close(code=4001)
        return
    except jwt.InvalidTokenError:
        error_msg = json.dumps({"type": "error", "error": "Token inválido"})
        await websocket.send_text(error_msg)
        await websocket.close(code=4001)
        return
    
    # Construir la URL del WebSocket del chat service con user_id
    chat_ws_url = settings.CHAT_SERVICE_URL.replace("http://", "ws://").replace("https://", "wss://")
    chat_ws_url = f"{chat_ws_url}/ws/{user_id}"
    
    chat_ws = None
    
    try:
        # Conectar al WebSocket del chat service
        chat_ws = await websockets.connect(chat_ws_url)
        
        async def forward_to_chat():
            """Reenvía mensajes del cliente al chat service."""
            try:
                while True:
                    data = await websocket.receive_text()
                    await chat_ws.send(data)
            except WebSocketDisconnect:
                pass
            except Exception:
                pass
        
        async def forward_to_client():
            """Reenvía mensajes del chat service al cliente."""
            try:
                async for message in chat_ws:
                    await websocket.send_text(message)
            except Exception:
                pass
        
        # Ejecutar ambas tareas en paralelo
        await asyncio.gather(
            forward_to_chat(),
            forward_to_client(),
            return_exceptions=True
        )
        
    except websockets.exceptions.InvalidStatusCode as e:
        # El chat service rechazó la conexión
        error_msg = json.dumps({"type": "error", "error": f"Connection rejected: {str(e)}"})
        await websocket.send_text(error_msg)
        await websocket.close(code=4001)
    except Exception as e:
        error_msg = json.dumps({"type": "error", "error": f"Connection error: {str(e)}"})
        try:
            await websocket.send_text(error_msg)
        except:
            pass
        await websocket.close(code=1011)
    finally:
        if chat_ws:
            await chat_ws.close()
