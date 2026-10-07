"""The benchmark, and the shape every model must follow.

The important one is `test_blanking_the_target_changes_nothing`. It is the whole
discipline of this stage in one assertion.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import features as F
from src import models as M


def frame(n: int = 400) -> pd.DataFrame:
    """A small feature frame with a learnable relationship in it.

    The target is built from two of the columns on purpose, so a working model
    scores clearly better than the naive rule and a broken one does not.
    """
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    rng = np.random.default_rng(0)
    residual = 30_000 + rng.normal(0, 4_000, n)
    hour = idx.tz_convert("Europe/Berlin").hour
    price = 0.003 * residual + 1.5 * hour + rng.normal(0, 3, n)

    df = pd.DataFrame(
        {"price": price, "residual_load": residual, "hour": hour.astype(float)},
        index=idx,
    )
    df["price_lag_168h"] = df["price"].shift(168)
    return df.dropna()


# ── The benchmark, which already works ────────────────────────────────────────

def test_naive_predicts_the_same_hour_one_week_earlier():
    df = frame()
    out = M.naive_forecast(df)
    pd.testing.assert_series_equal(out, df["price_lag_168h"], check_names=False)


def test_naive_is_indexed_like_the_frame_it_came_from():
    df = frame()
    assert M.naive_forecast(df).index.equals(df.index)


def test_naive_learns_nothing_and_needs_no_fitting():
    """It is a lookup, not a model. Two calls on the same frame are identical."""
    df = frame()
    pd.testing.assert_series_equal(M.naive_forecast(df), M.naive_forecast(df))


# ── The estimators ────────────────────────────────────────────────────────────

def test_linear_returns_something_that_can_be_fitted():
    est = M.linear()
    assert hasattr(est, "fit") and hasattr(est, "predict")


def test_gbm_returns_something_that_can_be_fitted():
    est = M.gbm()
    assert hasattr(est, "fit") and hasattr(est, "predict")


def test_gbm_is_seeded_so_two_runs_give_the_same_answer():
    """Without a fixed seed the same code produces two numbers, and the Third Law
    claim that any result regenerates from a clean clone quietly stops holding."""
    df = frame()
    a = M.forecast(M.fit(M.gbm(), df), df)
    b = M.forecast(M.fit(M.gbm(), df), df)
    pd.testing.assert_series_equal(a, b)


# ── Fitting and forecasting ───────────────────────────────────────────────────

def test_forecast_is_indexed_like_the_frame():
    df = frame()
    out = M.forecast(M.fit(M.linear(), df), df)
    assert isinstance(out, pd.Series)
    assert out.index.equals(df.index)


def test_blanking_the_target_changes_nothing():
    """The discipline of this stage, as one assertion.

    Blank out the answers and predict again. If the forecast moves, the target
    reached the prediction path — which is the failure this whole project is built
    to avoid, and which nothing else would report.

    Deliberately named to match `test_deleting_the_future_changes_nothing` in
    tests/test_features.py. Same shape, one level down: that one stops a column
    reaching forward in time, this one stops the answer column reaching sideways.
    """
    df = frame()
    model = M.fit(M.linear(), df)

    blanked = df.copy()
    blanked[F.TARGET] = np.nan                       # the answers are gone

    pd.testing.assert_series_equal(M.forecast(model, df), M.forecast(model, blanked))


def test_a_wrong_target_changes_nothing():
    """The same claim, by comparison rather than by crash.

    The test above blanks the answers with NaN, which is the honest picture of a day
    not yet cleared — but a linear fit refuses NaN outright, so a model that *did*
    read the target would raise before producing a forecast to compare. The failure
    would be loud, and for the wrong reason.

    Here the answers are replaced with a finite number that is simply wrong. Nothing
    can refuse it, so the forecast is actually produced, and the comparison the test
    claims to make is the one that runs.
    """
    df = frame()
    model = M.fit(M.linear(), df)

    wrong = df.copy()
    wrong[F.TARGET] = -999.0                         # plausible dtype, nonsense value

    pd.testing.assert_series_equal(M.forecast(model, df), M.forecast(model, wrong))


def test_a_fitted_model_beats_the_naive_rule_on_this_data():
    """Not a claim about the real market — only that the wiring works.

    The target here is built from two columns that are in the frame, so a model
    that is connected up properly must do better than a week-old lookup.
    """
    from src import evaluate as E

    df = frame()
    fitted = M.forecast(M.fit(M.linear(), df), df)
    assert E.rmae(fitted, M.naive_forecast(df), df[F.TARGET]) < 0.5


def test_fit_returns_the_estimator_rather_than_none():
    """`sklearn`'s own fit returns self; the wrapper must pass that back."""
    est = M.linear()
    assert M.fit(est, frame()) is not None


# ── Walking forward ───────────────────────────────────────────────────────────
# The rule under test: each period is forecast before the model may learn from it.
# A spy stands in for the model and records what it was shown, so the rule is
# checked on the hours themselves rather than inferred from a score.
#
# Three months on naive grid labels, as `train.run` passes them: December 2022 is
# history only, January to February 2023 is forecast.

def grid_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    idx = pd.date_range("2022-12-01", "2023-02-28 23:00", freq="h")   # naive: Berlin wall clock
    rng = np.random.default_rng(1)
    history = pd.DataFrame({"price": rng.normal(80, 20, len(idx)),
                            "residual_load": rng.normal(30_000, 4_000, len(idx))}, index=idx)
    return history, history.loc["2023-01-01":]


class Spy:
    """A model that learns nothing and remembers which hours it saw, fit by fit."""

    def __init__(self, log: list):
        self.log = log

    def fit(self, X, y):
        self.log.append({"first_seen": X.index.min(), "last_seen": X.index.max()})
        return self

    def predict(self, X):
        self.log[-1]["forecast"] = X.index                 # the hours this fit was used for
        return np.zeros(len(X))


def spied(every: str) -> tuple[list, pd.Series, pd.DataFrame]:
    log: list = []
    history, scored = grid_frames()
    out = M.walk_forward(lambda: Spy(log), history, scored, every)
    return log, out, scored


def test_walk_forward_never_learns_from_the_period_it_forecasts():
    """The leak this loop could introduce, checked hour by hour for every fit.

    It must also learn from everything right up to the period — every hour since
    the start, ending exactly one hour before the first forecast hour.
    """
    for every in ("D", "M"):
        log, _, _ = spied(every)
        for fit in log:
            first = fit["forecast"].min()
            assert fit["last_seen"] < first, f"{every}: learned from {first:%Y-%m-%d}"
            assert fit["last_seen"] == first - pd.Timedelta(hours=1)
            assert fit["first_seen"] == pd.Timestamp("2022-12-01 00:00")


def test_walk_forward_refits_once_per_period():
    """Daily means 59 fits for January and February, monthly means two."""
    assert len(spied("D")[0]) == 59
    assert len(spied("M")[0]) == 2


def test_walk_forward_forecasts_every_hour_exactly_once():
    _, out, scored = spied("D")
    assert out.index.equals(scored.index)


def test_walk_forward_once_a_year_is_the_single_fit():
    """One period, one fit on everything before it: the stage 1 recipe, unchanged."""
    history, scored = grid_frames()
    single = M.forecast(M.fit(M.linear(), history.loc[:"2022-12-31"]), scored)
    walked = M.walk_forward(M.linear, history, scored, "Y")
    pd.testing.assert_series_equal(walked, single)
