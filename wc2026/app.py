"""
World Cup 2026 – Live Analytics & Prediction Dashboard
Entry point: run with  →  streamlit run app.py
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from pages import live_scores, news_feed, predictions, player_ratings

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WC 2026 Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auto-refresh every 60 seconds (live data) ──────────────────────────────────
st_autorefresh(interval=60_000, key="live_refresh")

# ── Sidebar navigation ─────────────────────────────────────────────────────────
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/en/thumb/3/3e/2026_FIFA_World_Cup.svg/200px-2026_FIFA_World_Cup.svg.png",
    width=140,
)
st.sidebar.title("⚽ WC 2026")
st.sidebar.caption("Live Analytics & Predictions")

page = st.sidebar.radio(
    "Navigate",
    ["🟢 Live Scores", "📰 News Feed", "🔮 Match Predictions", "⭐ Player Ratings"],
)

st.sidebar.markdown("---")
st.sidebar.caption("Data refreshes every 60 seconds.")
st.sidebar.caption("Predictions use XGBoost + Poisson models.")

# ── Route to pages ─────────────────────────────────────────────────────────────
if page == "🟢 Live Scores":
    live_scores.render()
elif page == "📰 News Feed":
    news_feed.render()
elif page == "🔮 Match Predictions":
    predictions.render()
elif page == "⭐ Player Ratings":
    player_ratings.render()
