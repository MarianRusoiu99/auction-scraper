from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

@router.post("/", response_model=SubscriptionResponse)
def create_subscription(subscription: SubscriptionCreate, db: Session = Depends(get_db)):
    # Simple validation to ensure we don't duplicate exact same subscription
    # (Optional, but good practice)
    existing = db.query(Subscription).filter(
        Subscription.email == subscription.email,
        # Note: JSON comparison in SQL is tricky, skipping for now or doing simple check
    ).all()
    
    # For now, just add it
    db_subscription = Subscription(email=subscription.email, filters=subscription.filters)
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

@router.get("/", response_model=List[SubscriptionResponse])
def get_subscriptions(email: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Subscription)
    if email:
        query = query.filter(Subscription.email == email)
    return query.all()

@router.delete("/{subscription_id}")
def delete_subscription(subscription_id: int, db: Session = Depends(get_db)):
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    db.delete(subscription)
    db.commit()
    return {"message": "Subscription deleted"}
