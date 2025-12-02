from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    category = Column(String, index=True)
    status = Column(String, index=True)  # e.g., NEADJUDECAT, ADJUDECAT, Active
    auction_status = Column(String, index=True)  # e.g., Active, Closed, Not Started
    auction_type = Column(String, nullable=True)  # Type of auction
    
    # Price fields as strings - inconsistent formatting on website
    starting_price = Column(String, nullable=True)
    current_offer = Column(String, nullable=True)
    guarantee_amount = Column(String, nullable=True)  # Guarantee/deposit amount
    
    bid_count = Column(Integer, nullable=True, default=0)  # Number of bids
    
    auction_start_date = Column(DateTime, nullable=True)
    auction_end_date = Column(DateTime, nullable=True)
    registration_deadline = Column(DateTime, nullable=True)
    viewing_deadline = Column(DateTime, nullable=True)  # Deadline for viewing the item
    
    county = Column(String, nullable=True, index=True)
    city = Column(String, nullable=True, index=True)
    address = Column(Text, nullable=True)
    
    contact_person = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    
    description = Column(Text, nullable=True)
    observations = Column(Text, nullable=True)
    
    images = Column(JSON, nullable=True)  # List of image URLs
    documents = Column(JSON, nullable=True)  # List of document URLs
    
    detail_url = Column(String, unique=True, index=True)
    number_of_images = Column(Integer, default=0)
    
    # Tracking fields
    scrape_errors = Column(Text, nullable=True)  # Track any scraping errors
    is_active = Column(Boolean, default=True, index=True)  # Is listing active?
    is_sold = Column(Boolean, default=False, index=True)  # Was item sold?
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
