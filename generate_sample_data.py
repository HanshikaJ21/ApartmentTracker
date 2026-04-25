"""
generate_sample_data.py — Apartment Tracker
Generates realistic fake Mumbai apartment listings to seed the database
so you can build and test your PowerBI dashboard immediately,
without waiting for live scraping.
"""

import random
from datetime import datetime, timedelta
from database import init_db, save_listings
from export import export_to_csv
from colorama import Fore, Style, init

init(autoreset=True)

LOCALITIES = [
    "Bandra West", "Andheri East", "Andheri West", "Powai", "Thane",
    "Worli", "Lower Parel", "Goregaon East", "Malad West", "Kandivali",
    "Borivali", "Mulund", "Ghatkopar", "Chembur", "Dadar", "Vile Parle",
    "Santacruz", "Juhu", "Versova", "Kurla"
]

BHK_OPTIONS = [1, 2, 3, 4]
BHK_WEIGHTS = [15, 40, 35, 10]

# Price ranges per BHK (in Lakhs)
PRICE_RANGES = {
    1: (35,  90),
    2: (65,  180),
    3: (120, 400),
    4: (300, 900),
}

# Area ranges per BHK (in sqft)
AREA_RANGES = {
    1: (350,  650),
    2: (650,  1100),
    3: (950,  1600),
    4: (1400, 2800),
}

BUILDER_PREFIXES = [
    "Lodha", "Godrej", "Oberoi", "Rustomjee", "Runwal",
    "Shapoorji", "Hiranandani", "Mahindra", "Kalpataru", "Piramal"
]

SUFFIXES = [
    "Residences", "Heights", "Towers", "Enclave", "Park",
    "Avenue", "Grande", "Luxe", "Crest", "Vista"
]


def random_price(bhk: int, jitter_days: int = 0) -> float:
    """Generate a realistic price with a slight time-based drift for trend simulation."""
    lo, hi = PRICE_RANGES[bhk]
    base = random.uniform(lo, hi)
    # Simulate ~0.05% daily price growth (trend effect)
    growth = 1 + (jitter_days * 0.0005)
    return round(base * growth, 2)


def make_listing(bhk: int, locality: str, scraped_at: datetime) -> dict:
    builder = random.choice(BUILDER_PREFIXES)
    suffix  = random.choice(SUFFIXES)
    title   = f"{bhk} BHK Apartment in {builder} {suffix}, {locality}"
    area    = round(random.uniform(*AREA_RANGES[bhk]), 0)
    jitter  = (scraped_at - datetime(2025, 1, 1)).days
    price   = random_price(bhk, jitter)
    price_raw = f"₹{price:.1f} Lac" if price < 100 else f"₹{price/100:.2f} Cr"

    return {
        "title":      title,
        "price_lakh": price,
        "price_raw":  price_raw,
        "bhk":        bhk,
        "area_sqft":  area,
        "locality":   locality,
        "city":       "Mumbai",
        "url":        f"https://www.magicbricks.com/sample/{locality.replace(' ','-').lower()}-{bhk}bhk-{int(area)}sqft",
    }


def generate(num_records: int = 300, num_days: int = 60):
    """
    Generate `num_records` fake listings spread across `num_days` days of history.
    This gives PowerBI enough data to show meaningful price trends.
    """
    print(f"{Fore.CYAN}[SampleData] Generating {num_records} fake listings across {num_days} days…{Style.RESET_ALL}")

    init_db()
    all_batches = []

    start_date = datetime.utcnow() - timedelta(days=num_days)

    for day_offset in range(num_days):
        scrape_time = start_date + timedelta(days=day_offset)
        batch = []
        per_day = max(1, num_records // num_days)

        for _ in range(per_day):
            bhk      = random.choices(BHK_OPTIONS, weights=BHK_WEIGHTS)[0]
            locality = random.choice(LOCALITIES)
            listing  = make_listing(bhk, locality, scrape_time)
            batch.append(listing)

        # Override scraped_at so each batch has a different date for trend charts
        from database import SessionLocal, Listing
        session = SessionLocal()
        inserted = 0
        try:
            for item in batch:
                row = Listing(
                    title      = item["title"],
                    price_lakh = item["price_lakh"],
                    price_raw  = item["price_raw"],
                    bhk        = item["bhk"],
                    area_sqft  = item["area_sqft"],
                    locality   = item["locality"],
                    city       = item["city"],
                    url        = item["url"],
                    scraped_at = scrape_time,
                )
                session.add(row)
                inserted += 1
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"{Fore.RED}[SampleData] Error: {e}")
        finally:
            session.close()

    print(f"{Fore.GREEN}[SampleData] ✅ Done! Exporting CSV…{Style.RESET_ALL}")
    export_to_csv()


if __name__ == "__main__":
    generate(num_records=300, num_days=60)
