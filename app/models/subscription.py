from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    filters = Column(JSON)  # Stores the filter criteria
    created_at = Column(DateTime(timezone=True), server_default=func.now())
