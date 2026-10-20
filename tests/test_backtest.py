"""The battery's plan and its settlement, checked against cases worked out by hand.

The battery is the project's own: 1 MW, 2 MWh, 90 % each way, 8 EUR per MWh sold.
Every expected number below follows from those four figures on paper.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import backtest as BT


# ── One plan ──────────────────────────────────────────────────────────────────

def test_cheap_then_dear_charges_then_sells_what_survives_the_losses():
    # Buy 1 MWh at 10, 0.9 is stored, 0.81 reaches the grid at 100.
    got = BT.plan(np.array([10.0, 100.0]), start_mwh=0.0)
    assert got.charge == pytest.approx([1.0, 0.0], abs=1e-6)
    assert got.level == pytest.approx([0.9, 0.0], abs=1e-6)
    assert got.discharge == pytest.approx([0.0, 0.81], abs=1e-6)


def test_never_charges_and_discharges_in_the_same_hour():
    # Full battery, price -200.  Buying 1 and selling 0.81 at once keeps the level
    # at 2 MWh and nets 0.19 x 200 - 0.81 x 8 = 31.52 EUR for burning energy.
    # A real battery cannot; it can only sit still.
    got = BT.plan(np.array([-200.0]), start_mwh=2.0)
    assert got.charge * got.discharge == pytest.approx([0.0], abs=1e-9)
    assert got.charge == pytest.approx([0.0], abs=1e-6)


def test_wear_stops_a_trade_too_small_to_pay_for_it():
    # Buy at 50, sell 0.81 at 66: 53.46 - 50 = 3.46 EUR before wear, 6.48 of wear.
    got = BT.plan(np.array([50.0, 66.0]), start_mwh=0.0)
    assert got.charge.sum() == pytest.approx(0.0, abs=1e-6)


def test_stored_energy_stays_within_the_battery():
    # Six cheap hours could buy 6 MWh; only 2 fit, so 2 / 0.9 is bought.
    got = BT.plan(np.array([0.0] * 6 + [100.0] * 6), start_mwh=0.0)
    assert got.level.max() == pytest.approx(2.0, abs=1e-6)
    assert got.charge.sum() == pytest.approx(2.0 / 0.9, abs=1e-6)
    assert got.charge.max() <= 1.0 + 1e-9                         # 1 MW, one hour at a time


# ── Walking day by day ────────────────────────────────────────────────────────

def berlin_days(*days: list[float], start: str = "2023-01-10") -> pd.Series:
    """Prices given per Berlin delivery day, stored in UTC as `data.load` returns them."""
    hours = pd.date_range(start, periods=sum(map(len, days)), freq="h", tz="Europe/Berlin")
    return pd.Series(np.concatenate(days), index=hours.tz_convert("UTC"))


# Free power late on day 1, 200 early on day 2, 180 otherwise: worth holding over
# midnight, and not worth buying at 180, since only 0.81 x 200 = 162 comes back.
NIGHT = [180.0] * 22 + [0.0, 0.0]
MORNING = [180.0] * 7 + [200.0, 200.0] + [180.0] * 15
FLAT = [180.0] * 24


def test_charge_bought_late_is_held_over_midnight():
    got = BT.walk(berlin_days(NIGHT, MORNING))
    assert got.level.iloc[23] == pytest.approx(1.8, abs=1e-6)   # 2 MWh bought, 1.8 stored
    assert got.discharge.iloc[24:].sum() == pytest.approx(1.62, abs=1e-6)


def test_the_next_day_starts_where_the_kept_day_ended():
    # Day 1's two-day plan ends empty after selling on day 2.  Carrying that
    # end-of-window level instead of day 1's would leave day 2 nothing to sell.
    got = BT.walk(berlin_days(NIGHT, MORNING, FLAT))
    assert got.discharge.iloc[24:48].sum() == pytest.approx(1.62, abs=1e-6)



def test_each_day_is_replanned_with_the_day_after_in_view():
    # Day 1's plan sells on day 2's morning at 200.  Re-planned on day 2 with day 3
    # in view, it holds on for 300.  Keeping both days of day 1's plan would not.
    DEARER = [180.0] * 7 + [300.0, 300.0] + [180.0] * 15
    got = BT.walk(berlin_days(NIGHT, MORNING, DEARER))
    assert got.discharge.iloc[24:48].sum() == pytest.approx(0.0, abs=1e-6)
    # At 300 even 180 is worth buying (0.81 x 300 = 243), so day 2 tops up to 2 MWh.
    assert got.discharge.iloc[48:].sum() == pytest.approx(1.8, abs=1e-6)

def test_energy_adds_up_across_every_midnight():
    rng = np.random.default_rng(0)
    prices = berlin_days(*(list(rng.normal(80, 60, 24)) for _ in range(5)))
    got = BT.walk(prices, start_mwh=0.5)
    before = np.concatenate([[0.5], got.level.to_numpy()[:-1]])
    assert got.level.to_numpy() == pytest.approx(
        before + 0.9 * got.charge.to_numpy() - got.discharge.to_numpy() / 0.9, abs=1e-6)
    assert got.index.equals(prices.index)                         # every hour, once, in order


def test_a_day_is_a_berlin_day_with_23_hours_in_march():
    hours = pd.date_range("2023-03-25", "2023-03-28", freq="h", tz="Europe/Berlin",
                          inclusive="left").tz_convert("UTC")
    counts = pd.Series(1, index=hours).groupby(BT.delivery_days(hours)).size()
    assert list(counts) == [24, 23, 24]


def test_the_last_day_plans_alone():
    # Handed one day, the walk cannot see tomorrow's dear morning, so it does not buy.
    assert BT.walk(berlin_days(NIGHT)).charge.sum() == pytest.approx(0.0, abs=1e-6)


# ── Settlement and the ceiling ────────────────────────────────────────────────

def test_settlement_pays_the_real_price_minus_wear():
    # The plan from the first test, settled at 10 then 100: -10, then 81 - 6.48.
    prices = berlin_days([10.0, 100.0])
    schedule, earned = BT.ceiling(prices)
    assert earned.to_numpy() == pytest.approx([-10.0, 74.52], abs=1e-6)



def test_the_ceiling_plans_with_the_wear_it_is_charged():
    # 50 then 66: 3.46 EUR before wear, 6.48 of wear.  Planned without wear it
    # would trade and settle at -3.02; the ceiling sits still and earns nothing.
    _, earned = BT.ceiling(berlin_days([50.0, 66.0]))
    assert earned.sum() == pytest.approx(0.0, abs=1e-6)

def test_settlement_refuses_an_hour_with_no_price():
    prices = berlin_days([10.0, 100.0])
    schedule = BT.walk(prices)
    with pytest.raises(ValueError, match="no price"):
        BT.settle(schedule, prices.iloc[:1])


def test_nothing_beats_the_ceiling_within_one_window():
    # Plan on a noisy guess, settle at the truth: never more than planning on the truth.
    # One day, so one window.  Across windows this need not hold (see `ceiling`).
    rng = np.random.default_rng(1)
    for _ in range(20):
        truth = berlin_days(list(rng.normal(80, 60, 24)))
        guess = truth + rng.normal(0, 40, len(truth))
        _, best = BT.ceiling(truth)
        other = BT.settle(BT.walk(guess), truth)
        assert other.sum() <= best.sum() + 1e-6
