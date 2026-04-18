from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    username: str
    role: str  # 'candidate' or 'recruiter'

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "candidate"

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
