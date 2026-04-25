# 🏙️ Mumbai Apartment Price Tracker

A complete end-to-end system that scrapes Mumbai apartment listings from MagicBricks,
stores them in a SQLite database, and exports data for a PowerBI dashboard showing price trends.

---

## 📁 Project Structure

```
ApartmentTracker/
├── dashboard.py             # NEW: Streamlit Web Dashboard
├── scraper.py               # Web scraper (MagicBricks → Mumbai apartments)
├── database.py              # SQLite/Postgres DB setup & operations
├── export.py                # Export DB → CSV for PowerBI
├── run.py                   # Main pipeline (scrape + save + export)
├── generate_sample_data.py  # Generates 300 fake listings for demo/testing
├── requirements.txt         # Python dependencies
├── .github/workflows/       # Automated daily scraping (GitHub Actions)
├── apartments.db            # Local SQLite database
└── exports/                 # Auto-created folder with CSV exports
```

---

## ⚙️ Setup (One Time)

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

### Option A — Live Scraping (Real Data from MagicBricks)
```bash
python run.py
```

### Option B — Demo Data (60 Days of Simulated Price History)
```bash
python generate_sample_data.py
```

### Option C — Run Scraper Every 24 Hours Automatically
```bash
python run.py --schedule
```

### Option D — Launch Web Dashboard
```bash
streamlit run dashboard.py
```

---

## 🌐 Going Live (The "Right Way")

To make this project live and automated:

1. **Cloud Database**: Create a free Postgres database (e.g., on [Supabase](https://supabase.com)).
2. **Environment Variables**: Set `DATABASE_URL` to your cloud DB string.
3. **GitHub**: Push this repo to GitHub.
4. **Automation**: The included GitHub Action (`.github/workflows/scrape.yml`) will run the scraper daily at 2 AM automatically.
5. **Dashboard**: Connect your GitHub repo to [Streamlit Community Cloud](https://streamlit.io/cloud) (Free).

---

## 📊 PowerBI Dashboard

Open `powerbi_setup_guide.md` for full instructions. Quick summary:

1. Open **PowerBI Desktop** → **Get Data** → **Text/CSV**
2. Load the latest file from the `exports/` folder
3. Build these visuals:
   - 📈 **Line Chart** — Avg Price over Time (by BHK)
   - 🏘️ **Bar Chart** — Avg Price by Locality
   - 🥧 **Pie Chart** — Listings by BHK Type
   - 📐 **Scatter Plot** — Area vs. Price
   - 🔢 **KPI Cards** — Total Listings, Avg Price, Avg Area

---

## 🗃️ Database Schema

Table: `listings`

| Column       | Type    | Description                      |
|-------------|---------|----------------------------------|
| id           | Integer | Auto-increment primary key       |
| title        | String  | Listing title                    |
| price_lakh   | Float   | Price in ₹ Lakhs                 |
| price_raw    | String  | Raw price string (e.g. ₹2.1 Cr) |
| bhk          | Integer | Number of BHK                    |
| area_sqft    | Float   | Carpet area in sq.ft.            |
| locality     | String  | Mumbai neighbourhood             |
| city         | String  | Always "Mumbai"                  |
| url          | Text    | Listing URL                      |
| scraped_at   | DateTime| Timestamp of scrape              |

---

## 📦 Data Extracted Per Listing

- ✅ Title
- ✅ Price (converted to ₹ Lakhs)
- ✅ BHK (1/2/3/4)
- ✅ Area (sq.ft.)
- ✅ Locality / Neighbourhood
- ✅ Listing URL
- ✅ Scrape Timestamp

---

## 💡 Notes

- The scraper targets **MagicBricks.com** (Mumbai residential apartments)
- A polite delay of 2–5 seconds is added between page requests
- Duplicate listings (same URL + same scrape time) are automatically skipped
- CSV exports use **UTF-8 BOM** encoding for compatibility with Excel & PowerBI
