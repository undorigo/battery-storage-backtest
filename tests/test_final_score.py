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
from src import models as M


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


# ── What each recipe learns from ──────────────────────────────────────────────
# Two fits, and the difference between them is the whole point of scoring both. Getting
# either boundary wrong is silent: too cautious wastes a year, too loose fits on the very
# rows being judged.  The boundary hours are written out rather than read from
# `split()`, so these tests cannot agree with a mistake there.  Grid labels, so
# every year ends at 23:00 on the Berlin clock.

LAST_TRAIN_HOUR = pd.Timestamp("2022-12-31 23:00")
LAST_VALID_HOUR = pd.Timestamp("2023-12-31 23:00")
FIRST_TEST_HOUR = pd.Timestamp("2024-01-01 00:00")
LAST_TEST_HOUR = pd.Timestamp("2025-12-31 23:00")


def test_two_recipes_are_scored(frames):
    """One reading, two histories. Five rows, not three."""
    rows = FS.run(*frames)
    assert len(rows) == 5


def test_one_recipe_stops_at_the_training_years(frames):
    """The row that has to stay comparable to the validation score.

    Same recipe as `train.py` — fitted to the end of 2022 — so the only thing differing
    between it and the 0.488 is which years are being forecast.
    """
    train, _, _ = frames
    assert train.index.max() <= LAST_TRAIN_HOUR
    assert FS.label("gbm", train).endswith("2022")


def test_the_other_recipe_uses_the_validation_year_too(frames):
    """The headline row: every year available before the first delivery hour.

    Holding 2023 out was only needed while 2023 was being scored. Here the thing being
    scored is 2024 onwards, so 2023 is history like any other year.
    """
    train, valid, _ = frames
    history = pd.concat([train, valid])
    years = set(history.index.year)                  # grid labels are Berlin already
    assert {2022, 2023} <= years
    assert FS.label("gbm", history).endswith("2023")


def test_no_fit_ever_sees_a_held_back_row(frames, monkeypatch):
    """The failure that would matter: learning from the rows being judged.

    This watches what `run` actually hands to `M.fit`. The version it replaces built its
    own concatenation and checked that instead — so it could not notice if `run` fitted on
    something else entirely, and when the held-back years were let into the fit on purpose
    it stayed green. The leak was caught only incidentally, by the label test.
    """
    _, _, holdout = frames
    seen: list[pd.DataFrame] = []
    real_fit = M.fit

    def spy(estimator, frame):
        seen.append(frame)                           # record what was learned from
        return real_fit(estimator, frame)

    monkeypatch.setattr(M, "fit", spy)
    FS.run(*frames)

    assert len(seen) == 4, "expected two estimators over two histories"
    for frame in seen:
        assert frame.index.max() <= LAST_VALID_HOUR
        assert frame.index.intersection(holdout.index).empty


def test_the_label_is_derived_rather_than_written(frames):
    """A hardcoded span would be a second copy of the split dates, free to drift."""
    train, valid, _ = frames
    assert FS.label("linear", train) != FS.label("linear", pd.concat([train, valid]))


# ── What is scored ────────────────────────────────────────────────────────────

def test_only_held_back_rows_are_scored(frames):
    _, _, holdout = frames
    assert holdout.index.min() >= FIRST_TEST_HOUR
    assert holdout.index.max() <= LAST_TEST_HOUR


def test_no_blank_survives_into_any_frame(frames):
    for part in frames:
        assert not part.isna().to_numpy().any()


# ── The scored table ──────────────────────────────────────────────────────────

def test_every_row_is_labelled_as_held_back(frames):
    """A row from here must never be mistaken for a validation score in the record."""
    assert all(row["split"] == "test" for row in FS.run(*frames))


def test_the_benchmark_appears_once_and_scores_exactly_one(frames):
    rows = [r for r in FS.run(*frames) if r["model"] == "naive"]
    assert len(rows) == 1
    assert rows[0]["rmae"] == pytest.approx(1.0)


def test_both_estimators_appear_under_both_histories(frames):
    names = {r["model"] for r in FS.run(*frames)}
    assert names == {"naive", "linear 2022-2022", "gbm 2022-2022",
                     "linear 2022-2023", "gbm 2022-2023"}


def test_every_forecast_is_scored_on_the_same_hours(frames):
    """The same-exam rule. Five rows, one hour count."""
    assert len({row["n"] for row in FS.run(*frames)}) == 1


def test_no_model_is_its_own_benchmark(frames):
    """Same hole that survived a mutation in test_train.py, closed here too.

    Passing each model's own forecast as its denominator makes every rMAE exactly 1.000
    and every other check in this file still passes.
    """
    for row in FS.run(*frames):
        if row["model"] == "naive":
            continue
        assert row["rmae"] < 1.0, f"{row['model']} scored as though it were its own benchmark"


def test_the_two_recipes_do_not_score_identically(frames):
    """The second history really is longer, rather than the first one passed in twice.

    Named for what it checks. An earlier version claimed to verify that a fresh estimator
    is built per fit — sharing them was tried and every test still passed, because each row
    is scored before the next fit replaces the estimator.
    """
    rows = {r["model"]: r["mae"] for r in FS.run(*frames)}
    assert rows["gbm 2022-2022"] != rows["gbm 2022-2023"]


# ── The sentence a person actually reads ──────────────────────────────────────
# The commit column is the evidence that the held-back years were read twice; this note
# is what tells someone it happened. An enforcement message that says the wrong thing is
# worse than no message, so both branches are pinned.

def recorded(splits: list[str]) -> pd.DataFrame:
    """A stand-in for what `record` reads back out of the CSV."""
    return pd.DataFrame({"split": splits, "model": ["naive"] * len(splits)})


def test_the_note_calls_a_first_reading_a_first_reading():
    frame = recorded(["valid", "valid", "valid", "test", "test", "test"])
    assert "first reading" in FS.reading_note(frame, just_written=3)


def test_the_note_reports_a_second_reading_as_one():
    """Six held-back rows from two runs of three. This must not read as the first."""
    frame = recorded(["valid"] * 3 + ["test"] * 6)
    note = FS.reading_note(frame, just_written=3)
    assert "read before" in note
    assert "first reading" not in note


def test_validation_rows_are_never_counted_as_held_back():
    """The count must key on the split label, not on how many rows the file holds."""
    frame = recorded(["valid"] * 99 + ["test"] * 3)
    assert "first reading" in FS.reading_note(frame, just_written=3)
