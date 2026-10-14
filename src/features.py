"""Build the feature frame: one row per delivery hour, nothing the market did not know.

Owner of Contract 1 in its enforced form.  `src/sources/entsoe.py` *declares* when
each series becomes public; this file is where that declaration starts costing
something, because every column here has to survive the question "was this value
knowable at 12:00 on the day before delivery?"

The failure mode is silent.  A leaked column produces excellent metrics and a model
that loses money, and nothing raises.  So the guard is not a comment: `SOURCES` is
checked against the catalog at import, and `tests/test_features.py` rebuilds the
frame with the future deleted and asserts not one value moved.
"""

from __future__ import annotations

import holidays
import numpy as np
import pandas as pd

from src import config as cfg
from src import data
from src.sources import entsoe


# ── What this module is allowed to read ───────────────────────────────────────
# Three series, and one of them is the target.  Naming them here rather than at
# each call site means the permitted set is a single list a reader can check
# against the catalog — and the check below runs at import, so a fourth series
# added carelessly fails immediately rather than at review time.
#
# `actual_load` and `actual_generation` are absent on purpose.  They are the
# hindsight twins: same units, same shape, freely downloadable today, and unknown
# when the schedule was committed.

SOURCES = ("day_ahead_price", "load_forecast", "wind_solar_forecast")

for _key in SOURCES:
    _item = entsoe.get(_key)                                # raises on a typo, not returns None
    if not (_item.known_before_gate_closure or _item is entsoe.TARGET):
        raise ImportError(                                  # import-time, so it cannot be ignored
            f"{_key!r} is not knowable before gate closure and cannot be a feature source. "
            f"Catalog says: {_item.why}"
        )


# ── The lags, and why 24 hours is the shortest one allowed ────────────────────
# Prices for day D are published just after the auction clears at midday on D-1.
# So at the moment the schedule is committed, the whole of D-1 is public and none
# of D is.  For the 23:00 delivery hour a 12-hour lag would reach back into day D
# itself, which is the target; only a lag of 24 hours or more is safe for *every*
# hour of the day, which is why one number governs all of them.
#
# The four chosen are the standard set for this problem: yesterday, the two days
# before it, and the same hour last week, which carries the weekly shape.
#
# The 24 below follows from `config.GATE_CLOSURE_LOCAL` being noon.  It is not
# derived from it in code: the arithmetic needs the latest delivery hour, the
# publication lag and a rounding rule, and would be harder to check than the
# sentence above.  If that deadline ever moves, this is the number to revisit —
# searching for GATE_CLOSURE_LOCAL finds both ends.

MIN_PRICE_LAG_HOURS = 24
PRICE_LAGS = (24, 48, 72, 168)

assert min(PRICE_LAGS) >= MIN_PRICE_LAG_HOURS, "a lag shorter than 24 h reaches into day D"

# The same rule for the day table, where it can be said directly: a price input
# comes from a whole earlier day.  For the 00:00 model, D-1 at 23:00 is one hour
# back, but it cleared in D-1's auction, around 13:00 on D-2.  Forecasts need no
# lag, as below: those for day D are public on D-1.

MIN_PRICE_LAG_DAYS = 1
PRICE_DAYS = (1, 2, 3, 7)                                   # LEAR's set: D-1, D-2, D-3, D-7
FORECAST_DAYS = (0, 1, 7)                                   # D itself, D-1, D-7

assert min(PRICE_DAYS) >= MIN_PRICE_LAG_DAYS, "a price input reaches into day D"


def _hourly_span(*indexes: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """A gapless hourly index on the 24-slot grid, covering everything passed in.

    Both `shift` calls below move by one row rather than by one hour, so they are
    only correct on an index with no holes.  Building that index explicitly makes
    the assumption true instead of hoping it is — a missing hour would otherwise
    shorten every lag past it, and the result still looks like a price.  On the
    grid, one row back is always the same Berlin hour, clock changes included.
    """
    lo = min(i.min() for i in indexes)
    hi = max(i.max() for i in indexes)
    return pd.date_range(lo, hi, freq=cfg.RESOLUTION)       # naive labels: Berlin wall clock


def price_features(price: pd.Series, index: pd.DatetimeIndex) -> pd.DataFrame:
    """Lagged prices and a summary of yesterday, evaluated on `index`.

    Two kinds of memory.  The lags carry the same hour on earlier days, which is
    what a daily shape looks like to a model.  The daily summary carries the level
    and the width of yesterday — a battery cares about the spread, and yesterday's
    spread is the cheapest available guess at today's.

    `index` is passed in rather than taken from `price` because it may reach past
    the last cleared auction.  At gate closure tomorrow has forecasts but no price,
    and tomorrow is precisely the row a schedule has to be built from.
    """
    span = _hourly_span(price.index, index)
    full = price.reindex(span)                              # NaN wherever the price is not known yet
    out = pd.DataFrame(index=span)

    for lag in PRICE_LAGS:
        out[f"price_lag_{lag}h"] = full.shift(lag)

    # Daily summaries are computed on market-local days, because the auction clears
    # a Berlin calendar day as one block and a battery's cycle lives inside one.
    # Grid labels are already Berlin wall clock, so the date is read straight off.
    day = span.normalize()
    daily = full.groupby(day).agg(["min", "max", "mean"])
    daily["last"] = full.groupby(day).last()                # the final hour of the day
    yesterday = daily.shift(1)                              # safe: `day` runs without gaps

    for name in ("min", "max", "mean", "last"):
        out[f"price_d1_{name}"] = yesterday[name].reindex(day).to_numpy()
    out["price_d1_spread"] = out["price_d1_max"] - out["price_d1_min"]   # what was there to earn

    return out.reindex(index)


# ── The autumn midnight the publishers leave out ──────────────────────────────
# The TSOs publish each forecast in day blocks starting at midnight winter time,
# but the autumn clock-change day starts an hour earlier, at midnight summer time.
# So 00:00 on that day is in neither block: blank for load, onshore wind and solar
# in 2023-25.  It is filled the way the grid fills spring's 02:00, from two
# neighbours that were both published on D-1, so nothing leaks.
#
# Narrow on purpose.  "Fill any single blank hour" fills the same three rows today,
# but would also fill holes of other causes that nobody has decided about.

def fill_autumn_midnight(df: pd.DataFrame) -> pd.DataFrame:
    """Fill a blank 00:00 on each autumn clock-change day from 23:00 and 01:00."""
    twice = df.index.tz_localize(cfg.TZ_MARKET, ambiguous="NaT",
                                 nonexistent="shift_forward").isna()   # the 02:00 that happens twice
    midnight = df.index.isin(df.index[twice].normalize())              # 00:00 on those days
    neighbours = (df.shift(1) + df.shift(-1)) / 2                      # the grid has no gaps
    out = df.copy()
    out.loc[midnight] = df.loc[midnight].fillna(neighbours.loc[midnight])   # blanks only
    return out


# ── The forecasts, used at their own timestamp ────────────────────────────────
# These need no lag, and that is the whole reason they are worth having: the TSOs
# publish them on the morning of D-1, so the value for the hour being predicted was
# already public when the decision was made.
#
# Worth being clear about why, because the usual framing gets it backwards.  The
# forecast is not a permitted substitute for the actual — it is the *better*
# variable.  Bids were placed against the published forecast, so that is what set
# the price; the actual was measured afterwards and never touched the auction.  Here
# the contract and the correct modelling choice happen to be the same thing.

def forecast_features() -> pd.DataFrame:
    """Demand and renewable output as forecast before gate closure, plus residual load."""
    load = fill_autumn_midnight(data.to_slots(data_load("load_forecast"))).iloc[:, 0]
    ws = fill_autumn_midnight(data.to_slots(data_load("wind_solar_forecast")))

    out = pd.DataFrame(index=load.index)
    out["load_forecast"] = load
    out["wind_onshore"] = ws["Wind Onshore"]
    out["wind_offshore"] = ws["Wind Offshore"]
    out["solar"] = ws["Solar"]

    # What has to be covered by something dispatchable once the weather has supplied
    # what it can.  The single strongest driver of the price, and derived here so
    # that no downstream file has to remember the sign.
    out["residual_load"] = out.load_forecast - out.wind_onshore - out.wind_offshore - out.solar

    return out


# ── Calendar ──────────────────────────────────────────────────────────────────
# Read off the market clock, not UTC.  Demand follows when people in Berlin get up
# and go to work, so an hour-of-day taken from UTC would be an hour out for half
# the year and would smear the morning peak across two values.  The grid's labels
# already are the market clock, so they are read directly.
#
# Public holidays: the nine nationwide ones only, from the `holidays` package,
# which also works out the Easter-linked dates.  Each is fixed by law years ahead,
# so known at gate closure.  The load forecast already falls to Sunday's level on
# them; the flag tells the models why, where a weekday column says "Monday".
# Regional holidays (Corpus Christi, Reformation Day) are left out by decision.

def is_holiday(index: pd.DatetimeIndex) -> np.ndarray:
    """True on Germany's nationwide public holidays, read on the market clock."""
    days = index.normalize()                                # grid labels: Berlin days
    known = holidays.Germany(years=range(days.year.min(), days.year.max() + 1))   # no state: nationwide
    return days.isin(pd.to_datetime(list(known)))


def calendar_features(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Hour, weekday and holiday on the delivery day, in market time."""
    return pd.DataFrame(
        {
            "hour": index.hour,
            "dayofweek": index.dayofweek,
            "is_weekend": index.dayofweek >= 5,             # demand drops; the price shape changes
            "is_holiday": is_holiday(index),
        },
        index=index,
    )


# ── Assembling the frame ──────────────────────────────────────────────────────
# Each series is put on the 24-slot grid where it is loaded, not inside `data_load`.
# The tests replace `data_load` with world-clock fixtures, so translating out here
# sends fake and real data down one path — and the leak test can delete the future
# from the original before anything is averaged or filled from it.
#
# A row exists wherever the pre-gate-closure inputs exist, and the target is joined
# on afterwards rather than being required.  That ordering is the point: at 12:00 on
# D-1 tomorrow has forecasts and no price, and tomorrow is the row a schedule has to
# be built from.  Demanding the target first would make the builder unusable for the
# one moment the whole project is about.
#
# Rows with a missing value are kept rather than dropped.  What to do about the 37
# absent load-forecast days is a modelling decision recorded as open item 9, and
# burying it inside the builder would answer it by accident.

TARGET = "price"


def data_load(key: str) -> pd.DataFrame:
    """Load one permitted series. Refuses anything not declared in `SOURCES`.

    The check at the top of this file guards the *declaration*; this guards the
    *use*.  Without it, reaching past the list is a one-word edit inside any
    function here and the declaration stays innocent — which is how a hindsight
    series gets in while `SOURCES` still reads correctly.
    """
    if key not in SOURCES:
        raise ValueError(
            f"features.py may not read {key!r}. Permitted: {list(SOURCES)}. "
            f"Adding one means adding it to SOURCES, where the catalog check will see it."
        )
    return data.load(key)


def build() -> pd.DataFrame:
    """The feature frame for the whole history. NaNs intact, target possibly absent."""
    price = data.to_slots(data_load("day_ahead_price")).iloc[:, 0].rename(TARGET)
    forecasts = forecast_features()                         # defines which hours get a row

    frame = pd.concat([price_features(price, forecasts.index), forecasts], axis=1)
    frame = pd.concat([frame, calendar_features(frame.index)], axis=1)
    frame.insert(0, TARGET, price.reindex(frame.index))     # NaN for a day not yet cleared

    return frame.sort_index()


def complete_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Rows a model can actually train on: no missing value anywhere.

    Separate from `build` on purpose.  The first 168 hours have no week-old price
    and never will; the 2018 load-forecast gaps might be filled from a second
    source one day.  Keeping the drop visible keeps that choice visible too.
    """
    return frame.dropna()


def feature_columns(frame: pd.DataFrame) -> list[str]:
    """Every column except the target — what a model is allowed to see."""
    return [c for c in frame.columns if c != TARGET]


# ── The day table, for LEAR ───────────────────────────────────────────────────
# The same numbers as `build()`, one row per delivery day instead of per hour: the
# 24 prices of D as answers, and whole earlier days as clues, so the 18:00 model
# sees every hour of yesterday, not only 18:00.  Built here, not inside the model,
# so this file still answers "was this public by 12:00 on D-1?" for every table.
# Folding needs exactly 24 hours a day, which is what the grid guarantees.

def fold(series: pd.Series) -> pd.DataFrame:
    """One row per day, one column per hour. The label is split, nothing computed."""
    days_hours = pd.MultiIndex.from_arrays([series.index.normalize(), series.index.hour])
    return series.set_axis(days_hours).unstack()


def unfold(table: pd.DataFrame) -> pd.Series:
    """Back to one value per grid hour: date of the row plus hour of the column."""
    s = table.stack()                                       # keeps blanks, one per cell
    days, hours = s.index.get_level_values(0), s.index.get_level_values(1)
    return s.set_axis(days + pd.to_timedelta(hours, unit="h"))


def day_table() -> pd.DataFrame:
    """One row per delivery day: 24 answers, 240 day-shaped clues, 7 weekdays and a holiday."""
    price = fold(data.to_slots(data_load("day_ahead_price")).iloc[:, 0])
    fc = forecast_features()                                # filled, and on the grid
    load = fold(fc.load_forecast)
    renewables = fold(fc.wind_onshore + fc.wind_offshore + fc.solar)   # the field's sum
    days = load.index                                       # a row wherever forecasts exist

    # Every series is stretched over one shared run of days before shifting.  At
    # gate closure the price stops at D-1 while the forecasts reach D, and without
    # this, day D would have no row in the price table to receive yesterday from.
    # `to_slots` already returns every day, blank ones included, so one row back
    # is always one day back.
    span = pd.date_range(min(price.index.min(), days.min()),
                         max(price.index.max(), days.max()), freq="D")
    price, load, renewables = (t.reindex(span) for t in (price, load, renewables))

    blocks = {"price_d0": price}                            # the answers
    for k in PRICE_DAYS:
        blocks[f"price_d{k}"] = price.shift(k)              # k whole days back
    for k in FORECAST_DAYS:
        blocks[f"load_d{k}"] = load.shift(k)
        blocks[f"renew_d{k}"] = renewables.shift(k)

    table = pd.concat(blocks, axis=1).reindex(days)
    table.columns = [f"{name}_h{hour:02d}" for name, hour in table.columns]   # "price_d1_h18"
    for i in range(7):                                      # one yes/no column per weekday
        table[f"weekday_{i}"] = (table.index.dayofweek == i).astype(float)
    table["holiday"] = is_holiday(table.index).astype(float)    # yes/no, like the weekdays
    return table


def day_answer_columns(table: pd.DataFrame) -> list[str]:
    """The 24 prices of day D — what LEAR forecasts."""
    return [c for c in table.columns if c.startswith("price_d0_")]


def day_feature_columns(table: pd.DataFrame) -> list[str]:
    """Every column except the answers — what LEAR is allowed to see."""
    answers = set(day_answer_columns(table))
    return [c for c in table.columns if c not in answers]
