import os
from dotenv import load_dotenv
import jwt
from fastapi import FastAPI, Request, HTTPException
from typing import Callable

from .src.constant import PUBLIC_ROUTES
from .src.routes import auth, set

app = FastAPI()
app.include_router(auth.router)
app.include_router(set.router)

load_dotenv()

@app.middleware("http")
async def verify_auth_header(request: Request, call_next: Callable):
    print(f"==>> request.url.path: {request.url.path}")
    if request.url.path in PUBLIC_ROUTES:
        return await call_next(request)
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401)
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        request.state.user = payload["user"]
        request.state.userId = payload["user"]["id"]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401)
    
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
