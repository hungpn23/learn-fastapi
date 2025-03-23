from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
import jwt
from sqlmodel import SQLModel, select, or_

from ..dependencies import SessionDep

from ..models import User
from ..constant import JWT_SECRET

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "auth not found"}},
)

class RegisterDto(SQLModel):
    username: str
    email: str
    password: str
    confirmPassword: str

class LoginDto(SQLModel):
    email: str
    password: str

@router.post("/register")
def register(session: SessionDep, dto: RegisterDto):
    stmt = select(User).where(or_(User.username == dto.username, User.email == dto.email))
    user = session.exec(stmt).unique().one_or_none()

    if user:
        raise HTTPException(status_code=400, detail="username or email already exists")
    
    if dto.password != dto.confirmPassword:
        raise HTTPException(status_code=400, detail="passwords do not match")
    
    session.add(User(username=dto.username, email=dto.email, password=dto.password))
    session.commit()
    return

@router.post("/login")
def login(session: SessionDep, dto: LoginDto):
    stmt = select(User).where(User.email == dto.email)
    user = session.exec(stmt).unique().one_or_none()

    if not user or user.password != dto.password:
        raise HTTPException(status_code=400, detail="invalid email or password")

    payload = {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        },
        "exp": datetime.now() + timedelta(days=30)
    }
    
    access_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    return {"accessToken": access_token}

@router.post("/logout")
def logout():
    return