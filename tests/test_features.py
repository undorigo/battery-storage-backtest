"""Contract 1, enforced rather than declared.

The important test in this file is `test_deleting_the_future_changes_nothing`.
Every other check here can be satisfied by careful naming; that one cannot, because
it rebuilds the frame from data the market had not yet seen and compares the result
value by value.  If a feature ever reaches forward, it moves, and the test fails.

Everything runs on a synthetic fixture.  The real parquet files are gitignored, so a
test that needed them would pass on this machine and fail on a clean clone — which
is the opposite of what the Third Law asks for.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import config as cfg
from src import features as F
from src.sources import entsoe


# ── The fixture ───────────────────────────────────────────────────────────────
# Three months of hourly data on the world clock, as the cache stores it, ending just
# past the spring clock change on 31 March 2024 so that the grid's invented 02:00 is
# exercised rather than assumed.  Values are deterministic and deliberately unlike
# each other, so a column that picks up the wrong series is obvious instead of plausible.
#
# `build()` returns the 24-slot grid, so rows are looked up by naive Berlin labels.

START = pd.Timestamp("2024-01-01 00:00", tz="UTC")
END = pd.Timestamp("2024-04-02 23:00", tz="UTC")


def _index() -> pd.DatetimeIndex:
    return pd.date_range(START, END, freq="h", tz="UTC")


def _sources() -> dict[str, pd.DataFrame]:
    idx = _index()
    n = np.arange(len(idx), dtype=float)
    return {
        # A ramp plus a daily wave: every hour differs from every other, so a lag
        # that is off by one is caught rather than hidden behind a flat stretch.
        "day_ahead_price": pd.DataFrame({"price": n + 10 * np.sin(n / 24 * 2 * np.pi)}, index=idx),
        "load_forecast": pd.DataFrame({"load": 40000 + n}, index=idx),
        "wind_solar_forecast": pd.DataFrame(
            {"Wind Onshore": 5000 + n, "Wind Offshore": 1000 + n, "Solar": 2000 + n},
            index=idx,
        ),
    }


@pytest.fixture
def built(monkeypatch) -> pd.DataFrame:
    """The frame built from the fixture instead of the cache."""
    src = _sources()
    monkeypatch.setattr(F, "data_load", lambda key: src[key])
    return F.build()


# ── The permitted sources ─────────────────────────────────────────────────────
# `SOURCES` is checked when the module is imported, so these tests confirm the
# check is real rather than decorative — the second one reproduces the mistake it
# exists to stop.

def test_every_source_is_knowable_or_is_the_target():
    for key in F.SOURCES:
        item = entsoe.get(key)
        assert item.known_before_gate_closure or item is entsoe.TARGET


def test_the_hindsight_twins_are_not_sources():
    assert "actual_load" not in F.SOURCES
    assert "actual_generation" not in F.SOURCES


def test_adding_a_forbidden_series_would_fail_the_import_check():
    """Re-run the guard by hand: the trap has to actually spring."""
    item = entsoe.get("actual_generation")
    assert not (item.known_before_gate_closure or item is entsoe.TARGET)


@pytest.mark.parametrize("forbidden", ["actual_load", "actual_generation"])
def test_the_loader_refuses_a_series_outside_sources(forbidden):
    """Guards the use, not just the declaration.

    Reaching past SOURCES is otherwise a one-word edit inside any function in the
    module, and the declaration at the top would still read correctly.
    """
    with pytest.raises(ValueError, match="may not read"):
        F.data_load(forbidden)


def test_no_lag_reaches_into_the_delivery_day():
    # Day D's prices are published after gate closure for day D. A lag below 24 h
    # would reach them for the late evening hours.
    assert min(F.PRICE_LAGS) >= F.MIN_PRICE_LAG_HOURS == 24


# ── The headline test ─────────────────────────────────────────────────────────
# Rebuild one delivery day's features from a world that stops at gate closure, and
# require every value to be identical.  Prices for day D are cut because the auction
# publishes them after the decision; the forecasts for day D are kept because they
# were published that morning, which is exactly the distinction Contract 1 draws.
#
# The future is cut from the world-clock original, before `build()` translates it,
# because that is the order reality has.  1 April is the first day whose "yesterday"
# holds the grid's invented 02:00, filled from a later hour: if that fill ever
# reached into day D, this is the case that would move.

@pytest.mark.parametrize("day", ["2024-03-20", "2024-04-01"])   # an ordinary day; the first after the fill
def test_deleting_the_future_changes_nothing(monkeypatch, day):
    src = _sources()
    delivery_day = pd.Timestamp(day, tz=cfg.TZ_MARKET)
    day_start = delivery_day.tz_convert("UTC")               # where the cut falls in the cache
    day_end = (delivery_day + pd.DateOffset(days=1)).tz_convert("UTC")

    monkeypatch.setattr(F, "data_load", lambda key: src[key])
    full = F.build()

    # Everything the market had at 12:00 on D-1: prices up to the end of D-1, and
    # forecasts up to the end of D. Nothing beyond either.
    truncated = {
        "day_ahead_price": src["day_ahead_price"].loc[src["day_ahead_price"].index < day_start],
        "load_forecast": src["load_forecast"].loc[src["load_forecast"].index < day_end],
        "wind_solar_forecast": src["wind_solar_forecast"].loc[
            src["wind_solar_forecast"].index < day_end
        ],
    }
    monkeypatch.setattr(F, "data_load", lambda key: truncated[key])
    partial = F.build()

    grid_day = pd.Timestamp(day)                            # the same day as grid labels
    rows = full.index.normalize() == grid_day
    expected = full.loc[rows, F.feature_columns(full)]
    actual = partial.loc[partial.index.isin(full.index[rows]), F.feature_columns(partial)]

    assert len(actual) == len(expected) == 24
    pd.testing.assert_frame_equal(actual, expected)


def test_a_day_with_no_price_still_gets_its_features(monkeypatch):
    """The state at gate closure: tomorrow has forecasts, no price, and must be usable.

    This is the row stage 4 has to schedule from, so the builder has to produce it.
    The target is NaN — that is honest — but every feature is present.
    """
    src = _sources()
    day_start = pd.Timestamp("2024-03-20", tz=cfg.TZ_MARKET).tz_convert("UTC")
    truncated = dict(src)
    truncated["day_ahead_price"] = src["day_ahead_price"].loc[
        src["day_ahead_price"].index < day_start
    ]
    monkeypatch.setattr(F, "data_load", lambda key: truncated[key])

    frame = F.build()
    tomorrow = frame.loc[frame.index.normalize() == pd.Timestamp("2024-03-20")]

    assert len(tomorrow) == 24
    assert tomorrow[F.TARGET].isna().all()                          # the auction has not cleared
    assert tomorrow[F.feature_columns(frame)].notna().to_numpy().all()


# ── Lags and the daily summary ────────────────────────────────────────────────

def test_price_lags_match_the_series_shifted(built):
    src = _sources()["day_ahead_price"].iloc[:, 0]
    t = pd.Timestamp("2024-03-15 09:00")                            # Berlin, winter
    for lag in F.PRICE_LAGS:
        then = (t - pd.Timedelta(hours=lag)).tz_localize(cfg.TZ_MARKET)   # find it in the cache
        assert built.loc[t, f"price_lag_{lag}h"] == src.loc[then]


def test_a_lag_across_the_clock_change_is_the_same_berlin_hour(built):
    """What the grid changes: yesterday's 09:00, not the hour 24 real hours ago.

    31 March has 23 real hours, so 24 hours before 1 April 09:00 is 31 March 08:00.
    The morning ramp lives on the Berlin clock, and the lag should follow it.
    """
    src = _sources()["day_ahead_price"].iloc[:, 0]
    yesterday_9 = pd.Timestamp("2024-03-31 09:00", tz=cfg.TZ_MARKET)
    assert built.loc[pd.Timestamp("2024-04-01 09:00"), "price_lag_24h"] == src.loc[yesterday_9]


def test_daily_summary_describes_the_previous_market_local_day(built):
    src = _sources()["day_ahead_price"].iloc[:, 0]
    local = src.index.tz_convert(cfg.TZ_MARKET)
    yesterday = src[
        (local >= pd.Timestamp("2024-03-14", tz=cfg.TZ_MARKET))
        & (local < pd.Timestamp("2024-03-15", tz=cfg.TZ_MARKET))
    ]
    t = pd.Timestamp("2024-03-15 09:00")
    assert built.loc[t, "price_d1_min"] == yesterday.min()
    assert built.loc[t, "price_d1_max"] == yesterday.max()
    assert built.loc[t, "price_d1_last"] == yesterday.iloc[-1]
    assert built.loc[t, "price_d1_spread"] == yesterday.max() - yesterday.min()


def test_the_summary_flips_at_local_midnight_not_utc_midnight(built):
    """23:00 Berlin and 00:00 Berlin belong to different delivery days."""
    late = pd.Timestamp("2024-03-14 23:00")
    early = pd.Timestamp("2024-03-15 00:00")
    assert built.loc[late, "price_d1_max"] != built.loc[early, "price_d1_max"]


def test_a_missing_day_yields_nan_rather_than_the_day_before_last(monkeypatch):
    """`shift(1)` moves one row, so a gap would silently hand over the wrong day."""
    src = _sources()
    price = src["day_ahead_price"]
    local = price.index.tz_convert(cfg.TZ_MARKET)
    gap = (local >= pd.Timestamp("2024-02-10", tz=cfg.TZ_MARKET)) & (
        local < pd.Timestamp("2024-02-11", tz=cfg.TZ_MARKET)
    )
    src["day_ahead_price"] = price.loc[~gap]                # 10 February removed entirely
    monkeypatch.setattr(F, "data_load", lambda key: src[key])

    frame = F.build()
    t = pd.Timestamp("2024-02-11 09:00")                    # its "yesterday" is the missing day
    assert pd.isna(frame.loc[t, "price_d1_max"])


# ── The rest of the frame ─────────────────────────────────────────────────────

def test_residual_load_is_demand_minus_wind_and_solar(built):
    expected = (
        built.load_forecast - built.wind_onshore - built.wind_offshore - built.solar
    )
    pd.testing.assert_series_equal(built.residual_load, expected, check_names=False)


def test_calendar_is_read_on_the_market_clock(built):
    # 12:00 UTC in January is 13:00 in Berlin; in summer it would be 14:00.  The
    # price pins the row to the cache's hour, so the label cannot just agree with itself.
    src = _sources()["day_ahead_price"].iloc[:, 0]
    winter = pd.Timestamp("2024-01-15 13:00")
    assert built.loc[winter, F.TARGET] == src.loc[pd.Timestamp("2024-01-15 12:00", tz="UTC")]
    assert built.loc[winter, "hour"] == 13
    assert built.loc[winter, "dayofweek"] == 0                      # a Monday
    assert not built.loc[winter, "is_weekend"]


def test_the_short_clock_change_day_has_24_slots(built):
    on_the_day = built[built.index.normalize() == pd.Timestamp("2024-03-31")]
    assert len(on_the_day) == 24                                    # 02:00 is invented
    assert sorted(on_the_day.hour) == list(range(24))


def test_weekend_flag_marks_saturday_and_sunday(built):
    assert built.is_weekend.to_numpy().tolist() == (built.index.dayofweek >= 5).tolist()


def test_complete_rows_drops_exactly_the_rows_with_a_missing_value(built):
    complete = F.complete_rows(built)
    assert not complete.isna().to_numpy().any()
    assert len(complete) == len(built) - built.isna().any(axis=1).sum()


def test_the_first_week_has_no_week_old_price(built):
    assert built.price_lag_168h.head(168).isna().all()
    assert built.price_lag_168h.iloc[168:].notna().all()


def test_feature_columns_excludes_the_target(built):
    cols = F.feature_columns(built)
    assert F.TARGET not in cols
    assert set(cols) | {F.TARGET} == set(built.columns)


def test_the_frame_is_sorted_and_unique(built):
    assert built.index.is_monotonic_increasing
    assert built.index.is_unique
    assert built.index.tz is None                                   # the grid: Berlin wall clock


def test_every_whole_day_has_24_rows(built):
    """The grid's promise, checked on the built frame; the fixture's ends are part days."""
    per_day = built.groupby(built.index.normalize()).size()
    assert (per_day.iloc[1:-1] == 24).all()
