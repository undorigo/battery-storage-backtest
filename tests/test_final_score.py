"""Contract 2 from the other side.

`test_train.py` checks that the everyday script can never reach the held-back years. This
file checks the one script that may — that it scores them *and nothing else*, and that every
fit learns from everything published before the hours it forecasts, never from those hours.

The test that carries the weight is `test_every_fit_ends_before_the_hours_it_forecasts`.
The daily refits now learn from earlier held-back days on purpose, so "no fit sees a
held-back row" no longer holds; what must hold is that no fit sees its own day.
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
# in 2023, and three weeks of 2024 to be held back — short, because every held-back day is
# a refit of both estimators. Same shape as the one in test_train.py —
# cycles that never line up with a week, and no trend, so the benchmark can be beaten and
# the tree is never asked to predict past what it has seen.

START = pd.Timestamp("2022-10-01 00:00", tz="UTC")
END = pd.Timestamp("2024-01-21 23:00", tz="UTC")


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


class Calls:
    """Every fit and the forecast that follows it, in order, plus what LEAR was handed."""

    def __init__(self):
        self.pairs: list[tuple[pd.DataFrame, pd.DataFrame]] = []
        self.lear: dict = {}


@pytest.fixture(scope="module")
def scored():
    """One `FS.run` on the fixture, with fit, forecast and LEAR watched.

    A stand-in replaces LEAR, as in test_train.py: the wiring is what is tested here, and
    LEAR's own rule about its window is tested in test_models.py.  It skips the first
    held-back day, so the same-exam rule has something to remove.
    """
    src, calls = _sources(), Calls()
    real_fit, real_forecast = M.fit, M.forecast
    pending: list[pd.DataFrame] = []

    def fit(estimator, frame):
        pending.append(frame)                        # what was learned from
        return real_fit(estimator, frame)

    def forecast(model, frame):
        calls.pairs.append((pending.pop(), frame))   # ...and the hours it then forecast
        return real_forecast(model, frame)

    def lear(table, days):
        calls.lear["table"], calls.lear["days"] = table, days
        days = days[1:]                              # skips a day, as a blank clue would make it
        answers = table.loc[days, F.day_answer_columns(table)]
        answers.columns = [int(c[-2:]) for c in answers.columns]
        return F.unfold(answers + 1.0).rename("predicted")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(F, "data_load", lambda key: src[key])
        frames = FS.data()
        table = FS.day_rows()
        mp.setattr(M, "fit", fit)
        mp.setattr(M, "forecast", forecast)
        mp.setattr(M, "lear_walk_forward", lear)
        rows, forecasts = FS.run(*frames, table)
    return frames, rows, forecasts, calls


# ── What each fit learns from ─────────────────────────────────────────────────
# The boundary hours are written out rather than read from `split()`, so these tests
# cannot agree with a mistake there.  Grid labels, so every year ends at 23:00 on the
# Berlin clock.

LAST_TRAIN_HOUR = pd.Timestamp("2022-12-31 23:00")
LAST_VALID_HOUR = pd.Timestamp("2023-12-31 23:00")
FIRST_TEST_HOUR = pd.Timestamp("2024-01-01 00:00")
LAST_TEST_HOUR = pd.Timestamp("2025-12-31 23:00")


def test_every_fit_ends_before_the_hours_it_forecasts(scored):
    """The failure that would matter: learning from the hours being judged."""
    (_, _, holdout), _, _, calls = scored
    days = holdout.index.normalize().nunique()
    assert len(calls.pairs) == 2 * days + 2          # two estimators daily, two frozen
    for learned, forecast in calls.pairs:
        assert learned.index.max() < forecast.index.min()


def test_the_frozen_fits_use_every_year_before_2024_and_stop_there(scored):
    (train, _, holdout), _, _, calls = scored
    frozen = [learned for learned, forecast in calls.pairs if len(forecast) == len(holdout)]
    assert len(frozen) == 2
    for learned in frozen:
        assert learned.index.min() == train.index.min()
        assert learned.index.max() == LAST_VALID_HOUR


def test_the_daily_refits_learn_from_earlier_held_back_days(scored):
    """The cautious mistake: walking forward but never adding the held-back days."""
    (_, _, holdout), _, _, calls = scored
    last_day = holdout.index.normalize().max()
    final = [learned for learned, forecast in calls.pairs
             if forecast.index.min().normalize() == last_day]
    assert len(final) == 2
    for learned in final:
        assert learned.index.max() == last_day - pd.Timedelta(hours=1)   # 23:00 the day before


def test_lear_forecasts_held_back_days_only(scored):
    (_, _, holdout), _, _, calls = scored
    assert calls.lear["days"].isin(holdout.index.normalize()).all()
    assert calls.lear["table"].index.max() <= pd.Timestamp(cfg.TEST_END)


def test_the_label_is_derived_rather_than_written(scored):
    """A hardcoded span would be a second copy of the split dates, free to drift."""
    (train, valid, _), _, _, _ = scored
    assert FS.label("linear", train) != FS.label("linear", pd.concat([train, valid]))


# ── What is scored ────────────────────────────────────────────────────────────

def test_only_held_back_rows_are_scored(scored):
    (_, _, holdout), _, forecasts, _ = scored
    assert holdout.index.min() >= FIRST_TEST_HOUR
    assert holdout.index.max() <= LAST_TEST_HOUR
    assert forecasts.index.isin(holdout.index).all()


def test_no_blank_survives_into_any_frame(scored):
    frames, _, _, _ = scored
    for part in frames:
        assert not part.isna().to_numpy().any()


# ── The scored table ──────────────────────────────────────────────────────────

def test_every_row_is_labelled_as_held_back(scored):
    """A row from here must never be mistaken for a validation score in the record."""
    _, rows, _, _ = scored
    assert all(row["split"] == "test" for row in rows)


def test_the_benchmarks_come_first_and_each_scores_exactly_one(scored):
    _, rows, _, _ = scored
    assert rows[0]["model"] == "naive"
    assert rows[0]["rmae"] == pytest.approx(1.0)
    assert rows[1]["model"] == "naive_field"
    assert rows[1]["rmae_field"] == pytest.approx(1.0)


def test_the_field_benchmark_is_read_off_the_actual_prices_by_date(scored):
    """As in test_train.py: read from the prices by date, not through the lag columns.
    10:00 on a Monday, a Tuesday and a Saturday in January 2024."""
    frames, _, forecasts, _ = scored
    price = pd.concat(frames)[F.TARGET]
    day, week = pd.Timedelta(days=1), pd.Timedelta(days=7)
    for hour, back in (("2024-01-08 10:00", week), ("2024-01-09 10:00", day),
                       ("2024-01-13 10:00", week)):
        hour = pd.Timestamp(hour)
        assert forecasts.loc[hour, "naive_field"] == price[hour - back], hour.day_name()


def test_both_recipes_are_scored(scored):
    _, rows, _, _ = scored
    assert [r["model"] for r in rows] == ["naive", "naive_field", "linear daily", "gbm daily", "lear daily",
                                          "linear 2022-2023", "gbm 2022-2023"]


def test_every_forecast_is_scored_on_the_same_hours(scored):
    """The same-exam rule: the day LEAR skipped leaves every model's exam."""
    (_, _, holdout), rows, forecasts, _ = scored
    skipped = holdout.index.normalize().min()
    assert not (forecasts.index.normalize() == skipped).any()
    assert {row["n"] for row in rows} == {len(forecasts)}


def test_no_model_is_its_own_benchmark(scored):
    """Passing each model's own forecast as its denominator makes every rMAE exactly 1.000."""
    _, rows, _, _ = scored
    for row in rows[2:]:
        assert row["rmae"] < 1.0, f"{row['model']} scored as though it were its own benchmark"
        assert row["rmae_field"] < 1.0, f"{row['model']} scored as the field's benchmark"


def test_daily_and_frozen_do_not_score_identically(scored):
    """The daily rows really refit, rather than one model passed in twice."""
    _, rows, _, _ = scored
    mae = {r["model"]: r["mae"] for r in rows}
    assert mae["gbm daily"] != mae["gbm 2022-2023"]


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


# ── Stage 3's reading: the ranges ─────────────────────────────────────────────
# The same fixture's day table, with a stand-in for LEAR that records the days it is
# handed and forecasts each day as its price, scaled and shifted with a little noise, so
# the dots are not one exact line.  Small windows and seven percentiles keep it quick;
# that the real windows are the four chosen on 2023 is checked on the constant itself.

R_WINDOWS, R_LEVELS = [5, 10], (5, 10, 25, 50, 75, 90, 95)   # each band reported needs its pair
FIRST_TEST_DAY = pd.Timestamp("2024-01-01")


def stand_in_lear(table: pd.DataFrame, days: pd.DatetimeIndex) -> pd.Series:
    answers = table.loc[days, F.day_answer_columns(table)]
    answers.columns = [int(c[-2:]) for c in answers.columns]
    noise = np.random.default_rng(8).normal(0, 3, answers.shape)
    return F.unfold(0.9 * answers + 5 + noise).rename("predicted")


@pytest.fixture(scope="module")
def walked():
    seen: dict = {}

    def lear(table, days):
        seen["days"] = days
        return stand_in_lear(table, days)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(F, "data_load", lambda key: _sources()[key])
        table = FS.day_rows()
        mp.setattr(M, "lear_walk_forward", lear)
        days, forecast = FS.range_walk(table)
    from scripts import quantiles as Q
    return table, days, forecast, Q.prices(table), seen


@pytest.fixture(scope="module")
def read(walked):
    _, days, lear, actual, _ = walked
    return FS.ranges(lear, actual, days, R_WINDOWS, R_LEVELS)


def test_the_real_reading_averages_the_four_windows_chosen_on_2023():
    assert FS.RANGE_WINDOWS == [28, 56, 91, 182]
    assert FS.RANGE_START == pd.Timestamp("2023-07-03")      # 182 days before 2024


def test_lear_walks_from_182_days_before_2024_to_the_last_held_back_day(walked):
    table, days, _, _, seen = walked
    assert seen["days"].equals(days)
    assert days.min() == pd.Timestamp("2023-07-03")
    assert days.max() == pd.Timestamp("2024-01-21")          # the 22nd is incomplete: skipped
    assert (days < FIRST_TEST_DAY).sum() == 182


def test_only_the_two_averages_are_scored_and_only_on_held_back_hours(read):
    rows, kept = read
    assert [r["method"] for r in rows] == ["qra", "conformal"]
    hours = pd.date_range(FIRST_TEST_HOUR, "2024-01-21 23:00", freq="h")
    for row in rows:
        assert row["split"] == "test" and row["window"] == "5+10" and row["n"] == len(hours)
        assert kept[row["method"]].index.equals(hours)


def test_the_reading_is_the_average_of_the_windows_run_alone(walked, read):
    """Checked from outside: each window fitted again through `quantiles`, then averaged."""
    from scripts import quantiles as Q

    _, days, lear, actual, _ = walked
    scored = days[days >= FIRST_TEST_DAY]
    _, kept = read
    alone = [Q.lines(lear, actual, scored, w, R_LEVELS)["qra"][0] for w in R_WINDOWS]
    np.testing.assert_allclose(kept["qra"][list(R_LEVELS)], (alone[0] + alone[1]) / 2)


def test_a_held_back_day_never_learns_from_itself_or_later(walked, read):
    """Prices from 10 January on raised by 500: every range before that day unchanged,
    and 10 January's own range unchanged too, because its window ends the day before."""
    _, days, lear, actual, _ = walked
    _, base = read
    later = actual.copy()
    later[later.index >= pd.Timestamp("2024-01-10")] += 500
    _, moved = FS.ranges(lear, later, days, R_WINDOWS, R_LEVELS)
    until = pd.Timestamp("2024-01-10 23:00")
    for method in ("qra", "conformal"):
        pd.testing.assert_frame_equal(moved[method].loc[:until, list(R_LEVELS)],
                                      base[method].loc[:until, list(R_LEVELS)])
        assert not moved[method].loc["2024-01-11":, list(R_LEVELS)].equals(
            base[method].loc["2024-01-11":, list(R_LEVELS)])


def test_the_ranges_reading_runs_to_its_last_line(tmp_path):
    """`main` is untested elsewhere, and on 19 Oct 2026 the 2023 run crashed at its very
    last step, logging the average's text window as an MLflow number.  This runs the whole
    reading on the fixture, record and MLflow in a temporary folder, to the last line."""
    import functools

    from src import tracking as TR

    db, store = tmp_path / "mlflow.db", tmp_path / "mlruns"
    real_ranges = FS.ranges
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(F, "data_load", lambda key: _sources()[key])
        mp.setattr(M, "lear_walk_forward", stand_in_lear)
        mp.setattr(FS, "RANGE_WINDOWS", R_WINDOWS)
        mp.setattr(FS, "ranges", lambda lear, actual, days: real_ranges(
            lear, actual, days, R_WINDOWS, R_LEVELS))
        mp.setattr(cfg, "QUANTILE_SCORES", tmp_path / "quantile_scores.csv")
        mp.setattr(TR, "log_range", functools.partial(TR.log_range, db=db, store=store))
        assert FS.main(["ranges"]) == 0

    recorded = pd.read_csv(tmp_path / "quantile_scores.csv")
    assert recorded["split"].tolist() == ["test", "test"]
    assert recorded["window"].tolist() == ["5+10", "5+10"]
    for method in ("qra", "conformal"):
        run = TR.latest(db=db, model=method, window="5+10", split="test")
        assert run is not None
        _, kept = TR.read_range(run, db=db)
        assert len(kept) == 21 * 24
