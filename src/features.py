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

import pandas as pd

from src import config as cfg
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

MIN_PRICE_LAG_HOURS = 24
PRICE_LAGS = (24, 48, 72, 168)

assert min(PRICE_LAGS) >= MIN_PRICE_LAG_HOURS, "a lag shorter than 24 h reaches into day D"


def _hourly_span(*indexes: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """A gapless hourly index covering everything passed in.

    Both `shift` calls below move by one row rather than by one hour, so they are
    only correct on an index with no holes.  Building that index explicitly makes
    the assumption true instead of hoping it is — a missing hour would otherwise
    shorten every lag past it, and the result still looks like a price.
    """
    lo = min(i.min() for i in indexes)
    hi = max(i.max() for i in indexes)
    return pd.date_range(lo, hi, freq=cfg.RESOLUTION, tz=cfg.TZ_STORAGE)


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
    day = span.tz_convert(cfg.TZ_MARKET).normalize()
    daily = full.groupby(day).agg(["min", "max", "mean"])
    daily["last"] = full.groupby(day).last()                # the final hour of the day
    yesterday = daily.shift(1)                              # safe: `day` runs without gaps

    for name in ("min", "max", "mean", "last"):
        out[f"price_d1_{name}"] = yesterday[name].reindex(day).to_numpy()
    out["price_d1_spread"] = out["price_d1_max"] - out["price_d1_min"]   # what was there to earn

    return out.reindex(index)


# ── The forecasts, used at their own timestamp ────────────────────────────────
# These need no lag, and that is the whole reason they are worth having.  The TSOs
# publish their expectation for every hour of day D on the morning of D-1, before
# the auction closes, so the value for the hour being predicted was already public
# when the decision was made.  Their hindsight twins are the same numbers measured
# afterwards, and using those is the mistake this project exists to avoid.

def forecast_features() -> pd.DataFrame:
    """Demand and renewable output as forecast before gate closure, plus residual load."""
    load = data_load("load_forecast").iloc[:, 0]
    ws = data_load("wind_solar_forecast")

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
# the year and would smear the morning peak across two values.
#
# German public holidays are deliberately absent: they matter, but the moveable
# feasts need a dependency, and the naive benchmark already carries weekly shape.
# Revisit at stage 2 with a measured rMAE rather than an assumption.

def calendar_features(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Hour and weekday on the delivery day, in market time."""
    local = index.tz_convert(cfg.TZ_MARKET)
    return pd.DataFrame(
        {
            "hour": local.hour,
            "dayofweek": local.dayofweek,
            "is_weekend": local.dayofweek >= 5,             # demand drops; the price shape changes
        },
        index=index,
    )


# ── Assembling the frame ──────────────────────────────────────────────────────
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
    from src import data                                    # imported here to keep the seam thin
    return data.load(key)


def build() -> pd.DataFrame:
    """The feature frame for the whole history. NaNs intact, target possibly absent."""
    price = data_load("day_ahead_price").iloc[:, 0].rename(TARGET)
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
