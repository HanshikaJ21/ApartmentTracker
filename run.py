"""
run.py — Apartment Tracker
Main entry point. Runs the scraper, saves to DB, and exports CSV.
Optionally runs on a schedule (every 24 hours).
"""
import sys
import io
# Force UTF-8 output on Windows to support emoji/unicode in print statements
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


import time
import schedule
from colorama import Fore, Style, init

from scraper import scrape_mumbai_apartments
from database import init_db, save_listings
from export import export_to_csv

init(autoreset=True)


def run_pipeline():
    """Full pipeline: Scrape → Save to DB → Export CSV."""
    print(f"\n{Fore.MAGENTA}{'='*55}")
    print(f"  🚀  Starting Mumbai Apartment Price Tracker")
    print(f"{'='*55}{Style.RESET_ALL}")

    # Step 1 — Scrape
    listings = scrape_mumbai_apartments(max_pages=5)

    if not listings:
        print(f"{Fore.RED}[Pipeline] No listings scraped. Exiting.")
        return

    # Step 2 — Save to SQLite DB
    inserted = save_listings(listings)
    print(f"[Pipeline] {inserted} new records saved to apartments.db")

    # Step 3 — Export CSV for PowerBI
    csv_path = export_to_csv()
    if csv_path:
        print(f"[Pipeline] CSV ready for PowerBI → {csv_path}")

    print(f"\n{Fore.GREEN}✅ Pipeline complete!{Style.RESET_ALL}")


if __name__ == "__main__":
    # Initialise the database (creates tables if missing)
    init_db()

    if "--schedule" in sys.argv:
        # Run immediately, then every 24 hours
        print(f"{Fore.CYAN}[Scheduler] Running pipeline every 24 hours. Press Ctrl+C to stop.{Style.RESET_ALL}")
        run_pipeline()
        schedule.every(24).hours.do(run_pipeline)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        # One-shot run
        run_pipeline()
