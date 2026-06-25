"""
pages/bracket.py
─────────────────
Two tabs:
  Tab 1 — Interactive knockout bracket (R32 → Final), click any match for details
  Tab 2 — Full 104-match schedule with timezone converter
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from utils.api_client import get_all_fixtures, get_completed_fixtures

# ── Timezone options ───────────────────────────────────────────────────────────
TIMEZONES = {
    "UTC (tournament base)":       0,
    "Eastern — New York (ET)":    -4,
    "Central — Chicago (CT)":     -5,
    "Mountain — Denver (MT)":     -6,
    "Pacific — Los Angeles (PT)": -7,
    "Atlantic — Halifax":         -3,
    "London / Lisbon (BST)":       1,
    "Paris / Madrid (CEST)":       2,
    "Dubai (GST)":                 4,
    "India (IST)":                 5,
    "Manila / Singapore (PHT)":    8,
    "Tokyo / Seoul (JST)":         9,
    "Sydney (AEST)":              10,
}


def _convert_time(kickoff: str, tz_str: str, target_offset: int) -> str:
    """Convert 'HH:MM' + 'UTC±N' source tz to target offset string."""
    if not kickoff or kickoff == "TBD":
        return "TBD"
    try:
        h, m    = map(int, kickoff.split(":"))
        src_off = int(tz_str.replace("UTC", "").strip() or "0")
        total   = (h * 60 + m - src_off * 60 + target_offset * 60) % (24 * 60)
        return f"{total // 60:02d}:{total % 60:02d}"
    except Exception:
        return kickoff


def render():
    st.title("🏆 Bracket & Schedule")
    st.caption("Interactive knockout bracket · All 104 matches · Times in your timezone")

    tab1, tab2 = st.tabs(["🏆 Knockout bracket", "📅 Full schedule"])
    with tab1:
        _render_bracket()
    with tab2:
        _render_schedule()


# ══════════════════════════════════════════════════════════════════════════════
# Tab 1: Knockout bracket
# ══════════════════════════════════════════════════════════════════════════════

def _render_bracket():
    st.caption(
        "Click any match for details. Bracket fills as matches are completed. "
        "Group stage runs June 11–27 before the bracket begins."
    )

    tz_label  = st.selectbox("Your timezone", list(TIMEZONES.keys()),
                              key="bracket_tz")
    tz_offset = TIMEZONES[tz_label]

    all_fix   = get_all_fixtures()
    rounds: dict[str, list] = {}

    for f in all_fix:
        r = f.get("round", "") or f.get("group", "")
        if r in ("Round of 32","Round of 16","Quarter-finals",
                 "Semi-finals","Final","Third Place"):

            score_str = ""
            if f["home_goals"] is not None:
                score_str = f"{f['home_goals']}–{f['away_goals']}"
                if f["status"] in ("AET","Penalties"):
                    score_str += f" ({f['status']})"

            local_time = _convert_time(
                f.get("kickoff",""), f.get("timezone","UTC+0"), tz_offset
            )

            rounds.setdefault(r, []).append({
                "id":     f["fixture_id"],
                "date":   f["date"],
                "time":   local_time,
                "team1":  f["home_team"],
                "team2":  f["away_team"],
                "score":  score_str,
                "venue":  f["venue_city"].split("(")[0].strip(),
                "status": f["status"],
            })

    for r in rounds:
        rounds[r].sort(key=lambda x: x["id"])

    rounds_json = json.dumps(rounds, ensure_ascii=False)
    html = _bracket_html(rounds_json, tz_label)
    components.html(html, height=1000, scrolling=True)


def _bracket_html(rounds_json: str, tz_label: str) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:13px;
     background:transparent;color:#2c2c2a}}
.wrap{{padding:12px 8px;overflow-x:auto}}
.bracket{{display:flex;gap:0;min-width:960px;align-items:flex-start}}
.rcol{{display:flex;flex-direction:column}}
.rtitle{{font-size:10px;font-weight:500;color:#888;text-transform:uppercase;
         letter-spacing:.06em;text-align:center;padding:0 6px 10px;white-space:nowrap}}
.mcol{{display:flex;flex-direction:column;justify-content:space-around}}
.mwrap{{display:flex;align-items:center}}
.match{{background:#fff;border:.5px solid #d3d1c7;border-radius:8px;
        width:148px;overflow:hidden;cursor:pointer;flex-shrink:0;
        transition:border-color .15s,box-shadow .15s}}
.match:hover{{border-color:#888}}
.match.done{{border-color:#9fe1cb}}
.match.sel{{border-color:#185fa5;box-shadow:0 0 0 2px #b5d4f4}}
.tr{{display:flex;align-items:center;padding:5px 8px;gap:4px;
     border-bottom:.5px solid #f1efe8}}
.tr:last-child{{border-bottom:none}}
.tn{{flex:1;font-size:11.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#2c2c2a}}
.tn.tbd{{color:#b4b2a9;font-style:italic}}
.ts2{{font-size:11.5px;font-weight:500;min-width:16px;text-align:right}}
.mm{{padding:2px 8px;background:#f8f7f4;border-top:.5px solid #f1efe8;
     font-size:10px;color:#888;display:flex;justify-content:space-between}}
.conn{{width:14px;flex-shrink:0;align-self:stretch;display:flex;flex-direction:column;justify-content:space-around}}

.panel{{background:#fff;border:.5px solid #d3d1c7;border-radius:10px;
        padding:14px 16px;margin:10px 0;display:none}}
.panel.vis{{display:block}}
.panel h3{{font-size:14px;font-weight:500;margin-bottom:6px}}
.meta{{font-size:11px;color:#888;margin-bottom:2px}}
.sb{{display:flex;align-items:center;gap:10px;margin:10px 0}}
.sb-t{{flex:1;font-size:13px;font-weight:500}}
.sb-s{{font-size:18px;font-weight:500;color:#185fa5;min-width:56px;text-align:center}}
.badge{{display:inline-block;font-size:10px;padding:2px 7px;border-radius:4px}}
.done-b{{background:#e1f5ee;color:#0f6e56}}
.up-b{{background:#e6f1fb;color:#0c447c}}
.final-wrap{{display:flex;flex-direction:column;align-items:center;gap:16px;padding-top:10px}}
.fin-label{{font-size:10px;color:#888;text-align:center;margin-bottom:4px}}
@media(prefers-color-scheme:dark){{
  body{{color:#c2c0b6}}
  .match,.panel{{background:#1e1e1c;border-color:#444441}}
  .match.done{{border-color:#0f6e56}}
  .tr{{border-color:#2c2c2a}}
  .tn{{color:#c2c0b6}}
  .mm{{background:#2c2c2a;border-color:#444441;color:#888}}
  .rtitle{{color:#888}}
  .done-b{{background:#04342c;color:#9fe1cb}}
  .up-b{{background:#042c53;color:#b5d4f4}}
  .fin-label{{color:#888}}
}}
</style></head><body>
<div class="wrap">
<div id="panel" class="panel">
  <h3 id="p-title"></h3>
  <div class="meta" id="p-meta"></div>
  <div class="meta" id="p-venue"></div>
  <div class="sb">
    <span class="sb-t" id="p-home"></span>
    <span class="sb-s" id="p-score"></span>
    <span class="sb-t" style="text-align:right" id="p-away"></span>
  </div>
  <span class="badge" id="p-badge"></span>
</div>
<div class="bracket" id="br"></div>
</div>
<script>
const RD={rounds_json};
const ORDER=["Round of 32","Round of 16","Quarter-finals","Semi-finals"];
const SHORT={{"Round of 32":"R32","Round of 16":"R16","Quarter-finals":"QF","Semi-finals":"SF"}};
let selId=null;

function isTBD(n){{return !n||/^[12][A-L]$/.test(n)||/^[WL][0-9]+$/.test(n)||/^3rd/.test(n)}}

function mCard(m){{
  const done=["Match Finished","AET","Penalties"].includes(m.status);
  const sel=m.id===selId;
  let s1="",s2="";
  if(m.score){{const p=m.score.split("–");s1=p[0];s2=(p[1]||"").split(" ")[0]}}
  const t1=isTBD(m.team1),t2=isTBD(m.team2);
  return `<div class="match${{done?" done":""}}${{sel?" sel":""}}"
    onclick="sel(${{JSON.stringify(m).replace(/"/g,"&quot;")}})" data-id="${{m.id}}">
    <div class="tr"><span class="tn${{t1?" tbd":""}}">${{m.team1||"TBD"}}</span>
      ${{m.score?`<span class="ts2">${{s1}}</span>`:""}}
    </div>
    <div class="tr"><span class="tn${{t2?" tbd":""}}">${{m.team2||"TBD"}}</span>
      ${{m.score?`<span class="ts2">${{s2}}</span>`:""}}
    </div>
    <div class="mm"><span>${{m.date?m.date.slice(5):""}}</span><span>${{m.time}}</span></div>
  </div>`;
}}

function buildCol(round, gapPx){{
  const ms=RD[round]||[];
  if(!ms.length) return null;
  const col=document.createElement("div");
  col.className="rcol";
  col.innerHTML=`<div class="rtitle">${{SHORT[round]||round}}</div>`;
  const mc=document.createElement("div");
  mc.className="mcol";
  mc.style.gap=gapPx+"px";
  ms.forEach(m=>{{
    const w=document.createElement("div");
    w.className="mwrap";
    w.innerHTML=mCard(m);
    mc.appendChild(w);
  }});
  col.appendChild(mc);
  return col;
}}

function buildBracket(){{
  const br=document.getElementById("br");
  const gaps={{"Round of 32":4,"Round of 16":10,"Quarter-finals":24,"Semi-finals":56}};
  ORDER.forEach((round,i)=>{{
    const col=buildCol(round,gaps[round]||8);
    if(col){{
      br.appendChild(col);
      if(i<ORDER.length-1){{
        const c=document.createElement("div");
        c.className="conn";
        br.appendChild(c);
      }}
    }}
  }});

  // Final + third place
  const fw=document.createElement("div");
  fw.className="rcol";
  const fin=(RD["Final"]||[])[0];
  const tp=(RD["Third Place"]||[])[0];
  const fwrap=document.createElement("div");
  fwrap.className="final-wrap";
  if(fin){{
    fwrap.innerHTML=`<div><div class="fin-label">FINAL · Jul 19</div>${{mCard(fin)}}</div>`;
  }}
  if(tp){{
    fwrap.innerHTML+=`<div><div class="fin-label">3RD PLACE · Jul 18</div>${{mCard(tp)}}</div>`;
  }}
  fw.innerHTML=`<div class="rtitle">Final</div>`;
  fw.appendChild(fwrap);
  br.appendChild(fw);
}}

function sel(m){{
  selId=m.id;
  document.querySelectorAll(".match").forEach(el=>el.classList.remove("sel"));
  document.querySelectorAll(`[data-id="${{m.id}}"]`).forEach(el=>el.classList.add("sel"));
  const done=["Match Finished","AET","Penalties"].includes(m.status);
  const t1=isTBD(m.team1),t2=isTBD(m.team2);
  document.getElementById("panel").classList.add("vis");
  document.getElementById("p-title").textContent=(t1?"TBD":m.team1)+" vs "+(t2?"TBD":m.team2);
  document.getElementById("p-meta").textContent=m.date+(m.time?"  ·  "+m.time:"")+"  ·  {tz_label}";
  document.getElementById("p-venue").textContent="📍 "+m.venue;
  document.getElementById("p-home").textContent=t1?"TBD":m.team1;
  document.getElementById("p-away").textContent=t2?"TBD":m.team2;
  document.getElementById("p-score").textContent=done&&m.score?m.score:"vs";
  const badge=document.getElementById("p-badge");
  badge.textContent=done?(m.status==="Match Finished"?"FT":m.status):"Upcoming";
  badge.className="badge "+(done?"done-b":"up-b");
}}

buildBracket();
</script></body></html>"""


# ══════════════════════════════════════════════════════════════════════════════
# Tab 2: Full schedule with timezone converter
# ══════════════════════════════════════════════════════════════════════════════

def _render_schedule():
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        tz_label  = st.selectbox("Your timezone", list(TIMEZONES.keys()),
                                  key="sched_tz")
    with col2:
        stage = st.selectbox("Stage", [
            "All", "Group stage", "Round of 32", "Round of 16",
            "Quarter-finals", "Semi-finals", "Final",
        ])
    with col3:
        search = st.text_input("Team", placeholder="Brazil…")

    tz_offset = TIMEZONES[tz_label]
    fixtures  = get_all_fixtures()

    # Filter
    if stage != "All":
        if stage == "Group stage":
            fixtures = [f for f in fixtures if f.get("group")]
        else:
            fixtures = [f for f in fixtures if f.get("round") == stage]
    if search:
        s = search.lower()
        fixtures = [f for f in fixtures
                    if s in f["home_team"].lower() or s in f["away_team"].lower()]

    if not fixtures:
        st.info("No matches match that filter.")
        return

    # Count completed vs upcoming
    done    = sum(1 for f in fixtures if f["home_goals"] is not None)
    pending = len(fixtures) - done
    c1, c2, c3 = st.columns(3)
    c1.metric("Total matches", len(fixtures))
    c2.metric("Completed",     done)
    c3.metric("Upcoming",      pending)

    st.caption(f"Times shown in **{tz_label}**")
    st.divider()

    # Group by date
    by_date: dict[str, list] = {}
    for f in fixtures:
        by_date.setdefault(f["date"], []).append(f)

    for date_str in sorted(by_date.keys()):
        try:
            dt         = datetime.strptime(date_str, "%Y-%m-%d")
            date_label = dt.strftime("%A, %B %-d, %Y")
        except Exception:
            date_label = date_str

        st.markdown(f"#### {date_label}")

        for f in by_date[date_str]:
            home = f["home_team"]
            away = f["away_team"]
            hg   = f["home_goals"]
            ag   = f["away_goals"]
            lt   = _convert_time(
                f.get("kickoff",""), f.get("timezone","UTC+0"), tz_offset
            )

            c1, c2, c3, c4 = st.columns([3, 2, 3, 3])
            with c1:
                st.markdown(f"**{home}**")
            with c2:
                if hg is not None:
                    line = f"{hg} – {ag}"
                    if f["status"] in ("AET","Penalties"):
                        line += f" ({f['status']})"
                    st.markdown(
                        f"<div style='text-align:center;font-weight:500'>✅ {line}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='text-align:center;color:gray'>🕐 {lt}</div>",
                        unsafe_allow_html=True,
                    )
            with c3:
                st.markdown(
                    f"<div style='text-align:right'><b>{away}</b></div>",
                    unsafe_allow_html=True,
                )
            with c4:
                label = f.get("group") or f.get("round","")
                venue = f.get("venue_city","").split("(")[0].strip()
                st.caption(f"{label} · {venue}")

        st.divider()
