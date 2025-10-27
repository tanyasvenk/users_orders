from fastapi import FastAPI, HTTPException
from schemas import OrderCreate, OrderUpdate
from crud import create_order, get_order, list_orders, update_order, delete_order

app = FastAPI(title="Orders Service")

@app.post("/v1/orders")
def api_create_order(order: OrderCreate):
    return {"success": True, "data": create_order(order)}

@app.get("/v1/orders/{order_id}")
def api_get_order(order_id: str):
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"success": True, "data": order}

@app.get("/v1/orders")
def api_list_orders():
    return {"success": True, "data": list_orders()}

@app.put("/v1/orders/{order_id}")
def api_update_order(order_id: str, data: OrderUpdate):
    try:
        return {"success": True, "data": update_order(order_id, data)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/v1/orders/{order_id}")
def api_delete_order(order_id: str):
    try:
        return {"success": True, "data": delete_order(order_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
