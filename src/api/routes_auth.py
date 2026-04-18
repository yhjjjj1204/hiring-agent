from fastapi import APIRouter, HTTPException, Depends, status
from api.auth_models import UserCreate, User, Token, UserInDB
from api.auth_utils import get_password_hash, verify_password, create_access_token
from api.auth_repository import get_user, create_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=User)
def register(user_in: UserCreate):
    if get_user(user_in.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user_in.password)
    user_db = UserInDB(
        username=user_in.username,
        hashed_password=hashed_password,
        role=user_in.role
    )
    create_user(user_db)
    return User(username=user_in.username, role=user_in.role)

@router.post("/login", response_model=Token)
def login(user_in: UserCreate): # Using UserCreate for convenience to get username/password
    user = get_user(user_in.username)
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(user.username)
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=User)
def get_me(token: str):
    # In a real app we'd use OAuth2PasswordBearer, but staying simple as requested
    user = get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return User(username=user.username, role=user.role)
