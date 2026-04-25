"""
scraper.py — Apartment Tracker
Scrapes Mumbai apartment listings from MagicBricks.
Extracts: Title, Price (₹ Lakhs), BHK, Area (sqft), Locality, URL.
"""

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

init(autoreset=True)

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
BASE_URL = "https://www.magicbricks.com/property-for-sale/residential-real-estate"
CITY = "Mumbai"
MAX_PAGES = 5       # Increase for more results
DELAY_MIN = 2.0     # Seconds to wait between requests (be polite!)
DELAY_MAX = 5.0

PARAMS = {
    "proptype": "Multistorey-Apartment,Builder-Floor-Apartment,Studio-Apartment",
    "cityName": CITY,
    "BudgetMin": "0",
    "BudgetMax": "0",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.magicbricks.com/",
    "DNT": "1",
}

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def parse_price(raw: str) -> float | None:
    """
    Convert price strings like '₹85 Lac', '₹1.2 Cr', '85,00,000'
    to a float in Lakhs.
    """
    if not raw:
        return None
    raw = raw.replace(",", "").replace("₹", "").strip()
    try:
        if "Cr" in raw:
            num = float(re.findall(r"[\d.]+", raw)[0])
            return round(num * 100, 2)  # Crore → Lakhs
        elif "Lac" in raw or "Lakh" in raw:
            num = float(re.findall(r"[\d.]+", raw)[0])
            return round(num, 2)
        else:
            num = float(re.findall(r"[\d.]+", raw)[0])
            return round(num / 1e5, 2)  # Raw rupees → Lakhs
    except (IndexError, ValueError):
        return None


def parse_bhk(text: str) -> int | None:
    """Extract BHK number from strings like '2 BHK', '3BHK Apartment'."""
    if not text:
        return None
    match = re.search(r"(\d)\s*BHK", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def parse_area(text: str) -> float | None:
    """Extract numeric sqft from strings like '850 sq.ft.', '1200 Sq.Ft'."""
    if not text:
        return None
    match = re.search(r"([\d,]+(?:\.\d+)?)\s*(?:sq\.?ft\.?|sqft)", text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def get_page(url: str, params: dict | None = None, retries: int = 3) -> BeautifulSoup | None:
    """Fetch a page and return a BeautifulSoup object. Retries on failure."""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "lxml")
            else:
                print(f"{Fore.YELLOW}[Scraper] HTTP {resp.status_code} on attempt {attempt}")
        except requests.RequestException as e:
            print(f"{Fore.RED}[Scraper] Request failed (attempt {attempt}): {e}")
        time.sleep(DELAY_MIN * attempt)
    return None


# ──────────────────────────────────────────────
# Core Parsing Logic
# ──────────────────────────────────────────────

def parse_listings(soup: BeautifulSoup) -> list[dict]:
    """
    Parse apartment listing cards from a MagicBricks search results page.
    Returns a list of dicts with extracted fields.
    """
    listings = []

    # MagicBricks wraps each listing in a <div> with class containing 'mb-srp__card'
    cards = soup.find_all("div", class_=re.compile(r"mb-srp__card", re.I))

    if not cards:
        # Fallback: try generic article/li tags
        cards = soup.find_all(["article", "li"], class_=re.compile(r"listing|property|card", re.I))

    print(f"[Scraper] Found {len(cards)} listing cards on this page.")

    for card in cards:
        try:
            # ── Title ──
            title_tag = card.find(["h2", "h3", "a"], class_=re.compile(r"title|name|heading", re.I))
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            # ── URL ──
            link_tag = card.find("a", href=True)
            url = link_tag["href"] if link_tag else ""
            if url and not url.startswith("http"):
                url = "https://www.magicbricks.com" + url

            # ── Price ──
            price_tag = card.find(class_=re.compile(r"price|amount|cost", re.I))
            price_raw = price_tag.get_text(strip=True) if price_tag else ""
            price_lakh = parse_price(price_raw)

            # ── BHK ──
            # Try title first, then a dedicated BHK tag
            bhk = parse_bhk(title)
            if bhk is None:
                bhk_tag = card.find(class_=re.compile(r"bhk|bedroom|bed", re.I))
                if bhk_tag:
                    bhk = parse_bhk(bhk_tag.get_text(strip=True))

            # ── Area ──
            area_tag = card.find(class_=re.compile(r"area|size|sqft|carpet", re.I))
            area_sqft = None
            if area_tag:
                area_sqft = parse_area(area_tag.get_text(strip=True))
            if area_sqft is None:
                # Try searching all text in the card
                card_text = card.get_text(" ", strip=True)
                area_sqft = parse_area(card_text)

            # ── Locality ──
            locality_tag = card.find(class_=re.compile(r"localit|location|address|sublocal", re.I))
            locality = locality_tag.get_text(strip=True) if locality_tag else "Mumbai"

            if title == "N/A" and not url:
                continue  # Skip empty cards

            listings.append({
                "title":      title,
                "price_raw":  price_raw,
                "price_lakh": price_lakh,
                "bhk":        bhk,
                "area_sqft":  area_sqft,
                "locality":   locality,
                "city":       CITY,
                "url":        url,
            })

        except Exception as e:
            print(f"{Fore.RED}[Scraper] Error parsing card: {e}")
            continue

    return listings


# ──────────────────────────────────────────────
# Main Scraping Function
# ──────────────────────────────────────────────

def scrape_mumbai_apartments(max_pages: int = MAX_PAGES) -> list[dict]:
    """
    Scrape multiple pages of Mumbai apartment listings.
    Returns a combined list of all listing dicts.
    """
    all_listings = []
    print(f"\n{Fore.CYAN}{'='*55}")
    print(f"  🏙️  Mumbai Apartment Tracker — MagicBricks Scraper")
    print(f"{'='*55}{Style.RESET_ALL}\n")

    for page_num in range(1, max_pages + 1):
        params = {**PARAMS, "page": page_num}
        print(f"{Fore.BLUE}[Scraper] Fetching page {page_num}/{max_pages}…")

        soup = get_page(BASE_URL, params=params)
        if soup is None:
            print(f"{Fore.RED}[Scraper] Could not fetch page {page_num}. Stopping.")
            break

        page_listings = parse_listings(soup)
        all_listings.extend(page_listings)

        print(f"{Fore.GREEN}[Scraper] Page {page_num}: {len(page_listings)} listings collected.")

        if page_num < max_pages:
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            print(f"[Scraper] Waiting {delay:.1f}s before next request…")
            time.sleep(delay)

    print(f"\n{Fore.CYAN}[Scraper] Total listings scraped: {len(all_listings)}{Style.RESET_ALL}\n")
    return all_listings


if __name__ == "__main__":
    results = scrape_mumbai_apartments()
    for r in results[:5]:
        print(r)
