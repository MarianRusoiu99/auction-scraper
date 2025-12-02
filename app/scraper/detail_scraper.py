import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urljoin
from app.scraper.base import BaseScraper

logger = logging.getLogger(__name__)

class DetailScraper(BaseScraper):
    async def scrape_detail(self, url: str) -> Optional[Dict[str, Any]]:
        logger.info(f"Scraping detail page: {url}")
        html = await self.fetch_page(url)
        if not html:
            return None

        soup = self.parse_html(html)
        data = {"detail_url": url}

        # Title
        # Usually in an h1 or h2 or a specific class
        # Based on screenshot, it's a large title
        title_elem = soup.find('h1') or soup.find('h2') # Fallback
        if title_elem:
            data['title'] = title_elem.get_text(strip=True)
        
        # The page seems to have labels like "Pret de pornire:", "Oferta curenta:", etc.
        # We can look for these labels and get the next sibling or text
        
        text_content = soup.get_text(separator="\n")
        
        # Helper to extract value by label from the specific structure
        # Structure: <p><span class="ad-info-name">Label</span> <span class="ad-info-value">Value</span></p>
        def extract_by_label(label: str) -> Optional[str]:
            # Find span with class ad-info-name containing the label
            for span in soup.find_all('span', class_='ad-info-name'):
                if label.lower() in span.get_text(strip=True).lower():
                    # The value is usually in the next sibling span with class ad-info-value
                    value_elem = span.find_next_sibling('span', class_='ad-info-value')
                    if value_elem:
                        return value_elem.get_text(strip=True)
            return None

        # Prices - store as strings due to inconsistent formatting
        # "Pret" in Informatii generale
        price_str = extract_by_label("Pret")
        if price_str:
            data['starting_price'] = price_str.strip()
            
        # "Oferta actuala" - usually in sidebar h3
        # <h3><span class="left">Oferta actuala:</span> <span class="right">1,815.00 lei</span></h3>
        offer_header = soup.find('h3', string=re.compile("Oferta actuala"))
        if not offer_header:
            # Try finding h3 that contains the span
            for h3 in soup.find_all('h3'):
                if "Oferta actuala" in h3.get_text():
                    offer_header = h3
                    break
        
        if offer_header:
            right_span = offer_header.find('span', class_='right')
            if right_span:
                data['current_offer'] = right_span.get_text(strip=True)
        
        # Guarantee amount - look for "Garantie" or "Garanție" label
        guarantee_str = extract_by_label("Garantie") or extract_by_label("Garanție")
        if guarantee_str:
            data['guarantee_amount'] = guarantee_str.strip()
        
        # Auction type - look for "Tip licitatie" or similar
        auction_type = extract_by_label("Tip licitatie") or extract_by_label("Tip licitație")
        if auction_type:
            data['auction_type'] = auction_type.strip()
        
        # Bid count - look for number of offers/bids
        bid_count_str = extract_by_label("Numar oferte") or extract_by_label("Număr oferte")
        if bid_count_str:
            try:
                data['bid_count'] = int(re.sub(r'\D', '', bid_count_str))
            except (ValueError, AttributeError):
                data['bid_count'] = 0

        # Dates
        start_date_str = extract_by_label("Publicata la") # Using Publicata la as start for now
        if start_date_str:
            data['auction_start_date'] = self._parse_date(start_date_str)
            
        end_date_str = extract_by_label("Expira la")
        if end_date_str:
            data['auction_end_date'] = self._parse_date(end_date_str)
            
        # Registration deadline not explicitly found in debug HTML, might be "Termen limita" if present
        reg_deadline_str = extract_by_label("Termen limita") or extract_by_label("Termen limită")
        if reg_deadline_str:
            data['registration_deadline'] = self._parse_date(reg_deadline_str)
        
        # Viewing deadline - look for "Termen vizionare" or similar
        viewing_deadline_str = extract_by_label("Termen vizionare") or extract_by_label("Vizionare pana la")
        if viewing_deadline_str:
            data['viewing_deadline'] = self._parse_date(viewing_deadline_str)

        # Location
        # <p><span class="ad-info-name"><i class="fa fa-map-marker"></i>  Loc predare: </span> <span class="ad-info-value"> Bragadiru, Ilfov </span> </p>
        location_str = extract_by_label("Loc predare")
        if location_str:
            parts = [p.strip() for p in location_str.split(',')]
            if len(parts) >= 2:
                data['city'] = parts[0]
                data['county'] = parts[1]
            elif len(parts) == 1:
                data['county'] = parts[0]
            data['address'] = location_str

        # Contact
        # In sidebar-user-info
        user_info = soup.find('div', class_='sidebar-user-info')
        if user_info:
            # Phone
            phone_icon = user_info.find('i', class_='fa-phone')
            if phone_icon and phone_icon.parent:
                data['contact_phone'] = phone_icon.parent.get_text(strip=True)
            
            # Email
            email_icon = user_info.find('i', class_='fa-at')
            if email_icon and email_icon.parent:
                data['contact_email'] = email_icon.parent.get_text(strip=True)
                
            # Address/Person
            marker_icon = user_info.find('i', class_='fa-map-marker')
            if marker_icon and marker_icon.parent:
                data['contact_person'] = marker_icon.parent.get_text(strip=True) # Using address as contact info for now

        # Status - comprehensive detection
        title_upper = data.get('title', '').upper()
        
        # Initialize status flags
        data['is_active'] = True
        data['is_sold'] = False
        
        # Check title for NEADJUDECAT/ADJUDECAT
        if 'NEADJUDECAT' in title_upper:
            data['status'] = 'NEADJUDECAT'
            data['is_sold'] = False
            # Still active if auction hasn't ended
        elif 'ADJUDECAT' in title_upper:
            data['status'] = 'ADJUDECAT'
            data['is_sold'] = True
            data['is_active'] = False
        else:
            data['status'] = 'Active'

        # Auction Status
        # Check countdown div
        countdown = soup.find('div', class_='countdown')
        if countdown:
            if 'notstarted' in countdown.get('class', []):
                data['auction_status'] = 'Not Started'
                data['is_active'] = False  # Not yet started
            else:
                data['auction_status'] = 'Active'
                # Keep is_active as True unless already marked as sold
            
            # Parse countdown text for fallback
            countdown_text = countdown.get_text(strip=True)
            
            # Use data-expire-date attribute if available (more precise)
            expire_date_str = countdown.get('data-expire-date')
            if expire_date_str:
                try:
                    # Format: 2025-12-11 15:00:00
                    expire_date = datetime.strptime(expire_date_str, "%Y-%m-%d %H:%M:%S")
                    
                    # Based on analysis: this is usually the registration deadline
                    data['registration_deadline'] = expire_date
                except ValueError:
                    logger.warning(f"Could not parse data-expire-date: {expire_date_str}")
                    # Fallback to text parsing
                    end_time = self._parse_countdown(countdown_text)
                    if end_time:
                         data['registration_deadline'] = end_time
            else:
                # Fallback to text parsing
                end_time = self._parse_countdown(countdown_text)
                if end_time:
                    if "inregistra" in countdown_text.lower():
                        data['registration_deadline'] = end_time
                    else:
                        data['auction_end_date'] = end_time

        
        # If "Licitatie incheiata" text exists
        if soup.find(string=re.compile("Licitatie incheiata")) or soup.find(string=re.compile("Licitație încheiată")):
            data['auction_status'] = 'Closed'
            data['is_active'] = False
            # If closed and not adjudecat, it means it wasn't sold
            if data['status'] != 'ADJUDECAT':
                data['is_sold'] = False

        # Category
        # Try to find category in breadcrumbs or specific label
        # Based on user feedback, categories are like "Autovehicule", "Diverse", etc.
        # We'll look for "Categorie" label again, or try to infer from breadcrumbs if available
        data['category'] = extract_by_label("Categorie")
        if not data['category']:
            # Fallback: check if there is a breadcrumb list
            breadcrumb = soup.find('ol', class_='breadcrumb')
            if breadcrumb:
                items = breadcrumb.find_all('li')
                if len(items) > 1:
                    # Usually Home > Category > Listing
                    data['category'] = items[1].get_text(strip=True)

        # Description
        # Look for the description text block
        # It's usually after <div class="ads-detail">
        detail_div = soup.find('div', class_='ads-detail')
        if detail_div:
            # Get text but exclude the table and other specific elements if needed
            # For now, just get all text
            data['description'] = detail_div.get_text(strip=True)[:5000] # Limit length

        # Images
        images = []
        fotorama = soup.find('div', class_='fotorama')
        if fotorama:
            for img in fotorama.find_all('img'):
                src = img.get('src')
                if src:
                    if not src.startswith('http'):
                        src = urljoin("https://anabi.just.ro", src)
                    images.append(src)
        data['images'] = images
        data['number_of_images'] = len(images)
        
        # Documents
        documents = []
        # Look for "Descarca" links
        for a in soup.find_all('a', string=re.compile("Descarca", re.IGNORECASE)):
            href = a.get('href')
            if href:
                if not href.startswith('http'):
                    href = urljoin("https://anabi.just.ro", href)
                if href.endswith('.pdf'):
                    documents.append(href)
        data['documents'] = documents

        # Parse Table Data (Specifications)
        specs = []
        table = soup.find('div', class_='ads-detail').find('table') if soup.find('div', class_='ads-detail') else None
        if table:
            for tr in table.find_all('tr'):
                cells = tr.find_all('td')
                # Look for Label - Value pairs
                # Usually they are side by side, e.g. Marca | PORSCHE
                # But due to rowspan, the index might vary.
                # Simple heuristic: if we find a cell with text that looks like a known label, take the next cell.
                # Or just iterate and if we find 2 adjacent cells with text, treat as key-value.
                
                # Filter out empty cells or cells with just numbers (like "1.")
                text_cells = [td.get_text(strip=True) for td in cells if td.get_text(strip=True)]
                
                if len(text_cells) >= 2:
                    # Check for specific labels
                    label = text_cells[0].replace(":", "")
                    value = text_cells[1]
                    
                    # Common labels in these tables
                    known_labels = ["Marca", "Model", "Tipul", "Numărul de identificare", "Data primei înmatriculări", 
                                  "Capacitate cilindrică", "Putere", "Nr. de locuri", "Sursa de energie", "Culoare", 
                                  "Rulaj estimat", "Înmatriculat", "Carte de identitate", "Certificat înmatriculare", "Număr chei"]
                    
                    if label in known_labels:
                        specs.append(f"{label}: {value}")
                    elif label == "Observații":
                         # The value might be long
                         specs.append(f"Observații: {value}")

        if specs:
            specs_text = "\n".join(specs)
            if data.get('description'):
                data['description'] = specs_text + "\n\n" + data['description']
            else:
                data['description'] = specs_text

        return data

    def _parse_price(self, price_str: str) -> Optional[float]:
        if not price_str:
            return None
        # Remove currency symbols and ALL whitespace (including non-breaking spaces)
        clean_str = price_str.replace("RON", "").replace("LEI", "").replace("lei", "")
        clean_str = ''.join(clean_str.split())  # Remove all whitespace
        
        try:
            # Determine format based on separators
            # Romanian: "1.200,50" (dot=thousands, comma=decimal)
            # US: "1,200.50" (comma=thousands, dot=decimal)
            
            dot_count = clean_str.count('.')
            comma_count = clean_str.count(',')
            
            if dot_count == 0 and comma_count == 0:
                # Simple integer or decimal
                return float(clean_str)
            elif dot_count > 1:
                # Multiple dots = Romanian thousands separator "1.234.567,89"
                clean_str = clean_str.replace('.', '').replace(',', '.')
            elif comma_count > 1:
                # Multiple commas = US thousands separator "1,234,567.89"
                clean_str = clean_str.replace(',', '')
            elif dot_count == 1 and comma_count == 1:
                # Both present - check which comes last
                if clean_str.rfind(',') > clean_str.rfind('.'):
                    # Romanian: "1.200,50" -> comma is decimal
                    clean_str = clean_str.replace('.', '').replace(',', '.')
                else:
                    # US: "1,200.50" -> dot is decimal, remove comma
                    clean_str = clean_str.replace(',', '')
            elif comma_count == 1:
                # Only comma - European decimal "1200,50"
                clean_str = clean_str.replace(',', '.')
            # elif dot_count == 1: # Only dot - already correct format
            
            return float(clean_str)
        except (ValueError, AttributeError) as e:
            logger.error(f"Could not parse price '{price_str}' (cleaned: '{clean_str}'): {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        # Example: "29.11.2025 10:00"
        try:
            return datetime.strptime(date_str.strip(), "%d.%m.%Y %H:%M")
        except ValueError:
            try:
                return datetime.strptime(date_str.strip(), "%d.%m.%Y")
            except ValueError:
                return None

    def _parse_countdown(self, text: str) -> Optional[datetime]:
        if not text:
            return None
        
        days = 0
        hours = 0
        minutes = 0
        seconds = 0
        
        # Regex for each part
        days_match = re.search(r'(\d+)\s*zi(?:le)?', text)
        if days_match:
            days = int(days_match.group(1))
            
        hours_match = re.search(r'(\d+)h', text)
        if hours_match:
            hours = int(hours_match.group(1))
            
        minutes_match = re.search(r'(\d+)m', text)
        if minutes_match:
            minutes = int(minutes_match.group(1))
            
        seconds_match = re.search(r'(\d+)s', text)
        if seconds_match:
            seconds = int(seconds_match.group(1))
            
        if days == 0 and hours == 0 and minutes == 0 and seconds == 0:
            return None
            
        return datetime.now() + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
