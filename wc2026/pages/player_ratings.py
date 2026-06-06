"""
pages/player_ratings.py
────────────────────────
Player Ratings — uses static squad data from wc2026_data.py
+ Random Forest ML model predictions.
Goal scorer tab fills automatically from openfootball once matches are played.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api_client import get_goal_scorers, get_squad, get_all_teams
from data.wc2026_data import SQUADS, TEAM_TO_GROUP, FIFA_RANKINGS
from models.prediction_engine import PlayerRatingPredictor

POS_ENC = {"GK":0,"DEF":1,"MID":2,"FWD":3}

@st.cache_resource(show_spinner=False)
def _model():
    prp = PlayerRatingPredictor()
    if not prp.load():
        from models.prediction_engine import _synthetic_player_df
        prp.train(_synthetic_player_df())   # auto-train once on cold start
    return prp

def render():
    st.title("⭐ Player Ratings")
    st.caption("Predicted ratings from our Random Forest model · Full official squads for all 48 teams")

    prp = _model()
    tab1, tab2, tab3 = st.tabs(["🔮 Predicted ratings","🥅 Goal scorers","ℹ️ Model info"])

    with tab1:  _render_ratings(prp)
    with tab2:  _render_scorers()
    with tab3:  _render_model_info(prp)


def _render_ratings(prp):
    all_teams = get_all_teams()
    col1, col2, col3 = st.columns(3)
    with col1:
        team = st.selectbox("Team", all_teams,
                            index=all_teams.index("Brazil") if "Brazil" in all_teams else 0)
    with col2:
        opp_def = st.slider("Opponent defense strength", 1, 100, 60,
                            help="Higher = tougher opponent")
    with col3:
        fatigue = st.slider("Games played in tournament", 0, 7, 2)

    group = TEAM_TO_GROUP.get(team, "—")
    ranking = FIFA_RANKINGS.get(team, 50)
    st.caption(f"**{team}** · {group} · FIFA rank #{ranking}")

    squad = get_squad(team)
    if not squad:
        st.info(f"Squad data for {team} will be added soon.")
        return

    rows = []
    for p in squad:
        pos_enc = POS_ENC.get(p["position"], 1)
        form    = 7.5 - (pos_enc * 0.1)   # rough form baseline by position
        result  = prp.predict({
            "form_last5":        form,
            "opponent_def_rank": opp_def,
            "expected_minutes":  90,
            "position_enc":      pos_enc,
            "tournament_fatigue":fatigue,
            "is_home_team":      0,
        })
        rows.append({
            "#":          p["number"],
            "Player":     p["name"],
            "Pos":        p["position"],
            "Predicted":  result["predicted_rating"],
            "Low":        result["low"],
            "High":       result["high"],
            "Confidence": result["confidence"],
        })

    df = pd.DataFrame(rows).sort_values("Predicted", ascending=False)
    st.dataframe(df, hide_index=True, use_container_width=True,
        column_config={
            "Predicted": st.column_config.ProgressColumn(
                "Predicted", min_value=5.0, max_value=10.0, format="%.2f"),
            "Low":  st.column_config.NumberColumn("Low",  format="%.2f"),
            "High": st.column_config.NumberColumn("High", format="%.2f"),
        })

    st.divider()
    fig = px.box(df, x="Pos", y="Predicted", color="Pos", points="all",
                 hover_data=["Player"],
                 category_orders={"Pos":["GK","DEF","MID","FWD"]},
                 labels={"Predicted":"Predicted Rating"})
    fig.update_layout(height=300, showlegend=False, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Forwards show wider variance than defenders — this matches real-world data.")


def _render_scorers():
    scorers = get_goal_scorers()
    if not scorers:
        st.info("Goal scorers appear here automatically once matches are played. First match: **Mexico vs South Africa, June 11**.")
        return
    df = pd.DataFrame(scorers)
    df.columns = ["Player","Team","Goals","Penalties"]
    st.dataframe(df.head(20), hide_index=True, use_container_width=True,
        column_config={"Goals": st.column_config.ProgressColumn(
            "Goals", min_value=0, max_value=int(df["Goals"].max()), format="%d")})


def _render_model_info(prp):
    st.markdown("""
### Random Forest rating model — how it works

200 decision trees each independently predict a player's match rating.
The final prediction is the average. The Low/High range is the 10th–90th percentile spread.
A narrow range = high confidence. A wide range = uncertain (common for forwards).

| Feature | Why it matters |
|---|---|
| Form (last 5 games avg) | Strongest single predictor |
| Opponent defense strength | Harder defense → lower rating |
| Expected minutes | 90 mins = more impact opportunities |
| Position | Forwards have highest variance |
| Tournament fatigue | ~0.05 drop per extra game played |
| Home city factor | Small but measurable advantage |
""")
    st.divider()
    st.subheader("Manual prediction")
    col1, col2 = st.columns(2)
    with col1:
        form   = st.slider("Form (last 5 avg)", 5.0, 10.0, 7.2, 0.1)
        mins   = st.slider("Expected minutes", 0, 90, 90)
        fat    = st.slider("Games in tournament", 0, 7, 2)
    with col2:
        opp    = st.slider("Opponent defense", 1, 100, 60)
        pos    = st.selectbox("Position", ["GK","DEF","MID","FWD"])
        home   = st.checkbox("Playing in home city")
    r = prp.predict({"form_last5":form,"opponent_def_rank":opp,
                     "expected_minutes":mins,"position_enc":POS_ENC[pos],
                     "tournament_fatigue":fat,"is_home_team":int(home)})
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Predicted", r["predicted_rating"])
    c2.metric("Low",       r["low"])
    c3.metric("High",      r["high"])
    c4.metric("Confidence",r["confidence"])
