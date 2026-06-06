"""
pages/predictions.py
──────────────────────
Match Predictions page.

Shows:
  • Win / Draw / Loss probability bar chart (our XGBoost model)
  • Most likely scoreline (Poisson model)
  • Expected cards (Negative Binomial model)
  • Side-by-side comparison with API-Football's built-in predictions
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.api_client import get_todays_fixtures, get_api_predictions
from utils.data_helpers import fixtures_to_df
from models.prediction_engine import MatchPredictor, CardPredictor


# Load models once — cached in session state
@st.cache_resource
def _get_models():
    mp = MatchPredictor()
    mp.load()   # loads saved model if available, else uses rule-based fallback
    cp = CardPredictor()
    return mp, cp


def render():
    st.title("🔮 Match Predictions")
    st.caption("Our model vs API-Football baseline · Updated hourly")

    mp, cp = _get_models()

    # ── Fixture selector ───────────────────────────────────────────────────────
    today_raw = get_todays_fixtures()
    today_df  = fixtures_to_df(today_raw)

    if today_df.empty:
        st.info("No fixtures today. Come back on match days!")
        _render_manual_input(mp, cp)
        return

    # Build display labels: "Brazil vs France (14:00)"
    today_df["label"] = (
        today_df["home_team"] + " vs " + today_df["away_team"]
        + " · " + today_df["date"]
    )

    selected_label = st.selectbox("Select a fixture", today_df["label"].tolist())
    selected_row   = today_df[today_df["label"] == selected_label].iloc[0]
    fixture_id     = int(selected_row["fixture_id"])

    st.divider()

    col_our, col_api = st.columns(2)

    # ── Our model predictions ──────────────────────────────────────────────────
    with col_our:
        st.subheader("🤖 Our ML Model")
        _render_our_prediction(mp, cp, selected_row)

    # ── API-Football baseline ──────────────────────────────────────────────────
    with col_api:
        st.subheader("📊 API-Football Baseline")
        _render_api_prediction(fixture_id)

    # ── Card predictions ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("🟨 Discipline Forecast")
    _render_card_prediction(cp, selected_row)


def _render_our_prediction(mp: MatchPredictor, cp: CardPredictor, row: pd.Series):
    """Show our XGBoost match result prediction."""
    home = row["home_team"]
    away = row["away_team"]

    # Build feature dict — uses rule-based defaults when no training data yet
    features = {
        "home_ranking_diff":    10,    # placeholder — replace with real FIFA rank data
        "home_xg":              1.5,   # placeholder — replace with tournament xG
        "away_xg":              1.1,
        "travel_fatigue_home":  0.15,
        "travel_fatigue_away":  0.30,
        "is_knockout":          0,
        "h2h_home_winrate":     0.5,
    }

    probs = mp.predict(features)

    # Bar chart
    fig = go.Figure(go.Bar(
        x=[f"{home}\nwins", "Draw", f"{away}\nwins"],
        y=[probs["home_win"] * 100, probs["draw"] * 100, probs["away_win"] * 100],
        marker_color=["#185FA5", "#888780", "#D85A30"],
        text=[f"{v*100:.1f}%" for v in [probs["home_win"], probs["draw"], probs["away_win"]]],
        textposition="outside",
    ))
    fig.update_layout(
        yaxis=dict(range=[0, 100], title="Probability (%)"),
        showlegend=False,
        height=300,
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Poisson scoreline
    score_pred = mp.poisson_score_prediction(features["home_xg"], features["away_xg"])
    st.metric(
        "Most likely scoreline",
        score_pred["most_likely_score"],
        f"Probability: {score_pred['score_probability']*100:.1f}%",
    )

    st.caption("💡 Tip: Connect real FIFA ranking and xG data to improve accuracy.")


def _render_api_prediction(fixture_id: int):
    """Show API-Football's built-in prediction as baseline comparison."""
    api_pred = get_api_predictions(fixture_id)

    if not api_pred:
        st.info("API prediction not available for this fixture yet.")
        return

    try:
        pred    = api_pred.get("predictions", {})
        percent = pred.get("percent", {})

        home_pct = float(percent.get("home", "0%").replace("%", ""))
        draw_pct = float(percent.get("draw", "0%").replace("%", ""))
        away_pct = float(percent.get("away", "0%").replace("%", ""))

        winner = pred.get("winner", {}).get("name", "Unknown")

        fig = go.Figure(go.Bar(
            x=["Home wins", "Draw", "Away wins"],
            y=[home_pct, draw_pct, away_pct],
            marker_color=["#185FA5", "#888780", "#D85A30"],
            text=[f"{v:.1f}%" for v in [home_pct, draw_pct, away_pct]],
            textposition="outside",
        ))
        fig.update_layout(
            yaxis=dict(range=[0, 100], title="Probability (%)"),
            showlegend=False,
            height=300,
            margin=dict(t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.metric("API pick", winner)
        st.caption("Source: API-Football /predictions endpoint")
    except Exception as e:
        st.warning(f"Could not parse API prediction: {e}")


def _render_card_prediction(cp: CardPredictor, row: pd.Series):
    """Show card forecast using Negative Binomial model."""
    features = {
        "referee_cards_per_game": 3.8,  # average WC referee — update with real data
        "home_foul_rate":         14.0,
        "away_foul_rate":         13.5,
        "is_knockout":            0,
        "ranking_diff_abs":       10,
    }

    card_pred = cp.predict(features)

    col1, col2, col3 = st.columns(3)
    col1.metric("🟨 Expected yellows",
                card_pred["expected_yellows"],
                f"Range: {card_pred['range_yellows'][0]}–{card_pred['range_yellows'][1]}")
    col2.metric("🟥 Expected reds",
                card_pred["expected_reds"],
                f"Range: {card_pred['range_reds'][0]}–{card_pred['range_reds'][1]}")
    col3.metric("⚠️ Strongest predictor", "Referee strictness", "")

    st.caption(
        "Card model uses Negative Binomial regression. "
        "The referee's historical cards-per-game rate is the single "
        "most powerful predictor of discipline in a match."
    )


def _render_manual_input(mp: MatchPredictor, cp: CardPredictor):
    """Manual feature input when no live fixtures are available."""
    st.subheader("Try a manual prediction")
    st.caption("Adjust the sliders to simulate any fixture.")

    col1, col2 = st.columns(2)
    with col1:
        home_str = st.slider("Home team strength", 1, 100, 70)
        home_xg  = st.slider("Home xG", 0.5, 3.5, 1.5)
        fatigue_h = st.slider("Home travel fatigue", 0.0, 1.0, 0.1)
    with col2:
        away_str  = st.slider("Away team strength", 1, 100, 60)
        away_xg   = st.slider("Away xG", 0.5, 3.5, 1.1)
        fatigue_a = st.slider("Away travel fatigue", 0.0, 1.0, 0.4)

    is_ko = st.checkbox("Knockout stage match")

    if st.button("Run prediction"):
        features = {
            "home_ranking_diff":    home_str - away_str,
            "home_xg":              home_xg,
            "away_xg":              away_xg,
            "travel_fatigue_home":  fatigue_h,
            "travel_fatigue_away":  fatigue_a,
            "is_knockout":          int(is_ko),
            "h2h_home_winrate":     0.5,
        }
        probs = mp.predict(features)
        st.write("**Win probabilities:**", probs)
        score = mp.poisson_score_prediction(home_xg, away_xg)
        st.write("**Most likely scoreline:**", score["most_likely_score"],
                 f"({score['score_probability']*100:.1f}%)")
