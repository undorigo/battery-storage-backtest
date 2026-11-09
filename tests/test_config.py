"""Contract 2 (The Split) and the constants Contract 5 depends on.

These tests exist because the failure they guard against is silent.  A split
boundary off by one hour leaks validation data into training, changes no metric
visibly, and raises nothing.  The bug was live in this repository before
`split()` existed, so these are regression tests, not hypotheticals.

Scope is deliberately narrow: the contracts, not general coverage.
"""

import pandas as pd
import pytest

from src import config as cfg
from src import data


# ── split() ───────────────────────────────────────────────────────────────────
# Contract 2 states the split as bare calendar dates, and a delivery day is a
# Berlin concept: the last hour of 2022 is 23:00 in Berlin, which is 22:00 UTC.
# The first three tests check the sets fit together; the next two check where
# the cut falls, which the first three cannot see.

@pytest.fixture
def hourly_frame():
    """A UTC-indexed frame spanning both split boundaries."""
    idx = pd.date_range("2022-12-28", "2024-01-04", freq="h", tz="UTC")
    return pd.DataFrame({"price": range(len(idx))}, index=idx)


def test_split_partitions_have_no_overlap(hourly_frame):
    train, valid, test = cfg.split(hourly_frame)
    assert len(train.index.intersection(valid.index)) == 0
    assert len(valid.index.intersection(test.index)) == 0
    assert len(train.index.intersection(test.index)) == 0


def test_split_leaves_no_gap_between_partitions(hourly_frame):
    train, valid, test = cfg.split(hourly_frame)
    assert valid.index.min() - train.index.max() == pd.Timedelta(hours=1)
    assert test.index.min() - valid.index.max() == pd.Timedelta(hours=1)


def test_split_assigns_every_row_exactly_once(hourly_frame):
    """Nothing silently dropped between the partitions."""
    train, valid, test = cfg.split(hourly_frame)
    assert len(train) + len(valid) + len(test) == len(hourly_frame)


def test_the_boundaries_fall_at_berlin_midnight(hourly_frame):
    """Position, not just contiguity: a cut at UTC midnight passes every test above.

    Berlin midnight on New Year is 23:00 UTC, so the last training hour is 22:00 UTC.
    """
    train, valid, test = cfg.split(hourly_frame)
    assert train.index.max() == pd.Timestamp("2022-12-31 22:00", tz="UTC")
    assert valid.index.min() == pd.Timestamp("2022-12-31 23:00", tz="UTC")
    assert test.index.min() == pd.Timestamp("2023-12-31 23:00", tz="UTC")


def test_grid_rows_split_on_their_own_date(hourly_frame):
    """The models' copy: naive labels are already Berlin wall clock."""
    grid = data.to_slots(hourly_frame)
    train, valid, test = cfg.split(grid)
    assert train.index.max() == pd.Timestamp("2022-12-31 23:00")
    assert valid.index.min() == pd.Timestamp("2023-01-01 00:00")
    assert test.index.min() == pd.Timestamp("2024-01-01 00:00")
    assert len(train) + len(valid) + len(test) == len(grid)


def test_split_is_correct_for_a_non_utc_input(hourly_frame):
    """A Berlin-indexed frame must split identically to a UTC one."""
    berlin = hourly_frame.tz_convert(cfg.TZ_MARKET)
    a = cfg.split(hourly_frame)
    b = cfg.split(berlin)
    for utc_part, berlin_part in zip(a, b):
        assert len(utc_part) == len(berlin_part)


# ── 2026 sits outside the split ───────────────────────────────────────────────
# The replay's days must start the day after the test years end, and no 2026 day
# may land in any of the three blocks, or a held-back score would quietly grow.

def test_live_start_is_the_day_after_the_test_years():
    assert pd.Timestamp(cfg.LIVE_START) - pd.Timestamp(cfg.TEST_END) == pd.Timedelta(days=1)
    assert pd.Timestamp(cfg.REPLAY_END) > pd.Timestamp(cfg.LIVE_START)


def test_no_2026_day_lands_in_any_block():
    idx = pd.date_range("2025-12-30", "2026-01-03", freq="h", tz="UTC")
    frame = pd.DataFrame({"price": range(len(idx))}, index=idx)
    train, valid, test = cfg.split(frame)
    assert len(train) == len(valid) == 0
    last = test.index.max().tz_convert(cfg.TZ_MARKET)            # the last held-back hour
    assert last == pd.Timestamp(cfg.TEST_END + " 23:00", tz=cfg.TZ_MARKET)


# ── Market and battery constants ──────────────────────────────────────────────
# The two EIC codes differ by a few characters and name different markets.
# Confusing them splices the DE-LU zone onto the pre-October-2018 DE-AT-LU zone.

def test_bidding_zone_is_de_lu_not_de_at_lu():
    assert cfg.BIDDING_ZONE_EIC == "10Y1001A1001A82H"
    assert cfg.BIDDING_ZONE_EIC != cfg.DE_AT_LU_EIC
    assert cfg.DE_AT_LU_EIC == "10Y1001A1001A63L"     # the hazard, named so it stays named


def test_history_starts_when_the_de_lu_zone_did():
    assert cfg.HISTORY_START == "2018-10-01"


def test_battery_round_trip_efficiency():
    assert cfg.BATTERY.round_trip_efficiency == pytest.approx(0.81)
