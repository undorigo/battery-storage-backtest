"""The benchmark, and the shape every model must follow.

The naive tests pass already — that function is the worked example. The rest are
marked `pending` until `linear`, `gbm`, `fit` and `forecast` are written.

The important one is `test_blanking_the_target_changes_nothing`. It is the whole
discipline of this stage in one assertion.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import features as F
from src import models as M


# ── Marking what is not written yet ───────────────────────────────────────────
# These tests describe functions that do not exist, so they cannot pass. Rather
# than leaving the suite red — which tells anyone cloning this that it is broken —
# they are marked as expected failures, and narrowly: `raises=NotImplementedError`
# means the marker only forgives the *absent* function.
#
# So the three outcomes stay distinct, which is the point:
#   not written yet   -> xfail   (suite stays green)
#   written, wrong    -> FAIL    (a real, loud failure)
#   written, right    -> XPASS   (visible progress; remove the marker)

pending = pytest.mark.xfail(
    raises=NotImplementedError,
    reason="stage 1: not implemented yet — see the notes above it in src/",
)


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

@pending
def test_linear_returns_something_that_can_be_fitted():
    est = M.linear()
    assert hasattr(est, "fit") and hasattr(est, "predict")


@pending
def test_gbm_returns_something_that_can_be_fitted():
    est = M.gbm()
    assert hasattr(est, "fit") and hasattr(est, "predict")


@pending
def test_gbm_is_seeded_so_two_runs_give_the_same_answer():
    """Without a fixed seed the same code produces two numbers, and the Third Law
    claim that any result regenerates from a clean clone quietly stops holding."""
    df = frame()
    a = M.forecast(M.fit(M.gbm(), df), df)
    b = M.forecast(M.fit(M.gbm(), df), df)
    pd.testing.assert_series_equal(a, b)


# ── Fitting and forecasting ───────────────────────────────────────────────────

@pending
def test_forecast_is_indexed_like_the_frame():
    df = frame()
    out = M.forecast(M.fit(M.linear(), df), df)
    assert isinstance(out, pd.Series)
    assert out.index.equals(df.index)


@pending
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


@pending
def test_a_fitted_model_beats_the_naive_rule_on_this_data():
    """Not a claim about the real market — only that the wiring works.

    The target here is built from two columns that are in the frame, so a model
    that is connected up properly must do better than a week-old lookup.
    """
    from src import evaluate as E

    df = frame()
    fitted = M.forecast(M.fit(M.linear(), df), df)
    assert E.rmae(fitted, M.naive_forecast(df), df[F.TARGET]) < 0.5


@pending
def test_fit_returns_the_estimator_rather_than_none():
    """`sklearn`'s own fit returns self; the wrapper must pass that back."""
    est = M.linear()
    assert M.fit(est, frame()) is not None
