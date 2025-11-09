import uuid

from fastapi import FastAPI, HTTPException, Request, Header
from datetime import datetime, timedelta
import jwt
import os
from schemas import UserCreate, UserLogin, UserUpdate
from crud import create_user, verify_credentials, get_user, list_users
import uuid

app = FastAPI(title="Users Service")
SECRET_KEY = os.getenv("SECRET_KEY", "secret")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    print(f"[{request_id}] {request.method} {request.url}")
    return response


@app.post("/v1/users/register")
def register(user: UserCreate):
    try:
        uid = create_user(user)["id"]
        return {"success": True, "data": {"id": uid}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/users/login")
def login(data: UserLogin):
    user_id = verify_credentials(data.email, data.password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode(
        {"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=2)},
        SECRET_KEY,
        algorithm="HS256"
    )
    return {"success": True, "data": {"token": token}}


@app.get("/v1/users/me")
def get_profile(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = get_user(payload["sub"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "data": user}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.put("/v1/users/me")
def update_profile(data: UserUpdate, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = get_user(payload["sub"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.update({k: v for k, v in data.model_dump().items() if v is not None})
        return {"success": True, "data": user}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/v1/users")
def api_list_users():
    return {"success": True, "data": list_users()}
