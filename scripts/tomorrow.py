"""One day's forecast and plan — the code the 2026 replay and `just tomorrow` share.

`forecast_day` takes a delivery day D and what the cache holds, and returns what
arrived for D, five forecasts on D's 24 slots, the battery's plan on D's real hours,
and how long each part took.  The replay calls it once per day of 2026; the
evening run calls it once, for tomorrow.  One function, so ten months of replay
are also the test of the daily code (decided 31 October 2026).

**Day D's own price is in the cache when this runs live.**  The run starts at
19:00 on D-1, after D's auction cleared at about 12:45, so nothing but the rule
below keeps that price out: every fit learns from days before D, and every clue
is a whole earlier day.  `tests/test_tomorrow.py` plants an absurd price for D and
checks that nothing moves.

Nothing here settles or writes anything.  Filling in yesterday's earnings and
recording the run belong to the caller.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import pandas as pd

from src import backtest as BT
from src import config as cfg
from src import data
from src import features as F
from src import models as M


# ── What the cache holds, read once ───────────────────────────────────────────
# The feature frame and LEAR's day table are built once and handed to every day,
# because the replay forecasts some 300 days from the same cache.  The raw series
# come along because only they can say whether a quarter-hour arrived: averaging
# up to hours gives an hour a value from one quarter-hour of its four.

@dataclass(frozen=True)
class Inputs:
    """The cache as pulled, and the two tables the models read."""

    raw: dict[str, pd.DataFrame]                            # UTC, as pulled, for counting
    frame: pd.DataFrame                                     # features.build(): one row per slot
    table: pd.DataFrame                                     # features.day_table(): one row per day


def inputs() -> Inputs:
    """Everything a day's forecast reads, from the cache."""
    raw = {key: data.load_raw(key) for key in F.SOURCES}
    return Inputs(raw=raw, frame=F.build(), table=F.day_table())


# ── Has every quarter-hour arrived? ───────────────────────────────────────────
# The newest of each input only: D's four forecasts and D-1's price.  They are
# what arrives between one evening's run and the next, so they are what an hourly
# retry can wait for.  A gap in an older day shows up below, as a model unable to
# run.  Every series is quarter-hourly from 2026 on, so a Berlin day needs 96,
# 92 in spring and 100 in autumn.

NEWEST = {                                                  # name: cache key, column, days before D
    "load forecast": ("load_forecast", "Forecasted Load", 0),
    "wind onshore": ("wind_solar_forecast", "Wind Onshore", 0),
    "wind offshore": ("wind_solar_forecast", "Wind Offshore", 0),
    "solar": ("wind_solar_forecast", "Solar", 0),
    "price": ("day_ahead_price", "day_ahead_price", 1),
}
QUARTER = pd.Timedelta(minutes=15)


def count(day: pd.Timestamp, raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Per input: quarter-hours in the cache for its day, and how many that day has."""
    rows = {}
    for name, (key, column, back) in NEWEST.items():
        start = pd.Timestamp(day - pd.Timedelta(days=back), tz=cfg.TZ_MARKET)   # Berlin midnight
        end = start + pd.DateOffset(days=1)                 # 23, 24 or 25 hours later
        series = raw[key][column]
        inside = series[(series.index >= start) & (series.index < end)]
        rows[name] = {"have": int(inside.notna().sum()), "need": int((end - start) / QUARTER)}
    return pd.DataFrame.from_dict(rows, orient="index")


# ── What comes back ───────────────────────────────────────────────────────────
# The five forecasts sit on D's 24 slots, as the stored runs keep them; the plan
# sits on D's real hours, as the battery is paid.  `why` is empty when the plan is
# the average, and otherwise says what was missing, so a fallback day says why.

FORECASTS = ("LEAR", "tree", "straight line", "average", "naive (field)")   # the page's names


@dataclass(frozen=True)
class Day:
    """One delivery day: what arrived, what was forecast, what the battery plans."""

    day: pd.Timestamp
    counts: pd.DataFrame                                    # have / need per newest input
    forecasts: pd.DataFrame                                 # 24 slots, one column per forecast made
    plan_on: str                                            # "average" or "simple rule"
    why: str                                                # "" unless the plan fell back
    schedule: pd.DataFrame                                  # charge, discharge, level on real hours
    seconds: dict[str, float]

    @property
    def complete(self) -> bool:
        return bool((self.counts.have >= self.counts.need).all())


# ── The forecasts, fitted on days before D only ───────────────────────────────
# The same two walks the backtest used, handed one day: the tree and the line learn
# from every complete hour before D's first, LEAR from the `lear_window` complete
# days before D.  The strictly-before rule lives inside them, already tested; this
# file adds no fit of its own, so it has no second copy of that rule to get wrong.
#
# A model runs only when every input it reads for D is there.  The tree and the line
# read nothing LEAR does not, so in practice only LEAR can stop: a forecast for D-1
# or D-7 that never came.  Any model stopped, or an input for D incomplete, and the
# plan is the simple rule's (decided 6 November 2026), which needs only old prices.

HOURLY = {"tree": M.gbm, "straight line": M.linear}


def _first_blank(values: pd.DataFrame) -> str | None:
    blank = values.columns[values.isna().any()]
    return None if blank.empty else blank[0]


def _models(day: pd.Timestamp, given: Inputs, rows: pd.DataFrame,
            lear_window: int | None) -> tuple[dict[str, pd.Series], list[str], dict[str, float]]:
    made, stopped, seconds = {}, [], {}
    history = F.complete_rows(given.frame)                  # walk_forward keeps the hours before D
    for name, make in HOURLY.items():
        blank = _first_blank(rows[F.feature_columns(rows)])
        if blank:
            stopped.append(f"{name}: input missing, first {blank}")
            continue
        started = time.perf_counter()
        made[name] = M.walk_forward(make, history, rows, "D")
        seconds[name] = time.perf_counter() - started
    clues = given.table.loc[[day], F.day_feature_columns(given.table)]
    blank = _first_blank(clues)
    if blank:
        stopped.append(f"LEAR: clue missing, first {blank}")
    else:
        started = time.perf_counter()
        made["LEAR"] = M.lear_walk_forward(given.table, pd.DatetimeIndex([day]), lear_window)
        seconds["LEAR"] = time.perf_counter() - started
    return made, stopped, seconds


# ── One day, end to end ───────────────────────────────────────────────────────
# Count, forecast, plan.  The plan is the average laid onto D's real hours (23, 24
# or 25) and planned on its own, starting and ending empty, as every backtest day
# was (Contract 4).  With an input for D incomplete nothing is fitted: the caller
# retries in an hour, or after the last try sends this simple-rule plan.

def real_hours(day: pd.Timestamp) -> pd.DatetimeIndex:
    """D's delivery hours as they happen, in UTC."""
    start = pd.Timestamp(day, tz=cfg.TZ_MARKET)
    return pd.date_range(start, start + pd.DateOffset(days=1), freq="h",
                         inclusive="left").tz_convert(cfg.TZ_STORAGE)


def forecast_day(day: pd.Timestamp, given: Inputs,
                 lear_window: int | None = M.WINDOW_DAYS) -> Day:
    """What arrived for `day`, its forecasts from days before it, and the battery's plan."""
    day = pd.Timestamp(day).normalize()                     # a grid label: Berlin day, naive
    counts = count(day, given.raw)
    rows = given.frame[given.frame.index.normalize() == day]    # D's 24 slots
    forecasts = {"naive (field)": M.field_naive(rows)}      # old prices only: always made
    seconds = {}
    if (counts.have < counts.need).any():
        short = counts[counts.have < counts.need]
        why = "input missing: " + ", ".join(f"{n} {r.have}/{r.need}" for n, r in short.iterrows())
    else:
        made, stopped, seconds = _models(day, given, rows, lear_window)
        forecasts.update(made)
        if stopped:
            why = "; ".join(stopped)
        else:
            forecasts["average"] = sum(made[name] for name in ("LEAR", "tree", "straight line")) / 3
            why = ""
    plan_on = "simple rule" if why else "average"
    table = pd.DataFrame({name: forecasts[name] for name in FORECASTS if name in forecasts})

    started = time.perf_counter()
    prices = data.from_slots(table["naive (field)" if why else "average"], real_hours(day))
    schedule = BT.walk(prices)                              # one day, from empty, ending empty
    seconds["plan"] = time.perf_counter() - started
    return Day(day=day, counts=counts, forecasts=table, plan_on=plan_on, why=why,
               schedule=schedule, seconds=seconds)
