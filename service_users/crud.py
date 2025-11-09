from __future__ import annotations
from typing import Dict
from schemas import UserCreate
import uuid
import hashlib
from datetime import datetime

_db: Dict[str, dict] = {}


def create_user(user: UserCreate) -> dict:
    if any(u['email'] == user.email for u in _db.values()):
        raise ValueError("Email already registered")
    uid = str(uuid.uuid4())
    password_hash = hashlib.sha256(user.password.encode()).hexdigest()
    user_data = {
        "id": uid,
        "email": user.email,
        "password_hash": password_hash,
        "name": user.name,
        "roles": ["user"],
        "created_at": datetime.utcnow().isoformat(),
    }
    _db[uid] = user_data
    return {"id": uid}


def verify_credentials(email: str, password: str) -> str | None:
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    for u in _db.values():
        if u['email'] == email and u['password_hash'] == password_hash:
            return u['id']
    return None


def get_user(user_id: str) -> dict | None:
    return _db.get(user_id)


def list_users() -> list[dict]:
    return list(_db.values())
