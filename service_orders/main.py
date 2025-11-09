from fastapi import FastAPI, HTTPException, Header
from schemas import OrderCreate, OrderUpdate
from crud import create_order, get_order, list_orders, update_order, delete_order
import jwt
import os
from fastapi import Request
import uuid

app = FastAPI(title="Orders Service")

SECRET_KEY = os.getenv("SECRET_KEY", "secret")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    print(f"[{request_id}] {request.method} {request.url}")
    return response


def get_user_from_token(authorization: str):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return payload["sub"]


@app.post("/v1/orders")
def api_create_order(order: OrderCreate, authorization: str = Header(...)):
    user_id = get_user_from_token(authorization)
    order.user_id = user_id
    return {"success": True, "data": create_order(order)}


@app.get("/v1/orders/{order_id}")
def api_get_order(order_id: str, authorization: str = Header(...)):
    user_id = get_user_from_token(authorization)
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"success": True, "data": order}


@app.delete("/v1/orders/{order_id}")
def api_delete_order(order_id: str, authorization: str = Header(...)):
    user_id = get_user_from_token(authorization)
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"success": True, "data": delete_order(order_id)}


@app.get("/v1/orders")
def api_list_orders():
    return {"success": True, "data": list_orders()}


@app.put("/v1/orders/{order_id}")
def api_update_order(order_id: str, data: OrderUpdate):
    try:
        return {"success": True, "data": update_order(order_id, data)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
