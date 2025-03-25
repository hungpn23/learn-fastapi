import os
import random
import urllib
import jwt
import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel, select, or_

from ..dependencies import SessionDep

from ..models import User

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
def register(dto: RegisterDto, session: SessionDep):
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
def login(dto: LoginDto, session: SessionDep):
    stmt = select(User).where(User.email == dto.email)
    user = session.exec(stmt).unique().one_or_none()

    if not user or user.password != dto.password:
        raise HTTPException(status_code=400, detail="invalid email or password")

    return {"accessToken": create_access_token(user)}

@router.post("/logout")
def logout():
    return


@router.get("/google")
def google_redirect():
    options = {
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "response_type": "code",
        "scope": "profile email",
        "prompt": "select_account",
    }
    
    query_string = urllib.parse.urlencode(options)
    
    return RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + query_string)

@router.get("/google/callback")
async def google_callback(code: str, session: SessionDep):
    search_params = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "grant_type": "authorization_code",
    }
    query_string = urllib.parse.urlencode(search_params)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            content=query_string,
        )
        print(f"==>> response: {response}")
        data = response.json()
    
    decoded = jwt.decode(data["id_token"], options={"verify_signature": False})
    given_name = decoded["given_name"]
    family_name = decoded["family_name"]
    email = decoded["email"]
    email_verified = decoded["email_verified"]
    picture = decoded["picture"]
    
    stmt = select(User).where(User.email == email)
    found = session.exec(stmt).one_or_none()
    
    if found:
        return_search_params = urllib.parse.urlencode({"accessToken": create_access_token(found)})
        return RedirectResponse(f"http://localhost:3000/login?{return_search_params}")
    
    username = get_unique_username(given_name, family_name)
    user = User(
        username=username,
        email=email,
        is_email_verified=email_verified,
        avatar=picture,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return_search_params = urllib.parse.urlencode({"accessToken": create_access_token(user)})
    return RedirectResponse(f"http://localhost:3000/login?{return_search_params}")

def create_access_token(user: User):
    payload = {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        },
        "exp": datetime.now() + timedelta(days=30)
    }
    
    access_token = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")
    return access_token

def get_unique_username(given_name: str, family_name: str):
    base_username = f"{given_name.lower()}_{family_name.lower()}"
    return f"{base_username}_{random.randint(1000, 9999)}"