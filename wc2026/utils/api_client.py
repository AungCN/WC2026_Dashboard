"""
utils/api_client.py
────────────────────
Three-layer data strategy:

  LAYER 1 — Static data (data/wc2026_data.py)
    All 104 fixtures with CORRECT confirmed team names.
    Groups, squads, stadiums, referees — always available, zero latency.

  LAYER 2 — openfootball live JSON (GitHub raw)
    Merges SCORES and GOAL SCORERS into our static fixtures as matches
    are played. No key, no rate limit. Updated post-match (within hours).

  LAYER 3 — RSS news feeds
    Free football news from BBC/Guardian/ESPN/Goal/Google News.
    No API key. Falls back gracefully if any feed is blocked.
"""

import json, time, os, requests
import streamlit as st
import feedparser
from datetime import date, datetime
from typing import Optional

# ── Import static data ─────────────────────────────────────────────────────────
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.wc2026_data import (
    ALL_FIXTURES, GROUP_FIXTURES, KNOCKOUT_FIXTURES,
    GROUPS, TEAM_TO_GROUP, SQUADS, STADIUMS, STADIUM_BY_CITY,
    REFEREES, RSS_FEEDS, FIFA_RANKINGS, TEAM_FLAGS,
)

# ── Disk cache ─────────────────────────────────────────────────────────────────
_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", ".cache")
os.makedirs(_CACHE_DIR, exist_ok=True)

def _cache_path(key: str) -> str:
    safe = key.replace("/","_").replace("?","_").replace("&","_").replace(" ","_")
    return os.path.join(_CACHE_DIR, f"{safe}.json")

def _read_cache(key: str, max_age_s: int) -> Optional[list]:
    p = _cache_path(key)
    if not os.path.exists(p): return None
    if time.time() - os.path.getmtime(p) > max_age_s: return None
    try:
        with open(p) as f: return json.load(f)
    except: return None

def _write_cache(key: str, data) -> None:
    try:
        with open(_cache_path(key), "w") as f: json.dump(data, f, ensure_ascii=False)
    except: pass


# ══════════════════════════════════════════════════════════════════════════════
# Live score merge — openfootball JSON overlaid on static fixtures
# ══════════════════════════════════════════════════════════════════════════════

OPENFOOTBALL_URL = (
    "https://raw.githubusercontent.com/openfootball/worldcup.json"
    "/master/2026/worldcup.json"
)

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_live_scores() -> dict:
    """
    Fetch the openfootball JSON and return a dict keyed by (team1, team2)
    containing score and goal data for completed matches.
    Only fetches when cache is stale (5-min disk TTL).
    """
    cache_key = "openfootball_scores"
    cached = _read_cache(cache_key, max_age_s=300)
    if cached is not None:
        return {tuple(k): v for k, v in cached}

    try:
        r = requests.get(OPENFOOTBALL_URL, timeout=10)
        r.raise_for_status()
        matches = r.json().get("matches", [])
        scores = {}
        for m in matches:
            if "score" in m:
                key = (m["team1"], m["team2"])
                scores[key] = {
                    "score":  m["score"],
                    "goals1": m.get("goals1", []),
                    "goals2": m.get("goals2", []),
                }
        serialisable = [[list(k), v] for k, v in scores.items()]
        _write_cache(cache_key, serialisable)
        return scores
    except Exception as e:
        st.toast(f"📡 Live scores unavailable: {e}", icon="⚠️")
        stale = _read_cache(cache_key, max_age_s=86400 * 30)
        if stale:
            return {tuple(k): v for k, v in stale}
        return {}


def _enrich(fixture: dict, scores: dict) -> dict:
    """
    Merge live score data from openfootball into a static fixture dict.
    Returns the fixture with status, goals, and scorers added.
    """
    key = (fixture["team1"], fixture["team2"])
    live = scores.get(key)

    raw_time = fixture.get("time", "")
    kickoff  = raw_time.split(" ")[0] if raw_time else ""
    tz       = raw_time.split(" ")[1] if " " in raw_time else "UTC"

    if live:
        score  = live["score"]
        ft     = score.get("ft")
        ht     = score.get("ht")
        is_pen = "p" in score
        is_et  = "et" in score
        status = "Penalties" if is_pen else ("AET" if is_et else "Match Finished")
    else:
        ft, ht, status = None, None, "Not Started"

    # Venue → stadium info
    ground  = fixture.get("ground", "")
    stadium = STADIUM_BY_CITY.get(ground, {})

    return {
        "fixture_id":  fixture.get("num", 0),
        "date":        fixture["date"],
        "kickoff":     kickoff,
        "timezone":    tz,
        "round":       fixture.get("round", fixture.get("group", "")),
        "group":       fixture.get("group", ""),
        "status":      status,
        "elapsed":     None,
        "home_team":   fixture["team1"],
        "away_team":   fixture["team2"],
        "home_goals":  ft[0] if ft else None,
        "away_goals":  ft[1] if ft else None,
        "ht_home":     ht[0] if ht else None,
        "ht_away":     ht[1] if ht else None,
        "venue_city":  ground,
        "stadium":     stadium.get("stadium", ""),
        "capacity":    stadium.get("capacity"),
        "goals1":      live["goals1"] if live else [],
        "goals2":      live["goals2"] if live else [],
        "source":      "openfootball+static",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Public fixture functions
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_all_fixtures() -> list[dict]:
    """All 104 fixtures enriched with live scores where available."""
    scores = _fetch_live_scores()
    return [_enrich(f, scores) for f in ALL_FIXTURES]

@st.cache_data(ttl=300, show_spinner=False)
def get_todays_fixtures() -> list[dict]:
    """Today's fixtures enriched with live scores."""
    today  = date.today().isoformat()
    scores = _fetch_live_scores()
    return [_enrich(f, scores) for f in ALL_FIXTURES if f["date"] == today]

@st.cache_data(ttl=300, show_spinner=False)
def get_live_fixtures() -> list[dict]:
    """Fixtures with a score (completed today). openfootball is post-match only."""
    today  = date.today().isoformat()
    scores = _fetch_live_scores()
    return [_enrich(f, scores) for f in ALL_FIXTURES
            if f["date"] == today and (f["team1"], f["team2"]) in scores]

@st.cache_data(ttl=300, show_spinner=False)
def get_completed_fixtures() -> list[dict]:
    """All fixtures that have a final score."""
    scores = _fetch_live_scores()
    return [_enrich(f, scores) for f in ALL_FIXTURES
            if (f["team1"], f["team2"]) in scores]

@st.cache_data(ttl=300, show_spinner=False)
def get_upcoming_fixtures(n: int = 10) -> list[dict]:
    """Next N upcoming fixtures (no score yet), sorted by date."""
    today  = date.today().isoformat()
    scores = _fetch_live_scores()
    upcoming = [f for f in ALL_FIXTURES
                if f["date"] >= today and (f["team1"], f["team2"]) not in scores]
    return [_enrich(f, scores) for f in upcoming[:n]]

@st.cache_data(ttl=300, show_spinner=False)
def get_standings() -> list[dict]:
    """
    Group standings computed from completed match results.
    Each group is a sorted list of team dicts.
    Returns [] until matches have been played.
    """
    completed = [f for f in ALL_FIXTURES
                 if "group" in f and (f["team1"], f["team2"]) in _fetch_live_scores()]
    if not completed:
        return []

    scores = _fetch_live_scores()
    table: dict[str, dict[str, dict]] = {}

    for f in completed:
        g    = f["group"]
        home = f["team1"]
        away = f["team2"]
        live = scores[(home, away)]
        ft   = live["score"].get("ft") or [0, 0]
        hg, ag = ft[0], ft[1]

        table.setdefault(g, {})
        for team in [home, away]:
            table[g].setdefault(team, dict(
                team=team, played=0, won=0, drawn=0, lost=0,
                gf=0, ga=0, gd=0, points=0
            ))

        h = table[g][home]; a = table[g][away]
        h["played"] += 1; h["gf"] += hg; h["ga"] += ag
        a["played"] += 1; a["gf"] += ag; a["ga"] += hg

        if   hg > ag: h["won"]   += 1; h["points"] += 3; a["lost"]  += 1
        elif ag > hg: a["won"]   += 1; a["points"] += 3; h["lost"]  += 1
        else:         h["drawn"] += 1; h["points"] += 1; a["drawn"] += 1

    for g in table:
        for t in table[g]:
            table[g][t]["gd"] = table[g][t]["gf"] - table[g][t]["ga"]

    return [
        sorted(teams.values(), key=lambda t: (-t["points"], -t["gd"], -t["gf"]))
        for _, teams in sorted(table.items())
    ]

@st.cache_data(ttl=300, show_spinner=False)
def get_goal_scorers() -> list[dict]:
    """Top scorers from openfootball completed match data."""
    scores = _fetch_live_scores()
    tally: dict[str, dict] = {}
    for (home, away), live in scores.items():
        for goal in live.get("goals1", []):
            name = goal.get("name", "Unknown")
            tally.setdefault(name, {"player":name,"team":home,"goals":0,"penalties":0})
            tally[name]["goals"] += 1
            if goal.get("penalty"): tally[name]["penalties"] += 1
        for goal in live.get("goals2", []):
            name = goal.get("name", "Unknown")
            tally.setdefault(name, {"player":name,"team":away,"goals":0,"penalties":0})
            tally[name]["goals"] += 1
            if goal.get("penalty"): tally[name]["penalties"] += 1
    return sorted(tally.values(), key=lambda s: -s["goals"])


# ══════════════════════════════════════════════════════════════════════════════
# Squad helpers
# ══════════════════════════════════════════════════════════════════════════════

def get_squad(team: str) -> list[dict]:
    """Full squad for a team as list of dicts {number, name, position}."""
    raw = SQUADS.get(team, [])
    return [{"number": r[0], "name": r[1], "position": r[2]} for r in raw]

def get_all_teams() -> list[str]:
    """All 48 confirmed WC 2026 teams, sorted."""
    return sorted(TEAM_TO_GROUP.keys())


# ══════════════════════════════════════════════════════════════════════════════
# News — RSS feeds (free, no key)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=900, show_spinner=False)
def get_news(max_items: int = 20) -> list[dict]:
    """
    Fetch World Cup news from free RSS feeds.
    Tries each feed in priority order, merges results, deduplicates by title.
    Falls back to demo articles if all feeds fail.

    Works on the user's machine (standard Python environment).
    May be blocked in some server/sandbox environments.
    """
    cache_key = f"rss_news_{max_items}"
    cached = _read_cache(cache_key, max_age_s=900)
    if cached:
        return cached

    articles = []
    seen_titles: set[str] = set()

    for feed in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed["url"])
            for entry in parsed.entries[:10]:
                title = entry.get("title", "").strip()
                if not title or title in seen_titles:
                    continue
                # Filter for WC 2026 relevance
                combined = (title + entry.get("summary", "")).lower()
                if not any(kw in combined for kw in [
                    "world cup","worldcup","fifa","2026","messi","mbappe",
                    "ronaldo","soccer","football"
                ]):
                    continue
                seen_titles.add(title)
                articles.append({
                    "title":       title,
                    "description": entry.get("summary", "")[:300],
                    "url":         entry.get("link", "#"),
                    "urlToImage":  None,
                    "publishedAt": entry.get("published", datetime.utcnow().isoformat()),
                    "source":      {"name": feed["name"]},
                })
                if len(articles) >= max_items:
                    break
        except Exception:
            continue
        if len(articles) >= max_items:
            break

    if articles:
        _write_cache(cache_key, articles)
        return articles

    # All feeds failed — return demo articles
    return _demo_news()


def _demo_news() -> list[dict]:
    now = datetime.utcnow().isoformat() + "Z"
    return [
        {"title":"FIFA World Cup 2026 kicks off June 11 — everything you need to know",
         "description":"48 teams, 104 matches, 16 cities across USA, Canada and Mexico. The biggest World Cup ever.",
         "url":"https://wcup2026.org","urlToImage":None,"publishedAt":now,
         "source":{"name":"Install feedparser: pip install feedparser"}},
        {"title":"Group stage draw complete — see all 12 groups",
         "description":"Argentina, France, Brazil headline their respective groups in what promises to be the most competitive World Cup ever.",
         "url":"https://wcup2026.org/groups.php","urlToImage":None,"publishedAt":now,
         "source":{"name":"Data: openfootball/worldcup.json"}},
        {"title":"All 16 host stadiums: from Azteca to MetLife",
         "description":"The tournament spans 16 venues across three countries, with MetLife Stadium hosting the Final on July 19.",
         "url":"https://wcup2026.org/stadiums.php","urlToImage":None,"publishedAt":now,
         "source":{"name":"Source: wcup2026.org"}},
    ]


# ══════════════════════════════════════════════════════════════════════════════
# Stub kept for compatibility
# ══════════════════════════════════════════════════════════════════════════════

def get_fixture_players(fixture_id: int) -> list[dict]:
    """No free player-stats API available. Returns []. Ratings use ML model."""
    return []
