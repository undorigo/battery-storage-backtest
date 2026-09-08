"""Single source of truth for the split, the market, the clock and the battery.

Owner of Integration Contract 2 (The Split) and Contract 5 (Time and Resolution).
Nothing here is derived at runtime from data; every value is a decision that was
made once and must not drift.  Changing anything in this file invalidates every
previously reported number, so the Transparency Protocol applies to every edit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
# Resolved from this file's own location rather than the working directory, so a
# script behaves identically whether it is run from the repository root, from a
# notebook two levels down, or by a scheduler with no cwd at all.

ROOT = Path(__file__).resolve().parents[1]      # repository root, one level above src/
DATA = ROOT / "data"
RAW = DATA / "raw"                              # as returned by the source, never edited
INTERIM = DATA / "interim"                      # tz-normalised, hourly, gaps counted
PROCESSED = DATA / "processed"                  # feature frames ready for a model
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"

# ── Time and resolution — Contract 5 ──────────────────────────────────────────
# Two timezones with two different jobs.  Series are stored and joined in UTC,
# where every day has exactly 24 hours and no timestamp is ambiguous.  Calendar
# features are derived in market-local time, because load and solar follow the
# local clock, and because a delivery day is a local-day concept: the auction
# clears 23, 24 or 25 hours depending on the date.

TZ_STORAGE = "UTC"                              # index of every stored series
TZ_MARKET = "Europe/Berlin"                     # delivery days, hour-of-day features
RESOLUTION = "h"                                # one hourly convention end to end

# Quarter-hourly day-ahead products went live on this date, mid-test-period.  The
# API returns 96 periods per day after it and 24 before, in one concatenated
# series, so normalisation to RESOLUTION happens once, at load time.
QUARTER_HOUR_GOLIVE = pd.Timestamp("2025-10-01", tz=TZ_MARKET)

# ── Market ────────────────────────────────────────────────────────────────────
# DE-LU only.  The zone below it in the table is the market that existed before
# October 2018, when Germany, Austria and Luxembourg shared one price.  It is a
# different market, not an older name for this one, and splicing the two joins
# two different price formation regimes.

BIDDING_ZONE = "DE_LU"                          # entsoe-py Area key
BIDDING_ZONE_EIC = "10Y1001A1001A82H"           # DE-LU, the zone this project models
_DE_AT_LU_EIC = "10Y1001A1001A63L"              # pre-Oct-2018 DE-AT-LU; never use

# The auction closes at 12:00 on D-1 and covers all delivery periods of day D.
# Every feature must have been knowable before this moment (Contract 1).
GATE_CLOSURE_LOCAL = "12:00"                    # on D-1, in TZ_MARKET
HISTORY_START = "2018-10-01"                    # first day DE-LU existed as a zone

# ── The split — Contract 2 ────────────────────────────────────────────────────
# The dates are written exactly as the contract states them: bare calendar days,
# readable at a glance.  The tz-aware boundaries below are derived from them, and
# they are what code touches.  A bare date string sliced against a UTC index is
# off by the UTC offset, and pandas .loc is inclusive at both ends, so the
# obvious form puts the boundary hour in two sets at once and nothing errors.

TRAIN_END = "2022-12-31"
VALID_END = "2023-12-31"
TEST_START = "2024-01-01"
TEST_END = "2025-12-31"


def _first_delivery_hour(day: str) -> pd.Timestamp:
    """First delivery hour of a market-local day, expressed in UTC."""
    return pd.Timestamp(day, tz=TZ_MARKET).tz_convert(TZ_STORAGE)


def _last_delivery_hour(day: str) -> pd.Timestamp:
    """Last delivery hour of a market-local day, expressed in UTC.

    Derived as "next local midnight minus one hour" rather than as a fixed 23:00,
    because a clock-change day has 23 or 25 hours and its final hour is not 23:00.
    """
    next_midnight = pd.Timestamp(day, tz=TZ_MARKET) + pd.DateOffset(days=1)  # calendar-aware, not 24h
    return (next_midnight - pd.Timedelta(hours=1)).tz_convert(TZ_STORAGE)


TRAIN_END_UTC = _last_delivery_hour(TRAIN_END)      # last hour that may train a model
VALID_END_UTC = _last_delivery_hour(VALID_END)
TEST_START_UTC = _first_delivery_hour(TEST_START)
TEST_END_UTC = _last_delivery_hour(TEST_END)


def split(
    df: pd.DataFrame | pd.Series,
) -> tuple[pd.DataFrame | pd.Series, pd.DataFrame | pd.Series, pd.DataFrame | pd.Series]:
    """Partition a UTC-indexed series into train, validate and test.

    The intervals are half-open so that no hour can appear in two sets.  Every
    training and evaluation script goes through here rather than slicing on its
    own, which is what keeps the boundary arithmetic in one place instead of
    scattered across the scripts that Contract 2 warns about.
    """
    if df.index.tz is None:                                     # a naive index cannot be placed
        raise ValueError("Index must be tz-aware; normalise at load time (Contract 5).")

    idx = df.index.tz_convert(TZ_STORAGE)                       # compare in one timezone only
    train = df.loc[idx <= TRAIN_END_UTC]
    valid = df.loc[(idx > TRAIN_END_UTC) & (idx <= VALID_END_UTC)]
    test = df.loc[(idx >= TEST_START_UTC) & (idx <= TEST_END_UTC)]
    return train, valid, test


# ── Battery — Contract 4 ──────────────────────────────────────────────────────
# A standard two-hour asset.  Frozen because these are the terms the capture rate
# is measured against: if they change mid-project, revenue figures from before
# the change stop being comparable to the ones after it.

@dataclass(frozen=True)
class Battery:
    power_mw: float = 1.0                       # maximum charge and discharge rate
    capacity_mwh: float = 2.0                   # usable energy, two hours at full power
    efficiency_charge: float = 0.90             # one-way; round trip is 0.81
    efficiency_discharge: float = 0.90
    soc_min: float = 0.0                        # state of charge as a fraction of capacity
    soc_max: float = 1.0

    # Degradation penalty per MWh cycled.  CLAUDE.md specifies that a penalty
    # exists but not its size, and an invented figure would set the trade
    # threshold and therefore the revenue.  Left at zero until stage 4 sets it
    # from a cited source; zero means "no penalty", not "penalty unknown".
    cycle_cost_eur_per_mwh: float = 0.0

    @property
    def round_trip_efficiency(self) -> float:
        return self.efficiency_charge * self.efficiency_discharge


BATTERY = Battery()

# Overlapping horizon — Contract 4.  Optimise two days, keep the first, carry the
# state of charge forward.  Optimising exactly 24 hours would empty the battery
# every midnight, because a finite horizon has no reason to hold charge past its
# end.  All three runs (perfect foresight, model, naive) must share these numbers
# or the capture rate measures the convention rather than the forecast.
HORIZON_OPTIMISE_HOURS = 48
HORIZON_IMPLEMENT_HOURS = 24
