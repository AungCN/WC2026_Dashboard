"""
pages/player_ratings.py
────────────────────────
Player Ratings page.

Shows:
  • Per-player live ratings fetched from API-Football
  • Our Random Forest predicted ratings with confidence range
  • Sortable table: all players from a selected fixture
  • Position breakdown chart
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.api_client import get_todays_fixtures, get_fixture_players
from utils.data_helpers import fixtures_to_df, players_to_df
from models.prediction_engine import PlayerRatingPredictor


@st.cache_resource
def _get_rating_model():
    prp = PlayerRatingPredictor()
    prp.load()
    return prp


def render():
    st.title("⭐ Player Ratings")
    st.caption("Live ratings via API-Football + our Random Forest predictions")

    prp = _get_rating_model()

    # ── Fixture selector ───────────────────────────────────────────────────────
    today_raw = get_todays_fixtures()
    today_df  = fixtures_to_df(today_raw)

    if today_df.empty:
        st.info("Player ratings appear during and after matches.")
        _render_model_explainer(prp)
        return

    today_df["label"] = today_df["home_team"] + " vs " + today_df["away_team"]
    selected = st.selectbox("Select a match", today_df["label"].tolist())
    selected_row = today_df[today_df["label"] == selected].iloc[0]
    fixture_id   = int(selected_row["fixture_id"])

    st.divider()

    # ── Fetch player data ──────────────────────────────────────────────────────
    raw_players = get_fixture_players(fixture_id)
    player_df   = players_to_df(raw_players)

    if player_df.empty:
        st.info("Player stats not available yet for this fixture. Data appears after kick-off.")
        return

    # ── Add our predicted ratings ──────────────────────────────────────────────
    player_df = _add_model_predictions(player_df, prp, selected_row)

    # ── Filters ───────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        team_filter = st.selectbox("Team", ["All"] + player_df["team"].unique().tolist())
    with col2:
        pos_filter = st.selectbox("Position", ["All", "G", "D", "M", "F"])

    filtered = player_df.copy()
    if team_filter != "All":
        filtered = filtered[filtered["team"] == team_filter]
    if pos_filter != "All":
        filtered = filtered[filtered["position"] == pos_filter]

    # ── Ratings table ─────────────────────────────────────────────────────────
    st.subheader("Player Performance")
    display_cols = [
        "player_name", "team", "position", "minutes",
        "rating", "pred_rating", "confidence",
        "goals", "assists", "yellow_cards", "red_cards", "passes", "shots",
    ]
    # Rename for display
    rename_map = {
        "player_name":  "Player",
        "team":         "Team",
        "position":     "Pos",
        "minutes":      "Mins",
        "rating":       "Live Rating",
        "pred_rating":  "Predicted",
        "confidence":   "Confidence",
        "goals":        "G",
        "assists":      "A",
        "yellow_cards": "YC",
        "red_cards":    "RC",
        "passes":       "Passes",
        "shots":        "Shots",
    }

    # Color the rating column
    show_df = (
        filtered[display_cols]
        .rename(columns=rename_map)
        .sort_values("Live Rating", ascending=False)
    )
    st.dataframe(
        show_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Live Rating": st.column_config.ProgressColumn(
                "Live Rating", min_value=5.0, max_value=10.0, format="%.1f"
            ),
            "Predicted": st.column_config.ProgressColumn(
                "Predicted", min_value=5.0, max_value=10.0, format="%.1f"
            ),
        },
    )

    # ── Rating distribution chart ──────────────────────────────────────────────
    st.divider()
    st.subheader("Rating Distribution by Position")
    if not filtered.empty and "rating" in filtered.columns:
        fig = px.box(
            filtered[filtered["rating"] > 0],
            x="position",
            y="rating",
            color="team",
            points="all",
            labels={"position": "Position", "rating": "Rating (0–10)"},
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Notice how Forwards (F) have a wider spread than Defenders (D) — "
            "this is exactly why our model uses higher variance bounds for forwards."
        )


def _add_model_predictions(df: pd.DataFrame, prp: PlayerRatingPredictor,
                            fixture_row: pd.Series) -> pd.DataFrame:
    """Add our model's predicted rating column to the player DataFrame."""
    POSITION_MAP = {"G": 0, "D": 1, "M": 2, "F": 3}

    pred_ratings  = []
    pred_confs    = []

    for _, row in df.iterrows():
        features = {
            "form_last5":         row["rating"] if row["rating"] > 0 else 7.0,
            "opponent_def_rank":  50,   # placeholder — update with real rank data
            "expected_minutes":   row["minutes"] if row["minutes"] > 0 else 90,
            "position_enc":       POSITION_MAP.get(row["position"], 1),
            "tournament_fatigue": 2,    # placeholder — count games played so far
            "is_home_team":       0,    # placeholder — check team vs home team
        }
        result = prp.predict(features)
        pred_ratings.append(result["predicted_rating"])
        pred_confs.append(result["confidence"])

    df["pred_rating"] = pred_ratings
    df["confidence"]  = pred_confs
    return df


def _render_model_explainer(prp: PlayerRatingPredictor):
    """When no live data is available, explain the model instead."""
    st.subheader("How the Rating Model Works")

    st.markdown("""
    Our **Random Forest** model predicts player ratings using 6 features:

    | Feature | What it means | Why it matters |
    |---|---|---|
    | Form (last 5 games) | Average rating recently | Best single predictor |
    | Opponent defense rank | How strong is the other team's defense? | A striker vs top defense scores lower |
    | Expected minutes | Will they play the full 90? | More minutes = more impact |
    | Position | GK / DEF / MID / FWD | Forwards have more variance than defenders |
    | Tournament fatigue | Games played so far | Performance drops after 4+ games |
    | Home city factor | Playing near home? | Small but measurable effect |
    """)

    st.subheader("Try a manual prediction")
    col1, col2 = st.columns(2)
    with col1:
        form     = st.slider("Form (last 5 avg)", 5.0, 10.0, 7.2)
        minutes  = st.slider("Expected minutes", 0, 90, 90)
        fatigue  = st.slider("Games played in tournament", 0, 7, 2)
    with col2:
        opp_def  = st.slider("Opponent defense strength", 1, 100, 60)
        position = st.selectbox("Position", ["GK", "DEF", "MID", "FWD"])
        is_home  = st.checkbox("Playing at home city")

    pos_map = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}

    features = {
        "form_last5":         form,
        "opponent_def_rank":  opp_def,
        "expected_minutes":   minutes,
        "position_enc":       pos_map[position],
        "tournament_fatigue": fatigue,
        "is_home_team":       int(is_home),
    }
    result = prp.predict(features)

    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Predicted rating",   result["predicted_rating"])
    col2.metric("Low estimate",       result["low"])
    col3.metric("High estimate",      result["high"])
    col4.metric("Confidence",         result["confidence"])
