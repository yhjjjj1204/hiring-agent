import hashlib

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

# Simple token is just the username for this mock
def create_access_token(username: str) -> str:
    return username

def decode_access_token(token: str) -> str:
    return token
