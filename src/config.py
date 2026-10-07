"""Single source of truth for the split, the market, the clock and the battery.

Owner of Integration Contract 2 (The Split), and of the constants behind Contract 5
(Time and Resolution) — src/data.py is where those constants are applied, the same
way the catalog declares Contract 1 and features.py enforces it.

Nothing here is derived at runtime from data; every value is a decision that was
made once and must not drift.  Changing anything in this file invalidates every
previously reported number, so the Transparency Protocol applies to every edit.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from pathlib import Path

import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
# Resolved from this file's own location rather than the working directory, so a
# script behaves identically whether it is run from the repository root, from a
# notebook two levels down, or by a scheduler with no cwd at all.

ROOT = Path(__file__).resolve().parents[1]      # repository root, one level above src/
DATA = ROOT / "data"
RAW = DATA / "raw"                              # as returned by the source, never edited
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
SCORES = REPORTS / "scores.csv"       # every scored run, appended, stamped with its commit
MLFLOW = REPORTS / "mlflow"          # local only: MLflow stores full machine paths inside
MLFLOW_DB = MLFLOW / "mlflow.db"      # MLflow's run index
MLRUNS = MLFLOW / "mlruns"            # MLflow's files per run, e.g. the hourly forecasts

# There is deliberately no directory for feature frames.  One was reserved on day
# one and never used: `features.py` rebuilds all 63,575 rows in under a second, so
# a cache would buy a staleness problem and nothing else.  Raw data is cached
# because re-fetching it is slow, rate-limited and — after a revision — impossible.

# ── Time and resolution — Contract 5 ──────────────────────────────────────────
# Two timezones with two different jobs.  Series are stored in UTC, where no
# timestamp is ambiguous, and the cache stays that way.  The models work on Berlin
# delivery days, because load and solar follow the local clock and the auction
# clears 23, 24 or 25 hours depending on the date: `data.to_slots()` puts every
# day onto 24 slots, and series are joined there.  Settlement goes back to real hours.

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

# Public rather than private, despite never being used: a named hazard is easier
# to check against than an absent one.  The two codes differ by a few characters
# and name different markets, so the wrong one produces a spliced series rather
# than an error.
DE_AT_LU_EIC = "10Y1001A1001A63L"               # pre-Oct-2018 DE-AT-LU; never use

# The auction closes at 12:00 on D-1 and covers all delivery periods of day D.
# Every feature must have been knowable before this moment (Contract 1).
#
# No code reads this, and the original reason given here — that features.py would
# compare lag arithmetic against it — turned out to be wrong.  The deadline is
# enforced structurally instead: every price column is offset a fixed number of
# rows backwards, chosen so the latest delivery hour cannot reach it.  That needs
# no clock, so there is nothing to compare.  Kept as the market fact that explains
# why MIN_PRICE_LAG_HOURS is 24 and not 12.
GATE_CLOSURE_LOCAL = time(12, 0)                # on D-1, in TZ_MARKET
HISTORY_START = "2018-10-01"                    # first day DE-LU existed as a zone

# ── The split — Contract 2 ────────────────────────────────────────────────────
# The dates are written exactly as the contract states them: bare calendar days,
# readable at a glance, and `split()` compares against them directly.  A split is
# a question about delivery days, so every row is first given the Berlin date it
# delivers on.  Comparing a bare date against UTC timestamps instead puts the
# boundary one or two hours away from Berlin midnight, and nothing errors.

TRAIN_END = "2022-12-31"
VALID_END = "2023-12-31"
TEST_START = "2024-01-01"
TEST_END = "2025-12-31"

# Why these years, recorded 30 September 2026 — three weeks after the dates were set,
# because nobody had asked and the answer existed only in someone's head.
#
# The record cannot begin before October 2018: the DE-LU bidding zone did not exist, and
# splicing across that boundary joins two different markets.  From there the three blocks
# run in calendar order and never shuffle, because shuffling a time series lets a model
# learn from days that had not happened yet.  The most recent years are held back, since
# they are the closest thing available to what production would face; training takes the
# largest share because that is where data is worth most.
#
# The weakness worth knowing, stated rather than discovered later.  Training ends inside
# the 2022 gas crisis, validation is the recovery, and the held-back years are calmer
# still — so each block is unlike the one before it.  That is honest about the market but
# it makes validation an unusually harsh and unusually *different* exam.  Stage 1 saw the
# consequence directly: a model picked on validation lost its ranking on the held-back
# years.  Changing any boundary invalidates every number already published.


def split(
    df: pd.DataFrame | pd.Series,
) -> tuple[pd.DataFrame | pd.Series, pd.DataFrame | pd.Series, pd.DataFrame | pd.Series]:
    """Partition rows into train, validate and test by the Berlin day they deliver on.

    Takes both clocks the project uses: real hours in UTC (what settlement will
    split) and the 24-slot grid, whose naive labels are already Berlin wall clock
    (what the models split).  Every script goes through here rather than slicing
    on its own, so the boundaries live in one place, as Contract 2 requires.
    """
    idx = df.index
    if idx.tz is not None:                                      # real hours: read them on the Berlin clock
        idx = idx.tz_convert(TZ_MARKET).tz_localize(None)
    day = idx.normalize()                                       # the delivery day of each row

    train = df.loc[day <= pd.Timestamp(TRAIN_END)]
    valid = df.loc[(day > pd.Timestamp(TRAIN_END)) & (day <= pd.Timestamp(VALID_END))]
    test = df.loc[(day >= pd.Timestamp(TEST_START)) & (day <= pd.Timestamp(TEST_END))]
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

    # Degradation penalty, per MWh *discharged* — the convention matters, since
    # counting charge and discharge together would halve it.  Derived as cell
    # replacement cost over lifetime throughput: 70 EUR/kWh of LFP cells across
    # 8000 equivalent full cycles is ~8.75 EUR/MWh, and Montel's published
    # framework for a 50 MW two-hour GB battery uses GBP 7/MWh (~8 EUR/MWh).
    # It sets the spread below which cycling is not worth the wear, so stage 4
    # reports a sensitivity at 4 / 8 / 16 rather than resting on this figure.
    cycle_cost_eur_per_mwh: float = 8.0

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
