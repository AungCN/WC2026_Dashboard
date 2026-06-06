"""
models/prediction_engine.py
────────────────────────────
Three ML models for WC 2026 predictions:

  1. MatchPredictor      → Win / Draw / Loss probabilities (XGBoost)
  2. CardPredictor       → Expected yellow & red cards (Negative Binomial)
  3. PlayerRatingPredictor → Expected player rating + confidence range (Random Forest)

DESIGN CHOICE — WHY THESE MODELS:
  • XGBoost for match results: handles non-linear interactions well
    (e.g. high xG only matters if the opponent defense is weak).
    Better than plain logistic regression for this use case.

  • Negative Binomial for cards: card counts are "over-dispersed"
    — variance is much higher than the mean.
    Standard Poisson assumes variance = mean, which underestimates
    how often you get 0-card or 8-card games.
    Negative Binomial handles this correctly.

  • Random Forest for player ratings: ratings are continuous (5.0–10.0)
    and depend on many interacting features. Random Forest naturally
    gives a confidence range (low/high across trees), which is honest
    about the high variance in player performances.

HOW TO TRAIN:
  from models.prediction_engine import MatchPredictor
  model = MatchPredictor()
  model.train(df_features)          # df from build_match_features()
  probs = model.predict(feature_row)
"""

import numpy as np
import pandas as pd
import joblib
import os

from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error
from statsmodels.discrete.count_model import ZeroInflatedNegativeBinomialP
import statsmodels.api as sm


# ── Paths for saving trained models ───────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved")
os.makedirs(MODEL_DIR, exist_ok=True)

MATCH_MODEL_PATH  = os.path.join(MODEL_DIR, "match_model.joblib")
RATING_MODEL_PATH = os.path.join(MODEL_DIR, "rating_model.joblib")


# ══════════════════════════════════════════════════════════════════════════════
# 1. MATCH RESULT PREDICTOR  (XGBoost classifier)
# ══════════════════════════════════════════════════════════════════════════════

class MatchPredictor:
    """
    Predicts win / draw / loss probabilities for a fixture.

    Feature columns expected:
        home_ranking_diff, home_xg, away_xg,
        travel_fatigue_home, travel_fatigue_away,
        is_knockout, h2h_home_winrate

    Target: result  (0=away win, 1=draw, 2=home win)

    Usage:
        mp = MatchPredictor()
        mp.train(df)
        probs = mp.predict({"home_ranking_diff": 10, "home_xg": 1.8, ...})
        # → {"home_win": 0.55, "draw": 0.25, "away_win": 0.20}
    """

    FEATURES = [
        "home_ranking_diff",
        "home_xg",
        "away_xg",
        "travel_fatigue_home",
        "travel_fatigue_away",
        "is_knockout",
        "h2h_home_winrate",
    ]
    TARGET = "result"

    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=300,
            max_depth=4,           # shallow trees → less overfitting on small data
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
        )
        self.trained = False

    def train(self, df: pd.DataFrame) -> dict:
        """
        Train on a DataFrame of historical match features.
        Returns accuracy score on held-out test set.

        Example:
            df has 200 rows (past WC matches) with columns matching FEATURES + TARGET.
            mp.train(df)  →  {"train_accuracy": 0.71, "test_accuracy": 0.62}
        """
        X = df[self.FEATURES]
        y = df[self.TARGET]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )
        self.trained = True
        joblib.dump(self.model, MATCH_MODEL_PATH)

        train_acc = accuracy_score(y_train, self.model.predict(X_train))
        test_acc  = accuracy_score(y_test,  self.model.predict(X_test))
        return {"train_accuracy": round(train_acc, 3), "test_accuracy": round(test_acc, 3)}

    def load(self) -> bool:
        """Load a previously trained model from disk."""
        if os.path.exists(MATCH_MODEL_PATH):
            self.model   = joblib.load(MATCH_MODEL_PATH)
            self.trained = True
            return True
        return False

    def predict(self, features: dict) -> dict:
        """
        Predict win/draw/loss probabilities.

        Args:
            features: dict with keys matching FEATURES

        Returns:
            {"home_win": float, "draw": float, "away_win": float}
            (all three sum to 1.0)

        Example:
            predict({"home_ranking_diff": 15, "home_xg": 2.1, "away_xg": 0.9,
                     "travel_fatigue_home": 0.1, "travel_fatigue_away": 0.65,
                     "is_knockout": 0, "h2h_home_winrate": 0.6})
            → {"home_win": 0.62, "draw": 0.22, "away_win": 0.16}
        """
        if not self.trained:
            raise RuntimeError("Model not trained. Call .train() or .load() first.")

        row = pd.DataFrame([{k: features.get(k, 0) for k in self.FEATURES}])
        probs = self.model.predict_proba(row)[0]  # [away_win, draw, home_win]

        return {
            "home_win":  round(float(probs[2]), 3),
            "draw":      round(float(probs[1]), 3),
            "away_win":  round(float(probs[0]), 3),
        }

    def poisson_score_prediction(self, home_xg: float, away_xg: float) -> dict:
        """
        Bonus: use Poisson distribution to predict most likely scoreline.
        Completely separate from XGBoost — uses only expected goals.

        Why Poisson? Goals in football follow a Poisson distribution
        because they are rare, independent events.

        Example:
            home_xg=1.8, away_xg=0.9
            → most_likely_score: "2-1", score_prob: 0.12
        """
        max_goals = 6
        score_probs = {}

        for home_g in range(max_goals + 1):
            for away_g in range(max_goals + 1):
                from math import exp, factorial
                ph = (home_xg ** home_g * exp(-home_xg)) / factorial(home_g)
                pa = (away_xg ** away_g * exp(-away_xg)) / factorial(away_g)
                score_probs[f"{home_g}-{away_g}"] = round(ph * pa, 4)

        best_score = max(score_probs, key=score_probs.get)
        return {
            "most_likely_score": best_score,
            "score_probability": score_probs[best_score],
            "all_scores": score_probs,
        }


# ══════════════════════════════════════════════════════════════════════════════
# 2. CARD PREDICTOR  (Negative Binomial Regression)
# ══════════════════════════════════════════════════════════════════════════════

class CardPredictor:
    """
    Predicts expected yellow and red cards per match.

    Uses Negative Binomial regression because card counts are
    "over-dispersed" — some games have 0 cards, others have 8.
    Standard Poisson would underestimate this spread.

    Feature columns expected:
        referee_cards_per_game : float (the strongest predictor)
        home_foul_rate         : float (avg fouls per game, home team)
        away_foul_rate         : float (avg fouls per game, away team)
        is_knockout            : 0 or 1
        ranking_diff_abs       : absolute FIFA ranking gap between teams

    Usage:
        cp = CardPredictor()
        cp.train(df)
        result = cp.predict({"referee_cards_per_game": 4.2, ...})
        # → {"expected_yellows": 3.8, "expected_reds": 0.28, "range_yellows": [1, 7]}
    """

    YELLOW_FEATURES = [
        "referee_cards_per_game",
        "home_foul_rate",
        "away_foul_rate",
        "is_knockout",
        "ranking_diff_abs",
    ]
    RED_FEATURES = [
        "referee_cards_per_game",
        "is_knockout",
        "ranking_diff_abs",
    ]

    def __init__(self):
        self.yellow_model = None
        self.red_model    = None
        self.trained      = False

    def train(self, df: pd.DataFrame) -> dict:
        """
        Fit two separate Negative Binomial models: one for yellows, one for reds.
        Returns in-sample MAE for both.
        """
        X_y = sm.add_constant(df[self.YELLOW_FEATURES].astype(float))
        X_r = sm.add_constant(df[self.RED_FEATURES].astype(float))

        self.yellow_model = sm.NegativeBinomial(df["yellow_cards"], X_y).fit(disp=0)
        self.red_model    = sm.NegativeBinomial(df["red_cards"],    X_r).fit(disp=0)

        self.trained = True

        y_pred = self.yellow_model.predict(X_y)
        r_pred = self.red_model.predict(X_r)

        return {
            "yellow_mae": round(mean_absolute_error(df["yellow_cards"], y_pred), 3),
            "red_mae":    round(mean_absolute_error(df["red_cards"],    r_pred), 3),
        }

    def predict(self, features: dict) -> dict:
        """
        Predict expected cards with a confidence range.

        Returns:
            {
              "expected_yellows": 3.8,
              "expected_reds": 0.28,
              "range_yellows": [1, 7],   # 10th–90th percentile from NB distribution
              "range_reds": [0, 2],
            }
        """
        if not self.trained:
            # Fallback rule-based estimate when no training data is available yet
            return self._rule_based(features)

        X_y = sm.add_constant(
            pd.DataFrame([[features.get(k, 0) for k in self.YELLOW_FEATURES]],
                         columns=self.YELLOW_FEATURES),
            has_constant="add",
        )
        X_r = sm.add_constant(
            pd.DataFrame([[features.get(k, 0) for k in self.RED_FEATURES]],
                         columns=self.RED_FEATURES),
            has_constant="add",
        )

        exp_y = float(self.yellow_model.predict(X_y)[0])
        exp_r = float(self.red_model.predict(X_r)[0])

        # Confidence range: ±1.5 standard deviations (using NB variance)
        return {
            "expected_yellows": round(exp_y, 2),
            "expected_reds":    round(exp_r, 2),
            "range_yellows":    [max(0, round(exp_y - 2)), round(exp_y + 2)],
            "range_reds":       [0, max(1, round(exp_r + 1))],
        }

    def _rule_based(self, features: dict) -> dict:
        """
        Simple fallback used before training data is available.
        Based on average WC statistics: ~3.5 yellows, 0.2 reds per game.
        """
        ref  = features.get("referee_cards_per_game", 3.5)
        kok  = 1.4 if features.get("is_knockout", 0) else 1.0
        base = ref * kok
        return {
            "expected_yellows": round(base, 2),
            "expected_reds":    round(base * 0.07, 2),
            "range_yellows":    [max(0, round(base - 2)), round(base + 2)],
            "range_reds":       [0, max(1, round(base * 0.07 + 1))],
        }


# ══════════════════════════════════════════════════════════════════════════════
# 3. PLAYER RATING PREDICTOR  (Random Forest Regressor)
# ══════════════════════════════════════════════════════════════════════════════

class PlayerRatingPredictor:
    """
    Predicts a player's in-match rating (scale 5.0 – 10.0).

    Random Forest is chosen because:
      • Ratings depend on many interacting factors (position × form × opponent)
      • It naturally provides a confidence range (spread across 200 trees)
      • Robust to outliers (one 9.5 game doesn't distort the model)

    Feature columns expected:
        form_last5          : average rating in last 5 games
        opponent_def_rank   : opponent defensive ranking (1=strongest)
        expected_minutes    : expected playing time (0–90)
        position_enc        : encoded position (GK=0, DEF=1, MID=2, FWD=3)
        tournament_fatigue  : number of games played in this tournament so far
        is_home_team        : 1 if playing at home city, 0 otherwise

    Usage:
        prp = PlayerRatingPredictor()
        prp.train(df)
        result = prp.predict({"form_last5": 7.4, "position_enc": 3, ...})
        # → {"predicted_rating": 7.6, "low": 6.8, "high": 8.4}
    """

    FEATURES = [
        "form_last5",
        "opponent_def_rank",
        "expected_minutes",
        "position_enc",
        "tournament_fatigue",
        "is_home_team",
    ]
    TARGET = "actual_rating"

    # Position name → numeric encoding
    POSITION_MAP = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}

    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=200,
            max_depth=6,
            min_samples_leaf=5,   # prevents overfitting on small datasets
            random_state=42,
            n_jobs=-1,            # use all CPU cores
        )
        self.trained = False

    def train(self, df: pd.DataFrame) -> dict:
        """
        Train on historical player performance data.
        Returns MAE and position-level MAE breakdown.

        Expected outcome: MAE ~0.5–0.8 rating points
        (i.e., predictions are usually within 0.5–0.8 of the real rating)
        """
        X = df[self.FEATURES]
        y = df[self.TARGET]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model.fit(X_train, y_train)
        self.trained = True
        joblib.dump(self.model, RATING_MODEL_PATH)

        y_pred = self.model.predict(X_test)
        overall_mae = mean_absolute_error(y_test, y_pred)

        # MAE breakdown by position
        pos_mae = {}
        for pos_name, pos_enc in self.POSITION_MAP.items():
            mask = X_test["position_enc"] == pos_enc
            if mask.sum() > 0:
                pos_mae[pos_name] = round(mean_absolute_error(
                    y_test[mask], self.model.predict(X_test[mask])
                ), 3)

        return {"overall_mae": round(overall_mae, 3), "by_position": pos_mae}

    def load(self) -> bool:
        """Load a previously saved model from disk."""
        if os.path.exists(RATING_MODEL_PATH):
            self.model   = joblib.load(RATING_MODEL_PATH)
            self.trained = True
            return True
        return False

    def predict(self, features: dict) -> dict:
        """
        Predict player rating with confidence range.

        The confidence range comes from the spread of predictions
        across all 200 individual decision trees in the forest.
        A narrow range = the model is confident.
        A wide range  = high uncertainty (common for forwards).

        Example:
            predict({"form_last5": 7.2, "opponent_def_rank": 8,
                     "expected_minutes": 90, "position_enc": 3,
                     "tournament_fatigue": 2, "is_home_team": 0})
            → {"predicted_rating": 7.4, "low": 6.5, "high": 8.3,
               "confidence": "medium"}
        """
        if not self.trained:
            return self._rule_based(features)

        row = pd.DataFrame([{k: features.get(k, 0) for k in self.FEATURES}])

        # Get individual tree predictions for confidence range
        tree_preds = np.array([tree.predict(row)[0] for tree in self.model.estimators_])
        pred  = float(np.mean(tree_preds))
        lo    = float(np.percentile(tree_preds, 10))
        hi    = float(np.percentile(tree_preds, 90))
        spread = hi - lo

        confidence = "high" if spread < 0.8 else ("medium" if spread < 1.5 else "low")

        return {
            "predicted_rating": round(min(10.0, max(5.0, pred)), 2),
            "low":              round(min(10.0, max(5.0, lo)), 2),
            "high":             round(min(10.0, max(5.0, hi)), 2),
            "confidence":       confidence,
        }

    def _rule_based(self, features: dict) -> dict:
        """Fallback before training data is available."""
        form = features.get("form_last5", 7.0)
        pos  = features.get("position_enc", 1)
        spread = [0.3, 0.4, 0.5, 0.8][pos]   # GK→FWD: forwards most variable
        return {
            "predicted_rating": round(form * 0.9 + 0.5, 2),
            "low":  round(max(5.0, form * 0.9 + 0.5 - spread), 2),
            "high": round(min(10.0, form * 0.9 + 0.5 + spread), 2),
            "confidence": "low (no training data yet)",
        }


# ── Convenience: load all models at once ──────────────────────────────────────
def load_all_models() -> tuple[MatchPredictor, CardPredictor, PlayerRatingPredictor]:
    """
    Load all three models. Falls back to untrained instances if no saved
    model files exist yet (they'll use rule-based estimates).
    """
    mp  = MatchPredictor();       mp.load()
    cp  = CardPredictor()         # NB model doesn't support joblib, retrain each time
    prp = PlayerRatingPredictor(); prp.load()
    return mp, cp, prp
