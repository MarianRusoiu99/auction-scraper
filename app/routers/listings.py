from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.listing import Listing
from app.schemas.listing import ListingResponse, ListingFilter
from app.scraper.orchestrator import ScraperOrchestrator

router = APIRouter(prefix="/listings", tags=["listings"])

@router.get("/", response_model=List[ListingResponse])
def get_listings(
    filter: ListingFilter = Depends(),
    db: Session = Depends(get_db)
):
    query = db.query(Listing)
    
    if filter.category:
        query = query.filter(Listing.category == filter.category)
    if filter.status:
        query = query.filter(Listing.status == filter.status)
    if filter.auction_status:
        query = query.filter(Listing.auction_status == filter.auction_status)
    if filter.is_active is not None:
        query = query.filter(Listing.is_active == filter.is_active)
    if filter.is_sold is not None:
        query = query.filter(Listing.is_sold == filter.is_sold)
    if filter.county:
        query = query.filter(Listing.county == filter.county)
    if filter.city:
        query = query.filter(Listing.city == filter.city)
    if filter.search:
        search_terms = filter.search.strip().split()
        for term in search_terms:
            term_pattern = f"%{term}%"
            query = query.filter(
                (Listing.title.ilike(term_pattern)) | 
                (Listing.description.ilike(term_pattern)) |
                (Listing.category.ilike(term_pattern)) |
                (Listing.county.ilike(term_pattern)) |
                (Listing.city.ilike(term_pattern))
            )
        
    # Pagination
    skip = (filter.page - 1) * filter.page_size
    listings = query.offset(skip).limit(filter.page_size).all()
    return listings

@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

@router.post("/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    orchestrator = ScraperOrchestrator()
    background_tasks.add_task(orchestrator.run)
    return {"message": "Scraping started in background"}
