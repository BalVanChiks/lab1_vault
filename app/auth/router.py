from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.passwords import hash_password, verify_password, validate_policy, WeakPasswordError
from app.core.jwt import create_access_token
from app.core.deps import get_current_user
from app.auth.schemas import Credentials, TokenResponse, UserResponse
from app.audit.service import write_event

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
def register(creds: Credentials, request: Request, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == creds.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    try:
        validate_policy(creds.password, user_inputs=[creds.email])
    except WeakPasswordError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    user = User(email=creds.email, hashed_password=hash_password(creds.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    
    write_event(db, "user.created", actor_id=user.id, ip=request.client.host, user_agent=request.headers.get("user-agent"))
    
    token = create_access_token(sub=user.email)
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
def login(creds: Credentials, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    
    if not user or not verify_password(creds.password, user.hashed_password):
        write_event(db, "user.login.failure", metadata={"email": creds.email}, ip=request.client.host, user_agent=request.headers.get("user-agent"))
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")
        
    write_event(db, "user.login.success", actor_id=user.id, ip=request.client.host, user_agent=request.headers.get("user-agent"))
    token = create_access_token(sub=user.email)
    return TokenResponse(access_token=token)

@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return UserResponse(id=user.id, email=user.email, is_admin=user.is_admin)