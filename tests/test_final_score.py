"""Contract 2 from the other side.

`test_train.py` checks that the everyday script can never reach the held-back years. This
file checks the one script that may — that it reaches them *and nothing else*, and that it
learns from everything published beforehand rather than from a convenient subset.

The test that carries the weight is `test_the_fit_includes_the_validation_year`. Getting it
wrong in the cautious direction wastes a year of data; getting it wrong in the other
direction would fit on the very rows being scored, and no other check here would notice.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts import final_score as FS
from src import config as cfg
from src import features as F


# ── The fixture ───────────────────────────────────────────────────────────────
# Long enough to straddle both boundaries: training months in 2022, a full validation year
# in 2023, and half of 2024 to be held back. Same shape as the one in test_train.py —
# cycles that never line up with a week, and no trend, so the benchmark can be beaten and
# the tree is never asked to predict past what it has seen.

START = pd.Timestamp("2022-10-01 00:00", tz="UTC")
END = pd.Timestamp("2024-06-30 23:00", tz="UTC")


def _sources() -> dict[str, pd.DataFrame]:
    idx = pd.date_range(START, END, freq="h", tz="UTC")
    n = np.arange(len(idx), dtype=float)

    daily = np.sin(2 * np.pi * n / 24)
    slow = np.sin(2 * np.pi * n / (24 * 13))                   # 13 days: never lands on a week
    wobble = np.sin(2 * np.pi * n / (24 * 29 + 7))

    load = pd.DataFrame({"load": 40_000 + 6_000 * daily + 9_000 * slow + 3_000 * wobble},
                        index=idx)
    return {
        "day_ahead_price": pd.DataFrame({"price": 0.003 * load.load + 8 * daily**2}, index=idx),
        "load_forecast": load,
        "wind_solar_forecast": pd.DataFrame(
            {"Wind Onshore": 5_000 + n % 900, "Wind Offshore": 1_000 + n % 300,
             "Solar": 2_000 + n % 700},
            index=idx,
        ),
    }


@pytest.fixture
def frames(monkeypatch):
    """`FS.data()` run against the fixture instead of the cache."""
    src = _sources()
    monkeypatch.setattr(F, "data_load", lambda key: src[key])
    return FS.data()


# ── What is learned from ──────────────────────────────────────────────────────

def test_the_fit_includes_the_validation_year(frames):
    """The decision this script exists to embody, as an assertion.

    `train.py` stops learning at the end of 2022 so that 2023 stays unseen. Here 2023 has
    already done its job, so leaving it out would discard a year for nothing. Every 2023
    price was public long before any 2024 delivery hour, so Contract 1 is untouched.
    """
    history, _ = frames
    years = set(history.index.tz_convert(cfg.TZ_MARKET).year)
    assert 2023 in years, "the validation year is being wasted"
    assert 2022 in years, "the training years are missing"


def test_the_fit_stops_before_the_held_back_years(frames):
    """The failure that would matter: learning from the rows being judged."""
    history, _ = frames
    assert history.index.max() <= cfg.VALID_END_UTC


def test_the_two_frames_never_share_an_hour(frames):
    history, holdout = frames
    assert history.index.intersection(holdout.index).empty


# ── What is scored ────────────────────────────────────────────────────────────

def test_only_held_back_rows_are_scored(frames):
    _, holdout = frames
    assert holdout.index.min() >= cfg.TEST_START_UTC
    assert holdout.index.max() <= cfg.TEST_END_UTC


def test_no_blank_survives_into_either_frame(frames):
    history, holdout = frames
    assert not history.isna().to_numpy().any()
    assert not holdout.isna().to_numpy().any()


# ── The scored table ──────────────────────────────────────────────────────────

def test_every_row_is_labelled_as_held_back(frames):
    """A row from here must never be mistaken for a validation score in the record."""
    assert all(row["split"] == "test" for row in FS.run(*frames))


def test_all_three_forecasts_are_reported(frames):
    assert {r["model"] for r in FS.run(*frames)} == {"naive", "linear", "gbm"}


def test_the_benchmark_scores_exactly_one(frames):
    rows = {r["model"]: r for r in FS.run(*frames)}
    assert rows["naive"]["rmae"] == pytest.approx(1.0)


def test_every_forecast_is_scored_on_the_same_hours(frames):
    """The same-exam rule. Three rows, one hour count."""
    assert len({row["n"] for row in FS.run(*frames)}) == 1


def test_a_model_is_not_its_own_benchmark(frames):
    """Same hole that survived a mutation in test_train.py, closed here too.

    Passing each model's own forecast as its denominator makes every rMAE exactly 1.000
    and every other check in this file still passes.
    """
    rows = {r["model"]: r for r in FS.run(*frames)}
    for name in ("linear", "gbm"):
        assert rows[name]["rmae"] < 1.0, f"{name} scored as though it were its own benchmark"
