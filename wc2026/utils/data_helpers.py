"""
utils/data_helpers.py
──────────────────────
Helper functions used by ML models and pages.

NOTE: fixtures_to_df() now accepts the normalised dicts from api_client.py
directly — no raw API parsing needed since openfootball data is already clean.
"""

import math
import pandas as pd
import numpy as np
from datetime import datetime


# ── Venue coordinates (all 16 WC 2026 host cities) ────────────────────────────
VENUE_COORDS: dict[str, tuple[float, float]] = {
    "New York / New Jersey":              (40.8128,  -74.0742),
    "Los Angeles (Inglewood)":            (34.0141, -118.2879),
    "Dallas":                             (32.7480,  -97.0930),
    "San Francisco Bay Area (Santa Clara)":(37.4032, -121.9700),
    "Miami":                              (25.9580,  -80.2389),
    "Seattle":                            (47.5952, -122.3316),
    "Boston":                             (42.0910,  -71.0640),
    "Atlanta":                            (33.7554,  -84.4008),
    "Kansas City":                        (39.0489,  -94.4839),
    "Houston":                            (29.6847,  -95.4107),
    "Philadelphia":                       (39.9008,  -75.1675),
    "Vancouver":                          (49.2767, -123.1130),
    "Toronto":                            (43.7315,  -79.5685),
    "Guadalajara (Zapopan)":              (20.6721, -103.3106),
    "Mexico City":                        (19.3029,  -99.1505),
    "Monterrey (Guadalupe)":              (25.6694, -100.3118),
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance between two GPS coordinates in km."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def travel_fatigue_score(venue_from: str, venue_to: str, days_between: int) -> float:
    """
    Returns a fatigue score 0.0 (no fatigue) → 1.0 (maximum).
    Used as a feature in the match prediction model.
    """
    c1 = VENUE_COORDS.get(venue_from)
    c2 = VENUE_COORDS.get(venue_to)
    if not c1 or not c2:
        return 0.0
    dist = haversine_km(*c1, *c2)
    base = 0.05 if dist < 500 else (
        0.05 + (dist - 500) / 1000 * 0.35 if dist < 1500
        else 0.40 + min((dist - 1500) / 3000, 0.60)
    )
    recovery = max(0, days_between - 3)
    return round(min(base * (0.9 ** recovery), 1.0), 3)


def fixtures_to_df(normalised_fixtures: list[dict]) -> pd.DataFrame:
    """
    Convert a list of normalised fixture dicts (from api_client.py)
    into a flat DataFrame.

    Accepts the output of get_todays_fixtures(), get_all_fixtures(), etc.
    All fields are already clean — no raw API parsing needed.
    """
    if not normalised_fixtures:
        return pd.DataFrame(columns=[
            "fixture_id", "date", "kickoff", "round", "group", "status",
            "elapsed", "home_team", "away_team", "home_goals", "away_goals",
            "venue_city",
        ])
    return pd.DataFrame(normalised_fixtures)


def build_match_features(fixture: dict, team_stats: dict) -> dict:
    """
    Build one row of ML training features from a completed fixture.
    Used by models/train_models.py.

    Args:
        fixture:    Normalised fixture dict (from _normalise() in api_client.py)
        team_stats: Pre-aggregated stats per team {name: {ranking, xg, fatigue, h2h_winrate}}
    """
    home  = fixture.get("home_team", "")
    away  = fixture.get("away_team", "")
    hg    = fixture.get("home_goals") or 0
    ag    = fixture.get("away_goals") or 0
    round_str = fixture.get("round", "").lower()

    if   hg > ag: result = 2
    elif hg < ag: result = 0
    else:         result = 1

    is_knockout = int(any(
        k in round_str for k in ["round of", "quarter", "semi", "final"]
    ))

    hs = team_stats.get(home, {})
    as_ = team_stats.get(away, {})

    return {
        "home_ranking_diff":   hs.get("ranking", 50) - as_.get("ranking", 50),
        "home_xg":             hs.get("xg", 1.2),
        "away_xg":             as_.get("xg", 1.2),
        "travel_fatigue_home": hs.get("fatigue", 0.0),
        "travel_fatigue_away": as_.get("fatigue", 0.0),
        "is_knockout":         is_knockout,
        "h2h_home_winrate":    hs.get("h2h_winrate", 0.5),
        "result":              result,
    }
