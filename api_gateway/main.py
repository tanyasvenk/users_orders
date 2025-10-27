from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import jwt
from functools import lru_cache
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid
import os

app = FastAPI(title="API Gateway")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Service URLs
USERS_URL = os.getenv("USERS_URL", "http://service_users:8000")
ORDERS_URL = os.getenv("ORDERS_URL", "http://service_orders:8000")
SECRET_KEY = os.getenv("SECRET_KEY", "secret")

# Middleware for X-Request-ID
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Auth check
def verify_token(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = auth.split(" ")[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# Proxy routes
@app.get("/v1/users/{path:path}")
@app.post("/v1/users/{path:path}")
@app.put("/v1/users/{path:path}")
@app.delete("/v1/users/{path:path}")
@limiter.limit("10/minute")
async def proxy_users(request: Request, path: str):
    url = f"{USERS_URL}/v1/users/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers,
            json=await request.json() if request.method in ["POST", "PUT"] else None,
        )
    return JSONResponse(status_code=response.status_code, content=response.json())

@app.get("/v1/orders/{path:path}")
@app.post("/v1/orders/{path:path}")
@app.put("/v1/orders/{path:path}")
@app.delete("/v1/orders/{path:path}")
@limiter.limit("10/minute")
async def proxy_orders(request: Request, path: str):
    verify_token(request)
    url = f"{ORDERS_URL}/v1/orders/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers,
            json=await request.json() if request.method in ["POST", "PUT"] else None,
        )
    return JSONResponse(status_code=response.status_code, content=response.json())

@app.get("/health")
async def health():
    return {"status": "API Gateway running"}