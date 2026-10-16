"""What will tomorrow's prices be? — the benchmark, and the models that must beat it.

Everything here takes a feature frame and returns one predicted price per delivery
hour.  Nothing here decides what a feature is allowed to be; `features.py` settled
that, and this file simply uses what it was handed.

Every function here follows one shape: **in goes a frame, out comes a Series on the
same index.**  That shape is what lets `evaluate.py` line a forecast up against the
actual prices without knowing, or caring, which model produced it.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import Lasso, LassoLarsIC, LinearRegression, QuantileRegressor

from src import features as F


# ── The benchmarks ────────────────────────────────────────────────────────────
# Whatever is built must beat doing nothing clever.  Two versions of "nothing
# clever" are kept, and since the close of stage 2 the field's is the headline.
#
# The field's rule (epftoolbox, Lago et al. 2021): Tuesday to Friday, tomorrow's
# 3 p.m. is today's 3 p.m.; Saturday to Monday, it is last week's, because a
# weekend day or the Monday after one has a different shape from the day before.
# Yesterday is usually the closer guess, so this is the harder bar to beat.
#
# Ours until then: always last week's 3 p.m.  It was chosen on the reasoning that a
# one-day rule is too easy — wrong, since the field's rule already avoids the
# weekday mismatch and misses less (27.4 against 32.8 EUR/MWh on 2024-25).  It
# stays beside the field's so stages 0–2 can still be read against new numbers.
#
# Neither fits anything.  They are the scores to beat, and cost nothing to produce.

YESTERDAY_DAYS = {1, 2, 3, 4}                           # Tue–Fri; Mon is 0 in pandas


def naive_forecast(frame: pd.DataFrame) -> pd.Series:
    """Predict each hour with the price of the same hour one week earlier."""
    return frame["price_lag_168h"].rename("naive")      # already in the frame; no work to do


def field_naive(frame: pd.DataFrame) -> pd.Series:
    """The field's benchmark: same hour yesterday Tue–Fri, one week earlier Sat–Mon."""
    yesterday = frame.index.dayofweek.isin(YESTERDAY_DAYS)   # grid labels: Berlin weekdays
    return frame["price_lag_24h"].where(yesterday, frame["price_lag_168h"]).rename("naive_field")


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

# ── Walking forward: refitting as the year runs ───────────────────────────────
# A model fitted once on 2018–22 forecasts December 2023 knowing nothing of 2023.
# Refitting lets it keep up, under one rule: **each period is forecast before the
# model may learn from it.**  Every score is still earned on hours the model had not
# seen, which is what the split protects (*walk-forward evaluation*).
#
# Learning from all of day D−1 to forecast day D is legal: D−1's prices were
# published around 13:00 on D−2, a day before the 12:00 decision on D−1.
#
# `every` is a pandas period: "D" daily, "M" monthly, "Y" once a year.  "Y" over
# a single year is one fit on everything before it — the stage 1 recipe, so the
# old numbers must come back unchanged through this path.

def walk_forward(make: Callable[[], BaseEstimator], history: pd.DataFrame,
                 scored: pd.DataFrame, every: str) -> pd.Series:
    """Forecast `scored` period by period, each from a model fitted on everything before it."""
    parts = []
    for _, period in scored.groupby(scored.index.to_period(every)):   # grid labels: Berlin days
        known = history[history.index < period.index.min()]          # strictly before: the rule
        parts.append(forecast(fit(make(), known), period))           # a fresh model each time
    return pd.concat(parts)


# ── LEAR: the field's benchmark, one Lasso per delivery hour ──────────────────
# Lago et al. (2021) and epftoolbox's `_lear.py`, kept as published so the number
# compares with theirs.  Lasso charges each clue for the size of its weight, so
# every clue is first put on one ruler: its median and spread over the window,
# then asinh to squash the spikes.  The ruler is measured on the window alone and
# the day being forecast is read with it, never measured itself.  Weekday and
# holiday columns stay 0/1: their spread is zero, and the ruler would divide by it.

WINDOW_DAYS = 364 * 3                                       # epftoolbox's default: 1,092 days
MAD_TO_STD = 0.6744897501960817                             # statsmodels' Gaussian.ppf(3/4), not 0.6745


def robust_ruler(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Median and spread of each column, which a single spike cannot move."""
    median = df.median()
    spread = (df - median).abs().median() / MAD_TO_STD      # MAD, sized like a std
    return median, spread


def _squash(df: pd.DataFrame, ruler: tuple[pd.Series, pd.Series]) -> pd.DataFrame:
    median, spread = ruler
    return np.arcsinh((df - median) / spread)               # aligned by column name


def _unsquash(df: pd.DataFrame, ruler: tuple[pd.Series, pd.Series]) -> pd.DataFrame:
    median, spread = ruler
    return np.sinh(df) * spread + median                    # back to EUR/MWh


# Twenty-four models, one per delivery hour.  AIC picks each one's charge, then a
# plain `Lasso` is refitted at it, as epftoolbox does.  A third of the refits stop
# at 2,500 steps before settling, and scikit-learn warns each time; that warning
# is silenced, as epftoolbox silences it, because on eight days of 2023 forty
# times the steps moved the forecasts by 0.09 EUR/MWh on average.

class LEAR:
    """Twenty-four Lasso models on the day table, all on one robust ruler."""

    def fit(self, X: pd.DataFrame, Y: pd.DataFrame) -> LEAR:
        self.scaled = [c for c in X.columns if not c.startswith(("weekday_", "holiday"))]
        self.x_ruler = robust_ruler(X[self.scaled])         # measured on the window only
        self.y_ruler = robust_ruler(Y)                      # one ruler per delivery hour
        Xs, Ys = self._clues(X), _squash(Y, self.y_ruler)
        self.models = {}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)    # measured harmless: see above
            for hour in Y.columns:
                alpha = LassoLarsIC(criterion="aic", max_iter=2500).fit(Xs, Ys[hour]).alpha_
                self.models[hour] = Lasso(alpha=alpha, max_iter=2500).fit(Xs, Ys[hour])
        return self

    def _clues(self, X: pd.DataFrame) -> pd.DataFrame:
        out = X.copy()
        out[self.scaled] = _squash(X[self.scaled], self.x_ruler)   # weekdays left as 0/1
        return out

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        Xs = self._clues(X)                                 # the window's ruler, not X's own
        z = pd.DataFrame({h: m.predict(Xs) for h, m in self.models.items()}, index=X.index)
        return _unsquash(z, self.y_ruler)


# ── LEAR walking forward, one day at a time ───────────────────────────────────
# The same rule as `walk_forward`, on day rows: each day is forecast from a fresh
# LEAR that has seen only the 1,092 complete days before it.  Counted in complete
# days, as epftoolbox counts rows, so every fit learns from the same amount; the
# blank days of 2022 push the window's start back rather than shrinking it.
# `window=None` keeps every complete day before D instead: the expanding window
# that suited the tree, measured here as LEAR's one variant.
#
# The forecasts are unfolded to hour labels on the way out, so they line up with
# the hourly models' in `evaluate.aligned`.  Nothing is computed in the unfolding.

def lear_walk_forward(table: pd.DataFrame, days: pd.DatetimeIndex,
                      window: int | None = WINDOW_DAYS,
                      make: Callable[[], LEAR] = LEAR) -> pd.Series:
    """Forecast each of `days` from the `window` complete days before it (None: all). Hourly out."""
    clues, answers = F.day_feature_columns(table), F.day_answer_columns(table)
    complete = table.dropna()                               # a fit needs every cell
    parts = []
    for day in days:
        known = complete[complete.index < day]              # strictly before: the rule
        if window is not None:
            known = known.iloc[-window:]                    # the last `window` of them
        model = make().fit(known[clues], known[answers])
        parts.append(model.predict(table.loc[[day], clues]))       # the clues only, never D's prices
    out = pd.concat(parts)
    out.columns = [int(c[-2:]) for c in out.columns]        # "price_d0_h18" -> 18, as unfold reads
    return F.unfold(out).rename("predicted")


# ── A range around LEAR: QRA and conformal, on the same walk ──────────────────
# Stage 3 turns LEAR's one number per hour into 99 (Lipiecki, Uniejewski & Weron
# 2024), two ways, from the same dots: for one delivery hour, each of the window's
# days gives LEAR's forecast and the real price.  The walk below is shared, so the
# strictly-before rule, the window and the labels live in one place for both.
#
# The window ends at D−1, as `walk_forward`'s does: D−1's prices were public by
# 13:00 on D−2.  The dots must be forecasts LEAR really made, never its fit on
# its own training days, or the misses look small and the band comes out narrow.

QRA_WINDOW = 182                                            # days of dots per fit
PERCENTILES = tuple(range(1, 100))                          # p1 to p99, whole numbers


def _range_walk(point: pd.Series, actual: pd.Series, days: pd.DatetimeIndex,
                window: int, levels: tuple[int, ...], rule: Callable) -> pd.DataFrame:
    x = F.fold(point)                                       # one row per day, one column per hour
    y = F.fold(actual).reindex(x.index)                     # prices span years more: LEAR's days only
    rows = []
    for day in days:
        before = x.index < day                              # strictly before: the rule
        lines = {}
        for hour in x.columns:
            dots = pd.DataFrame({"x": x.loc[before, hour], "y": y.loc[before, hour]})
            dots = dots.dropna().iloc[-window:]             # the last `window` days with both
            lines[hour] = rule(dots, x.at[day, hour], levels)   # today: LEAR's forecast for D
        block = pd.DataFrame(lines, index=list(levels)).T          # hours down, percentiles across
        block.index = day + pd.to_timedelta(block.index, unit="h")  # back to grid hour labels
        rows.append(block)
    return pd.concat(rows)


# QRA fits a line through the dots per percentile by pinball loss, so the p90
# line has 9 dots in 10 below it.  Each line has its own slope, so the band can
# widen on days LEAR expects to be expensive (*quantile regression averaging*).
# The paper feeds it the average of four LEARs; here it is one.  `alpha=0`
# because QRA has no penalty: scikit-learn's default charges for the slope, and
# on real 19:00 data moved the p90 line by 12 EUR/MWh.

def _qra_hour(dots: pd.DataFrame, today: float, levels: tuple[int, ...]) -> list[float]:
    return [QuantileRegressor(quantile=p / 100, alpha=0, solver="highs")
            .fit(dots[["x"]].to_numpy(), dots["y"]).predict([[today]])[0]
            for p in levels]


def qra(point: pd.Series, actual: pd.Series, days: pd.DatetimeIndex,
        window: int = QRA_WINDOW, levels: tuple[int, ...] = PERCENTILES) -> pd.DataFrame:
    """99 lines per delivery hour of `days`, each from the `window` days before. Hourly out."""
    return _range_walk(point, actual, days, window, levels, _qra_hour)


# Conformal keeps only how big each miss was, never its direction, so the band is
# centred on LEAR and as wide above as below — the paper's form, which it notes
# assumes misses fall evenly both ways.  pX sits at the miss size that covered
# |2X − 100| % of the window's days: p90 and p10 both at the 80 % size, so the
# p10–p90 band holds 8 in 10.  Plain percentile, without the (n + 1)/n rounding of
# textbook conformal; which one the paper uses is not checked.  Its width comes
# from past misses only, so it cannot widen on a day that looks expensive.

def _conformal_hour(dots: pd.DataFrame, today: float, levels: tuple[int, ...]) -> np.ndarray:
    size = (dots["y"] - dots["x"]).abs().to_numpy()         # how far LEAR missed, either way
    level = np.asarray(levels)
    reach = np.quantile(size, np.abs(2 * level / 100 - 1))  # p90 and p10 -> the 80 % size
    return today + np.sign(level - 50) * reach              # below the forecast under p50


def conformal(point: pd.Series, actual: pd.Series, days: pd.DatetimeIndex,
              window: int = QRA_WINDOW, levels: tuple[int, ...] = PERCENTILES) -> pd.DataFrame:
    """A symmetric band per delivery hour of `days`, from the sizes of LEAR's misses before."""
    return _range_walk(point, actual, days, window, levels, _conformal_hour)


# Lines fitted one at a time can cross: p91 a little below p90 on some hour.  The
# usual repair is to sort each hour's values back into order, which can only
# lower pinball loss.  How many hours needed it is returned beside the result,
# so the repair is counted rather than hidden.

def untangle(lines: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Each hour's percentiles sorted into order, and how many hours had crossed."""
    ordered = np.sort(lines.to_numpy(), axis=1)             # lowest percentile first
    crossed = int((ordered != lines.to_numpy()).any(axis=1).sum())
    return pd.DataFrame(ordered, index=lines.index, columns=lines.columns), crossed
