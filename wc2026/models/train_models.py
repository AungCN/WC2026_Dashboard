"""
models/train_models.py
───────────────────────
Run this script ONCE to train all three ML models on historical data.
After training, the models are saved to models/saved/ as .joblib files.
The Streamlit app then loads these saved models (no retraining needed).

HOW TO RUN:
    python models/train_models.py

WHAT HAPPENS:
    1. Fetches historical WC fixtures (2018, 2022) from API-Football
    2. Builds training DataFrames
    3. Trains MatchPredictor (XGBoost)
    4. Trains PlayerRatingPredictor (Random Forest)
    5. Saves models to models/saved/
    6. Prints accuracy scores

NOTE:
    CardPredictor (Negative Binomial) requires referee-level data
    not available in API-Football's basic plan.
    We include a mock dataset so you can test the training pipeline.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
from utils.api_client import get_historical_fixtures
from utils.data_helpers import build_match_features
from models.prediction_engine import MatchPredictor, CardPredictor, PlayerRatingPredictor


# ── Step 1: Fetch historical fixture data ─────────────────────────────────────
def fetch_training_data() -> pd.DataFrame:
    """
    Fetch WC 2018 and WC 2022 completed fixtures as training data.
    These are the two most recent tournaments with full data in API-Football.
    """
    print("Fetching WC 2022 historical fixtures…")
    fixtures_2022 = get_historical_fixtures(2022)

    print("Fetching WC 2018 historical fixtures…")
    fixtures_2018 = get_historical_fixtures(2018)

    all_fixtures = fixtures_2022 + fixtures_2018
    print(f"Total fixtures fetched: {len(all_fixtures)}")
    return all_fixtures


# ── Step 2: Build match feature DataFrame ─────────────────────────────────────
def build_match_training_df(raw_fixtures: list[dict]) -> pd.DataFrame:
    """
    Convert raw fixtures into one row per match with all ML features.

    We use PLACEHOLDER team stats here — in production you would
    enrich this with real FIFA rankings, xG data, and H2H records
    from a database or additional API calls.
    """
    # Mock team stats (replace with real data in production)
    # Format: team_name → {ranking, xg, fatigue, h2h_winrate}
    mock_team_stats = {team: {
        "ranking":     np.random.randint(1, 100),
        "xg":          round(np.random.uniform(0.8, 2.5), 2),
        "fatigue":     round(np.random.uniform(0.0, 0.5), 2),
        "h2h_winrate": round(np.random.uniform(0.3, 0.7), 2),
    } for team in [
        "Brazil", "France", "Argentina", "England", "Germany", "Spain",
        "Portugal", "Netherlands", "Belgium", "Croatia", "Morocco", "Japan",
        "Senegal", "USA", "Mexico", "Canada", "South Korea", "Australia",
        "Switzerland", "Poland", "Denmark", "Serbia", "Uruguay", "Ecuador",
    ]}

    rows = []
    for fixture in raw_fixtures:
        try:
            row = build_match_features(fixture, mock_team_stats)
            rows.append(row)
        except Exception:
            continue  # skip malformed fixtures

    df = pd.DataFrame(rows).dropna()
    print(f"Match training rows built: {len(df)}")
    return df


# ── Step 3: Build player rating training DataFrame ───────────────────────────
def build_player_training_df(n_samples: int = 500) -> pd.DataFrame:
    """
    In production: fetch from get_fixture_players() for every historical game.
    Here we generate realistic synthetic data to demonstrate the training pipeline.

    In reality, you would:
      1. Loop through all historical fixture IDs
      2. Call get_fixture_players(fixture_id) for each
      3. Join with the match result to add context features
    """
    np.random.seed(42)
    positions = [0, 1, 2, 3]  # GK, DEF, MID, FWD
    pos_variance = {0: 0.3, 1: 0.4, 2: 0.5, 3: 0.9}  # forwards most variable

    rows = []
    for _ in range(n_samples):
        pos        = np.random.choice(positions)
        form       = np.random.uniform(5.5, 9.0)
        opp_def    = np.random.randint(1, 100)
        minutes    = np.random.choice([45, 60, 75, 90], p=[0.1, 0.15, 0.15, 0.6])
        fatigue    = np.random.randint(0, 7)
        is_home    = np.random.randint(0, 2)

        # Simulate actual rating — correlated with features + noise
        base = (
            form * 0.6
            + (100 - opp_def) / 100 * 1.5
            + (minutes / 90) * 0.5
            - fatigue * 0.05
            + is_home * 0.1
        )
        noise  = np.random.normal(0, pos_variance[pos])
        rating = round(min(10.0, max(5.0, base + noise)), 2)

        rows.append({
            "form_last5":         round(form, 2),
            "opponent_def_rank":  opp_def,
            "expected_minutes":   minutes,
            "position_enc":       pos,
            "tournament_fatigue": fatigue,
            "is_home_team":       is_home,
            "actual_rating":      rating,
        })

    df = pd.DataFrame(rows)
    print(f"Player training rows built: {len(df)}")
    return df


# ── Step 4: Build card training DataFrame ─────────────────────────────────────
def build_card_training_df(n_samples: int = 300) -> pd.DataFrame:
    """
    Synthetic card data for training CardPredictor.
    In production: fetch referee data from a dedicated sports stats API.
    """
    np.random.seed(99)
    rows = []
    for _ in range(n_samples):
        ref_rate   = round(np.random.uniform(1.5, 6.5), 2)
        home_foul  = round(np.random.uniform(10, 18), 1)
        away_foul  = round(np.random.uniform(10, 18), 1)
        is_ko      = np.random.randint(0, 2)
        rank_diff  = np.random.randint(0, 50)

        # Yellow cards: mainly driven by referee + knockout stage
        mu_yellow = ref_rate * (1.3 if is_ko else 1.0) + (home_foul + away_foul) * 0.05
        yellow = int(np.random.negative_binomial(2, 2 / (2 + mu_yellow)))

        # Red cards: rare, ~7% of yellow rate
        mu_red = mu_yellow * 0.07
        red    = int(np.random.negative_binomial(1, 1 / (1 + mu_red)))

        rows.append({
            "referee_cards_per_game": ref_rate,
            "home_foul_rate":         home_foul,
            "away_foul_rate":         away_foul,
            "is_knockout":            is_ko,
            "ranking_diff_abs":       rank_diff,
            "yellow_cards":           yellow,
            "red_cards":              red,
        })

    df = pd.DataFrame(rows)
    print(f"Card training rows built: {len(df)}")
    return df


# ── Main: train everything ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("WC 2026 — Model Training Pipeline")
    print("=" * 60)

    # --- Match predictor ---
    print("\n[1/3] Training MatchPredictor (XGBoost)…")
    try:
        raw = fetch_training_data()
        match_df = build_match_training_df(raw)
    except Exception as e:
        print(f"  API fetch failed ({e}), using synthetic data for demo.")
        # Generate minimal synthetic match data
        np.random.seed(42)
        match_df = pd.DataFrame({
            "home_ranking_diff":    np.random.randint(-40, 40, 200),
            "home_xg":              np.random.uniform(0.5, 2.8, 200),
            "away_xg":              np.random.uniform(0.5, 2.8, 200),
            "travel_fatigue_home":  np.random.uniform(0, 0.7, 200),
            "travel_fatigue_away":  np.random.uniform(0, 0.7, 200),
            "is_knockout":          np.random.randint(0, 2, 200),
            "h2h_home_winrate":     np.random.uniform(0.2, 0.8, 200),
            "result":               np.random.choice([0, 1, 2], 200, p=[0.33, 0.27, 0.40]),
        })

    mp = MatchPredictor()
    mp_scores = mp.train(match_df)
    print(f"  ✅ Train accuracy: {mp_scores['train_accuracy']*100:.1f}%  "
          f"Test accuracy: {mp_scores['test_accuracy']*100:.1f}%")

    # --- Card predictor ---
    print("\n[2/3] Training CardPredictor (Negative Binomial)…")
    card_df = build_card_training_df()
    cp = CardPredictor()
    cp_scores = cp.train(card_df)
    print(f"  ✅ Yellow MAE: {cp_scores['yellow_mae']}  Red MAE: {cp_scores['red_mae']}")

    # --- Player rating predictor ---
    print("\n[3/3] Training PlayerRatingPredictor (Random Forest)…")
    player_df = build_player_training_df()
    prp = PlayerRatingPredictor()
    prp_scores = prp.train(player_df)
    print(f"  ✅ Overall MAE: {prp_scores['overall_mae']}  "
          f"By position: {prp_scores['by_position']}")

    print("\n" + "=" * 60)
    print("All models trained and saved to models/saved/")
    print("Run  →  streamlit run app.py  to start the dashboard.")
    print("=" * 60)
