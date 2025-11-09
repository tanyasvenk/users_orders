from pydantic import BaseModel
from typing import List


class OrderCreate(BaseModel):
    user_id: str
    items: List[dict]
    total: float


class OrderUpdate(BaseModel):
    status: str
