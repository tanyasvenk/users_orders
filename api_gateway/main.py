from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid
import os

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)

# Service URLs
USERS_URL = os.getenv("USERS_URL", "http://service_users:8000")
ORDERS_URL = os.getenv("ORDERS_URL", "http://service_orders:8000")
SECRET_KEY = os.getenv("SECRET_KEY", "secret")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


def verify_token(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = auth.split(" ")[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def clean_headers(headers):
    h = dict(headers)
    h.pop("host", None)
    h.pop("content-length", None)
    return h


async def safe_request(method: str, url: str, headers=None, data=None):
    headers = headers or {}
    timeout = httpx.Timeout(5.0, connect=2.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            response = await client.request(method, url, headers=headers, json=data)
            try:
                content = response.json()
            except Exception:
                content = {"raw": response.text}
            return response.status_code, content
        except httpx.RequestError as e:
            return 502, {"detail": f"Service unreachable: {str(e)}"}


@app.api_route("/v1/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@limiter.limit("10/minute")
async def proxy_users(request: Request, path: str = ""):
    url = f"{USERS_URL}/v1/users" + (f"/{path}" if path else "")
    print(f"[Users Proxy] URL: {url}, Method: {request.method}")
    data = None
    if request.method in ["POST", "PUT"]:
        try:
            data = await request.json()
        except Exception:
            data = None
    status, content = await safe_request(request.method, url, headers=clean_headers(request.headers), data=data)
    return JSONResponse(status_code=status, content=content)


@app.api_route("/v1/orders/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@limiter.limit("10/minute")
async def proxy_orders(request: Request, path: str = ""):
    verify_token(request)
    url = f"{ORDERS_URL}/v1/orders" + (f"/{path}" if path else "")
    print(f"[Orders Proxy] URL: {url}, Method: {request.method}")
    data = None
    if request.method in ["POST", "PUT"]:
        try:
            data = await request.json()
        except Exception:
            data = None
    status, content = await safe_request(request.method, url, headers=clean_headers(request.headers), data=data)
    return JSONResponse(status_code=status, content=content)


@app.get("/health")
async def health():
    return {"status": "API Gateway running"}
