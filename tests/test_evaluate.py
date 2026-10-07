"""Scoring rules, checked against numbers worked out by hand.

Every expected value here is small enough to verify on paper, so a green test
means the function is right rather than merely running.
"""

from __future__ import annotations

from statistics import NormalDist

import numpy as np
import pandas as pd
import pytest

from src import evaluate as E


def series(values: list[float], start: str = "2024-01-01") -> pd.Series:
    """A short hourly series, so every test reads as a handful of numbers."""
    idx = pd.date_range(start, periods=len(values), freq="h", tz="UTC")
    return pd.Series(values, index=idx, dtype=float)


# ── Lining up ─────────────────────────────────────────────────────────────────

def test_aligned_keeps_only_the_hours_both_series_cover():
    a = series([1, 2, 3, 4])
    b = series([9, 9, 9], start="2024-01-01 02:00")      # starts two hours later
    p, act = E.aligned(a, b)
    assert len(p) == 2                                   # 02:00 and 03:00 only
    assert list(p) == [3.0, 4.0]


def test_aligned_drops_blanks_rather_than_averaging_over_them():
    a = series([1, 2, None, 4])
    b = series([1, 2, 3, 4])
    p, act = E.aligned(a, b)
    assert len(p) == 3                                   # the blank hour is gone from both


def test_aligned_refuses_two_series_that_never_overlap():
    a = series([1, 2, 3])
    b = series([1, 2, 3], start="2025-06-01")
    with pytest.raises(ValueError, match="share no hours"):
        E.aligned(a, b)


# ── MAE ───────────────────────────────────────────────────────────────────────
# Misses of 2, 2 and 0 -> average 4/3.

def test_mae_is_the_average_size_of_a_miss():
    predicted = series([10, 20, 30])
    actual = series([12, 18, 30])
    assert E.mae(predicted, actual) == pytest.approx(4 / 3)


def test_mae_does_not_care_which_direction_the_miss_went():
    actual = series([50, 50])
    too_high = series([60, 60])
    too_low = series([40, 40])
    assert E.mae(too_high, actual) == E.mae(too_low, actual) == 10.0


def test_a_perfect_forecast_scores_zero():
    actual = series([7, -3, 112.5])
    assert E.mae(actual, actual) == 0.0


def test_mae_survives_negative_prices():
    """The reason MAE and not a percentage error: these prices cross zero."""
    predicted = series([-100, 0, 100])
    actual = series([-90, 10, 90])
    assert E.mae(predicted, actual) == pytest.approx(10.0)


# ── rMAE ──────────────────────────────────────────────────────────────────────

def test_the_benchmark_scores_exactly_one_against_itself():
    """The property that makes rMAE readable: 1.0 means 'no better than nothing'."""
    actual = series([10, 20, 30, 40])
    benchmark = series([12, 19, 33, 38])
    assert E.rmae(benchmark, benchmark, actual) == pytest.approx(1.0)


def test_half_the_error_scores_one_half():
    actual = series([100, 100, 100])
    benchmark = series([120, 120, 120])                  # out by 20
    model = series([110, 110, 110])                      # out by 10
    assert E.rmae(model, benchmark, actual) == pytest.approx(0.5)


def test_a_model_worse_than_the_benchmark_scores_above_one():
    actual = series([100, 100])
    benchmark = series([105, 105])                       # out by 5
    model = series([120, 120])                           # out by 20
    assert E.rmae(model, benchmark, actual) == pytest.approx(4.0)


def test_a_perfect_model_scores_zero():
    actual = series([10, 20, 30])
    benchmark = series([15, 15, 15])
    assert E.rmae(actual, benchmark, actual) == 0.0


def test_both_forecasts_are_scored_on_the_same_hours():
    """The numerator and the denominator must sit the same exam.

    Here the benchmark reaches an hour the model does not — exactly the real case,
    where the naive rule has a value for the opening week and a fitted model does
    not. Scored separately, the two errors come from different sets of hours and
    the ratio between them means nothing.

    The hour the model is missing is one the benchmark happens to get right, so
    including it would flatter the benchmark and make the model look worse.
    """
    actual = series([100, 100, 100, 100])
    benchmark = series([100, 120, 120, 120])            # perfect on hour 0, out by 20 after
    model = series([None, 110, 110, 110])               # no forecast for hour 0, out by 10 after

    # On the three hours all of them cover: model 10, benchmark 20 -> exactly 0.5.
    assert E.rmae(model, benchmark, actual) == pytest.approx(0.5)


def test_an_hour_missing_from_the_benchmark_is_dropped_too():
    """Same rule in the other direction — whichever side is short, both give it up.

    The model's error is deliberately uneven: 50 on the hour the benchmark cannot
    reach, 10 on the rest. An even error would make this test pass whether the hour
    was dropped or not, and a test that cannot fail is not a test.
    """
    actual = series([100, 100, 100])
    benchmark = series([None, 120, 120])                # nothing for hour 0
    model = series([50, 110, 110])                      # out by 50 there, 10 elsewhere

    # Both sides scored on hours 1 and 2 only: model 10, benchmark 20 -> 0.5.
    # Score the model on all three and its MAE becomes 23.3, giving 1.17.
    assert E.rmae(model, benchmark, actual) == pytest.approx(0.5)


# ── Diebold-Mariano ───────────────────────────────────────────────────────────
# Too many numbers to check on paper, so the anchor is the field's own code instead:
# epftoolbox's multivariate test, transcribed below, must come out identical once
# the echo correction is switched off.  Forecasts sit on grid labels, 24 a day.

def _days(n_days: int, seed: int) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Actual prices and two forecasts; the second misses a little less on average."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-03-01", periods=24 * n_days, freq="h")   # naive, as on the grid
    actual = pd.Series(rng.normal(100, 30, len(idx)), index=idx)
    first = actual + rng.normal(0, 12, len(idx))
    second = actual + rng.normal(0, 11, len(idx))
    return first, second, actual


def _epftoolbox(first, second, actual) -> float:
    """epftoolbox `DM(..., norm=1, version='multivariate')`, line for line."""
    p_real, p_pred_1, p_pred_2 = (s.to_numpy().reshape(-1, 24) for s in (actual, first, second))
    errors_pred_1 = p_real - p_pred_1
    errors_pred_2 = p_real - p_pred_2
    d = np.mean(np.abs(errors_pred_1), axis=1) - np.mean(np.abs(errors_pred_2), axis=1)
    N = d.size
    DM_stat = np.mean(d) / np.sqrt((1 / N) * np.var(d, ddof=0))
    return 1 - NormalDist().cdf(DM_stat)                 # stats.norm.cdf, without scipy


def test_dm_without_the_echo_correction_is_the_field_reference():
    """The departure from epftoolbox is one switch; with it off, the answers agree."""
    first, second, actual = _days(60, seed=1)
    assert E.dm(first, second, actual, lags=0) == pytest.approx(_epftoolbox(first, second, actual))


def test_dm_echo_correction_worked_out_by_hand():
    """Three days whose gaps are 1, 3 and 2, with one day of echo.

    Mean 2, deviations -1, 1, 0.  Plain spread (1 + 1 + 0) / 3 = 2/3.  Echo one day
    apart (-1·1 + 1·0) / 3 = -1/3, weighted 2 · (1 - 1/2) = 1, so the spread is
    2/3 - 1/3 = 1/3.  Statistic 2 / sqrt((1/3) / 3) = 6.
    """
    idx = pd.date_range("2023-03-01", periods=72, freq="h")
    actual = pd.Series(0.0, index=idx)
    first = actual + 10                                  # misses by 10 every hour
    second = actual + 10 - np.repeat([1.0, 3.0, 2.0], 24)  # misses by 1, 3, 2 less, day by day
    assert E.dm(first, second, actual, lags=1) == pytest.approx(1 - NormalDist().cdf(6))


def test_dm_says_which_forecast_is_better():
    """One-sided: small when the second is clearly better, near one when it is worse."""
    first, second, actual = _days(365, seed=2)
    better = actual + (second - actual) / 3              # the second, missing a third as much
    assert E.dm(first, better, actual) < 0.01
    assert E.dm(better, first, actual) > 0.99


def test_dm_is_more_cautious_when_days_echo_each_other():
    """Gaps that run in streaks of good and bad weeks are weaker evidence than scattered ones.

    The second forecast's edge comes and goes by the week, so neighbouring days agree
    with each other.  Counting them as unconnected overstates the evidence.
    """
    rng = np.random.default_rng(3)
    idx = pd.date_range("2023-01-02", periods=364 * 24, freq="h")
    actual = pd.Series(100.0, index=idx)
    miss = 20 + rng.normal(0, 2, len(idx))                       # the first's miss, always above
    weeks = rng.normal(0, 3, 52)
    weeks -= weeks.mean()                                        # streaks, but no net edge of their own
    edge = 0.5 + np.repeat(weeks, 7 * 24) + rng.normal(0, 1, len(idx))
    first, second = actual + miss, actual + miss - edge          # the second misses by less
    assert E.dm(first, second, actual, lags=7) > E.dm(first, second, actual, lags=0)


# ── The report ────────────────────────────────────────────────────────────────

def test_score_carries_the_hour_count_so_two_rows_can_be_compared():
    actual = series([10, 20, 30])
    benchmark = series([12, 22, 32])
    model = series([11, 21, 31])
    row = E.score("linear", "valid", model, benchmark, actual)
    assert row["model"] == "linear" and row["split"] == "valid"
    assert row["n"] == 3
    assert row["rmae"] == pytest.approx(0.5)


def test_score_counts_the_hours_all_three_series_cover():
    """`n` has to describe the hours the row's own numbers came from.

    The benchmark reaches an hour the model does not, so only three hours are
    scorable. If `n` were counted from the model against the actuals alone it would
    still say three here — so the model is made short at one end and the benchmark
    at the other, leaving an intersection smaller than either pair.
    """
    actual = series([100, 100, 100, 100, 100])
    model = series([None, 110, 110, 110, 110])          # nothing for hour 0
    benchmark = series([120, 120, 120, 120, None])      # nothing for hour 4

    row = E.score("linear", "valid", model, benchmark, actual)
    assert row["n"] == 3                                # hours 1, 2 and 3 only
    assert row["mae"] == pytest.approx(10.0)            # not diluted by the hours dropped
    assert row["rmae"] == pytest.approx(0.5)


def test_table_renders_one_line_per_row():
    rows = [
        {"model": "naive", "split": "valid", "n": 8759, "mae": 21.4, "rmae": 1.0},
        {"model": "linear", "split": "valid", "n": 8759, "mae": 17.9, "rmae": 0.836},
    ]
    out = E.table(rows)
    assert out.count("\n") == 3                          # header, rule, two rows
    assert "8,759" in out and "0.836" in out
