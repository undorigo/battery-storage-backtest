"""Contract 2, enforced rather than promised.

Two tests here carry the weight. `test_no_test_period_row_is_ever_returned` is the
one that makes "the test years are unreachable from this script" checkable instead of
a comment. `test_every_forecast_is_scored_on_the_same_hours` is the same-exam rule
from `evaluate.py`, one level up: there it guarded a single ratio, here it guards a
whole table.

Everything runs on a synthetic fixture spanning the train/validate boundary, because
the real parquet files are gitignored — a test that needed them would pass here and
fail on a clean clone.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts import train as T
from src import config as cfg
from src import evaluate as E
from src import features as F


# ── The fixture ───────────────────────────────────────────────────────────────
# Fifteen months of hourly data straddling the train/validate boundary, running a
# week into 2024 so there is real test-period data for `data()` to wrongly return.
# Two rows are blanked, one either side of the boundary, so that "complete rows only"
# is tested against something rather than asserted.
#
# The price deliberately carries no trend. An earlier version rose steadily, which
# made the week-old lookup nearly perfect and put every validation price above
# anything in training — a tree can only predict values it has already seen, so it
# scored fifteen times worse than doing nothing. Cycles that never line up with a
# week fix both halves: the models find something, the benchmark misses something.

START = pd.Timestamp("2022-10-01 00:00", tz="UTC")
END = pd.Timestamp("2024-01-07 23:00", tz="UTC")

BLANK_TRAIN = pd.Timestamp("2022-11-15 09:00", tz="UTC")
BLANK_VALID = pd.Timestamp("2023-06-20 14:00", tz="UTC")
BLANK_TRAIN_SLOT = pd.Timestamp("2022-11-15 10:00")        # the same hours on the grid: CET is UTC+1
BLANK_VALID_SLOT = pd.Timestamp("2023-06-20 16:00")        # and CEST is UTC+2


def _sources() -> dict[str, pd.DataFrame]:
    idx = pd.date_range(START, END, freq="h", tz="UTC")
    n = np.arange(len(idx), dtype=float)

    daily = np.sin(2 * np.pi * n / 24)                         # the shape of a day
    slow = np.sin(2 * np.pi * n / (24 * 13))                   # 13 days: never lands on a week
    wobble = np.sin(2 * np.pi * n / (24 * 29 + 7))             # shares no period with the others

    load = pd.DataFrame({"load": 40_000 + 6_000 * daily + 9_000 * slow + 3_000 * wobble},
                        index=idx)
    load.loc[[BLANK_TRAIN, BLANK_VALID], "load"] = np.nan      # the two holes

    return {
        # Built from the load, so a model holding the load forecast has something to
        # find. Filled at the two holes, so those rows drop for one reason, not two.
        "day_ahead_price": pd.DataFrame({"price": 0.003 * load.load.ffill() + 8 * daily**2},
                                        index=idx),
        "load_forecast": load,
        "wind_solar_forecast": pd.DataFrame(
            {"Wind Onshore": 5_000 + n % 900, "Wind Offshore": 1_000 + n % 300,
             "Solar": 2_000 + n % 700},
            index=idx,
        ),
    }


@pytest.fixture
def frames(monkeypatch):
    """`T.data()` run against the fixture instead of the cache."""
    src = _sources()
    monkeypatch.setattr(F, "data_load", lambda key: src[key])
    return T.data()


# ── Contract 2 — the boundary ─────────────────────────────────────────────────
# The boundary hours are written out rather than read from `split()`, so these
# tests cannot agree with a mistake there.  The frames are on the 24-slot grid, so
# the last hour of each year is 23:00 on the Berlin clock.

LAST_TRAIN_HOUR = pd.Timestamp("2022-12-31 23:00")
LAST_VALID_HOUR = pd.Timestamp("2023-12-31 23:00")


def test_no_test_period_row_is_ever_returned(frames):
    """The claim the module docstring makes, as an assertion.

    The fixture runs a week into 2024, so there is genuine test-period data sitting
    there to be returned by mistake. Nothing this script hands back may touch it.
    """
    train, valid = frames
    for name, part in (("train", train), ("valid", valid)):
        assert part.index.max() <= LAST_VALID_HOUR, f"{name} reaches into the test years"


def test_train_and_validate_never_share_an_hour(frames):
    train, valid = frames
    assert train.index.intersection(valid.index).empty


def test_training_stops_at_the_split_date(frames):
    train, valid = frames
    assert train.index.max() <= LAST_TRAIN_HOUR
    assert valid.index.min() > LAST_TRAIN_HOUR


# ── Complete rows only ────────────────────────────────────────────────────────

def test_no_blank_survives_into_either_frame(frames):
    """A blank anywhere drops the whole row, on both sides of the boundary."""
    train, valid = frames
    assert not train.isna().to_numpy().any()
    assert not valid.isna().to_numpy().any()


def test_the_blanked_hours_are_the_ones_missing(frames):
    """Not merely 'no blanks' — the two holes we made are the rows that went.

    Asked on grid labels, with the hour before each hole required present.  A
    UTC timestamp is never `in` a naive index, so the old form would pass whatever
    happened, and only the neighbour check proves the question was asked right.
    """
    train, valid = frames
    hour = pd.Timedelta(hours=1)
    assert BLANK_TRAIN_SLOT not in train.index and BLANK_TRAIN_SLOT - hour in train.index
    assert BLANK_VALID_SLOT not in valid.index and BLANK_VALID_SLOT - hour in valid.index


# ── The scored table ──────────────────────────────────────────────────────────

def test_every_forecast_is_scored_on_the_same_hours(frames):
    """The same-exam rule, one level up from `evaluate.py`.

    Three forecasts, three rows, and the hour count must be identical across them.
    If it is not, the rMAE column is comparing scores drawn from different sets of
    hours and the table means nothing.
    """
    rows, _ = T.run(*frames)
    assert len({row["n"] for row in rows}) == 1


def test_the_benchmark_scores_exactly_one(frames):
    """A free check on the wiring: the benchmark divided by itself is 1.000."""
    rows, _ = T.run(*frames)
    naive = [r for r in rows if r["model"] == "naive"]
    assert len(naive) == 1
    assert naive[0]["rmae"] == pytest.approx(1.0)


def test_all_three_forecasts_are_reported(frames):
    rows, _ = T.run(*frames)
    assert {r["model"] for r in rows} == {"naive", "linear", "gbm"}


def test_every_row_is_labelled_as_validation(frames):
    """Contract 2 again: nothing produced here may claim to be a test score."""
    rows, _ = T.run(*frames)
    assert all(row["split"] == "valid" for row in rows)


def test_a_model_is_not_its_own_benchmark(frames):
    """Written because a mutant survived without it.

    Passing each model's own forecast as its denominator makes every rMAE exactly
    1.000 and the table meaningless — and every other test here still passed. The
    fixture's price is built from the load, which is a feature, so a model that is
    wired up properly must beat a week-old lookup rather than tie with it.
    """
    scored, _ = T.run(*frames)
    rows = {row["model"]: row for row in scored}
    for name in ("linear", "gbm"):
        assert rows[name]["rmae"] < 1.0, f"{name} scored as though it were its own benchmark"


def test_the_kept_forecasts_are_the_ones_that_were_scored(frames):
    """The hourly table must reproduce every score, or a test built on it reads other numbers.

    One row per validation hour, one column per forecast, and rescoring each column
    from the table gives back the rMAE in the score rows exactly.
    """
    rows, forecasts = T.run(*frames)
    _, valid = frames
    assert forecasts.index.equals(valid.index)
    assert set(forecasts.columns) == {"actual", "naive", "linear", "gbm"}
    for row in rows:
        again = E.rmae(forecasts[row["model"]], forecasts["naive"], forecasts["actual"])
        assert again == row["rmae"]


# ── The record ────────────────────────────────────────────────────────────────
# `record` is written already, so these are plain tests rather than specifications.

def test_record_appends_rather_than_replacing(tmp_path):
    """The whole point of the file. A record that can be overwritten is not one."""
    path = tmp_path / "scores.csv"
    first = [{"model": "naive", "split": "valid", "n": 10, "mae": 20.0, "rmae": 1.0}]
    second = [{"model": "linear", "split": "valid", "n": 10, "mae": 10.0, "rmae": 0.5}]

    T.record(first, path)
    history = T.record(second, path)

    assert len(history) == 2
    assert list(history.model) == ["naive", "linear"]


def test_record_stamps_each_row_with_a_commit_and_a_time(tmp_path):
    """Without these a row is a number nobody can trace back to the code."""
    path = tmp_path / "scores.csv"
    history = T.record([{"model": "naive", "split": "valid", "n": 10,
                         "mae": 20.0, "rmae": 1.0}], path)

    assert history.loc[0, "commit"]
    assert history.loc[0, "run_at"].endswith("Z")


def test_record_writes_one_header_not_two(tmp_path):
    """Appending a second run must not append a second header row with it."""
    path = tmp_path / "scores.csv"
    row = [{"model": "naive", "split": "valid", "n": 10, "mae": 20.0, "rmae": 1.0}]

    T.record(row, path)
    T.record(row, path)

    assert path.read_text().count("model") == 1


def test_record_creates_the_directory_if_it_is_missing(tmp_path):
    """A clean clone may not have the output directory; the first run must not fail."""
    path = tmp_path / "results" / "scores.csv"
    T.record([{"model": "naive", "split": "valid", "n": 1, "mae": 1.0, "rmae": 1.0}], path)
    assert path.exists()
