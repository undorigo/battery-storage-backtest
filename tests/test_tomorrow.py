"""One day's forecast, as the 2026 replay and `just tomorrow` will make it.

The important test here is `test_a_planted_price_for_day_d_changes_nothing`.  The
live run starts at 19:00 on D-1, when day D's auction has already cleared, so D's
real price is in the cache the run reads.  Nothing else stands between that price
and the forecast: the test plants an absurd one and demands the forecasts and the
plan come out identical to a run that never saw it.

Everything runs on a synthetic cache.  The real parquet files are gitignored, and
no held-back year is read.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts import tomorrow as T
from src import config as cfg
from src import data

# ── The fixture: a year of quarter-hours, as the cache stores them ────────────
# From December 2025 to the end of day D, so LEAR has more days than its 248 clues
# (LassoLarsIC needs that to estimate its noise) and a short window still fits.
# The spring clock change of 29 March 2026 sits inside, for the 92 quarter-hours.
# Column names are the cache's own.  Prices stop at the end of D-1 unless planted.

DAY = pd.Timestamp("2026-11-20")                            # a Friday; Berlin day, grid label
WINDOW = 300                                                # LEAR's window, shortened for speed
PLANTED = 9_999.0                                           # EUR/MWh: no forecast would say this

START = pd.Timestamp("2025-12-01", tz=cfg.TZ_MARKET).tz_convert("UTC")
END = (pd.Timestamp(DAY, tz=cfg.TZ_MARKET) + pd.DateOffset(days=1)).tz_convert("UTC")
D_START = pd.Timestamp(DAY, tz=cfg.TZ_MARKET).tz_convert("UTC")   # where D begins in the cache


def _cache(planted: bool = False) -> dict[str, pd.DataFrame]:
    idx = pd.date_range(START, END, freq="15min", inclusive="left")
    hour = idx.tz_convert(cfg.TZ_MARKET).hour.to_numpy()
    rng = np.random.default_rng(5)
    noise = lambda size: rng.normal(0, size, len(idx))      # noqa: E731 - one-line helper
    load = 50_000 + 8_000 * np.sin(2 * np.pi * (hour - 6) / 24) + noise(2_000)
    onshore, offshore = 12_000 + noise(5_000), 3_000 + noise(1_000)
    solar = np.clip(15_000 * np.sin(np.pi * (hour - 6) / 12), 0, None) + noise(500)
    price = 0.003 * (load - onshore - offshore - solar) + noise(5)   # residual load sets the price
    prices = pd.DataFrame({"day_ahead_price": price}, index=idx)
    if planted:
        prices.loc[prices.index >= D_START] = PLANTED       # D has cleared: 19:00 on D-1
    else:
        prices = prices[prices.index < D_START]             # D has not cleared: noon on D-1
    return {
        "day_ahead_price": prices,
        "load_forecast": pd.DataFrame({"Forecasted Load": load}, index=idx),
        "wind_solar_forecast": pd.DataFrame(
            {"Solar": solar, "Wind Offshore": offshore, "Wind Onshore": onshore}, index=idx),
    }


def _run(cache: dict[str, pd.DataFrame], day: pd.Timestamp = DAY) -> T.Day:
    """The one-day forecast on this cache, read through the real loaders."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(data, "load_raw", lambda key, root=None: cache[key])   # every loader reads this
        return T.forecast_day(day, T.inputs(), lear_window=WINDOW)


@pytest.fixture(scope="module")
def unplanted() -> T.Day:
    """The ordinary run, D's price not yet out; fitted once for every test that reads it."""
    return _run(_cache())


# ── The guard: day D's own price never reaches its forecast ───────────────────
# Planted at 9,999 EUR/MWh across all of D.  If any fit learned from D, or any clue
# read it, the forecasts move by far more than rounding, and so does the plan.

def test_a_planted_price_for_day_d_changes_nothing(unplanted):
    planted = _run(_cache(planted=True))
    pd.testing.assert_frame_equal(planted.forecasts, unplanted.forecasts)
    pd.testing.assert_frame_equal(planted.schedule, unplanted.schedule)
    assert planted.plan_on == unplanted.plan_on == "average"


# ── What a complete day returns ───────────────────────────────────────────────
# Five forecasts on D's 24 slots, and a plan on D's real hours that starts and ends
# empty (Contract 4), made from the average.

def test_a_complete_day_forecasts_with_every_model(unplanted):
    assert unplanted.complete and unplanted.why == ""
    assert list(unplanted.forecasts.columns) == list(T.FORECASTS)
    assert (unplanted.forecasts.index.normalize() == DAY).all()
    assert len(unplanted.forecasts) == 24
    assert unplanted.forecasts.notna().to_numpy().all()


def test_the_average_is_the_three_models_hour_by_hour(unplanted):
    f = unplanted.forecasts
    pd.testing.assert_series_equal(f["average"], (f["LEAR"] + f["tree"] + f["straight line"]) / 3,
                                   check_names=False)


def test_the_plan_is_the_average_on_ds_real_hours_ending_empty(unplanted):
    s = unplanted.schedule
    assert s.index.tz is not None and len(s) == 24          # real hours, as the battery is paid
    assert s.index[0] == D_START
    assert s.level.iloc[-1] == pytest.approx(0, abs=1e-9)   # ends empty
    bought, sold = s.charge.sum(), s.discharge.sum()
    assert sold > 0 and bought > sold                       # it traded, and paid for its losses


def test_every_part_is_timed(unplanted):
    assert set(unplanted.seconds) == {"tree", "straight line", "LEAR", "plan"}
    assert all(v >= 0 for v in unplanted.seconds.values())


# ── Counting what has arrived for D ───────────────────────────────────────────
# The newest of each input: D's four forecasts and D-1's price.  An input is there
# only when every quarter-hour of its day is (decided 5 November 2026).

def test_a_complete_day_counts_96_of_96(unplanted):
    c = unplanted.counts
    assert list(c.index) == list(T.NEWEST)
    assert (c.have == 96).all() and (c.need == 96).all()


def test_the_spring_clock_change_needs_92():
    """D's forecasts on 29 March, the short day; the price the day after, from D-1."""
    on, after = (T.count(pd.Timestamp(d), _cache()) for d in ("2026-03-29", "2026-03-30"))
    assert (on.drop("price").need == 92).all() and on.loc["price", "need"] == 96
    assert (after.drop("price").need == 96).all() and after.loc["price", "need"] == 92
    assert (on.have == on.need).all() and (after.have == after.need).all()


def test_half_a_published_forecast_is_missing_and_the_plan_is_the_simple_rule():
    cache = _cache()
    ws = cache["wind_solar_forecast"]
    cache["wind_solar_forecast"] = ws[ws.index < D_START + pd.Timedelta(hours=12)]   # half of D
    got = _run(cache)
    assert got.counts.loc["wind onshore", "have"] == 48
    assert not got.complete and got.plan_on == "simple rule"
    assert "wind onshore 48/96" in got.why
    assert list(got.forecasts.columns) == ["naive (field)"]     # no model was fitted
    assert got.seconds.keys() == {"plan"}


# ── An older input missing: LEAR cannot run, the others can ───────────────────
# LEAR reads yesterday's forecasts as clues, the tree and the line do not.  A
# forecast for D-1 that never arrived leaves D's counts complete and LEAR stopped:
# the plan is the simple rule's, saying which clue was missing.

def test_a_missing_forecast_for_yesterday_stops_lear_and_the_plan_is_the_simple_rule():
    cache = _cache()
    ws = cache["wind_solar_forecast"]
    yesterday = D_START - pd.Timedelta(days=1)
    cache["wind_solar_forecast"] = ws[(ws.index < yesterday) | (ws.index >= D_START)]
    got = _run(cache)
    assert got.complete                                     # D's own inputs are all there
    assert got.plan_on == "simple rule"
    assert got.why.startswith("LEAR: clue missing, first renew_d1_h00")
    assert {"tree", "straight line"} <= set(got.forecasts.columns)
    assert "LEAR" not in got.forecasts.columns


# ── The evening's rows: every decision, no money ──────────────────────────────
# Tomorrow's rows are written before tomorrow begins: what each forecast said, and
# what each plan would buy and sell.  The price and the euros stay blank until the
# next evening settles them, so nothing written that night can be paid money it
# did not know about.  A day already written is never written again.

MADE_AT, COMMIT = "2026-11-19T19:05:00Z", "abc1234"


def test_tomorrows_rows_are_its_real_hours_with_every_decision_and_no_money(unplanted):
    got = T.rows(unplanted, None, MADE_AT, COMMIT)
    assert list(got.columns) == list(T.DAILY_COLUMNS)
    assert got.index.equals(T.real_hours(DAY))
    assert (got["day"] == "2026-11-20").all() and (got["plan_on"] == "average").all()
    assert (got["made_at"] == MADE_AT).all() and (got["commit"] == COMMIT).all()
    money = [c for c in got.columns if c == "price" or c.startswith("earned:") or c == "net:ceiling"]
    assert got[money].isna().all().all()                    # settled the next evening, not now
    sent = unplanted.schedule
    pd.testing.assert_series_equal(got["net:average"], sent.discharge - sent.charge, check_names=False)


def test_each_forecasts_net_is_its_own_plan(unplanted):
    from src import backtest as BT

    got = T.rows(unplanted, None, MADE_AT, COMMIT)
    for name in T.FORECASTS:
        plan = BT.walk(data.from_slots(unplanted.forecasts[name], T.real_hours(DAY)))
        pd.testing.assert_series_equal(got[f"net:{name}"], plan.discharge - plan.charge,
                                       check_names=False)
        pd.testing.assert_series_equal(got[f"forecast:{name}"],
                                       data.from_slots(unplanted.forecasts[name], T.real_hours(DAY)),
                                       check_names=False)


def test_a_fallback_day_writes_the_simple_rules_plan_and_says_why():
    cache = _cache()
    ws = cache["wind_solar_forecast"]
    cache["wind_solar_forecast"] = ws[ws.index < D_START + pd.Timedelta(hours=12)]
    got = T.rows(_run(cache), None, MADE_AT, COMMIT)
    assert (got["plan_on"] == "simple rule").all()
    assert got["why"].str.contains("wind onshore 48/96").all()
    assert got["forecast:LEAR"].isna().all() and got["net:average"].isna().all()
    assert got["net:naive (field)"].notna().all()           # the plan that was sent


def test_the_record_reads_back_as_written(unplanted, tmp_path):
    path = tmp_path / "daily.csv"
    written = T.rows(unplanted, None, MADE_AT, COMMIT)
    T.write(written, path)
    pd.testing.assert_frame_equal(T.read(path), written, check_freq=False)


def test_a_day_already_written_is_never_written_again(unplanted, tmp_path):
    path = tmp_path / "daily.csv"
    T.write(T.rows(unplanted, None, MADE_AT, COMMIT), path)
    before = path.read_text()
    with pytest.raises(ValueError, match="2026-11-20 is already written"):
        T.write(T.rows(unplanted, None, "2026-11-19T21:05:00Z", COMMIT), path)
    assert path.read_text() == before                       # the plan sent stands


# ── The next evening: paying what was decided ─────────────────────────────────
# A made-up price for D, two waves a day, so the plans have something to trade.
# Settling fills the money columns from the real price and the trades written the
# night before, through the one function that pays a plan; it never touches a
# decision, never pays a day twice, and leaves a day whose price is not out blank.

def _cleared(day: pd.Timestamp = DAY) -> pd.Series:
    """D's real prices, as `data.load` returns them: real hours, UTC."""
    hours = T.real_hours(day)
    return pd.Series(60 + 40 * np.sin(np.arange(len(hours)) * np.pi / 6), index=hours)


def test_settling_pays_each_plan_at_the_real_price_and_changes_no_decision(unplanted):
    from src import backtest as BT

    written = T.rows(unplanted, None, MADE_AT, COMMIT)
    paid = T.settle(written, _cleared())
    decided = [c for c in T.DAILY_COLUMNS if c not in T.MONEY]
    pd.testing.assert_frame_equal(paid[decided], written[decided])
    pd.testing.assert_series_equal(paid["price"], _cleared(), check_names=False)
    best, best_earned = BT.ceiling(_cleared())
    pd.testing.assert_series_equal(paid["earned:ceiling"], best_earned, check_names=False)
    for name in T.FORECASTS:
        plan = BT.walk(data.from_slots(unplanted.forecasts[name], T.real_hours(DAY)))
        _, earned = BT.fixed(data.from_slots(unplanted.forecasts[name], T.real_hours(DAY)), _cleared())
        pd.testing.assert_series_equal(paid[f"earned:{name}"], earned, check_names=False)
        assert paid[f"earned:{name}"].sum() <= paid["earned:ceiling"].sum() + 1e-6, name


def test_a_day_whose_price_is_not_out_stays_unpaid(unplanted):
    written = T.rows(unplanted, None, MADE_AT, COMMIT)
    half = _cleared().iloc[:12]                             # the auction result not complete
    pd.testing.assert_frame_equal(T.settle(written, half), written)


def test_a_paid_day_is_never_paid_again(unplanted):
    paid = T.settle(T.rows(unplanted, None, MADE_AT, COMMIT), _cleared())
    revised = _cleared() + 50                               # ENTSO-E changing a price later
    pd.testing.assert_frame_equal(T.settle(paid, revised), paid)


def test_a_fallback_day_pays_the_simple_rules_plan_and_nothing_it_did_not_make():
    cache = _cache()
    ws = cache["wind_solar_forecast"]
    cache["wind_solar_forecast"] = ws[ws.index < D_START + pd.Timedelta(hours=12)]
    paid = T.settle(T.rows(_run(cache), None, MADE_AT, COMMIT), _cleared())
    assert paid["earned:naive (field)"].notna().all() and paid["earned:ceiling"].notna().all()
    assert paid["earned:average"].isna().all()               # no plan was made, none is paid


def test_paying_the_record_rewrites_only_money(unplanted, tmp_path):
    path = tmp_path / "daily.csv"
    T.write(T.rows(unplanted, None, MADE_AT, COMMIT), path)
    record, days = T.pay(_cleared(), path)
    assert days == ["2026-11-20"]
    pd.testing.assert_frame_equal(T.read(path), record, check_freq=False)
    assert T.pay(_cleared(), path)[1] == []                 # nothing left to pay
