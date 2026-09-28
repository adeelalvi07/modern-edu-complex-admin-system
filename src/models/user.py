"""
User and Role Domain Models.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Role:
    id: Optional[int]
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class User:
    id: Optional[int]
    username: str
    password_hash: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    role_id: int
    role_name: Optional[str] = None
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
