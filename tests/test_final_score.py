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


# ── Stage 4's reading: the battery ────────────────────────────────────────────
# A stand-in cache around both edges of the held-back years, with 5,000 EUR on the
# last day before them and the first day after: neither may reach the reading.
# Stand-in stored runs are found only when asked for by their held-back names, so a
# reading that slipped back to 2023's runs or range finds nothing.  As in the 2023
# command's test, LEAR and the tree miss one way and the line twice as far the
# other, so only the true average plans the ceiling.

def berlin_days(*days: list[float], start: str) -> pd.Series:
    """Prices given per Berlin delivery day, stored in UTC as `data.load` returns them."""
    hours = pd.date_range(start, periods=sum(map(len, days)), freq="h", tz="Europe/Berlin")
    return pd.Series(np.concatenate(days), index=hours.tz_convert("UTC"))


def stand_in_battery(monkeypatch, tmp_path):
    from scripts import backtest as SB
    from src import backtest as BT
    from src import data, tracking as TR

    rng = np.random.default_rng(5)
    cache = pd.concat([berlin_days(*(list(rng.normal(80, 60, 24)) for _ in range(3)), start=start)
                       for start in ("2023-12-30", "2025-12-30")])
    day = BT.delivery_days(cache.index)
    cache[day.isin(pd.DatetimeIndex(["2023-12-31", "2026-01-01"], tz="Europe/Berlin"))] = 5000.0
    monkeypatch.setattr(data, "load", lambda key: cache.to_frame("day_ahead_price"))
    held = cache[(day.year >= 2024) & (day.year <= 2025)]
    slots = data.to_slots(held.to_frame("actual"))["actual"].dropna()
    miss = pd.Series(40 * np.sin(np.arange(len(slots)) * np.pi / 6), index=slots.index)
    run = pd.DataFrame({"actual": slots + 50.0,                       # wrong on purpose: never paid
                        "lear daily": slots + miss, "gbm daily": slots + miss,
                        "linear daily": slots - 2 * miss, "naive_field": 160.0 - slots})
    band = pd.DataFrame({"lear": slots + miss, 75: slots + miss, 25: slots + miss})
    daily = {**SB.DAILY, "split": "test"}
    qra = {**SB.QRA_RUN, "split": "test"}

    def latest(**where):
        if where == qra:
            return "range"
        return "run" if where == {**daily, "model": where["model"]} and \
            where["model"].endswith(" daily") else None
    monkeypatch.setattr(TR, "latest", latest)
    monkeypatch.setattr(TR, "read", lambda run_id: ({"commit": "abc1234"}, run))
    monkeypatch.setattr(TR, "read_range", lambda run_id: ({"commit": "def5678"}, band))
    monkeypatch.setattr(cfg, "CAPTURE_SCORES", tmp_path / "capture_scores.csv")
    return SB


def test_the_battery_reading_reads_2024_25_alone_and_records_what_it_printed(
        monkeypatch, tmp_path, capsys):
    SB = stand_in_battery(monkeypatch, tmp_path)
    assert FS.main(["battery"]) == 0
    out = capsys.readouterr().out
    assert "The battery on 2024-25, 3 days" in out                # 1 Jan 2024, 30 and 31 Dec 2025
    assert "runs at abc1234" in out and "at def5678" in out
    assert "This is the first reading." in out

    recorded = pd.read_csv(tmp_path / "capture_scores.csv")
    assert recorded["run"].tolist() == ["ceiling", "LEAR", "tree", "straight line", "average",
                                        "naive (field)", "bids strict", "bids pair"]
    assert set(recorded["split"]) == {"test"}
    assert set(recorded["days"]) == {3}
    rows = recorded.set_index("run")
    _, fixed = SB.capture(SB.actual_prices("test"), "test")
    _, _, bid = SB.bids(SB.actual_prices("test"), "test")
    for name, row in fixed.items():
        assert rows.loc[name, "earned"] == pytest.approx(row["earned"])
    for rule in ("strict", "pair"):
        assert rows.loc[f"bids {rule}", "earned"] == pytest.approx(bid[rule]["earned"])
        assert rows.loc[f"bids {rule}", "lost"] == 0
    assert rows.loc["average", "capture"] == pytest.approx(1.0)   # the true shape: the ceiling
    assert rows.loc["LEAR", "capture"] < 1.0
    assert fixed["ceiling"]["earned"] < 1000 * 3                  # 5,000 EUR never seen


def test_the_battery_reading_names_the_held_back_run_it_needs(monkeypatch):
    from scripts import backtest as SB
    from src import tracking as TR

    monkeypatch.setattr(TR, "latest", lambda **where: None)
    hours = pd.DatetimeIndex([], tz="UTC")
    with pytest.raises(LookupError, match="no stored 2024-25 LEAR run: run `just final-score` first"):
        SB.forecasts(hours, "test")
    with pytest.raises(LookupError, match="2024-25 QRA range: run `just final-score ranges` first"):
        SB.ranges(hours, pd.Series(dtype=float), "test")


# ── Stage 5's reading: 2026, replayed once ────────────────────────────────────
# A synthetic cache of quarter-hours from March 2025 to 4 January 2026, read through the
# real loaders, the replay shortened to 1-3 January with two short windows and three
# percentiles.  LEAR is the real one on a short window, because the point of the replay
# is that every day goes through `forecast_day` unchanged.  4 January sits in the cache
# at 5,000 EUR, as November does in the real one: nothing may read it.

LIVE_DAYS = pd.date_range("2026-01-01", "2026-01-03")
L_WINDOWS, L_LEVELS, L_LEAR = [3, 5], (25, 50, 75), 260     # LEAR needs more days than its 248 clues
PLANTED = 9_999.0                                           # EUR/MWh: no forecast would say this


def live_cache(planted: str | None = None, blank_wind: str | None = None) -> dict[str, pd.DataFrame]:
    """The cache as pulled: UTC quarter-hours, the cache's own column names."""
    idx = pd.date_range(pd.Timestamp("2025-03-01", tz=cfg.TZ_MARKET).tz_convert("UTC"),
                        pd.Timestamp("2026-01-05", tz=cfg.TZ_MARKET).tz_convert("UTC"),
                        freq="15min", inclusive="left")
    local = idx.tz_convert(cfg.TZ_MARKET)
    day, hour = local.normalize().tz_localize(None), local.hour.to_numpy()
    rng = np.random.default_rng(11)
    noise = lambda size: rng.normal(0, size, len(idx))      # noqa: E731 - one-line helper
    load = 50_000 + 8_000 * np.sin(2 * np.pi * (hour - 6) / 24) + noise(2_000)
    onshore, offshore = 12_000 + noise(5_000), 3_000 + noise(1_000)
    solar = np.clip(15_000 * np.sin(np.pi * (hour - 6) / 12), 0, None) + noise(500)
    price = 0.003 * (load - onshore - offshore - solar) + noise(5)   # residual load sets the price
    price[day == pd.Timestamp("2026-01-04")] = 5_000.0      # after the replay: never read
    if planted:
        price[day == pd.Timestamp(planted)] = PLANTED
    wind = pd.DataFrame({"Solar": solar, "Wind Offshore": offshore, "Wind Onshore": onshore}, index=idx)
    if blank_wind:
        wind = wind[day != pd.Timestamp(blank_wind)]        # that day's forecast never came
    return {"day_ahead_price": pd.DataFrame({"day_ahead_price": price}, index=idx),
            "load_forecast": pd.DataFrame({"Forecasted Load": load}, index=idx),
            "wind_solar_forecast": wind}


def live_world(mp: pytest.MonkeyPatch, cache: dict, tmp_path) -> None:
    """Every loader reads `cache`, the replay is 1-3 January, records and MLflow in `tmp_path`."""
    import functools

    from src import data
    from src import tracking as TR

    db, store = tmp_path / "mlflow.db", tmp_path / "mlruns"
    mp.setattr(data, "load_raw", lambda key, root=None: cache[key])
    mp.setattr(cfg, "LIVE_START", "2026-01-01")
    mp.setattr(cfg, "REPLAY_END", "2026-01-03")
    mp.setattr(cfg, "CAPTURE_SCORES", tmp_path / "capture_scores.csv")
    mp.setattr(TR, "latest", functools.partial(TR.latest, db=db))
    mp.setattr(TR, "log_replay", functools.partial(TR.log_replay, db=db, store=store))


def live_replay(tmp_path, **cache) -> dict:
    with pytest.MonkeyPatch.context() as mp:
        live_world(mp, live_cache(**cache), tmp_path)
        return FS.replay_2026(L_WINDOWS, L_LEVELS, L_LEAR)


@pytest.fixture(scope="module")
def replayed(tmp_path_factory) -> dict:
    """The ordinary replay; fitted once for every test that reads it."""
    return live_replay(tmp_path_factory.mktemp("replay"))


def test_the_real_replay_is_the_ten_months_and_its_window_the_half_year_before():
    days = FS.live_days()
    assert len(days) == 304 and days[0] == pd.Timestamp("2026-01-01")
    assert days[-1] == pd.Timestamp("2026-10-31")
    table = pd.DataFrame(index=pd.date_range("2025-01-01", "2025-12-31"))   # no clue columns: all ready
    assert FS.warm_up_days(table, FS.RANGE_WINDOWS)[0] == pd.Timestamp("2025-07-03")


# ── Every day is forecast_day's ───────────────────────────────────────────────
# The replay adds no fit of its own: its forecasts for a day are the ones the evening
# run would make for it, and the average's fixed plan is the very plan that run sends.

def test_each_replayed_day_is_what_forecast_day_makes(replayed, tmp_path):
    from scripts import tomorrow as T
    from src import backtest as BT

    assert (replayed["forecasts"].index.normalize().unique() == LIVE_DAYS).all()
    assert list(replayed["forecasts"].columns) == list(T.FORECASTS)
    with pytest.MonkeyPatch.context() as mp:
        live_world(mp, live_cache(), tmp_path)
        alone = T.forecast_day(pd.Timestamp("2026-01-02"), T.inputs(), L_LEAR)
    pd.testing.assert_frame_equal(replayed["forecasts"].loc["2026-01-02"], alone.forecasts)

    from src import data
    average = data.from_slots(replayed["forecasts"]["average"], replayed["actual"].index)
    pd.testing.assert_frame_equal(BT.fixed(average, replayed["actual"])[0], replayed["sent"])


def test_lear_walks_the_longest_window_before_the_first_day_then_every_replayed_day(replayed):
    days = replayed["lear"].index.normalize().unique()
    assert days[0] == pd.Timestamp("2025-12-27") and days[-1] == pd.Timestamp("2026-01-03")
    assert len(days) == max(L_WINDOWS) + len(LIVE_DAYS)
    pd.testing.assert_series_equal(replayed["lear"].loc["2026-01-01":], replayed["forecasts"]["LEAR"],
                                   check_names=False)


def test_the_range_is_qra_alone_each_window_run_by_quantiles_then_averaged(replayed, tmp_path):
    """Checked from outside: each window fitted again through `quantiles`, then averaged."""
    from scripts import quantiles as Q

    with pytest.MonkeyPatch.context() as mp:
        live_world(mp, live_cache(), tmp_path)
        prices = Q.prices(F.day_table())                    # the real prices on the grid
    alone = [Q.lines(replayed["lear"], prices, LIVE_DAYS, w, L_LEVELS)["qra"][0] for w in L_WINDOWS]
    np.testing.assert_allclose(replayed["range"][list(L_LEVELS)], (alone[0] + alone[1]) / 2)
    assert replayed["range"].index.equals(replayed["forecasts"].index)   # the replayed hours only


# ── What a replayed day may read ──────────────────────────────────────────────
# 9,999 EUR planted on 2 January.  Everything decided for 1 and 2 January must come out
# identical: their forecasts, their range and the plans sent.  What 2 January earned must
# move, because settlement is the one step that reads the real price.  (3 January's
# forecasts may move: by then 2 January's price is a day old and public.)

def test_a_planted_price_reaches_only_its_own_days_settlement(replayed, tmp_path):
    planted = live_replay(tmp_path, planted="2026-01-02")
    until = "2026-01-02 23:00"
    pd.testing.assert_frame_equal(planted["forecasts"].loc[:until], replayed["forecasts"].loc[:until])
    pd.testing.assert_frame_equal(planted["range"].loc[:until], replayed["range"].loc[:until])
    end = pd.Timestamp("2026-01-03", tz=cfg.TZ_MARKET).tz_convert("UTC")
    pd.testing.assert_frame_equal(planted["sent"][planted["sent"].index < end],
                                  replayed["sent"][replayed["sent"].index < end])
    for run in ("average", "LEAR", "naive (field)"):
        was, now = replayed["fixed"][run]["per_day"], planted["fixed"][run]["per_day"]
        assert now.iloc[0] == pytest.approx(was.iloc[0])     # 1 January: untouched
        assert abs(now.iloc[1] - was.iloc[1]) > 100          # 2 January: paid at 9,999


def test_the_battery_is_settled_on_the_replayed_days_alone(replayed):
    from src import backtest as BT

    days = BT.delivery_days(replayed["actual"].index).unique()
    assert list(days.strftime("%Y-%m-%d")) == ["2026-01-01", "2026-01-02", "2026-01-03"]
    assert replayed["actual"].max() < 5_000                  # 4 January never reached


def test_no_run_beats_the_ceiling_and_no_filled_round_loses(replayed):
    for name, row in replayed["fixed"].items():
        assert row["days_above"] == 0, name
        assert row["earned"] <= replayed["fixed"]["ceiling"]["earned"] + 1e-6, name
    for rule in ("strict", "pair"):
        assert replayed["bid"][rule]["lost"] == 0


# ── A day that fell back stops the reading ────────────────────────────────────
# Decided 9 November 2026: no 2026 day falls back, so no rule for scoring one is built.
# If one ever does, the reading names it and scores nothing.

def test_a_day_that_fell_back_stops_the_replay_and_names_it(tmp_path):
    with pytest.raises(ValueError, match=r"2026-01-02 fell back \(input missing: wind onshore 0/96"):
        live_replay(tmp_path, blank_wind="2026-01-02")


# ── The reading, recorded once and visibly ────────────────────────────────────
# Run to its last line on the fixture: the rows go to the capture record labelled 2026,
# the note calls it the first reading, and the replay's hourly table comes back from MLflow.

def test_the_2026_reading_records_its_rows_and_stores_the_replay(tmp_path, capsys):
    from src import tracking as TR

    with pytest.MonkeyPatch.context() as mp:
        live_world(mp, live_cache(), tmp_path)
        assert FS.read_2026(L_WINDOWS, L_LEVELS, L_LEAR) == 0
    out = capsys.readouterr().out
    assert "3 days through forecast_day, none fell back" in out
    assert "no stored 2024-25 LEAR to check it against" in out
    assert "8 2026 rows recorded. This is the first reading." in out

    recorded = pd.read_csv(tmp_path / "capture_scores.csv")
    assert recorded["run"].tolist() == ["ceiling", "LEAR", "tree", "straight line", "average",
                                        "naive (field)", "bids strict", "bids pair"]
    assert set(recorded["split"].astype(str)) == {"2026"} and set(recorded["days"]) == {3}

    db = tmp_path / "mlflow.db"
    run = TR.latest(db=db, model="replay", split="2026")
    params, kept = TR.read_range(run, db=db)
    assert params["window"] == "3+5" and params["lear_window"] == "260"
    assert len(kept) == 3 * 24
    assert {"actual", "LEAR", "average", "naive (field)", 25, 50, 75} <= set(kept.columns)


def test_the_note_counts_2026_rows_apart_from_the_held_back_ones():
    first = recorded(["test"] * 8 + [2026] * 8)             # read back from CSV as a number
    assert "8 2026 rows recorded. This is the first reading." in FS.reading_note(first, 8, "2026")
    second = recorded(["test"] * 8 + ["2026"] * 16)
    note = FS.reading_note(second, 8, "2026")
    assert "2026 has been read before" in note and "first reading" not in note
