from pydantic import BaseModel, EmailStr, field_validator
from datetime import date, datetime
from typing import Optional, List


# ============ AUTH SCHEMAS ============

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    turnstile_token: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    turnstile_token: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    complete_profile: bool
    user_id: int
    next_endpoint: str


# ============ PROFILE SCHEMAS ============

class ProfileComplete(BaseModel):
    username: str
    introduction: str
    birthday: date
    gender_id: int
    sexual_orientation_id: int
    interest_ids: list[int] = []
    image_urls: list[str] = []
    
    @field_validator('birthday')
    def validate_age(cls, birthday):
        today = date.today()
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        
        if age < 18:
            raise ValueError('Must be at least 18 years old')
        if age > 120:
            raise ValueError('Invalid birth date')
        
        return birthday
    
    @field_validator('image_urls')
    def validate_images(cls, image_urls):
        if len(image_urls) > 6:
            raise ValueError('Maximum 6 images allowed')
        return image_urls


class ProfileCompleteResponse(BaseModel):
    message: str
    profile_id: int
    access_token: str
    token_type: str
    complete_profile: bool
    user_id: int
    next_endpoint: str


# ============ CHAT SCHEMAS ============

class MessageResponse(BaseModel):
    """Schema de respuesta para un mensaje."""
    id: int
    chat_id: int
    sender_id: int
    content: str
    created_at: datetime
    is_read: bool


class MessageListResponse(BaseModel):
    """Schema para lista de mensajes paginada."""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ChatPreviewResponse(BaseModel):
    """Schema para preview de un chat en lista."""
    chat_id: int
    relationship_id: int
    partner_id: int
    last_message: Optional[str]
    last_message_at: Optional[datetime]
    unread_count: int


class ChatListResponse(BaseModel):
    """Schema para lista de chats."""
    chats: List[ChatPreviewResponse]
    total: int


class ChatResponse(BaseModel):
    """Schema de respuesta para un chat."""
    id: int
    relationship_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


# ============ MATCHING SCHEMAS ============

class RelationshipCheckResponse(BaseModel):
    """Schema para verificar si existe un match."""
    exists: bool
    relationship_id: Optional[int] = None
    user1_id: Optional[int] = None
    user2_id: Optional[int] = None
    state: Optional[str] = None
    creation_date: Optional[int] = None


class ActiveRelationshipResponse(BaseModel):
    """Schema para relación activa de un usuario."""
    has_active_match: bool
    relationship_id: Optional[int] = None
    user1_id: Optional[int] = None
    user2_id: Optional[int] = None
    partner_id: Optional[int] = None
    state: Optional[str] = None
    creation_date: Optional[int] = None

