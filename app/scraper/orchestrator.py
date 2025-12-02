import logging
import asyncio
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.listing import Listing
from app.scraper.listings_scraper import ListingsScraper
from app.scraper.detail_scraper import DetailScraper
from app.schemas.listing import ListingCreate

logger = logging.getLogger(__name__)

class ScraperOrchestrator:
    def __init__(self):
        self.listings_scraper = ListingsScraper()
        self.detail_scraper = DetailScraper()
        # Check if we should only scrape active unsold listings
        self.active_unsold_only = os.getenv('SCRAPE_ACTIVE_UNSOLD_ONLY', 'false').lower() == 'true'

    async def run(self):
        logger.info("Starting scraping job")
        if self.active_unsold_only:
            logger.info("Mode: Active unsold listings only")
        db = SessionLocal()
        try:
            # 1. Get all detail URLs from listings pages
            # No longer using "last scraped" checking - we scrape all pages
            all_listings_meta = []
            page = 1
            
            while True:
                listings_batch = await self.listings_scraper.scrape_page(page)
                if not listings_batch:
                    break
                
                for meta in listings_batch:
                    all_listings_meta.append(meta)
                    
                page += 1
                if page > 50: # Safety break
                    break
            
            logger.info(f"Found {len(all_listings_meta)} listings to process")

            # 2. Process each listing
            new_count = 0
            updated_count = 0
            skipped_count = 0
            error_count = 0
            
            for meta in all_listings_meta:
                url = meta['detail_url']
                category = meta.get('category')
                
                try:
                    # Scrape details
                    detail_data = await self.detail_scraper.scrape_detail(url)
                    if not detail_data:
                        logger.warning(f"No data scraped for {url}")
                        error_count += 1
                        continue
                    
                    # Merge category if found in listing page but not in detail
                    if category and not detail_data.get('category'):
                        detail_data['category'] = category
                    
                    # Apply filter if active_unsold_only is enabled
                    if self.active_unsold_only:
                        is_active = detail_data.get('is_active', True)
                        is_sold = detail_data.get('is_sold', False)
                        if not is_active or is_sold:
                            logger.debug(f"Skipping {url} (active={is_active}, sold={is_sold})")
                            skipped_count += 1
                            continue
                    
                    # Check if exists
                    existing = db.query(Listing).filter(Listing.detail_url == url).first()
                    
                    if existing:
                        # Update existing listing with new data
                        logger.debug(f"Updating existing listing: {url}")
                        
                        # Update all fields that might have changed
                        for key, value in detail_data.items():
                            if key != 'detail_url' and hasattr(existing, key):
                                setattr(existing, key, value)
                        
                        # Clear any previous errors
                        existing.scrape_errors = None
                        
                        db.commit()
                        updated_count += 1
                    else:
                        # Create new listing
                        logger.debug(f"Creating new listing: {url}")
                        listing = Listing(**detail_data)
                        db.add(listing)
                        db.commit()
                        new_count += 1
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing listing {url}: {e}", exc_info=True)
                    
                    # Try to save error to database if listing exists
                    try:
                        existing = db.query(Listing).filter(Listing.detail_url == url).first()
                        if existing:
                            existing.scrape_errors = str(e)[:500]  # Limit error message length
                            db.commit()
                    except Exception as save_error:
                        logger.error(f"Could not save error to database: {save_error}")
                    
                    db.rollback()
            
            logger.info(f"Scraping finished. New: {new_count}, Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}")

        finally:
            db.close()
            await self.listings_scraper.close()
            await self.detail_scraper.close()
