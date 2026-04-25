import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_all_listings, init_db
from datetime import datetime

# Page Config
st.set_page_config(
    page_title="Mumbai Apartment Tracker",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] {
        color: #F4A300;
        font-size: 2rem;
    }
    .stPlotlyChart {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# ─── Data Loading ───
@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_data():
    listings = get_all_listings()
    if not listings:
        return pd.DataFrame()
    df = pd.DataFrame(listings)
    df['scraped_at'] = pd.to_datetime(df['scraped_at'])
    df['date'] = df['scraped_at'].dt.date
    return df

# Auto-seed DB with sample data on first run (e.g. Streamlit Cloud)
init_db()
if not get_all_listings():
    from generate_sample_data import generate
    generate(num_records=300, num_days=60)
    st.cache_data.clear()

df = load_data()

# ─── Sidebar Filters ───
st.sidebar.image("https://img.icons8.com/clouds/100/000000/city.png", width=100)
st.sidebar.title("Filters")

if not df.empty:
    # Locality Filter
    all_localities = sorted(df['locality'].unique().tolist())
    selected_localities = st.sidebar.multiselect("Localities", all_localities, default=all_localities[:5] if len(all_localities) > 5 else all_localities)

    # BHK Filter
    bhk_options = sorted([b for b in df['bhk'].unique() if b is not None])
    selected_bhk = st.sidebar.multiselect("BHK Type", bhk_options, default=bhk_options)

    # Price Range Filter
    min_price = float(df['price_lakh'].min()) if not df['price_lakh'].dropna().empty else 0
    max_price = float(df['price_lakh'].max()) if not df['price_lakh'].dropna().empty else 1000
    price_range = st.sidebar.slider("Price Range (₹ Lakh)", min_price, max_price, (min_price, max_price))

    # Apply Filters
    mask = (
        df['locality'].isin(selected_localities) &
        df['bhk'].isin(selected_bhk) &
        (df['price_lakh'].between(price_range[0], price_range[1]))
    )
    filtered_df = df[mask]
else:
    st.sidebar.warning("No data available.")
    filtered_df = df

# ─── Main Dashboard ───
st.title("🏙️ Mumbai Apartment Market Tracker")
st.markdown("Real-time insights into Mumbai's residential real estate market.")

if not filtered_df.empty:
    # ─── KPI Row ───
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Listings", len(filtered_df))
    with col2:
        avg_price = filtered_df['price_lakh'].mean()
        st.metric("Avg Price", f"₹{avg_price:.1f}L")
    with col3:
        avg_area = filtered_df['area_sqft'].mean()
        st.metric("Avg Area", f"{avg_area:.0f} sqft")
    with col4:
        num_localities = filtered_df['locality'].nunique()
        st.metric("Localities", num_localities)

    st.markdown("---")

    # ─── Charts Row 1 ───
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📈 Price Trend Over Time")
        # Group by date and BHK for trend
        trend_df = filtered_df.groupby(['date', 'bhk'])['price_lakh'].mean().reset_index()
        fig_trend = px.line(
            trend_df, 
            x='date', 
            y='price_lakh', 
            color='bhk',
            title="Avg Price by BHK Type",
            labels={'price_lakh': 'Avg Price (Lakh)', 'date': 'Date', 'bhk': 'BHK'},
            markers=True,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_trend.update_layout(hovermode="x unified", margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        st.subheader("🏘️ Top Localities by Price")
        loc_df = filtered_df.groupby('locality')['price_lakh'].mean().sort_values(ascending=False).head(10).reset_index()
        fig_loc = px.bar(
            loc_df,
            x='price_lakh',
            y='locality',
            orientation='h',
            title="Avg Price (₹ Lakh)",
            labels={'price_lakh': 'Avg Price', 'locality': ''},
            color='price_lakh',
            color_continuous_scale='Sunset'
        )
        fig_loc.update_layout(showlegend=False, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_loc, use_container_width=True)

    # ─── Charts Row 2 ───
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("🥧 BHK Distribution")
        fig_pie = px.pie(
            filtered_df, 
            names='bhk', 
            hole=0.4,
            title="Market Composition",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c4:
        st.subheader("📐 Area vs Price")
        fig_scatter = px.scatter(
            filtered_df,
            x='area_sqft',
            y='price_lakh',
            color='bhk',
            hover_data=['locality', 'title'],
            title="Correlation: Size vs Price",
            labels={'area_sqft': 'Area (sqft)', 'price_lakh': 'Price (Lakh)'}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ─── Data Table ───
    st.subheader("📋 Latest Listings")
    display_df = filtered_df[['scraped_at', 'locality', 'bhk', 'area_sqft', 'price_lakh', 'title', 'url']].sort_values('scraped_at', ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.info("Adjust your filters to see more listings.")

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data Source: MagicBricks")
