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
