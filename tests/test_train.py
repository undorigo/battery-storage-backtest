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
from src import features as F


# ── Marking what is not written yet ───────────────────────────────────────────
# `data` and `run` are specified here before they are written, so these describe
# functions that cannot pass yet. Marked narrowly — `raises=NotImplementedError`
# forgives only the absent function, so the three outcomes stay distinct:
#   not written yet   -> xfail   (the suite stays green for anyone cloning this)
#   written, wrong    -> FAIL    (a real failure, loudly)
#   written, right    -> XPASS   (remove the marker)

pending = pytest.mark.xfail(
    raises=NotImplementedError,
    reason="stage 1: not implemented yet — see the notes above it in scripts/train.py",
)


# ── The fixture ───────────────────────────────────────────────────────────────
# Fifteen months of hourly data, from October 2022 to the end of 2023. It straddles
# the train/validate boundary on purpose, and runs a week into 2024 so there is real
# test-period data available for `data()` to wrongly return.
#
# Two rows are deliberately blanked, one on each side of the boundary, so that
# "complete rows only" is tested against something rather than asserted.

START = pd.Timestamp("2022-10-01 00:00", tz="UTC")
END = pd.Timestamp("2024-01-07 23:00", tz="UTC")

BLANK_TRAIN = pd.Timestamp("2022-11-15 09:00", tz="UTC")
BLANK_VALID = pd.Timestamp("2023-06-20 14:00", tz="UTC")


def _sources() -> dict[str, pd.DataFrame]:
    idx = pd.date_range(START, END, freq="h", tz="UTC")
    n = np.arange(len(idx), dtype=float)

    load = pd.DataFrame({"load": 40_000 + 5_000 * np.sin(n / 24 * 2 * np.pi)}, index=idx)
    load.loc[[BLANK_TRAIN, BLANK_VALID], "load"] = np.nan      # the two holes

    return {
        # Price is built from the load so a fitted model has something real to find;
        # the ramp keeps every hour distinct, so an off-by-one lag cannot hide.
        "day_ahead_price": pd.DataFrame({"price": 0.002 * (40_000 + n) + 0.001 * load.load},
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

@pending
def test_no_test_period_row_is_ever_returned(frames):
    """The claim the module docstring makes, as an assertion.

    The fixture runs a week into 2024, so there is genuine test-period data sitting
    there to be returned by mistake. Nothing this script hands back may touch it.
    """
    train, valid = frames
    for name, part in (("train", train), ("valid", valid)):
        assert part.index.max() <= cfg.VALID_END_UTC, f"{name} reaches into the test years"


@pending
def test_train_and_validate_never_share_an_hour(frames):
    train, valid = frames
    assert train.index.intersection(valid.index).empty


@pending
def test_training_stops_at_the_split_date(frames):
    train, valid = frames
    assert train.index.max() <= cfg.TRAIN_END_UTC
    assert valid.index.min() > cfg.TRAIN_END_UTC


# ── Complete rows only ────────────────────────────────────────────────────────

@pending
def test_no_blank_survives_into_either_frame(frames):
    """A blank anywhere drops the whole row, on both sides of the boundary."""
    train, valid = frames
    assert not train.isna().to_numpy().any()
    assert not valid.isna().to_numpy().any()


@pending
def test_the_blanked_hours_are_the_ones_missing(frames):
    """Not merely 'no blanks' — the two holes we made are the rows that went."""
    train, valid = frames
    assert BLANK_TRAIN not in train.index
    assert BLANK_VALID not in valid.index


# ── The scored table ──────────────────────────────────────────────────────────

@pending
def test_every_forecast_is_scored_on_the_same_hours(frames):
    """The same-exam rule, one level up from `evaluate.py`.

    Three forecasts, three rows, and the hour count must be identical across them.
    If it is not, the rMAE column is comparing scores drawn from different sets of
    hours and the table means nothing.
    """
    rows = T.run(*frames)
    assert len({row["n"] for row in rows}) == 1


@pending
def test_the_benchmark_scores_exactly_one(frames):
    """A free check on the wiring: the benchmark divided by itself is 1.000."""
    rows = T.run(*frames)
    naive = [r for r in rows if r["model"] == "naive"]
    assert len(naive) == 1
    assert naive[0]["rmae"] == pytest.approx(1.0)


@pending
def test_all_three_forecasts_are_reported(frames):
    rows = T.run(*frames)
    assert {r["model"] for r in rows} == {"naive", "linear", "gbm"}


@pending
def test_every_row_is_labelled_as_validation(frames):
    """Contract 2 again: nothing produced here may claim to be a test score."""
    assert all(row["split"] == "valid" for row in T.run(*frames))


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
    """A clean clone has no results/ directory; the first run must not fail on that."""
    path = tmp_path / "results" / "scores.csv"
    T.record([{"model": "naive", "split": "valid", "n": 1, "mae": 1.0, "rmae": 1.0}], path)
    assert path.exists()
