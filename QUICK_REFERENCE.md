# Quick Reference: What Changed

## Schema Changes

### Price Fields (Critical Change ⚠️)
```python
# BEFORE
starting_price = Column(Float, nullable=True)
current_offer = Column(Float, nullable=True)

# AFTER  
starting_price = Column(String, nullable=True)  # No validation
current_offer = Column(String, nullable=True)   # No validation
```

### New Fields Added ✨
```python
guarantee_amount = Column(String, nullable=True)     # NEW
auction_type = Column(String, nullable=True)         # NEW
bid_count = Column(Integer, nullable=True)           # NEW
viewing_deadline = Column(DateTime, nullable=True)   # NEW
scrape_errors = Column(Text, nullable=True)          # NEW
is_active = Column(Boolean, default=True)            # NEW (indexed)
is_sold = Column(Boolean, default=False)             # NEW (indexed)
```

## Scraper Logic Changes

### Status Detection - BEFORE:
```python
if data.get('title', '').startswith('NEADJUDECAT'):
    data['status'] = 'NEADJUDECAT'
elif data.get('title', '').startswith('ADJUDECAT'):
    data['status'] = 'ADJUDECAT'
```

### Status Detection - AFTER:
```python
title_upper = data.get('title', '').upper()

# Check for keywords anywhere in title (not just start)
if 'NEADJUDECAT' in title_upper:
    data['status'] = 'NEADJUDECAT'
    data['is_sold'] = False
    data['is_active'] = True  # Unless auction closed
elif 'ADJUDECAT' in title_upper:
    data['status'] = 'ADJUDECAT'
    data['is_sold'] = True
    data['is_active'] = False

# Check if auction closed
if soup.find(string=re.compile("Licitație încheiată")):
    data['auction_status'] = 'Closed'
    data['is_active'] = False
    if data['status'] != 'ADJUDECAT':
        data['is_sold'] = False  # Closed but not sold
```

## Orchestrator Changes

### Update Logic - BEFORE (❌ NOT WORKING):
```python
if existing:
    # TODO: Implement update logic
    pass
else:
    # Create new
    listing = Listing(**detail_data)
    db.add(listing)
```

### Update Logic - AFTER (✅ WORKING):
```python
if existing:
    # Update all fields
    for key, value in detail_data.items():
        if key != 'detail_url' and hasattr(existing, key):
            setattr(existing, key, value)
    existing.scrape_errors = None  # Clear errors
    db.commit()
    updated_count += 1
else:
    # Create new
    listing = Listing(**detail_data)
    db.add(listing)
    db.commit()
    new_count += 1
```

### Scraping Control - BEFORE:
```python
# Check for latest listing in DB
latest_listing = db.query(Listing).order_by(
    Listing.auction_start_date.desc()
).first()
latest_url = latest_listing.detail_url if latest_listing else None

# Stop when we find it
if latest_url and meta['detail_url'] == latest_url:
    logger.info(f"Found latest, stopping...")
    stop_scraping = True
    break
```

### Scraping Control - AFTER:
```python
# Scrape ALL pages (no early stopping)
while True:
    listings_batch = await self.listings_scraper.scrape_page(page)
    if not listings_batch:
        break
    
    for meta in listings_batch:
        all_listings_meta.append(meta)
    
    page += 1

# NEW: Optional filtering
if self.active_unsold_only:
    is_active = detail_data.get('is_active', True)
    is_sold = detail_data.get('is_sold', False)
    if not is_active or is_sold:
        skipped_count += 1
        continue
```

## Environment Variable

Add to `.env`:
```bash
# Only scrape active, unsold listings
SCRAPE_ACTIVE_UNSOLD_ONLY=false  # Default: scrape everything
# SCRAPE_ACTIVE_UNSOLD_ONLY=true  # Enable to skip sold/closed
```

## API Changes

### Filtering - BEFORE:
```python
?category=Autovehicule
&min_price=5000
&max_price=50000
```

### Filtering - AFTER:
```python
?category=Autovehicule
&is_active=true      # Only active listings
&is_sold=false       # Only unsold listings
```

## Data Extraction Improvements

### New Labels Being Extracted:
```python
# Guarantee
"Garantie" or "Garanție" → guarantee_amount

# Auction Type  
"Tip licitatie" or "Tip licitație" → auction_type

# Bid Count
"Numar oferte" or "Număr oferte" → bid_count

# Viewing Deadline
"Termen vizionare" or "Vizionare pana la" → viewing_deadline
```

## Quick Test Commands

```bash
# 1. Apply migration
.venv/bin/alembic upgrade head

# 2. Test imports
.venv/bin/python -c "from app.models.listing import Listing; print('OK')"

# 3. Run scraper (in background)
# POST to /listings/scrape

# 4. Check active unsold listings
# GET /listings/?is_active=true&is_sold=false
```

## Key Benefits

1. ✅ **Price parsing errors eliminated** - Stored as strings
2. ✅ **Complete data capture** - All fields now extracted
3. ✅ **Accurate status tracking** - Proper is_active/is_sold flags
4. ✅ **Updates working** - Listings refresh on each scrape
5. ✅ **Error tracking** - Know what went wrong
6. ✅ **Flexible filtering** - Filter by active/sold status
7. ✅ **Environment control** - Choose what to scrape
