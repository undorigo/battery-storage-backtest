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


# ── The derived boundaries ────────────────────────────────────────────────────
# Contract 2 states the split as bare calendar dates.  A delivery day is a
# market-local concept, so the last hour of 2022-12-31 is 23:00 in Berlin, which
# is 22:00 UTC — not 00:00, and not 23:00 UTC.  Both wrong answers look
# plausible in a diff, which is why they are pinned here.

def test_train_end_is_last_berlin_delivery_hour():
    assert cfg.TRAIN_END_UTC == pd.Timestamp("2022-12-31 22:00", tz="UTC")
    local = cfg.TRAIN_END_UTC.tz_convert(cfg.TZ_MARKET)      # what the market saw
    assert (local.hour, local.day, local.month) == (23, 31, 12)


def test_test_start_is_first_berlin_delivery_hour():
    assert cfg.TEST_START_UTC == pd.Timestamp("2023-12-31 23:00", tz="UTC")
    assert cfg.TEST_START_UTC.tz_convert(cfg.TZ_MARKET).hour == 0   # midnight local


def test_validate_and_test_are_contiguous():
    """No missing hour between the sets, and no shared one."""
    assert cfg.TEST_START_UTC - cfg.VALID_END_UTC == pd.Timedelta(hours=1)


# ── Clock changes ─────────────────────────────────────────────────────────────
# A Berlin day is not always 24 hours.  Deriving the last delivery hour as a
# hard-coded 23:00 would be wrong on both transition days, so it is derived as
# "next local midnight minus one hour" instead.  These are the two days a year
# where that difference shows.

@pytest.mark.parametrize(
    "day, expected_hours",
    [
        ("2023-03-26", 23),      # spring forward, the 25-hour day's opposite
        ("2023-10-29", 25),      # autumn back, 02:00 local happens twice
        ("2023-06-15", 24),      # an ordinary day, as control
    ],
)
def test_delivery_day_length_handles_clock_changes(day, expected_hours):
    first = cfg._first_delivery_hour(day)
    last = cfg._last_delivery_hour(day)
    hours = int((last - first) / pd.Timedelta(hours=1)) + 1     # inclusive count
    assert hours == expected_hours
    assert last.tz_convert(cfg.TZ_MARKET).hour == 23            # always 23:00 local


# ── split() ───────────────────────────────────────────────────────────────────
# The helper exists because a correct constant used with pandas .loc is still
# wrong: .loc is inclusive at both ends, so the boundary hour lands in two sets.

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


def test_split_rejects_a_naive_index(hourly_frame):
    """A naive timestamp cannot be placed on the clock, so it must not be guessed."""
    with pytest.raises(ValueError, match="tz-aware"):
        cfg.split(hourly_frame.tz_localize(None))


def test_split_is_correct_for_a_non_utc_input(hourly_frame):
    """A Berlin-indexed frame must split identically to a UTC one."""
    berlin = hourly_frame.tz_convert(cfg.TZ_MARKET)
    a = cfg.split(hourly_frame)
    b = cfg.split(berlin)
    for utc_part, berlin_part in zip(a, b):
        assert len(utc_part) == len(berlin_part)


# ── Market and battery constants ──────────────────────────────────────────────
# The two EIC codes differ by a few characters and name different markets.
# Confusing them splices the DE-LU zone onto the pre-October-2018 DE-AT-LU zone.

def test_bidding_zone_is_de_lu_not_de_at_lu():
    assert cfg.BIDDING_ZONE_EIC == "10Y1001A1001A82H"
    assert cfg.BIDDING_ZONE_EIC != cfg._DE_AT_LU_EIC


def test_history_starts_when_the_de_lu_zone_did():
    assert cfg.HISTORY_START == "2018-10-01"


def test_battery_round_trip_efficiency():
    assert cfg.BATTERY.round_trip_efficiency == pytest.approx(0.81)


def test_horizon_implements_less_than_it_optimises():
    """Contract 4: optimise 48 h, implement 24 h, carry state of charge forward.

    Optimising exactly the implemented window would empty the battery every
    midnight, because a finite horizon has no reason to hold charge past its end.
    """
    assert cfg.HORIZON_IMPLEMENT_HOURS < cfg.HORIZON_OPTIMISE_HOURS
