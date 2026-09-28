"""What will tomorrow's prices be? — the benchmark, and the models that must beat it.

Everything here takes a feature frame and returns one predicted price per delivery
hour.  Nothing here decides what a feature is allowed to be; `features.py` settled
that, and this file simply uses what it was handed.

Every function here follows one shape: **in goes a frame, out comes a Series on the
same index.**  That shape is what lets `evaluate.py` line a forecast up against the
actual prices without knowing, or caring, which model produced it.
"""

from __future__ import annotations

import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression

from src import features as F


# ── The benchmark — WORKED EXAMPLE, already written ───────────────────────────
# Whatever is built must beat doing nothing clever.  For day-ahead prices the
# standard "nothing clever" is: tomorrow's 3 p.m. will be whatever last week's 3
# p.m. was.
#
# One week rather than one day, because a week lands on the same weekday.  A
# Saturday predicted from a Friday is wrong in a way that has nothing to do with
# forecasting skill — the whole daily shape differs — so a one-day rule would set a
# bar that is too low to be honest.
#
# Note there is no fitting here and nothing is learned.  That is the point: this is
# the score to beat, and it costs nothing to produce.

def naive_forecast(frame: pd.DataFrame) -> pd.Series:
    """Predict each hour with the price of the same hour one week earlier."""
    return frame["price_lag_168h"].rename("naive")      # already in the frame; no work to do


# ── Estimators ────────────────────────────────────────────────────────────────
# Two, and deliberately only two.
#
# The straight-line model is here because it can be checked by hand: seventeen
# numbers, one per column, saying how much each one moves the price.  If it does
# something surprising, you can read why.
#
# The tree model is here because the relationship plainly is not a straight line —
# the same residual load cleared near 42 EUR/MWh in 2019 and near 119 in 2025.  It
# sets a realistic bar for stage 2 to improve on.
#
# No tuning, no scaling, no search.  Stage 1 asks one question — does modelling beat
# not-modelling — and a tuned model answers it no better than an untuned one.
#
# The seed on the tree model is not decoration.  It fixes the random choices made
# while fitting, so the same data gives the same answer twice.  Without it a number
# printed in the README could not be regenerated from a clean clone.

def linear() -> BaseEstimator:
    """An ordinary least-squares fit: one coefficient per feature."""
    return LinearRegression()


def gbm() -> BaseEstimator:
    """Gradient-boosted trees: many small rules, each correcting the last."""
    return HistGradientBoostingRegressor(random_state=0)


# ── Fitting, and the one line that matters ────────────────────────────────────
# Training shows the model both the features and the answers, and that is not
# leakage — it is what learning is.  The discipline is elsewhere: when the model is
# asked to *predict*, it gets the features and nothing else.
#
# `F.feature_columns(frame)` returns every column except the target.  Using it in
# both functions below is what keeps that promise, in one place, checkably.
#
# `forecast` returns a Series carrying the frame's own index rather than the bare
# array `predict` hands back.  An array has no timestamps, so `evaluate.aligned` would
# have nothing to match on and every score would depend on the row order happening to
# agree — which it does not, once a forecast covers one split and the prices cover
# seven years.

def fit(estimator: BaseEstimator, frame: pd.DataFrame) -> BaseEstimator:
    """Learn from a frame of complete rows. Returns the fitted estimator."""
    features = F.feature_columns(frame)                 # every column except the answer
    estimator.fit(frame[features], frame[F.TARGET])     # showing it the answers is the training
    return estimator


def forecast(model: BaseEstimator, frame: pd.DataFrame) -> pd.Series:
    """Predict one price per delivery hour, indexed like the frame it came from."""
    features = F.feature_columns(frame)                 # the same call, so the same promise
    return pd.Series(model.predict(frame[features]), index=frame.index, name="predicted")