"""Scoring rules, checked against numbers worked out by hand.

These fail until `mae` and `rmae` are written. That is deliberate — run
`just test`, read the failure, write the function, run it again.

Every expected value here is small enough to verify on paper, so a green test
means the function is right rather than merely running.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src import evaluate as E

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

@pending
def test_mae_is_the_average_size_of_a_miss():
    predicted = series([10, 20, 30])
    actual = series([12, 18, 30])
    assert E.mae(predicted, actual) == pytest.approx(4 / 3)


@pending
def test_mae_does_not_care_which_direction_the_miss_went():
    actual = series([50, 50])
    too_high = series([60, 60])
    too_low = series([40, 40])
    assert E.mae(too_high, actual) == E.mae(too_low, actual) == 10.0


@pending
def test_a_perfect_forecast_scores_zero():
    actual = series([7, -3, 112.5])
    assert E.mae(actual, actual) == 0.0


@pending
def test_mae_survives_negative_prices():
    """The reason MAE and not a percentage error: these prices cross zero."""
    predicted = series([-100, 0, 100])
    actual = series([-90, 10, 90])
    assert E.mae(predicted, actual) == pytest.approx(10.0)


# ── rMAE ──────────────────────────────────────────────────────────────────────

@pending
def test_the_benchmark_scores_exactly_one_against_itself():
    """The property that makes rMAE readable: 1.0 means 'no better than nothing'."""
    actual = series([10, 20, 30, 40])
    benchmark = series([12, 19, 33, 38])
    assert E.rmae(benchmark, benchmark, actual) == pytest.approx(1.0)


@pending
def test_half_the_error_scores_one_half():
    actual = series([100, 100, 100])
    benchmark = series([120, 120, 120])                  # out by 20
    model = series([110, 110, 110])                      # out by 10
    assert E.rmae(model, benchmark, actual) == pytest.approx(0.5)


@pending
def test_a_model_worse_than_the_benchmark_scores_above_one():
    actual = series([100, 100])
    benchmark = series([105, 105])                       # out by 5
    model = series([120, 120])                           # out by 20
    assert E.rmae(model, benchmark, actual) == pytest.approx(4.0)


@pending
def test_a_perfect_model_scores_zero():
    actual = series([10, 20, 30])
    benchmark = series([15, 15, 15])
    assert E.rmae(actual, benchmark, actual) == 0.0


# ── The report ────────────────────────────────────────────────────────────────

@pending
def test_score_carries_the_hour_count_so_two_rows_can_be_compared():
    actual = series([10, 20, 30])
    benchmark = series([12, 22, 32])
    model = series([11, 21, 31])
    row = E.score("linear", "valid", model, benchmark, actual)
    assert row["model"] == "linear" and row["split"] == "valid"
    assert row["n"] == 3
    assert row["rmae"] == pytest.approx(0.5)


def test_table_renders_one_line_per_row():
    rows = [
        {"model": "naive", "split": "valid", "n": 8759, "mae": 21.4, "rmae": 1.0},
        {"model": "linear", "split": "valid", "n": 8759, "mae": 17.9, "rmae": 0.836},
    ]
    out = E.table(rows)
    assert out.count("\n") == 3                          # header, rule, two rows
    assert "8,759" in out and "0.836" in out
