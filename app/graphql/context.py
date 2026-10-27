from app.db.session import SessionLocal
from app.core.jwt import decode_token
from app.models.user import User


async def get_context_value(request, data):
    db = SessionLocal()
    user = None
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
            email = payload.get("sub")
            if email:
                user = db.query(User).filter(User.email == email).first()
        except Exception:
            # Токен невалидный или истёк, пользователь остаётся None
            pass
            
    return {"request": request, "db": db, "user": user}