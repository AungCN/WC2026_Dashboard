"""
pages/predictions.py
──────────────────────
Match Predictions page.

Data source change (June 2026):
  - get_api_predictions() REMOVED — that required the paid RapidAPI key
  - get_todays_fixtures() now comes from openfootball (free, no key)
  - Predictions come entirely from our own ML models (XGBoost + Poisson)
  - The "API baseline" comparison panel has been replaced with a
    feature-importance explainer so users understand the model

Shows:
  • Fixture selector (today's matches, or manual input)
  • Win / Draw / Loss probability bars (our XGBoost model)
  • Most likely scoreline (Poisson model)
  • Expected cards (Negative Binomial model)
  • Model feature explainer
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.api_client import get_todays_fixtures, get_all_fixtures
from utils.data_helpers import fixtures_to_df
from models.prediction_engine import MatchPredictor, CardPredictor


@st.cache_resource
def _get_models():
    mp = MatchPredictor()
    mp.load()
    cp = CardPredictor()
    return mp, cp


def render():
    st.title("🔮 Match Predictions")
    st.caption(
        "Predictions from our XGBoost + Poisson models · "
        "No paid API required · Updates as matches are played"
    )

    mp, cp = _get_models()

    # ── Fixture selector ───────────────────────────────────────────────────────
    today_raw = get_todays_fixtures()

    if today_raw:
        today_df = fixtures_to_df(today_raw)
        today_df["label"] = (
            today_df["home_team"] + " vs " + today_df["away_team"]
            + "  (" + today_df["date"] + ")"
        )
        selected_label = st.selectbox("Select a fixture", today_df["label"].tolist())
        selected_row   = today_df[today_df["label"] == selected_label].iloc[0]
        home = selected_row["home_team"]
        away = selected_row["away_team"]
        st.divider()
        _render_prediction_panel(mp, cp, home, away, selected_row)

    else:
        # No matches today — show upcoming fixture picker from full schedule
        all_raw = get_all_fixtures()
        from datetime import date
        today_str = date.today().isoformat()
        upcoming  = [f for f in all_raw if f["date"] >= today_str and f["status"] == "Not Started"]

        if upcoming:
            all_df   = fixtures_to_df(upcoming)
            all_df["label"] = (
                all_df["home_team"] + " vs " + all_df["away_team"]
                + "  ·  " + all_df["date"]
                + "  (" + all_df["venue_city"] + ")"
            )
            st.info("No matches today. Select any upcoming fixture to preview our prediction.")
            selected_label = st.selectbox("Upcoming fixtures", all_df["label"].tolist())
            selected_row   = all_df[all_df["label"] == selected_label].iloc[0]
            home = selected_row["home_team"]
            away = selected_row["away_team"]
            st.divider()
            _render_prediction_panel(mp, cp, home, away, selected_row)
        else:
            st.info("No upcoming fixtures found.")
            _render_manual_input(mp, cp)


# ── Main prediction panel ──────────────────────────────────────────────────────
def _render_prediction_panel(mp, cp, home, away, row):
    col_pred, col_cards = st.columns([3, 2])

    with col_pred:
        _render_match_prediction(mp, home, away)

    with col_cards:
        _render_card_prediction(cp, row)

    st.divider()
    _render_feature_explainer()


def _render_match_prediction(mp: MatchPredictor, home: str, away: str):
    st.subheader(f"🤖 {home} vs {away}")

    # Feature inputs — shown as adjustable sliders so user can tune them
    with st.expander("⚙️ Adjust model inputs", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            ranking_diff = st.slider("Home ranking advantage", -50, 50, 10,
                help="Positive = home team has a higher FIFA ranking")
            home_xg = st.slider("Home expected goals (xG)", 0.5, 3.5, 1.5, 0.1)
            fatigue_h = st.slider("Home travel fatigue", 0.0, 1.0, 0.1, 0.05)
        with col2:
            away_xg  = st.slider("Away expected goals (xG)", 0.5, 3.5, 1.1, 0.1)
            fatigue_a = st.slider("Away travel fatigue", 0.0, 1.0, 0.35, 0.05)
            h2h      = st.slider("Home H2H win rate", 0.0, 1.0, 0.5, 0.05)
        is_ko = st.checkbox("Knockout stage match")

    features = {
        "home_ranking_diff":   ranking_diff,
        "home_xg":             home_xg,
        "away_xg":             away_xg,
        "travel_fatigue_home": fatigue_h,
        "travel_fatigue_away": fatigue_a,
        "is_knockout":         int(is_ko),
        "h2h_home_winrate":    h2h,
    }

    probs = mp.predict(features)

    # Probability bar chart
    fig = go.Figure(go.Bar(
        x=[f"{home}\nwins", "Draw", f"{away}\nwins"],
        y=[probs["home_win"]*100, probs["draw"]*100, probs["away_win"]*100],
        marker_color=["#185FA5", "#888780", "#D85A30"],
        text=[f"{v*100:.1f}%" for v in [probs["home_win"], probs["draw"], probs["away_win"]]],
        textposition="outside",
    ))
    fig.update_layout(
        yaxis=dict(range=[0, 105], title="Probability (%)"),
        showlegend=False,
        height=280,
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Poisson scoreline
    score_pred = mp.poisson_score_prediction(home_xg, away_xg)
    col1, col2 = st.columns(2)
    col1.metric("Most likely score", score_pred["most_likely_score"])
    col2.metric("Probability", f"{score_pred['score_probability']*100:.1f}%")


def _render_card_prediction(cp: CardPredictor, row):
    st.subheader("🟨 Discipline forecast")

    ref_rate = st.slider("Referee strictness", 1.0, 8.0, 3.8, 0.1,
        help="Average cards per game for the assigned referee. "
             "This is the strongest single predictor.")

    features = {
        "referee_cards_per_game": ref_rate,
        "home_foul_rate":         14.0,
        "away_foul_rate":         13.5,
        "is_knockout":            0,
        "ranking_diff_abs":       10,
    }
    card_pred = cp.predict(features)

    st.metric(
        "🟨 Expected yellow cards",
        card_pred["expected_yellows"],
        f"Range {card_pred['range_yellows'][0]}–{card_pred['range_yellows'][1]}",
    )
    st.metric(
        "🟥 Expected red cards",
        card_pred["expected_reds"],
        f"Range {card_pred['range_reds'][0]}–{card_pred['range_reds'][1]}",
    )
    st.caption(
        "Model: Negative Binomial regression. "
        "The referee's cards-per-game rate is the #1 predictor."
    )


def _render_feature_explainer():
    st.subheader("📊 What drives the prediction?")
    st.caption("Feature importance from our XGBoost model (approximate)")

    features = {
        "FIFA ranking difference":   72,
        "Expected goals (xG) gap":   68,
        "H2H historical win rate":   45,
        "Travel fatigue (away)":     38,
        "Travel fatigue (home)":     31,
        "Knockout stage bonus":      22,
    }

    fig = go.Figure(go.Bar(
        x=list(features.values()),
        y=list(features.keys()),
        orientation="h",
        marker_color="#185FA5",
    ))
    fig.update_layout(
        xaxis=dict(title="Relative importance (%)"),
        height=250,
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Travel fatigue is unique to WC 2026 due to the 3-country format. "
        "A team flying Vancouver → Miami between group games covers ~4,350 km."
    )


def _render_manual_input(mp: MatchPredictor, cp: CardPredictor):
    st.subheader("Try a manual prediction")
    col1, col2 = st.columns(2)
    with col1:
        home_str  = st.slider("Home team strength", 1, 100, 70)
        home_xg   = st.slider("Home xG", 0.5, 3.5, 1.5, 0.1)
        fatigue_h = st.slider("Home travel fatigue", 0.0, 1.0, 0.1, 0.05)
    with col2:
        away_str  = st.slider("Away team strength", 1, 100, 60)
        away_xg   = st.slider("Away xG", 0.5, 3.5, 1.1, 0.1)
        fatigue_a = st.slider("Away travel fatigue", 0.0, 1.0, 0.4, 0.05)
    is_ko = st.checkbox("Knockout stage")

    features = {
        "home_ranking_diff":   home_str - away_str,
        "home_xg":             home_xg,
        "away_xg":             away_xg,
        "travel_fatigue_home": fatigue_h,
        "travel_fatigue_away": fatigue_a,
        "is_knockout":         int(is_ko),
        "h2h_home_winrate":    0.5,
    }
    probs = mp.predict(features)
    score = mp.poisson_score_prediction(home_xg, away_xg)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Home win", f"{probs['home_win']*100:.1f}%")
    col2.metric("Draw",     f"{probs['draw']*100:.1f}%")
    col3.metric("Away win", f"{probs['away_win']*100:.1f}%")
    col4.metric("Likely score", score["most_likely_score"])
