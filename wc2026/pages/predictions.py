"""
pages/predictions.py
──────────────────────
Match Predictions page.
Models auto-train on synthetic data on first run — no manual setup needed.
Works on Streamlit Cloud, local dev, and Docker out of the box.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.api_client import get_todays_fixtures, get_all_fixtures
from utils.data_helpers import fixtures_to_df
from models.prediction_engine import MatchPredictor, CardPredictor, _synthetic_match_df
from data.wc2026_data import FIFA_RANKINGS


@st.cache_resource(show_spinner=False)
def _get_models():
    """
    Load saved models if they exist, otherwise auto-train on synthetic data.
    Cached for the session lifetime — training runs at most once per cold start.
    Never raises RuntimeError regardless of disk state.
    """
    mp = MatchPredictor()
    if not mp.load():
        mp.train(_synthetic_match_df())   # ~5–10 sec, happens once per cold start

    cp = CardPredictor()
    return mp, cp


def render():
    st.title("🔮 Match Predictions")
    st.caption(
        "XGBoost + Poisson models · "
        "Auto-trains on first run · No API key needed"
    )

    # Show a spinner only the very first time (when models aren't cached yet)
    with st.spinner("Preparing prediction models… (first run only, ~10 seconds)"):
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
    else:
        # No matches today — pick from upcoming
        from datetime import date
        today_str = date.today().isoformat()
        all_raw   = get_all_fixtures()
        upcoming  = [f for f in all_raw
                     if f["date"] >= today_str and f["status"] == "Not Started"]

        if not upcoming:
            st.info("No upcoming fixtures found.")
            _render_manual_input(mp, cp)
            return

        all_df = fixtures_to_df(upcoming)
        all_df["label"] = (
            all_df["home_team"] + " vs " + all_df["away_team"]
            + "  ·  " + all_df["date"]
            + "  (" + all_df["venue_city"] + ")"
        )
        st.info("No matches today. Showing upcoming fixtures.")
        selected_label = st.selectbox("Upcoming fixtures", all_df["label"].tolist())
        selected_row   = all_df[all_df["label"] == selected_label].iloc[0]
        home = selected_row["home_team"]
        away = selected_row["away_team"]

    st.divider()
    col_pred, col_cards = st.columns([3, 2])
    with col_pred:
        _render_match_prediction(mp, home, away)
    with col_cards:
        _render_card_prediction(cp, selected_row)

    st.divider()
    _render_feature_explainer()


# ── Match prediction panel ─────────────────────────────────────────────────────
def _render_match_prediction(mp: MatchPredictor, home: str, away: str):
    st.subheader(f"🤖 {home} vs {away}")

    # Auto-derive ranking diff from FIFA rankings
    home_rank = FIFA_RANKINGS.get(home, 50)
    away_rank = FIFA_RANKINGS.get(away, 50)
    default_diff = away_rank - home_rank   # positive = home team is ranked higher

    with st.expander("⚙️ Adjust model inputs", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            ranking_diff = st.slider(
                "Home ranking advantage", -50, 50, int(default_diff),
                help=f"{home} #{home_rank} vs {away} #{away_rank}"
            )
            home_xg  = st.slider("Home xG", 0.5, 3.5, 1.5, 0.1)
            fatigue_h = st.slider("Home travel fatigue", 0.0, 1.0, 0.10, 0.05)
        with col2:
            away_xg   = st.slider("Away xG", 0.5, 3.5, 1.1, 0.1)
            fatigue_a = st.slider("Away travel fatigue", 0.0, 1.0, 0.30, 0.05)
            h2h       = st.slider("Home H2H win rate", 0.0, 1.0, 0.50, 0.05)
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

    fig = go.Figure(go.Bar(
        x=[f"{home}\nwins", "Draw", f"{away}\nwins"],
        y=[probs["home_win"]*100, probs["draw"]*100, probs["away_win"]*100],
        marker_color=["#185FA5", "#888780", "#D85A30"],
        text=[f"{v*100:.1f}%" for v in
              [probs["home_win"], probs["draw"], probs["away_win"]]],
        textposition="outside",
    ))
    fig.update_layout(
        yaxis=dict(range=[0, 105], title="Probability (%)"),
        showlegend=False, height=280,
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    score_pred = mp.poisson_score_prediction(home_xg, away_xg)
    c1, c2 = st.columns(2)
    c1.metric("Most likely score",  score_pred["most_likely_score"])
    c2.metric("Probability",        f"{score_pred['score_probability']*100:.1f}%")

    st.caption(
        f"🏆 FIFA rankings: {home} #{home_rank} · {away} #{away_rank}  ·  "
        "Model trained on synthetic data — improves with real WC data"
    )


# ── Card prediction panel ──────────────────────────────────────────────────────
def _render_card_prediction(cp: CardPredictor, row):
    st.subheader("🟨 Discipline forecast")

    is_ko = 1 if row.get("group","") == "" else 0
    ref_rate = st.slider(
        "Referee strictness", 1.0, 8.0, 3.8, 0.1,
        help="Avg cards/game for this referee — the strongest predictor"
    )
    features = {
        "referee_cards_per_game": ref_rate,
        "home_foul_rate":         14.0,
        "away_foul_rate":         13.5,
        "is_knockout":            is_ko,
        "ranking_diff_abs":       10,
    }
    pred = cp.predict(features)

    st.metric("🟨 Expected yellows", pred["expected_yellows"],
              f"Range {pred['range_yellows'][0]}–{pred['range_yellows'][1]}")
    st.metric("🟥 Expected reds",    pred["expected_reds"],
              f"Range {pred['range_reds'][0]}–{pred['range_reds'][1]}")
    st.caption("Model: Negative Binomial regression. "
               "Referee's cards/game rate is the #1 predictor.")


# ── Feature importance explainer ──────────────────────────────────────────────
def _render_feature_explainer():
    st.subheader("📊 What drives the prediction?")
    features = {
        "FIFA ranking difference":  72,
        "Expected goals (xG) gap":  68,
        "H2H historical win rate":  45,
        "Away travel fatigue":      38,
        "Home travel fatigue":      31,
        "Knockout stage bonus":     22,
    }
    fig = go.Figure(go.Bar(
        x=list(features.values()),
        y=list(features.keys()),
        orientation="h",
        marker_color="#185FA5",
    ))
    fig.update_layout(
        xaxis=dict(title="Relative importance (%)"),
        height=240, margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Travel fatigue is unique to WC 2026 — 3 countries, up to 4,350 km between venues. "
        "A team flying Vancouver → Miami between group games is measurably disadvantaged."
    )


# ── Manual input fallback ──────────────────────────────────────────────────────
def _render_manual_input(mp: MatchPredictor, cp: CardPredictor):
    st.subheader("Manual prediction")
    col1, col2 = st.columns(2)
    with col1:
        home_str  = st.slider("Home team strength", 1, 100, 70)
        home_xg   = st.slider("Home xG", 0.5, 3.5, 1.5, 0.1)
        fatigue_h = st.slider("Home fatigue", 0.0, 1.0, 0.1, 0.05)
    with col2:
        away_str  = st.slider("Away team strength", 1, 100, 60)
        away_xg   = st.slider("Away xG", 0.5, 3.5, 1.1, 0.1)
        fatigue_a = st.slider("Away fatigue", 0.0, 1.0, 0.4, 0.05)
    is_ko = st.checkbox("Knockout stage")

    features = {
        "home_ranking_diff":   home_str - away_str,
        "home_xg":             home_xg, "away_xg": away_xg,
        "travel_fatigue_home": fatigue_h, "travel_fatigue_away": fatigue_a,
        "is_knockout":         int(is_ko), "h2h_home_winrate": 0.5,
    }
    probs = mp.predict(features)
    score = mp.poisson_score_prediction(home_xg, away_xg)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Home win", f"{probs['home_win']*100:.1f}%")
    c2.metric("Draw",     f"{probs['draw']*100:.1f}%")
    c3.metric("Away win", f"{probs['away_win']*100:.1f}%")
    c4.metric("Score",    score["most_likely_score"])
