Here is the complete project brief for your World Cup 2026 dashboard. This outlines the full scope, verifies the necessary API endpoints, and details the architecture for your predictive modeling.

### **Project Brief: World Cup 2026 Live Analytics & Prediction Dashboard**

**Objective:**
To deploy a real-time, rate-limit-protected web application using Python and Streamlit that provides live match updates, news, and advanced predictive analytics for the 2026 FIFA World Cup.

#### **1. System Requirements**

* **Frontend & State Management:** Streamlit (Python), `streamlit-autorefresh` for hands-free live updates.
* **Backend & Caching:** Python `requests` library, Streamlit `@st.cache_data` (TTL configured to 60 seconds for live data, 1-24 hours for historical/static data) to prevent API exhaustion.
* **Deployment:** Dockerized container hosted on a cloud provider (e.g., AWS, Heroku, or Streamlit Community Cloud) for global accessibility.
* **Machine Learning Stack:** `scikit-learn`, `xgboost`, or `statsmodels` for the prediction engine, `pandas` and `numpy` for data manipulation.

#### **2. Verified API Integration Plan**

To populate the dashboard with accurate data, including player ratings and cards, you will need a robust sports data provider. Based on current available infrastructure, here are the exact endpoints you can use from the two leading providers:

**Option A: API-Football (via RapidAPI)** *Recommended for broad feature sets.*

* **Live Scores:** `GET /fixtures?live=all&league=15&season=2026` (Updates every 15 seconds).
* **Player Stats, Ratings & Cards:** `GET /fixtures/players?fixture={id}`. This returns in-match player ratings, yellow/red cards, passes, and shots.
* **Built-in Predictions:** `GET /predictions?fixture={id}` (Provides baseline probability data if you want to compare it against your own model).

**Option B: Sportmonks (v3 API)** *Recommended for deep, highly granular statistics.*

* **Live Scores:** `GET /v3/football/livescores/inplay`.
* **Player Statistics:** `GET /v3/football/players/{id}?include=statistics.details.type`. You can filter for specific event types like `118` (Rating), `84` (Yellow Cards), and `83` (Red Cards).

**News API:**

* `GET https://newsapi.org/v2/everything?q="World Cup 2026"` for the latest tournament articles.

#### **3. Predictive Modeling Strategy**

Building a model to predict match results is standard, but predicting player ratings and specific card counts introduces high variance. Here is the realistic approach to building these models:

* **Match Results (Win/Draw/Loss):**
* **Method:** Use a bivariate Poisson regression model or an XGBoost classifier.
* **Features:** Historical Head-to-Head, current tournament Expected Goals (xG), FIFA World Ranking differentials, and travel fatigue (critical for 2026 due to the geographic spread across North America).


* **Discipline (Red & Yellow Cards):**
* **Method:** Negative Binomial Regression (better suited for over-dispersed count data than standard Poisson).
* **Features:** The assigned referee's historical cards-per-match rate (this is the strongest predictor), historical team foul rates, and match stakes (e.g., knockout stage vs. group stage).


* **Player Ratings:**
* **Method:** Random Forest Regressor.
* **Features:** Expected minutes played, opponent defensive strength, player form in the last 5 matches, and position (forwards often have higher variance in ratings than defenders).



---

### **Visualizing the Prediction Engine**

To understand how these different variables interact within your application before you write the complex Python backend, we can simulate the logic. Adjusting team strength and match volatility will directly shift the predicted outcomes for scores and cards.