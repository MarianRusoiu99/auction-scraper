from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
from app.scraper.orchestrator import ScraperOrchestrator
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def run_daily_scrape():
    logger.info("Running daily scheduled scrape")
    orchestrator = ScraperOrchestrator()
    await orchestrator.run()

def start_scheduler():
    trigger = CronTrigger(hour=settings.DAILY_SCRAPE_HOUR)
    scheduler.add_job(run_daily_scrape, trigger)
    scheduler.start()
    logger.info(f"Scheduler started. Daily scrape at {settings.DAILY_SCRAPE_HOUR}:00")
