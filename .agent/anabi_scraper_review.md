# ANABI Scraper - Comprehensive Review & Improvement Plan

**Date**: 2025-12-01  
**Status**: Draft  
**Priority**: High

---

## Executive Summary

This document provides a comprehensive review of the ANABI auction scraper, identifying current issues, missing features, and proposing a systematic improvement plan.

---

## Current Implementation Analysis

### ✅ Working Components

1. **Basic Structure**
   - Multi-stage scraping (listings → details)
   - Async/await pattern for performance
   - Database persistence with SQLAlchemy
   - Incremental scraping logic

2. **Data Extraction**
   - Title extraction
   - Image and document collection
   - Basic location parsing
   - Category from listings page

### ⚠️ Issues Identified

#### 1. **Price Handling** (CRITICAL)

**Current Issues**:
- `starting_price` extraction from "Pret" label ✓ (works)
- `current_offer` from "Oferta actuala" in sidebar ✓ (works)
- **MISSING**: Guarantee amount ("Garanție de participare")
- **MISSING**: Price currency (always assumes LEI)
- **ISSUE**: Price may be in different formats (with/without tax)

**Example from website**:
```html
<h3><span class="left">Oferta actuala:</span> <span class="right">63,826.50 lei</span></h3>
<p><span class="ad-info-name">Pret</span> <span class="ad-info-value">63,826.50 lei</span></p>
<p><span class="ad-info-name">Garanție de participare</span> <span class="ad-info-value">6382.65 lei</span></p>
```

**Recommendation**: Add `guarantee_amount` field to model

---

#### 2. **Auction Status & Dates** (HIGH PRIORITY)

**Current Issues**:
- ✓ Correctly extracts `registration_deadline` from `data-expire-date`
- ✓ Extracts `auction_end_date` from "Expira la" label
- ✓ Parses countdown timer as fallback
- **ISSUE**: Status logic is incomplete
- **MISSING**: Distinction between "not started", "active", "closed", "sold"

**Status Sources on Website**:
1. Title prefix: `NEADJUDECAT` / `ADJUDECAT`
2. Countdown div classes: `countdown notstarted` vs `countdown`
3. Text: "Licitatie incheiata"
4. Alert: "Trebuie sa va autentificati" (auction not closed)

**Current Logic**:
```python
if data.get('title', '').startswith('NEADJUDECAT'):
    data['status'] = 'NEADJUDECAT'
elif data.get('title', '').startswith('ADJUDECAT'):
    data['status'] = 'ADJUDECAT'
else:
    data['status'] = 'Active'
```

**Issues**:
- Doesn't handle "not started" properly
- Doesn't detect if auction ended but item not sold
- `auction_status` and `status` fields overlap

---

#### 3. **Data Completeness** (MEDIUM PRIORITY)

**Missing Fields**:
- Guarantee amount (critical for bidders)
- Number of bids/offers
- Bid history
- Viewing deadline (different from auction end)
- Auction type (first, second, third licitatie)

**Improvement Needed**:
- Location parsing sometimes incomplete (only county, missing city)
- Contact info extraction could be more robust

---

#### 4. **Error Handling** (MEDIUM PRIORITY)

**Current Issues**:
- No validation of scraped data
- No retry logic for failed requests
- No detection of malformed pages
- Continue on error but don't log which fields failed

---

#### 5. **Performance** (LOW PRIORITY)

**Current**:
- Sequential scraping of detail pages
- No caching
- No rate limiting

**Recommendation**:
- Add configurable rate limiting
- Consider parallel scraping with semaphore
- Cache unchanged listings

---

## Data Model Review

### Current Schema (`app/models/listing.py`)

```python
class Listing(Base):
    # Identifiers
    id, title, detail_url ✓
    
    # Classification
    category, status, auction_status ✓
    
    # Pricing
    starting_price, current_offer ✓
    # MISSING: guarantee_amount, currency
    
    # Dates
    auction_start_date, auction_end_date, registration_deadline ✓
    # MISSING: viewing_deadline
    
    # Location
    county, city, address ✓
    
    # Contact
    contact_person, contact_phone, contact_email ✓
    
    # Content
    description, observations ✓
    images, documents, number_of_images ✓
    
    # Meta
    created_at, updated_at ✓
    # MISSING: scraped_at, auction_type, bid_count
```

### Recommended Schema Changes

```python
# Add fields:
guarantee_amount = Column(Float, nullable=True)
currency = Column(String, default='LEI')
viewing_deadline = Column(DateTime, nullable=True)
auction_type = Column(String, nullable=True)  # "Prima licitatie", "A doua licitatie"
bid_count = Column(Integer, default=0)
last_scraped_at = Column(DateTime, nullable=True)
scrape_error = Column(Text, nullable=True)  # Track scraping issues

# Rename for clarity:
auction_status -> bidding_status  # "Not Started", "Active", "Closed"
status -> sale_status  # "NEADJUDECAT", "ADJUDECAT", "Active"
```

---

## Orchestrator Review

### Current Issues

1. **Incremental Scraping Logic**
   - Uses `auction_start_date` for finding latest listing
   - **ISSUE**: If auction_start_date is None, query fails
   - **ISSUE**: Doesn't handle listings with same start date
   - Stops on first match, but listings may be reordered

2. **Update Logic**
   - Currently commented out (line 59: `pass`)
   - **CRITICAL**: Existing listings never update
   - No detection of price changes, status changes, new bids

3. **Error Recovery**
   - Rollback on error but continues
   - No retry for failed listings
   - No tracking of which listings failed

---

## Test Coverage

**Current**: None

**Recommendation**: Create test suite with:
- Unit tests for each parsing function
- Integration tests with saved HTML samples
- Mock server for full scraper tests

---

## Improvement Plan

### Phase 1: Critical Fixes (Week 1)

1. **Database Schema Updates**
   ```sql
   ALTER TABLE listings ADD COLUMN guarantee_amount FLOAT;
   ALTER TABLE listings ADD COLUMN viewing_deadline DATETIME;
   ALTER TABLE listings ADD COLUMN auction_type VARCHAR(50);
   ALTER TABLE listings ADD COLUMN bid_count INTEGER DEFAULT 0;
   ALTER TABLE listings ADD COLUMN last_scraped_at DATETIME;
   ```

2. **Fix Guarantee Extraction**
   - Add extraction of "Garanție de participare"
   - Store in new `guarantee_amount` field

3. **Implement Update Logic**
   - Compare existing data with new scrape
   - Update fields that changed
   - Track last_scraped_at

4. **Improve Status Detection**
   - Implement comprehensive status logic
   - Handle all edge cases
   - Add logging for status changes

### Phase 2: Enhancements (Week 2)

1. **Add Missing Data Fields**
   - Viewing deadline extraction
   - Auction type detection
   - Bid count/history

2. **Error Handling**
   - Validate all extracted data
   - Add retry logic
   - Store scrape errors in database

3. **Data Quality**
   - Add validation for prices (must be > 0)
   - Validate date ordering
   - Check for required fields

### Phase 3: Optimization (Week 3)

1. **Performance**
   - Add rate limiting
   - Implement parallel scraping
   - Cache unchanged listings

2. **Monitoring**
   - Add metrics collection
   - Track scrape success rate
   - Alert on failures

3. **Testing**
   - Create test suite
   - Add CI/CD pipeline
   - Performance benchmarks

---

## Specific Code Changes Needed

### 1. DetailScraper Improvements

```python
# Add guarantee extraction
guarantee_str = extract_by_label("Garanție de participare")
if guarantee_str:
    data['guarantee_amount'] = self._parse_price(guarantee_str)

# Add auction type detection
if 'a doua licitatie' in text_content.lower():
    data['auction_type'] = 'A doua licitatie'
elif 'a treia licitatie' in text_content.lower():
    data['auction_type'] = 'A treia licitatie'
elif 'prima licitatie' in text_content.lower():
    data['auction_type'] = 'Prima licitatie'

# Improve status logic
def _determine_status(self, soup, data):
    # Check title
    title = data.get('title', '')
    if title.startswith('ADJUDECAT'):
        return 'ADJUDECAT', 'Closed'
    if title.startswith('NEADJUDECAT'):
        return 'NEADJUDECAT', 'Closed'
    
    # Check countdown
    countdown = soup.find('div', class_='countdown')
    if countdown:
        if 'notstarted' in countdown.get('class', []):
            return 'Active', 'Not Started'
        else:
            return 'Active', 'Active Bidding'
    
    # Check for closed
    if soup.find(string=re.compile("Licitatie incheiata")):
        return 'NEADJUDECAT', 'Closed'
    
    return 'Active', 'Unknown'
```

### 2. Orchestrator Update Logic

```python
if existing:
    # Compare and update
    changed = False
    
    # Check price changes
    if detail_data.get('current_offer') != existing.current_offer:
        existing.current_offer = detail_data.get('current_offer')
        changed = True
    
    # Check status changes
    if detail_data.get('auction_status') != existing.auction_status:
        existing.auction_status = detail_data.get('auction_status')
        changed = True
    
    # Update all fields
    for key, value in detail_data.items():
        if hasattr(existing, key) and getattr(existing, key) != value:
            setattr(existing, key, value)
            changed = True
    
    existing.last_scraped_at = datetime.now()
    
    if changed:
        db.commit()
        updated_count += 1
        logger.info(f"Updated listing {url}")
```

---

## Migration Script Needed

```python
# migrations/add_new_fields.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('listings', sa.Column('guarantee_amount', sa.Float(), nullable=True))
    op.add_column('listings', sa.Column('viewing_deadline', sa.DateTime(), nullable=True))
    op.add_column('listings', sa.Column('auction_type', sa.String(50), nullable=True))
    op.add_column('listings', sa.Column('bid_count', sa.Integer(), default=0))
    op.add_column('listings', sa.Column('last_scraped_at', sa.DateTime(), nullable=True))
    op.add_column('listings', sa.Column('scrape_error', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('listings', 'scrape_error')
    op.drop_column('listings', 'last_scraped_at')
    op.drop_column('listings', 'bid_count')
    op.drop_column('listings', 'auction_type')
    op.drop_column('listings', 'viewing_deadline')
    op.drop_column('listings', 'guarantee_amount')
```

---

## Success Metrics

- [ ] 100% of listings have all required fields
- [ ] No scraping errors for valid listings
- [ ] Updates detected within 1 hour
- [ ] Price changes captured accurately
- [ ] Status transitions tracked
- [ ] Test coverage > 80%

---

## Next Steps

1. Review this document with stakeholders
2. Prioritize fixes based on user feedback
3. Create Alembic migration for schema changes
4. Implement Phase 1 fixes
5. Test with production data
6. Deploy incrementally

---

## Questions for User

1. Is the guarantee amount (`Garanție de participare`) critical for your use case?
2. Do you need bid history or just current bid count?
3. How often should the scraper run? (currently set up for hourly)
4. Should we archive old (ended) auctions or keep them?
5. Do you need alerts for specific events (new listings, price drops)?
