# ANABI Scraper Schema & Logic Improvements - Summary

## Overview
This document summarizes all changes made to address comprehensive data extraction, schema improvements, and scraper logic enhancements.

## Changes Made

### 1. Database Schema Changes (`app/models/listing.py`)

#### Price Fields - Changed from Float to String
- **Reason**: Inconsistent price formats on the website
- **Fields Changed**:
  - `starting_price`: Float → String
  - `current_offer`: Float → String
  
#### New Fields Added:
1. **`guarantee_amount`** (String): Captures the guarantee/deposit amount required
2. **`auction_type`** (String): Type of auction
3. **`bid_count`** (Integer): Number of bids/offers received
4. **`viewing_deadline`** (DateTime): Deadline for viewing the item
5. **`scrape_errors`** (Text): Tracks any scraping errors for validation
6. **`is_active`** (Boolean, indexed): Whether listing is currently active
7. **`is_sold`** (Boolean, indexed): Whether item was sold

### 2. Scraper Improvements (`app/scraper/detail_scraper.py`)

#### Price Handling:
- Prices now stored as raw strings (no parsing/validation)
- Preserves original format from website

#### New Data Extraction:
- **Guarantee Amount**: Extracts from "Garantie" or "Garanție" labels
- **Auction Type**: Extracts from "Tip licitatie" or "Tip licitație" labels  
- **Bid Count**: Extracts from "Numar oferte" or "Număr oferte" labels
- **Viewing Deadline**: Extracts from "Termen vizionare" or similar labels

#### Enhanced Status Detection:
- **Comprehensive status logic**: 
  - Checks title for NEADJUDECAT/ADJUDECAT keywords (case-insensitive)
  - Properly sets `is_active` and `is_sold` flags
  - Handles "Licitatie incheiata" / "Licitație încheiată" text
  - Detects "Not Started" auctions
  
- **Status Rules**:
  - ADJUDECAT → `is_sold=True`, `is_active=False`
  - NEADJUDECAT → `is_sold=False`, `is_active=True` (unless auction ended)
  - Closed auction without ADJUDECAT → `is_sold=False`, `is_active=False`
  - Not started → `is_active=False`

### 3. Orchestrator Logic (`app/scraper/orchestrator.py`)

#### Removed "Last Scraped" Checking:
- **Before**: Stopped scraping when encountering the latest existing listing
- **After**: Scrapes all pages regardless of existing data
- **Benefit**: Ensures listings are updated with latest information

#### Implemented Update Logic:
- **Before**: Only inserted new listings, never updated existing ones
- **After**: Properly updates all fields for existing listings
- **Process**:
  1. Scrape detail data
  2. Check if listing exists by `detail_url`
  3. If exists: Update all fields with new data
  4. If new: Create new listing
  
#### Error Tracking:
- Captures and logs all errors during scraping
- Saves error messages to `scrape_errors` field in database
- Continues processing other listings on error
- Reports counts: New, Updated, Skipped, Errors

#### Active/Unsold Filter:
- New environment variable: `SCRAPE_ACTIVE_UNSOLD_ONLY`
- When enabled (`true`): Only scrapes/saves active listings that were not sold
- When disabled (`false`): Scrapes all listings
- Filter applied after data extraction (so status is accurate)

### 4. Environment Configuration (`.env.example`)

New variable added:
```bash
# Scraper Filter - Only scrape active listings that were not sold
# Set to 'true' to skip closed/sold listings, 'false' to scrape all
SCRAPE_ACTIVE_UNSOLD_ONLY=false
```

### 5. Database Migration
- **File**: `alembic/versions/f45a2841c8ac_update_schema_for_comprehensive_listing_.py`
- **Migration**: Converts Float price columns to String
- **Adds**: All new columns (guarantee_amount, auction_type, bid_count, etc.)
- **Indexes**: Creates indexes on is_active and is_sold for efficient filtering
- **SQLite Compatible**: Handles SQLite limitations with column type changes

### 6. API Schema Updates (`app/schemas/listing.py`)

#### Pydantic Models Updated:
- Changed price fields from `float` to `str` in all models
- Added all new fields to `ListingBase`
- Updated `ListingFilter`:
  - Removed: `min_price`, `max_price` (prices are now strings)
  - Added: `is_active`, `is_sold` boolean filters

### 7. API Endpoint Updates (`app/routers/listings.py`)

#### Filter Logic:
- Removed price-based filtering (min_price/max_price)
- Added `is_active` and `is_sold` boolean filters
- Supports filtering for:
  - Active listings: `?is_active=true`
  - Unsold listings: `?is_sold=false`
  - Active AND unsold: `?is_active=true&is_sold=false`

## Critical Issues Addressed

### ✅ Price parsing - FIXED
- Prices now stored as strings without validation
- No more parsing errors from inconsistent formats

### ✅ Guarantee amount - FIXED
- New field `guarantee_amount` captures this data
- Extracted from appropriate labels

### ✅ Status logic - IMPROVED
- Comprehensive detection of NEADJUDECAT/ADJUDECAT
- Proper handling of closed auctions
- Accurate `is_active` and `is_sold` flags

### ✅ Update logic - IMPLEMENTED
- Listings now properly update after first scrape
- All fields refreshed with latest data
- No more stale data

### ✅ Missing audit fields - ADDED
- `viewing_deadline`: Deadline for viewing items
- `auction_type`: Type of auction
- `bid_count`: Number of bids received
- `scrape_errors`: Validation and error tracking

## Testing the Changes

### 1. Run the migration:
```bash
.venv/bin/alembic upgrade head
```

### 2. Test the scraper:
```bash
# Run a full scrape (all listings)
# Make sure SCRAPE_ACTIVE_UNSOLD_ONLY=false in .env

# Or run with filter enabled
# Set SCRAPE_ACTIVE_UNSOLD_ONLY=true in .env
```

### 3. Test API filtering:
```bash
# Get all active listings
curl "http://localhost:8000/listings/?is_active=true"

# Get unsold listings
curl "http://localhost:8000/listings/?is_sold=false"

# Get active AND unsold
curl "http://localhost:8000/listings/?is_active=true&is_sold=false"
```

## Migration Path

### For Existing Database:
1. Backup database: `cp anabi.db anabi.db.backup`
2. Run migration: `.venv/bin/alembic upgrade head`
3. Existing prices will be converted to strings
4. New boolean fields will default to `is_active=True`, `is_sold=False`
5. Re-run scraper to populate new fields with accurate data

### For Production:
- Review migration file before running
- Test on staging/dev environment first
- Consider running a full re-scrape after migration to ensure data accuracy

## Next Steps (Optional Improvements)

1. **Add retry logic** for failed scrapes
2. **Implement scheduling** for automatic re-scraping of active listings
3. **Add email notifications** when listing status changes
4. **Create admin dashboard** to view scrape errors and statistics
5. **Add data validation reports** to identify missing/incorrect data

## File Changes Summary

Modified:
- `app/models/listing.py` - Schema changes
- `app/scraper/detail_scraper.py` - Enhanced extraction
- `app/scraper/orchestrator.py` - Update logic & filtering
- `app/schemas/listing.py` - Pydantic models
- `app/routers/listings.py` - API filtering
- `.env.example` - New environment variable

Created:
- `alembic/versions/f45a2841c8ac_update_schema_for_comprehensive_listing_.py` - Migration

## Environment Variables

```bash
# Add to your .env file:
SCRAPE_ACTIVE_UNSOLD_ONLY=false  # or true to filter
```
