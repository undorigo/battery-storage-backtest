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


# Free power late on day 1, 200 early on day 2, 180 otherwise.  Holding the free
# power over midnight would pay; a one-day plan cannot know that, so it buys nothing.
NIGHT = [180.0] * 22 + [0.0, 0.0]
MORNING = [180.0] * 7 + [200.0, 200.0] + [180.0] * 15
DEARER = [180.0] * 7 + [300.0, 300.0] + [180.0] * 15
FLAT = [180.0] * 24


def test_a_day_is_planned_without_seeing_tomorrow():
    # At 12:00 on D-1 nobody has a forecast for D+1.  Day 1's plan must come out the
    # same whatever day 2 holds, or a year of forecasts handed over at once would
    # plan each day on the forecast made a day later.
    plans = [BT.walk(berlin_days(NIGHT, after)).iloc[:24] for after in (MORNING, DEARER, FLAT)]
    for other in plans[1:]:
        pd.testing.assert_frame_equal(plans[0], other)
    assert plans[0].charge.sum() == pytest.approx(0.0, abs=1e-6)   # free power, nothing to sell into


def test_the_next_day_starts_where_the_last_one_ended():
    # Start full.  Day 1 sells 1 MWh at 100, leaving 2 - 1/0.9 = 0.89 stored; at 5 the
    # rest is not worth selling (5 < 8 of wear).  Day 2 sells what is left: 0.89 x 0.9.
    got = BT.walk(berlin_days([100.0] + [5.0] * 23, [100.0] * 24), start_mwh=2.0)
    assert got.level.iloc[23] == pytest.approx(2.0 - 1.0 / 0.9, abs=1e-6)
    assert got.discharge.iloc[24:].sum() == pytest.approx(0.8, abs=1e-6)


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


def test_nothing_beats_the_ceiling_on_a_day_that_starts_empty():
    # Plan on a noisy guess, settle at the truth: never more than planning on the truth.
    # One day, starting empty.  Starting a day with charge the ceiling lacks, it can.
    rng = np.random.default_rng(1)
    for _ in range(20):
        truth = berlin_days(list(rng.normal(80, 60, 24)))
        guess = truth + rng.normal(0, 40, len(truth))
        _, best = BT.ceiling(truth)
        other = BT.settle(BT.walk(guess), truth)
        assert other.sum() <= best.sum() + 1e-6


# ── The command, to its last line ─────────────────────────────────────────────

def test_the_ceiling_command_runs_on_2023_alone(monkeypatch, capsys):
    """Runs `just backtest ceiling` on a stand-in cache spanning both year ends.
    A dear morning on 1 January 2024 must not reach a 2023 run, nor 31 December 2022."""
    from scripts import backtest as SB
    from src import data

    rng = np.random.default_rng(2)
    edges = [berlin_days(*(list(rng.normal(80, 60, 24)) for _ in range(3)), start=start)
             for start in ("2022-12-31", "2023-12-30")]
    cache = pd.concat(edges)
    cache[BT.delivery_days(cache.index) == pd.Timestamp("2024-01-01", tz="Europe/Berlin")] = 5000.0
    monkeypatch.setattr(data, "load", lambda key: cache.to_frame("day_ahead_price"))

    assert SB.main(["ceiling"]) == 0
    assert "4 days, 96 hours" in capsys.readouterr().out
    years = BT.delivery_days(SB.actual_prices().index).year
    assert set(years) == {2023}
    assert SB.ceiling(SB.actual_prices())["best_day"] < 1000      # 5,000 EUR never seen
