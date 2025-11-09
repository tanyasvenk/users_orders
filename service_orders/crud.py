from __future__ import annotations
from typing import Dict
from schemas import OrderCreate, OrderUpdate
import uuid
from datetime import datetime

_db: Dict[str, dict] = {}


def create_order(order: OrderCreate) -> dict:
    oid = str(uuid.uuid4())
    order_data = {
        "id": oid,
        "user_id": order.user_id,
        "items": order.items,
        "status": "created",
        "total": order.total,
        "created_at": datetime.utcnow().isoformat(),
    }
    _db[oid] = order_data
    return order_data


def get_order(order_id: str) -> dict | None:
    return _db.get(order_id)


def list_orders() -> list[dict]:
    return list(_db.values())


def update_order(order_id: str, data: OrderUpdate) -> dict:
    if order_id not in _db:
        raise ValueError("Order not found")
    _db[order_id]["status"] = data.status
    _db[order_id]["updated_at"] = datetime.utcnow().isoformat()
    return _db[order_id]


def delete_order(order_id: str) -> dict:
    if order_id not in _db:
        raise ValueError("Order not found")
    return _db.pop(order_id)
