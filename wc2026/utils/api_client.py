"""
utils/api_client.py
────────────────────
VERIFIED API SOURCES (tested June 6, 2026 before writing this file):

SOURCE 1 — openfootball/worldcup.json (GitHub Raw)
  URL:  https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json
  Test: ✅ HTTP 200, returns valid JSON with all 104 matches
  Key:  None required — plain HTTP GET, no auth header
  Limits: None — static file on GitHub CDN
  Gives us:
    • All 104 fixtures: dates, times (with UTC offset), venues, groups
    • Scores added to the file AFTER each match completes (within hours)
    • Goal scorer names + minute
    • 12 group stage groups + all knockout rounds
  Does NOT give:
    • Real-time in-play scores (updated post-match, not during 90 mins)
    • Player ratings, cards, or individual stats
  Score structure once matches are played:
    {"score": {"ft": [2, 1], "ht": [1, 0]}, "goals1": [...], "goals2": [...]}

SOURCE 2 — worldcup26.ir
  Test: ❌ HTTP 403 on all endpoints — geo-blocked or requires browser
  Decision: DROPPED. Cannot be used from a Python server.

SOURCE 3 — wc2026api.com, balldontlie, ESPN, TheSportsDB, football-data.org
  Test: ❌ All return 403 from server-side Python requests
  Decision: DROPPED.

FINAL ARCHITECTURE:
  openfootball  → fixtures, schedule, results, goal scorers
  Our ML models → match predictions (no external API needed)
  Demo data     → fallback when file is unreachable
  No paid API   → zero rate limits, zero cost, zero key management
"""

import json
import time
import requests
import streamlit as st
from datetime import date, datetime
from typing import Optional

# ── Source URL ─────────────────────────────────────────────────────────────────
OPENFOOTBALL_URL = (
    "https://raw.githubusercontent.com/openfootball/worldcup.json"
    "/master/2026/worldcup.json"
)

# ── Disk cache ─────────────────────────────────────────────────────────────────
import os
_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", ".cache")
os.makedirs(_CACHE_DIR, exist_ok=True)

def _cache_path(key: str) -> str:
    return os.path.join(_CACHE_DIR, f"{key}.json")

def _read_disk_cache(key: str, max_age_s: int) -> Optional[dict]:
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    if time.time() - os.path.getmtime(path) > max_age_s:
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None

def _write_disk_cache(key: str, data) -> None:
    try:
        with open(_cache_path(key), "w") as f:
            json.dump(data, f)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Core fetch — all data comes from one file, parsed into different views
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_all_matches() -> list[dict]:
    """
    Fetch the full WC 2026 match list from openfootball.
    Disk-cached for 5 minutes — the file only changes after a match ends,
    so polling every 5 min is more than sufficient.

    Returns a flat list of match dicts. Each dict has at minimum:
      round, date, time, team1, team2, ground
    Group stage matches also have: group
    Completed matches also have:  score ({"ft":[h,a],"ht":[h,a]}), goals1, goals2

    Returns [] if the network is unreachable and no cache exists.
    """
    cache_key = "openfootball_all_matches"

    # 1. Fresh disk cache (< 5 min old)
    cached = _read_disk_cache(cache_key, max_age_s=300)
    if cached is not None:
        return cached

    # 2. Try the live URL
    try:
        r = requests.get(OPENFOOTBALL_URL, timeout=10)
        r.raise_for_status()
        matches = r.json().get("matches", [])
        _write_disk_cache(cache_key, matches)
        return matches
    except Exception as e:
        st.toast(f"📡 Could not reach openfootball: {e}. Showing cached data.", icon="⚠️")

    # 3. Stale disk cache (any age)
    stale = _read_disk_cache(cache_key, max_age_s=86400 * 30)
    if stale is not None:
        return stale

    # 4. Nothing at all — return demo data
    return _demo_matches()


# ══════════════════════════════════════════════════════════════════════════════
# Public functions — each filters the master list differently
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_todays_fixtures() -> list[dict]:
    """
    Today's matches in normalised dict format compatible with fixtures_to_df().

    Fields returned per match:
      fixture_id, date, status, elapsed,
      home_team, away_team, home_goals, away_goals,
      venue_city, round, group
    """
    today   = date.today().isoformat()
    matches = _fetch_all_matches()
    todays  = [m for m in matches if m.get("date") == today]
    return [_normalise(m) for m in todays]


@st.cache_data(ttl=300, show_spinner=False)
def get_live_fixtures() -> list[dict]:
    """
    'Live' fixtures = today's matches that have a score already in the file.
    openfootball is not real-time during a match, but scores appear within
    a few hours of full time. This is the best we can do without a paid API.
    """
    today   = date.today().isoformat()
    matches = _fetch_all_matches()
    live    = [m for m in matches
               if m.get("date") == today and "score" in m]
    return [_normalise(m) for m in live]


@st.cache_data(ttl=300, show_spinner=False)
def get_all_fixtures() -> list[dict]:
    """All 104 fixtures, normalised. Used for the full schedule view."""
    return [_normalise(m) for m in _fetch_all_matches()]


@st.cache_data(ttl=300, show_spinner=False)
def get_completed_fixtures() -> list[dict]:
    """Fixtures that have a final score — used for standings calculation."""
    return [_normalise(m) for m in _fetch_all_matches() if "score" in m]


@st.cache_data(ttl=300, show_spinner=False)
def get_standings() -> list[dict]:
    """
    Build group standings from completed match results in the openfootball file.

    Returns a list of groups, each a list of team dicts:
    [
      [{"team": "Mexico", "played": 1, "won": 1, "drawn": 0, "lost": 0,
        "gf": 2, "ga": 0, "gd": 2, "points": 3}, ...],
      ...
    ]
    Returns [] if no matches have been played yet.
    """
    matches = _fetch_all_matches()
    completed = [m for m in matches if "score" in m and "group" in m]
    if not completed:
        return []

    # Aggregate per team per group
    table: dict[str, dict[str, dict]] = {}  # group → team → stats

    for m in completed:
        group  = m["group"]
        home   = m["team1"]
        away   = m["team2"]
        score  = m["score"]
        # Use "ft" (full time). Falls back to first available key.
        result = score.get("ft") or score.get("et") or [0, 0]
        hg, ag = result[0], result[1]

        table.setdefault(group, {})
        for team in [home, away]:
            table[group].setdefault(team, {
                "team": team, "played": 0, "won": 0, "drawn": 0,
                "lost": 0, "gf": 0, "ga": 0, "gd": 0, "points": 0,
            })

        h = table[group][home]
        a = table[group][away]

        h["played"] += 1; h["gf"] += hg; h["ga"] += ag
        a["played"] += 1; a["gf"] += ag; a["ga"] += hg

        if hg > ag:
            h["won"] += 1;   h["points"] += 3
            a["lost"] += 1
        elif ag > hg:
            a["won"] += 1;   a["points"] += 3
            h["lost"] += 1
        else:
            h["drawn"] += 1; h["points"] += 1
            a["drawn"] += 1; a["points"] += 1

    for group in table:
        for team in table[group]:
            table[group][team]["gd"] = (
                table[group][team]["gf"] - table[group][team]["ga"]
            )

    # Sort each group: points → gd → gf
    return [
        sorted(teams.values(),
               key=lambda t: (-t["points"], -t["gd"], -t["gf"]))
        for group, teams in sorted(table.items())
    ]


@st.cache_data(ttl=300, show_spinner=False)
def get_goal_scorers() -> list[dict]:
    """
    Top scorers from completed matches.
    Returns list of {"player": str, "team": str, "goals": int, "penalties": int}
    sorted by goals descending.
    """
    matches   = _fetch_all_matches()
    completed = [m for m in matches if "goals1" in m or "goals2" in m]
    scorers: dict[str, dict] = {}

    for m in completed:
        home = m.get("team1", "")
        away = m.get("team2", "")
        for goal in m.get("goals1", []):
            name = goal.get("name", "Unknown")
            scorers.setdefault(name, {"player": name, "team": home, "goals": 0, "penalties": 0})
            scorers[name]["goals"] += 1
            if goal.get("penalty"):
                scorers[name]["penalties"] += 1
        for goal in m.get("goals2", []):
            name = goal.get("name", "Unknown")
            scorers.setdefault(name, {"player": name, "team": away, "goals": 0, "penalties": 0})
            scorers[name]["goals"] += 1
            if goal.get("penalty"):
                scorers[name]["penalties"] += 1

    return sorted(scorers.values(), key=lambda s: -s["goals"])


# ══════════════════════════════════════════════════════════════════════════════
# Helper: normalise openfootball match → our standard format
# ══════════════════════════════════════════════════════════════════════════════

def _normalise(m: dict) -> dict:
    """
    Convert an openfootball match dict into the format that
    fixtures_to_df() and the pages expect.

    openfootball field → our field:
      team1       → home_team
      team2       → away_team
      ground      → venue_city
      score.ft[0] → home_goals
      score.ft[1] → away_goals
      round       → round (kept as-is)
      group       → group (kept, absent for knockout)
    """
    score  = m.get("score", {})
    ft     = score.get("ft")          # [home, away] or None
    ht     = score.get("ht")
    is_et  = "et" in score            # extra time was played
    is_pen = "p"  in score            # went to penalties

    # Status derivation:
    # openfootball has no "in-play" concept — match is either scheduled or finished
    if ft is not None:
        if is_pen:
            status = "Penalties"
        elif is_et:
            status = "AET"
        else:
            status = "Match Finished"
    else:
        status = "Not Started"

    # Parse kick-off time (stored as "13:00 UTC-6" or "13:00")
    raw_time = m.get("time", "")
    kickoff_display = raw_time.split(" ")[0] if raw_time else ""

    return {
        "fixture_id":   m.get("num", hash(f"{m.get('date')}{m.get('team1')}{m.get('team2')}")),
        "date":         m.get("date", ""),
        "kickoff":      kickoff_display,
        "timezone":     raw_time.split(" ")[1] if " " in raw_time else "UTC",
        "round":        m.get("round", ""),
        "group":        m.get("group", ""),          # empty string for knockout
        "status":       status,
        "elapsed":      None,                        # openfootball has no in-play data
        "home_team":    m.get("team1", "TBD"),
        "away_team":    m.get("team2", "TBD"),
        "home_goals":   ft[0] if ft else None,
        "away_goals":   ft[1] if ft else None,
        "ht_home":      ht[0] if ht else None,
        "ht_away":      ht[1] if ht else None,
        "venue_city":   m.get("ground", ""),
        "goals1":       m.get("goals1", []),         # list of {name, minute, penalty?}
        "goals2":       m.get("goals2", []),
        "source":       "openfootball",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Demo data — shown when the network is completely unreachable
# ══════════════════════════════════════════════════════════════════════════════

def _demo_matches() -> list[dict]:
    """
    Minimal realistic fallback — first 6 group stage matches.
    Only used when GitHub raw is unreachable AND no disk cache exists.
    These are real WC 2026 group A & B fixtures from the official schedule.
    """
    return [
        {"round": "Matchday 1", "date": "2026-06-11", "time": "13:00 UTC-6",
         "team1": "Mexico",      "team2": "South Africa",  "group": "Group A", "ground": "Mexico City"},
        {"round": "Matchday 1", "date": "2026-06-11", "time": "20:00 UTC-6",
         "team1": "South Korea", "team2": "Czech Republic", "group": "Group A", "ground": "Guadalajara (Zapopan)"},
        {"round": "Matchday 2", "date": "2026-06-12", "time": "15:00 UTC-4",
         "team1": "Canada",      "team2": "Portugal",       "group": "Group B", "ground": "Toronto"},
        {"round": "Matchday 3", "date": "2026-06-13", "time": "12:00 UTC-7",
         "team1": "Qatar",       "team2": "Switzerland",    "group": "Group B", "ground": "San Francisco Bay Area (Santa Clara)"},
        {"round": "Matchday 4", "date": "2026-06-13", "time": "15:00 UTC-4",
         "team1": "USA",         "team2": "Brazil",         "group": "Group C", "ground": "New York / New Jersey"},
        {"round": "Matchday 5", "date": "2026-06-14", "time": "18:00 UTC-4",
         "team1": "Argentina",   "team2": "France",         "group": "Group D", "ground": "Miami"},
    ]


# ══════════════════════════════════════════════════════════════════════════════
# Stub: player stats (no free source available — see notes)
# ══════════════════════════════════════════════════════════════════════════════

def get_fixture_players(fixture_id: int) -> list[dict]:
    """
    Player-level data (ratings, cards, passes) requires a paid API.
    No free source tested was accessible from server-side Python.
    Returns empty list — the player ratings page uses ML model predictions instead.
    """
    return []


def get_news(query: str = "World Cup 2026", page_size: int = 20) -> list[dict]:
    """
    NewsAPI requires a key. Returns placeholder articles when key not set.
    Add NEWSAPI_KEY to .streamlit/secrets.toml to enable real news.
    """
    try:
        newsapi_key = os.getenv("NEWSAPI_KEY") or st.secrets.get("NEWSAPI_KEY", "")
    except Exception:
        newsapi_key = os.getenv("NEWSAPI_KEY", "")

    if not newsapi_key or newsapi_key == "YOUR_KEY_HERE":
        return _demo_news()

    cache_key = f"news_{query.replace(' ', '_')}_{page_size}"
    cached    = _read_disk_cache(cache_key, max_age_s=900)
    if cached is not None:
        return cached

    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={"q": query, "apiKey": newsapi_key,
                    "pageSize": page_size, "sortBy": "publishedAt", "language": "en"},
            timeout=8,
        )
        if r.status_code == 429:
            st.toast("⏳ NewsAPI rate limit. Showing demo news.", icon="⏳")
            return _read_disk_cache(cache_key, max_age_s=86400) or _demo_news()
        r.raise_for_status()
        result = r.json().get("articles", [])
        _write_disk_cache(cache_key, result)
        return result
    except Exception:
        return _read_disk_cache(cache_key, max_age_s=86400) or _demo_news()


def _demo_news() -> list[dict]:
    return [
        {"title": "FIFA World Cup 2026 kicks off June 11 — everything you need to know",
         "description": "The biggest World Cup ever — 48 teams, 104 matches, 16 cities across USA, Canada and Mexico.",
         "url": "https://github.com/openfootball/worldcup.json",
         "urlToImage": None,
         "publishedAt": datetime.utcnow().isoformat() + "Z",
         "source": {"name": "Add your NEWSAPI_KEY to secrets.toml for live news"}},
        {"title": "Group stage fixtures: all 72 group matches at a glance",
         "description": "From Mexico vs South Africa on June 11 to the final group games on June 24.",
         "url": "https://github.com/openfootball/worldcup.json",
         "urlToImage": None,
         "publishedAt": datetime.utcnow().isoformat() + "Z",
         "source": {"name": "Data: openfootball/worldcup.json (free, no key)"}},
    ]
