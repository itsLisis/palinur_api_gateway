from pydantic import BaseModel, EmailStr, field_validator
from datetime import date

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    complete_profile: bool
    user_id: int
    next_endpoint: str

class ProfileComplete(BaseModel):
    username: str
    introduction: str
    birthday: date
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

