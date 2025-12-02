# ANABI Auction Scraper

A FastAPI-based web scraper for ANABI (Romanian National Agency for the Management of Seized Assets) auction listings.

## Features

- Scrapes auction listings from [ANABI website](https://anabi.just.ro/licitatiionline/ads)
- Stores data in SQLite (default) or PostgreSQL
- REST API for filtering, searching, and retrieving listings
- Incremental updates (adds only new listings)
- Daily scheduled scraping
- Docker-ready structure

## Setup

1. **Install Dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   # OR using poetry
   poetry install
   ```

2. **Configuration**
   Copy `.env.example` to `.env` and adjust settings if needed:
   ```bash
   cp .env.example .env
   ```

3. **Database Setup**
   Initialize the database with migrations:
   ```bash
   alembic upgrade head
   ```

## Running the Application

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive documentation: `http://localhost:8000/docs`.

## Usage

### Trigger Scraper Manually
```bash
curl -X POST http://localhost:8000/listings/scrape
```

### API Endpoints
- `GET /listings`: List all auctions (supports filtering by status, category, price, etc.)
- `GET /listings/{id}`: Get details of a specific auction
- `GET /listings/stats`: Get auction statistics

## Development

- **Migrations**: `alembic revision --autogenerate -m "message"`
- **Tests**: `pytest`
