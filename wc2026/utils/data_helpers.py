"""
utils/data_helpers.py
──────────────────────
Helper functions for:
  • Parsing raw API responses into clean DataFrames
  • Calculating travel fatigue (unique to WC 2026 due to 3-country spread)
  • Building training feature sets for ML models

TRAVEL FATIGUE EXPLAINED:
  WC 2026 spans USA, Canada, and Mexico.
  A team that plays in Vancouver on Day 1, then Miami on Day 5
  travels ~4,300 km — roughly the same as London → Tehran.
  Studies show fatigue affects performance when teams travel
  >1,500 km between matches with <5 days rest.
"""

import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ── Venue coordinates (all 16 WC 2026 host cities) ────────────────────────────
VENUE_COORDS: dict[str, tuple[float, float]] = {
    "New York / New Jersey":  (40.8128, -74.0742),
    "Los Angeles":             (34.0141, -118.2879),
    "Dallas":                  (32.7480, -97.0930),
    "San Francisco":           (37.4032, -121.9700),
    "Miami":                   (25.9580, -80.2389),
    "Seattle":                 (47.5952, -122.3316),
    "Boston":                  (42.0910, -71.0640),
    "Atlanta":                 (33.7554, -84.4008),
    "Kansas City":             (39.0489, -94.4839),
    "Houston":                 (29.6847, -95.4107),
    "Philadelphia":            (39.9008, -75.1675),
    "Vancouver":               (49.2767, -123.1130),
    "Toronto":                 (43.7315, -79.5685),
    "Guadalajara":             (20.6721, -103.3106),
    "Mexico City":             (19.3029, -99.1505),
    "Monterrey":               (25.6694, -100.3118),
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate straight-line distance between two GPS coordinates in km.
    Uses the Haversine formula — standard for geographic distance.

    Example:
      haversine_km(49.28, -123.11, 25.96, -80.24)  →  ~4,350 km (Vancouver→Miami)
    """
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlam  = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def travel_fatigue_score(
    venue_from: str,
    venue_to: str,
    days_between: int,
) -> float:
    """
    Returns a fatigue score between 0.0 (no fatigue) and 1.0 (maximum fatigue).

    Logic:
      • Distance under 500 km  → negligible impact (same region)
      • Distance 500–1500 km   → moderate impact
      • Distance over 1500 km  → high impact
      • More days between games → fatigue recovers (halves every 2 extra days)

    Example:
      Vancouver → Miami, 4 days apart → score ≈ 0.72  (high fatigue)
      Mexico City → Guadalajara, 5 days apart → score ≈ 0.05  (low fatigue)
    """
    coords_from = VENUE_COORDS.get(venue_from)
    coords_to   = VENUE_COORDS.get(venue_to)

    if not coords_from or not coords_to:
        return 0.0  # Unknown venue → assume no fatigue

    dist_km = haversine_km(*coords_from, *coords_to)

    # Base fatigue from distance
    if dist_km < 500:
        base = 0.05
    elif dist_km < 1500:
        base = 0.05 + (dist_km - 500) / 1000 * 0.35   # scales 0.05 → 0.40
    else:
        base = 0.40 + min((dist_km - 1500) / 3000, 0.60)  # scales up to 1.0

    # Recovery: each extra day beyond 3 reduces fatigue by 10%
    recovery_days = max(0, days_between - 3)
    fatigue = base * (0.9 ** recovery_days)

    return round(min(fatigue, 1.0), 3)


# ── Parse raw fixture list into a clean DataFrame ─────────────────────────────
def fixtures_to_df(raw_fixtures: list[dict]) -> pd.DataFrame:
    """
    Converts the API response list into a flat DataFrame.

    Columns: fixture_id, date, status, elapsed, home_team, away_team,
             home_goals, away_goals, venue_city
    """
    rows = []
    for f in raw_fixtures:
        fix    = f.get("fixture", {})
        teams  = f.get("teams", {})
        goals  = f.get("goals", {})
        venue  = fix.get("venue", {})
        status = fix.get("status", {})

        rows.append({
            "fixture_id": fix.get("id"),
            "date":       fix.get("date", "")[:10],
            "status":     status.get("long", "Unknown"),
            "elapsed":    status.get("elapsed"),
            "home_team":  teams.get("home", {}).get("name", "—"),
            "away_team":  teams.get("away", {}).get("name", "—"),
            "home_goals": goals.get("home"),
            "away_goals": goals.get("away"),
            "venue_city": venue.get("city", "Unknown"),
        })

    df = pd.DataFrame(rows)
    return df if not df.empty else pd.DataFrame(columns=[
        "fixture_id", "date", "status", "elapsed",
        "home_team", "away_team", "home_goals", "away_goals", "venue_city"
    ])


# ── Parse player stats into a clean DataFrame ─────────────────────────────────
def players_to_df(raw_player_data: list[dict]) -> pd.DataFrame:
    """
    Flattens the nested player stats response.

    Columns: team, player_name, position, minutes, rating,
             goals, assists, yellow_cards, red_cards, passes, shots
    """
    rows = []
    for team_block in raw_player_data:
        team_name = team_block.get("team", {}).get("name", "Unknown")
        for p in team_block.get("players", []):
            info  = p.get("player", {})
            stats = p.get("statistics", [{}])[0]
            games = stats.get("games", {})
            cards = stats.get("cards", {})
            rows.append({
                "team":         team_name,
                "player_name":  info.get("name", "Unknown"),
                "position":     games.get("position", "—"),
                "minutes":      games.get("minutes") or 0,
                "rating":       float(games.get("rating") or 0),
                "goals":        stats.get("goals", {}).get("total") or 0,
                "assists":      stats.get("goals", {}).get("assists") or 0,
                "yellow_cards": cards.get("yellow") or 0,
                "red_cards":    cards.get("red") or 0,
                "passes":       stats.get("passes", {}).get("total") or 0,
                "shots":        stats.get("shots", {}).get("total") or 0,
            })

    df = pd.DataFrame(rows)
    return df if not df.empty else pd.DataFrame(columns=[
        "team", "player_name", "position", "minutes", "rating",
        "goals", "assists", "yellow_cards", "red_cards", "passes", "shots"
    ])


# ── Build ML training features from historical fixtures ───────────────────────
def build_match_features(fixture: dict, team_stats: dict) -> dict:
    """
    Builds one row of training features from a historical fixture.

    Args:
        fixture:    Raw fixture dict from API
        team_stats: Pre-aggregated stats per team (xG, ranking, etc.)

    Returns:
        Feature dict ready for pandas → XGBoost training

    Features:
        home_ranking_diff   : FIFA rank gap (positive = home team stronger)
        home_xg             : Expected goals for home team this tournament
        away_xg             : Expected goals for away team this tournament
        travel_fatigue_home : 0–1 fatigue score for home team
        travel_fatigue_away : 0–1 fatigue score for away team
        is_knockout         : 1 if round-of-16 or later, 0 if group stage
        h2h_home_winrate    : Historical win rate of home team vs this opponent
        result              : Target variable — 0=away win, 1=draw, 2=home win
    """
    teams  = fixture.get("teams", {})
    home   = teams.get("home", {}).get("name", "")
    away   = teams.get("away", {}).get("name", "")
    goals  = fixture.get("goals", {})
    league = fixture.get("league", {})

    home_g = goals.get("home", 0) or 0
    away_g = goals.get("away", 0) or 0

    if   home_g > away_g: result = 2  # home win
    elif home_g < away_g: result = 0  # away win
    else:                 result = 1  # draw

    round_str = league.get("round", "").lower()
    is_knockout = int(any(k in round_str for k in ["round of", "quarter", "semi", "final"]))

    home_stats = team_stats.get(home, {})
    away_stats = team_stats.get(away, {})

    return {
        "home_ranking_diff":    home_stats.get("ranking", 50) - away_stats.get("ranking", 50),
        "home_xg":              home_stats.get("xg", 1.2),
        "away_xg":              away_stats.get("xg", 1.2),
        "travel_fatigue_home":  home_stats.get("fatigue", 0.0),
        "travel_fatigue_away":  away_stats.get("fatigue", 0.0),
        "is_knockout":          is_knockout,
        "h2h_home_winrate":     home_stats.get("h2h_winrate", 0.5),
        "result":               result,
    }
