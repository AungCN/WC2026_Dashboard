"""
World Cup 2026 – Live Analytics & Prediction Dashboard
install requirements -> pip install -r requirements.txt
Train Models -> python models/train_models.py
Entry point: run with  →  streamlit run app.py
"""

import time
import streamlit as st
from pages import live_scores, news_feed, predictions, player_ratings

# ── streamlit-autorefresh (optional — graceful fallback if not installed) ──────
# Install with:  pip install streamlit-autorefresh
try:
    from streamlit_autorefresh import st_autorefresh
    _HAS_AUTOREFRESH = True
except ModuleNotFoundError:
    _HAS_AUTOREFRESH = False

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WC 2026 Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auto-refresh every 60 seconds ─────────────────────────────────────────────
# Uses streamlit-autorefresh when available; otherwise a lightweight fallback
# that tracks elapsed time in session state and calls st.rerun().
REFRESH_INTERVAL_S = 60

if _HAS_AUTOREFRESH:
    st_autorefresh(interval=REFRESH_INTERVAL_S * 1000, key="live_refresh")
else:
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()

    elapsed   = int(time.time() - st.session_state.last_refresh)
    remaining = max(0, REFRESH_INTERVAL_S - elapsed)

    if remaining == 0:
        st.session_state.last_refresh = time.time()
        st.rerun()

# ── Sidebar navigation ─────────────────────────────────────────────────────────
st.sidebar.title("FIFA World Cup 2026")
st.sideber.title("United States:Canada:Mexico")
st.sidebar.caption("Live Analytics & Predictions")

page = st.sidebar.radio(
    "Navigate",
    ["⚽ Live Scores", "📰 News Feed", "🎯 Match Predictions", "📈 Player Ratings"],
)

st.sidebar.markdown("---")

# Show refresh status in sidebar
if _HAS_AUTOREFRESH:
    st.sidebar.caption("🔄 Auto-refreshes every 60 seconds.")
else:
    st.sidebar.caption(
        "💡 Install `streamlit-autorefresh` for seamless live updates:\n"
        "`pip install streamlit-autorefresh`"
    )

st.sidebar.caption("Predictions use XGBoost + Poisson models.")

# ── Route to pages ─────────────────────────────────────────────────────────────
if page == "⚽ Live Scores":
    live_scores.render()
elif page == "📰 News Feed":
    news_feed.render()
elif page == "🎯 Match Predictions":
    predictions.render()
elif page == "📈 Player Ratings":
    player_ratings.render()
