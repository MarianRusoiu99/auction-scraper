from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any

class ListingBase(BaseModel):
    title: str
    category: Optional[str] = None
    status: Optional[str] = None
    auction_status: Optional[str] = None
    auction_type: Optional[str] = None
    starting_price: Optional[str] = None  # Changed to string due to inconsistent formats
    current_offer: Optional[str] = None  # Changed to string due to inconsistent formats
    guarantee_amount: Optional[str] = None
    bid_count: Optional[int] = 0
    auction_start_date: Optional[datetime] = None
    auction_end_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    viewing_deadline: Optional[datetime] = None
    county: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    description: Optional[str] = None
    observations: Optional[str] = None
    images: Optional[List[str]] = []
    documents: Optional[List[Any]] = []
    detail_url: str
    number_of_images: Optional[int] = 0
    scrape_errors: Optional[str] = None
    is_active: Optional[bool] = True
    is_sold: Optional[bool] = False

class ListingCreate(ListingBase):
    pass

class ListingResponse(ListingBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ListingFilter(BaseModel):
    category: Optional[str] = None
    status: Optional[str] = None
    auction_status: Optional[str] = None
    is_active: Optional[bool] = None  # Filter by active status
    is_sold: Optional[bool] = None  # Filter by sold status
    county: Optional[str] = None
    city: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 20
