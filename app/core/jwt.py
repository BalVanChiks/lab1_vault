import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings

def create_access_token(sub: str, ttl_min: int = None) -> str:
    ttl = ttl_min or settings.access_token_ttl_min
    expire = datetime.now(timezone.utc) + timedelta(minutes=ttl)
    to_encode = {
        "sub": sub,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "typ": "access"
    }
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")