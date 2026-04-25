"""
export.py — Apartment Tracker
Exports all database records to a CSV file for easy import into PowerBI.
"""

import os
import pandas as pd
from database import get_all_listings
from colorama import Fore, Style, init
from datetime import datetime

init(autoreset=True)

OUTPUT_DIR = "exports"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def export_to_csv(filename: str | None = None) -> str:
    """
    Fetch all listings from the database and export to CSV.
    Returns the path to the generated CSV file.
    """
    listings = get_all_listings()

    if not listings:
        print(f"{Fore.YELLOW}[Export] No data found in the database. Run the scraper first.")
        return ""

    df = pd.DataFrame(listings)

    # Friendly column order for PowerBI
    cols = ["id", "scraped_at", "city", "locality", "bhk", "area_sqft",
            "price_lakh", "price_raw", "title", "url"]
    df = df[[c for c in cols if c in df.columns]]

    # Format datetime for PowerBI
    df["scraped_at"] = pd.to_datetime(df["scraped_at"]).dt.strftime("%Y-%m-%d %H:%M")

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_DIR, f"mumbai_apartments_{timestamp}.csv")

    df.to_csv(filename, index=False, encoding="utf-8-sig")  # utf-8-sig for Excel compat
    print(f"{Fore.GREEN}[Export] ✅ CSV saved → {filename}")
    print(f"[Export] Total rows: {len(df)}")

    # Summary stats
    print(f"\n{Fore.CYAN}── Quick Summary ──")
    if "price_lakh" in df.columns:
        valid = df["price_lakh"].dropna()
        if not valid.empty:
            print(f"  Avg Price    : ₹{valid.mean():.1f} Lakh")
            print(f"  Min Price    : ₹{valid.min():.1f} Lakh")
            print(f"  Max Price    : ₹{valid.max():.1f} Lakh")
    if "bhk" in df.columns:
        print(f"\n  BHK Distribution:")
        print(df["bhk"].value_counts().to_string())
    if "area_sqft" in df.columns:
        valid_area = df["area_sqft"].dropna()
        if not valid_area.empty:
            print(f"\n  Avg Area     : {valid_area.mean():.0f} sqft")
    print(Style.RESET_ALL)

    return filename


if __name__ == "__main__":
    export_to_csv()
