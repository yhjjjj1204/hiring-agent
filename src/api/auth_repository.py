from typing import Optional
from db.mongo import get_database
from api.auth_models import UserInDB

def get_user(username: str) -> Optional[UserInDB]:
    db = get_database()
    user_data = db.users.find_one({"username": username})
    if user_data:
        # Pydantic models don't like MongoDB's _id ObjectId by default
        if "_id" in user_data:
            user_data.pop("_id")
        return UserInDB(**user_data)
    return None

def create_user(user: UserInDB):
    db = get_database()
    db.users.insert_one(user.model_dump())

def ensure_auth_indexes():
    db = get_database()
    db.users.create_index("username", unique=True)
