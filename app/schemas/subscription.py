from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class SubscriptionBase(BaseModel):
    email: EmailStr
    filters: Dict[str, Any]

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionResponse(SubscriptionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
