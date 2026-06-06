"""
utils/api_client.py
────────────────────
All external API calls live here.
Every function is wrapped with @st.cache_data so the same data
is NOT re-fetched if another user (or auto-refresh) triggers it
within the TTL window.

WHY THIS MATTERS:
  Without caching → 100 page loads = 100 API calls → hit rate limit fast.
  With caching    → 100 page loads = 1 API call    → safe and fast.

APIs used:
  • API-Football (via RapidAPI) — best all-around choice for WC 2026
  • NewsAPI — World Cup articles
"""

import os
import requests
import streamlit as st

# ── Read secrets (set in Streamlit Cloud or .env locally) ──────────────────────
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", st.secrets.get("RAPIDAPI_KEY", "YOUR_KEY_HERE"))
NEWSAPI_KEY  = os.getenv("NEWSAPI_KEY",  st.secrets.get("NEWSAPI_KEY",  "YOUR_KEY_HERE"))

RAPIDAPI_HOST = "api-football-v1.p.rapidapi.com"
RAPIDAPI_BASE = "https://api-football-v1.p.rapidapi.com/v3"

WC2026_LEAGUE_ID = 15    # FIFA World Cup league ID in API-Football
WC2026_SEASON    = 2026


def _headers() -> dict:
    """Return RapidAPI auth headers."""
    return {
        "X-RapidAPI-Key":  RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }


# ── Live scores  (cache: 60 seconds) ──────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner="Fetching live scores…")
def get_live_fixtures() -> list[dict]:
    """
    Returns all currently in-play WC 2026 fixtures.
    Updates every 15 seconds on the API side; we cache for 60s on our side.

    Example response item:
    {
      "fixture": {"id": 123, "date": "2026-06-15", "status": {"elapsed": 45}},
      "teams":   {"home": {"name": "Brazil"}, "away": {"name": "France"}},
      "goals":   {"home": 1, "away": 0}
    }
    """
    try:
        r = requests.get(
            f"{RAPIDAPI_BASE}/fixtures",
            headers=_headers(),
            params={"live": "all", "league": WC2026_LEAGUE_ID, "season": WC2026_SEASON},
            timeout=8,
        )
        r.raise_for_status()
        return r.json().get("response", [])
    except Exception as e:
        st.warning(f"Could not fetch live scores: {e}")
        return []


# ── Today's scheduled fixtures  (cache: 5 minutes) ────────────────────────────
@st.cache_data(ttl=300, show_spinner="Fetching today's fixtures…")
def get_todays_fixtures() -> list[dict]:
    """All WC 2026 fixtures scheduled for today."""
    from datetime import date
    today = date.today().isoformat()
    try:
        r = requests.get(
            f"{RAPIDAPI_BASE}/fixtures",
            headers=_headers(),
            params={"date": today, "league": WC2026_LEAGUE_ID, "season": WC2026_SEASON},
            timeout=8,
        )
        r.raise_for_status()
        return r.json().get("response", [])
    except Exception as e:
        st.warning(f"Could not fetch today's fixtures: {e}")
        return []


# ── Player stats for a specific fixture  (cache: 60 seconds) ──────────────────
@st.cache_data(ttl=60, show_spinner="Loading player stats…")
def get_fixture_players(fixture_id: int) -> list[dict]:
    """
    Returns per-player stats for a fixture:
    ratings, yellow/red cards, passes, shots, minutes played.

    Endpoint: GET /fixtures/players?fixture={id}
    """
    try:
        r = requests.get(
            f"{RAPIDAPI_BASE}/fixtures/players",
            headers=_headers(),
            params={"fixture": fixture_id},
            timeout=8,
        )
        r.raise_for_status()
        return r.json().get("response", [])
    except Exception as e:
        st.warning(f"Could not fetch player data: {e}")
        return []


# ── API-Football built-in predictions  (cache: 1 hour) ────────────────────────
@st.cache_data(ttl=3600, show_spinner="Loading baseline predictions…")
def get_api_predictions(fixture_id: int) -> dict:
    """
    Returns API-Football's own probability estimates.
    We use this as a BASELINE to compare against our own ML model.

    Returns dict with keys: "predictions", "teams", "comparison"
    """
    try:
        r = requests.get(
            f"{RAPIDAPI_BASE}/predictions",
            headers=_headers(),
            params={"fixture": fixture_id},
            timeout=8,
        )
        r.raise_for_status()
        resp = r.json().get("response", [])
        return resp[0] if resp else {}
    except Exception as e:
        st.warning(f"Could not fetch API predictions: {e}")
        return {}


# ── Historical fixtures for model training  (cache: 24 hours) ─────────────────
@st.cache_data(ttl=86400, show_spinner="Loading historical data…")
def get_historical_fixtures(season: int) -> list[dict]:
    """
    Fetches all completed fixtures for a given season.
    Used to build training data for our ML models.
    Cache for 24 hours — historical data never changes.
    """
    try:
        r = requests.get(
            f"{RAPIDAPI_BASE}/fixtures",
            headers=_headers(),
            params={"league": WC2026_LEAGUE_ID, "season": season, "status": "FT"},
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("response", [])
    except Exception as e:
        st.warning(f"Could not fetch historical fixtures (season {season}): {e}")
        return []


# ── Standings / Group table  (cache: 10 minutes) ──────────────────────────────
@st.cache_data(ttl=600, show_spinner="Loading standings…")
def get_standings() -> list[dict]:
    """Returns current WC 2026 group standings."""
    try:
        r = requests.get(
            f"{RAPIDAPI_BASE}/standings",
            headers=_headers(),
            params={"league": WC2026_LEAGUE_ID, "season": WC2026_SEASON},
            timeout=8,
        )
        r.raise_for_status()
        resp = r.json().get("response", [])
        if resp:
            return resp[0]["league"]["standings"]
        return []
    except Exception as e:
        st.warning(f"Could not fetch standings: {e}")
        return []


# ── News  (cache: 15 minutes) ─────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner="Loading news…")
def get_news(query: str = "World Cup 2026", page_size: int = 20) -> list[dict]:
    """
    Returns latest news articles from NewsAPI.
    Cache 15 minutes — news doesn't need to be real-time.

    Example item:
    {
      "title": "Brazil squad announced…",
      "description": "…",
      "url": "https://…",
      "urlToImage": "https://…",
      "publishedAt": "2026-06-10T08:30:00Z",
      "source": {"name": "BBC Sport"}
    }
    """
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q":        query,
                "apiKey":   NEWSAPI_KEY,
                "pageSize": page_size,
                "sortBy":   "publishedAt",
                "language": "en",
            },
            timeout=8,
        )
        r.raise_for_status()
        return r.json().get("articles", [])
    except Exception as e:
        st.warning(f"Could not fetch news: {e}")
        return []
