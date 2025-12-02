from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.routers import listings
from app.utils.logger import setup_logging
from app.tasks.scheduler import start_scheduler, scheduler

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine) # Create tables if not exist
    start_scheduler()
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(
    title="ANABI Scraper API",
    description="API for ANABI auction listings",
    version="0.1.0",
    lifespan=lifespan
)

from fastapi.staticfiles import StaticFiles
from app.routers import listings, subscriptions

app.include_router(listings.router)
app.include_router(subscriptions.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

from fastapi.responses import FileResponse

@app.get("/")
def root():
    return FileResponse("app/static/index.html")

