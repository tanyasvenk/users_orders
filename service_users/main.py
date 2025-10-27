from fastapi import FastAPI, HTTPException, Depends, Header
from datetime import datetime, timedelta
import jwt
import os
from schemas import UserCreate, UserLogin
from crud import create_user, verify_credentials, get_user, list_users

app = FastAPI(title="Users Service")
SECRET_KEY = os.getenv("SECRET_KEY", "secret")

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

@app.get("/v1/users")
def api_list_users():
    return {"success": True, "data": list_users()}
