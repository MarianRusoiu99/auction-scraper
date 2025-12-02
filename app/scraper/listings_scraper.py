import logging
from typing import List, Dict, Any
from urllib.parse import urljoin
from app.scraper.base import BaseScraper

logger = logging.getLogger(__name__)

class ListingsScraper(BaseScraper):
    BASE_URL = "https://anabi.just.ro/licitatiionline/ads"

    async def get_total_pages(self) -> int:
        # Logic to determine total pages, or we can just iterate until no more results
        # For now, let's assume we iterate until we find no listings or a "next" button is disabled
        # But to be safe, we can inspect the pagination control if it exists
        html = await self.fetch_page(self.BASE_URL)
        if not html:
            return 1
        soup = self.parse_html(html)
        # TODO: Implement pagination logic based on actual HTML structure
        # For now, we will just return a safe number or handle it in the loop
        return 100 # Placeholder, better to loop until empty

    async def scrape_page(self, page: int) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}?page={page}"
        logger.info(f"Scraping listings page: {url}")
        html = await self.fetch_page(url)
        if not html:
            return []

        soup = self.parse_html(html)
        listings = []
        
        # Find all listing boxes
        for box in soup.find_all('div', class_='licitatie-box'):
            # Extract URL
            title_link = box.find('a', class_='licitatie-box-title')
            if not title_link or not title_link.get('href'):
                continue
                
            full_url = title_link['href']
            if not full_url.startswith('http'):
                full_url = urljoin("https://anabi.just.ro", full_url)
            
            # Extract Category
            category = None
            cat_div = box.find('div', class_='licitatie-box-category')
            if cat_div:
                cat_link = cat_div.find('a')
                if cat_link:
                    category = cat_link.get_text(strip=True)
            
            listings.append({
                "detail_url": full_url,
                "category": category
            })
        
        return listings
