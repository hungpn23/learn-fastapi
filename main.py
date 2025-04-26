import os
from dotenv import load_dotenv
import jwt
from fastapi import FastAPI, Request, HTTPException
from typing import Callable


from .src.constant import PUBLIC_ROUTES, Role
from .src.routes import auth, set, user, admin

app = FastAPI()
app.include_router(auth.router)
app.include_router(set.router)
app.include_router(user.router)
app.include_router(admin.router)

load_dotenv()

@app.middleware("http")
async def verify_auth_header(request: Request, call_next: Callable):
    if request.url.path in PUBLIC_ROUTES:
        return await call_next(request)
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401)
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        print(f"==>> payload: {payload}")
        request.state.user = payload["user"]
        request.state.userId = payload["user"]["id"]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401)
    
    if request.url.path.startswith('/admin') and request.state.user["role"] != Role.ADMIN:
        raise HTTPException(status_code=403)
    else:
        return await call_next(request)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
