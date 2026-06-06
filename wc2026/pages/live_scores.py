"""
pages/live_scores.py
─────────────────────
Live Scores page for the WC 2026 Dashboard.

Shows:
  • In-play matches with live score + minute
  • Today's upcoming fixtures
  • Group standings table
"""

import streamlit as st
import pandas as pd
from utils.api_client import get_live_fixtures, get_todays_fixtures, get_standings
from utils.data_helpers import fixtures_to_df


def render():
    st.title("🟢 Live Scores")
    st.caption("Auto-refreshes every 60 seconds · Powered by API-Football")

    # ── Live matches ───────────────────────────────────────────────────────────
    st.subheader("In Play Now")
    live_raw = get_live_fixtures()
    live_df  = fixtures_to_df(live_raw)

    if live_df.empty:
        st.info("No matches currently in play. Check back during match times.")
    else:
        for _, row in live_df.iterrows():
            _render_scoreboard(row, live=True)

    # ── Today's fixtures ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("Today's Fixtures")
    today_raw = get_todays_fixtures()
    today_df  = fixtures_to_df(today_raw)

    # Split by status: finished vs upcoming
    if not today_df.empty:
        finished  = today_df[today_df["status"].isin(["Match Finished"])]
        upcoming  = today_df[~today_df["status"].isin(["Match Finished", "First Half",
                                                        "Second Half", "Half Time"])]
        if not upcoming.empty:
            st.markdown("**Upcoming**")
            for _, row in upcoming.iterrows():
                _render_scoreboard(row, live=False)

        if not finished.empty:
            st.markdown("**Finished**")
            for _, row in finished.iterrows():
                _render_scoreboard(row, live=False)
    else:
        st.info("No fixtures scheduled today.")

    # ── Standings ──────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Group Standings")
    standings_raw = get_standings()

    if not standings_raw:
        st.info("Standings will appear once the group stage begins.")
    else:
        for group in standings_raw:
            rows = []
            for team in group:
                rows.append({
                    "Team":   team["team"]["name"],
                    "P":      team["all"]["played"],
                    "W":      team["all"]["win"],
                    "D":      team["all"]["draw"],
                    "L":      team["all"]["lose"],
                    "GF":     team["all"]["goals"]["for"],
                    "GA":     team["all"]["goals"]["against"],
                    "GD":     team["goalsDiff"],
                    "Pts":    team["points"],
                })
            df = pd.DataFrame(rows).sort_values("Pts", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)


def _render_scoreboard(row: pd.Series, live: bool):
    """Render a single fixture as a clean scoreboard card."""
    col1, col2, col3 = st.columns([3, 2, 3])

    with col1:
        st.markdown(f"**{row['home_team']}**")

    with col2:
        if pd.notna(row["home_goals"]) and pd.notna(row["away_goals"]):
            score = f"{int(row['home_goals'])} – {int(row['away_goals'])}"
            if live and pd.notna(row["elapsed"]):
                label = f"🔴 {score}  {int(row['elapsed'])}\'"
            else:
                label = score
        else:
            label = f"🕐 {row['date']}"
        st.markdown(f"<div style='text-align:center;font-size:1.1rem;font-weight:600'>{label}</div>",
                    unsafe_allow_html=True)

    with col3:
        st.markdown(f"<div style='text-align:right'><b>{row['away_team']}</b></div>",
                    unsafe_allow_html=True)

    st.markdown(f"<div style='text-align:center;font-size:0.75rem;color:gray'>{row.get('venue_city','')}</div>",
                unsafe_allow_html=True)
    st.divider()
