import httpx
import logging
import asyncio
from bs4 import BeautifulSoup
from app.config import settings
from typing import Optional

logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": settings.SCRAPER_USER_AGENT
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)

    async def fetch_page(self, url: str) -> Optional[str]:
        try:
            await asyncio.sleep(settings.SCRAPER_REQUEST_DELAY)
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None

    def parse_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    async def close(self):
        await self.client.aclose()
