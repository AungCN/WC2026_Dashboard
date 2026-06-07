# ⚽ World Cup 2026 — Live Analytics & Prediction Dashboard

A free, open-source Streamlit dashboard for the 2026 FIFA World Cup.
Live scores, match schedules, group standings, news, and ML-powered predictions — all without a paid API.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What it does

| Page | What you see |
|---|---|
| 🟢 Live Scores | Today's fixtures, results, goal scorers, group standings, top scorers |
| 📰 News Feed | Latest WC 2026 articles from BBC, Guardian, ESPN, Goal.com — no API key |
| 🔮 Match Predictions | Win/Draw/Loss probabilities, most likely scoreline, card forecast |
| ⭐ Player Ratings | Predicted ratings for all 48 team squads, with confidence ranges |

---

## Data sources

Everything is free. No paid API required.

| Source | What it provides | Key |
|---|---|---|
| [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json) | Live scores and goal scorers (updated post-match) | None |
| [openfootball/world-cup](https://github.com/openfootball/world-cup) | All 104 fixtures, correct confirmed team names | None |
| `data/wc2026_data.py` | Groups, squads, stadiums, referees, FIFA rankings | None — static file |
| RSS feeds | News from BBC, Guardian, ESPN, Goal.com, Google News | None |

The app uses the same data source as [wcup2026.org](https://wcup2026.org) — openfootball, which is public domain.

---

## Project structure

```
wc2026/
├── app.py                      ← Entry point — run this
├── requirements.txt
├── Dockerfile
│
├── data/
│   ├── __init__.py
│   └── wc2026_data.py          ← All static data: 48 teams, 104 fixtures,
│                                  squads, referees, stadiums, FIFA rankings
│
├── models/
│   ├── __init__.py
│   ├── prediction_engine.py    ← 3 ML models (XGBoost, NegBin, Random Forest)
│   ├── train_models.py         ← Optional: run to train on real historical data
│   └── saved/                  ← Trained .joblib files saved here
│
├── pages/
│   ├── __init__.py
│   ├── live_scores.py          ← Scores, standings, goal scorers
│   ├── news_feed.py            ← RSS news aggregator
│   ├── predictions.py          ← Match prediction panel
│   └── player_ratings.py       ← Squad viewer + rating predictions
│
└── utils/
    ├── __init__.py
    ├── api_client.py           ← All data fetching with disk cache
    └── data_helpers.py         ← Travel fatigue model, data parsers
```

---

## Quickstart

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/yourusername/wc2026-dashboard.git
cd wc2026-dashboard/wc2026
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

That's it. The app works immediately with no API keys and no manual setup. On first launch, the ML models auto-train on synthetic data (takes ~10 seconds, once per session).

---

## Optional: train models on real data

The prediction models auto-train on synthetic data by default. To train on real WC 2018 and 2022 historical data from the API, add your RapidAPI key first (see Configuration below), then run:

```bash
python models/train_models.py
```

This saves trained `.joblib` files to `models/saved/`. The app loads them on the next start instead of re-training. Expected accuracy with real data: 55–65% for match results (compared to 38–48% on synthetic data).

---

## Configuration

The app works with zero configuration. API keys are only needed for optional enhancements.

Create `.streamlit/secrets.toml`:

```toml
# Optional: real historical data for model training (free tier available)
# Get key at: https://rapidapi.com/api-sports/api/api-football
RAPIDAPI_KEY = "your_key_here"

# Optional: real news articles
# Get key at: https://newsapi.org/register
NEWSAPI_KEY = "your_key_here"
```

When no keys are set the app falls back to:
- **Fixtures / scores:** openfootball GitHub JSON (free, always works)
- **News:** RSS feeds from BBC, Guardian, ESPN (free, no key)
- **ML models:** auto-train on synthetic data on first run

---

## ML prediction models

Three models run inside the app, each auto-training on first use if no saved file exists.

### Match result — XGBoost classifier

Predicts Win / Draw / Loss probabilities.

| Feature | Why it matters |
|---|---|
| FIFA ranking difference | Strongest team-level signal |
| Expected goals (xG) | Attack quality for each team |
| H2H historical win rate | Past head-to-head record |
| Home travel fatigue | Distance flown between venues (unique to WC 2026) |
| Away travel fatigue | Opponent's travel burden |
| Knockout stage flag | Higher stakes = different patterns |

Travel fatigue is a feature unique to WC 2026. The tournament spans three countries — USA, Canada, and Mexico — across 16 cities. A team playing in Vancouver then flying to Miami covers ~4,350 km, roughly London to Tehran. This is modelled using the Haversine formula in `utils/data_helpers.py`.

### Card forecast — Negative Binomial regression

Predicts expected yellow and red cards per match.

Negative Binomial is used instead of standard Poisson because card counts are over-dispersed — some games have 0 cards, others have 8. The model's strongest single predictor is the assigned referee's historical cards-per-game rate.

### Player ratings — Random Forest regressor

Predicts each player's in-match rating (scale 5.0–10.0) with a confidence range.

The confidence range (Low / High) comes from the spread of predictions across all 200 individual trees in the forest. A narrow range means high confidence. Forwards consistently have the widest range — matching real-world data where a striker can score 9.5 one game and 5.8 the next.

---

## Deployment

### Streamlit Community Cloud (free)

1. Push the project to a public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo
3. Set `app.py` as the entry point
4. Add any optional API keys under **Settings → Secrets**
5. Deploy — the app handles cold starts automatically (no pre-training needed)

### Docker

```bash
# Build
docker build -t wc2026-dashboard .

# Run
docker run -p 8501:8501 wc2026-dashboard

# With optional API keys
docker run -p 8501:8501 \
  -e RAPIDAPI_KEY=your_key \
  -e NEWSAPI_KEY=your_key \
  wc2026-dashboard
```

Open [http://localhost:8501](http://localhost:8501).

---

## How scores update

openfootball is not a real-time API. Scores appear in the JSON file within a few hours of each match ending, added manually by the maintainer. The app fetches the file every 5 minutes (disk-cached) and merges any new scores into the fixture list automatically.

For the group stage (June 11 – June 27) and knockout rounds (June 28 – July 19), check the **Live Scores** page after each match ends.

---

## Tournament dates

| Stage | Dates |
|---|---|
| Group stage | June 11 – June 27, 2026 |
| Round of 32 | June 28 – July 3, 2026 |
| Round of 16 | July 4 – July 7, 2026 |
| Quarter-finals | July 9 – July 11, 2026 |
| Semi-finals | July 14 – July 15, 2026 |
| Third place | July 18, 2026 |
| **Final** | **July 19, 2026 — MetLife Stadium, New Jersey** |

---

## Requirements

- Python 3.10 or higher
- See `requirements.txt` for all package versions

---

## License

MIT — free to use, modify, and deploy. Data from openfootball is public domain.

---

## Acknowledgements

- [openfootball](https://github.com/openfootball/worldcup.json) — the open public domain football data project that powers this dashboard
- [wcup2026.org](https://wcup2026.org) — community fan site using the same data source, used for cross-verification
- [Streamlit](https://streamlit.io) — the framework that makes this possible in pure Python
