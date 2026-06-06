"""
pages/live_scores.py
─────────────────────
Live Scores page — powered by openfootball/worldcup.json (free, no key).

Data source reality (verified):
  • openfootball updates the JSON file AFTER each match ends (not real-time)
  • "Live" tab shows today's matches with scores when available
  • "Schedule" tab shows full fixture list
  • Standings are calculated from completed match results in the file
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
from utils.api_client import (
    get_todays_fixtures,
    get_all_fixtures,
    get_standings,
    get_goal_scorers,
)


def render():
    st.title("⚽ Scores & Schedule")
    st.caption(
        "Data: [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json) "
        "· Free · No API key · Updates after each match"
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📅 Today", "📋 Full Schedule", "🏆 Standings", "🥅 Top Scorers"]
    )

    with tab1:
        _render_today()

    with tab2:
        _render_schedule()

    with tab3:
        _render_standings()

    with tab4:
        _render_scorers()


# ── Tab 1: Today ───────────────────────────────────────────────────────────────
def _render_today():
    today    = date.today().isoformat()
    fixtures = get_todays_fixtures()

    if not fixtures:
        # Tournament hasn't started yet — show next match day
        all_fix  = get_all_fixtures()
        upcoming = [f for f in all_fix if f["date"] >= today]
        if upcoming:
            next_date = upcoming[0]["date"]
            next_matches = [f for f in all_fix if f["date"] == next_date]
            st.info(
                f"No matches today ({today}). "
                f"Tournament begins **{next_date}** — "
                f"{len(next_matches)} matches on opening day."
            )
            st.subheader(f"Next match day — {next_date}")
            for f in next_matches:
                _scoreboard_card(f)
        else:
            st.info("No upcoming fixtures found.")
        return

    finished = [f for f in fixtures if f["status"] == "Match Finished"]
    pending  = [f for f in fixtures if f["status"] != "Match Finished"]

    if pending:
        st.subheader("Upcoming today")
        for f in pending:
            _scoreboard_card(f)

    if finished:
        st.subheader("Results")
        for f in finished:
            _scoreboard_card(f)


# ── Tab 2: Full schedule ───────────────────────────────────────────────────────
def _render_schedule():
    all_fix = get_all_fixtures()
    today   = date.today().isoformat()

    # Group by round
    rounds: dict[str, list] = {}
    for f in all_fix:
        rounds.setdefault(f["round"], []).append(f)

    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        show_filter = st.selectbox(
            "Show", ["All matches", "Upcoming only", "Completed only"]
        )
    with col2:
        group_filter = st.selectbox(
            "Group / Round",
            ["All"] + sorted(set(
                f["group"] if f["group"] else f["round"] for f in all_fix
            )),
        )

    for round_name, matches in rounds.items():
        if group_filter != "All":
            matches = [
                m for m in matches
                if m["group"] == group_filter or m["round"] == group_filter
            ]
        if not matches:
            continue

        if show_filter == "Upcoming only":
            matches = [m for m in matches if m["status"] != "Match Finished"]
        elif show_filter == "Completed only":
            matches = [m for m in matches if m["status"] == "Match Finished"]

        if not matches:
            continue

        with st.expander(f"**{round_name}** — {len(matches)} matches", expanded=False):
            for f in matches:
                _scoreboard_card(f, compact=True)


# ── Tab 3: Standings ───────────────────────────────────────────────────────────
def _render_standings():
    standings = get_standings()

    if not standings:
        st.info(
            "Standings will populate automatically once matches are played. "
            "The first match is **Mexico vs South Africa** on June 11."
        )
        return

    group_labels = [chr(65 + i) for i in range(len(standings))]  # A, B, C...
    cols = st.columns(2)

    for i, (label, group) in enumerate(zip(group_labels, standings)):
        with cols[i % 2]:
            st.markdown(f"**Group {label}**")
            df = pd.DataFrame(group)[
                ["team", "played", "won", "drawn", "lost", "gf", "ga", "gd", "points"]
            ]
            df.columns = ["Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]
            st.dataframe(df, hide_index=True, use_container_width=True)


# ── Tab 4: Top scorers ─────────────────────────────────────────────────────────
def _render_scorers():
    scorers = get_goal_scorers()

    if not scorers:
        st.info("Goal scorer data will appear once matches are played.")
        return

    df = pd.DataFrame(scorers)
    df.columns = ["Player", "Team", "Goals", "Penalties"]
    st.dataframe(
        df.head(20),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Goals": st.column_config.ProgressColumn(
                "Goals", min_value=0, max_value=df["Goals"].max(), format="%d"
            )
        },
    )


# ── Scoreboard card ────────────────────────────────────────────────────────────
def _scoreboard_card(f: dict, compact: bool = False):
    """Render one match as a clean row with score or kick-off time."""
    home = f["home_team"]
    away = f["away_team"]
    hg   = f["home_goals"]
    ag   = f["away_goals"]

    col1, col2, col3 = st.columns([3, 2, 3])

    with col1:
        st.markdown(f"**{home}**")

    with col2:
        if hg is not None and ag is not None:
            ht_str = ""
            if f["ht_home"] is not None:
                ht_str = f"<br><span style='font-size:0.7rem;color:gray'>HT {f['ht_home']}–{f['ht_away']}</span>"
            suffix = ""
            if f["status"] == "Penalties":
                p = f.get("goals1")   # repurpose as penalty score if stored
                suffix = " (Pen)"
            elif f["status"] == "AET":
                suffix = " (AET)"
            label = (
                f"<div style='text-align:center;font-size:1.2rem;font-weight:600'>"
                f"{'✅' if f['status']=='Match Finished' else '🔴'} "
                f"{hg} – {ag}{suffix}</div>{ht_str}"
            )
        else:
            label = (
                f"<div style='text-align:center;font-size:0.95rem;color:gray'>"
                f"🕐 {f['kickoff']} {f['timezone']}</div>"
            )
        st.markdown(label, unsafe_allow_html=True)

    with col3:
        st.markdown(
            f"<div style='text-align:right'><b>{away}</b></div>",
            unsafe_allow_html=True,
        )

    if not compact:
        venue = f.get("venue_city", "")
        group = f.get("group", "")
        meta  = " · ".join(filter(None, [group, venue, f["date"]]))
        if meta:
            st.markdown(
                f"<div style='text-align:center;font-size:0.72rem;color:gray'>{meta}</div>",
                unsafe_allow_html=True,
            )

        # Goal scorers if available
        goals1 = f.get("goals1", [])
        goals2 = f.get("goals2", [])
        if goals1 or goals2:
            gc1, gc2 = st.columns(2)
            with gc1:
                for g in goals1:
                    pen = " (P)" if g.get("penalty") else ""
                    st.caption(f"⚽ {g['name']} {g['minute']}'{pen}")
            with gc2:
                for g in goals2:
                    pen = " (P)" if g.get("penalty") else ""
                    st.caption(f"⚽ {g['name']} {g['minute']}'{pen}")

    st.divider()
