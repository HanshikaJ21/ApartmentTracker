"""
database.py — Apartment Tracker
Handles all SQLite database operations using SQLAlchemy.
"""

import os
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Text, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Connection logic: Use Cloud Postgres if available, else fallback to Local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///apartments.db")

# Fix for Render/Heroku/Vercel (Postgres URLs often start with 'postgres://' which SQLAlchemy needs as 'postgresql://')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Listing(Base):
    """ORM model representing a single apartment listing."""
    __tablename__ = "listings"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    title       = Column(String(500))
    price_lakh  = Column(Float, nullable=True)       # Price in Lakhs (₹)
    price_raw   = Column(String(100), nullable=True) # Raw price string as scraped
    bhk         = Column(Integer, nullable=True)     # Number of BHK
    area_sqft   = Column(Float, nullable=True)       # Area in sq.ft.
    locality    = Column(String(200), nullable=True) # Neighbourhood / locality
    city        = Column(String(100), default="Mumbai")
    url         = Column(Text, nullable=True)
    scraped_at  = Column(DateTime, default=datetime.utcnow)

    # Prevent exact duplicate rows per URL + scrape date
    __table_args__ = (
        UniqueConstraint("url", "scraped_at", name="uix_url_date"),
    )


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print("[DB] Database initialised -> apartments.db")


def save_listings(listings: list[dict]) -> int:
    """
    Insert new listings into the database.
    Skips duplicates (same URL + same scrape date).
    Returns the count of rows inserted.
    """
    session = SessionLocal()
    inserted = 0
    now = datetime.utcnow().replace(second=0, microsecond=0)  # minute-level dedup

    try:
        for item in listings:
            # Check for duplicate
            exists = (
                session.query(Listing)
                .filter(Listing.url == item.get("url"),
                        Listing.scraped_at == now)
                .first()
            )
            if exists:
                continue

            row = Listing(
                title      = item.get("title"),
                price_lakh = item.get("price_lakh"),
                price_raw  = item.get("price_raw"),
                bhk        = item.get("bhk"),
                area_sqft  = item.get("area_sqft"),
                locality   = item.get("locality"),
                city       = item.get("city", "Mumbai"),
                url        = item.get("url"),
                scraped_at = now,
            )
            session.add(row)
            inserted += 1

        session.commit()
        print(f"[DB] Inserted {inserted} new listings.")
    except Exception as e:
        session.rollback()
        print(f"[DB] Error saving listings: {e}")
    finally:
        session.close()

    return inserted


def get_all_listings() -> list[dict]:
    """Fetch all stored listings as a list of dicts."""
    session = SessionLocal()
    try:
        rows = session.query(Listing).order_by(Listing.scraped_at.desc()).all()
        result = []
        for r in rows:
            result.append({
                "id":         r.id,
                "title":      r.title,
                "price_lakh": r.price_lakh,
                "price_raw":  r.price_raw,
                "bhk":        r.bhk,
                "area_sqft":  r.area_sqft,
                "locality":   r.locality,
                "city":       r.city,
                "url":        r.url,
                "scraped_at": r.scraped_at,
            })
        return result
    finally:
        session.close()
