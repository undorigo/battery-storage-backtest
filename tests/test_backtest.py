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
    # Empty battery, price -200.  Buying 1 and selling 0.81 at once keeps the level
    # at 0, so the day still ends empty, and nets 0.19 x 200 - 0.81 x 8 = 31.52 EUR
    # for burning energy.  A real battery cannot; it can only sit still.
    got = BT.plan(np.array([-200.0]), start_mwh=0.0)
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


def test_every_day_ends_empty_even_when_holding_on_would_pay():
    # Paid 50 to take power at 22:00 and 23:00.  Free to end full, the plan would buy
    # both hours and keep 1.8 MWh.  Held to empty, it buys 1 at 22:00 and sells 0.81
    # at 23:00: +50 - 0.81 x 50 - 0.81 x 8 = +3.02 EUR.  Day 2 starts with nothing.
    got = BT.walk(berlin_days([180.0] * 22 + [-50.0, -50.0], MORNING))
    day_ends = got.level.iloc[[23, 47]]
    assert day_ends.to_numpy() == pytest.approx([0.0, 0.0], abs=1e-6)
    assert got.charge.iloc[22] == pytest.approx(1.0, abs=1e-6)
    assert got.discharge.iloc[23] == pytest.approx(0.81, abs=1e-6)


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

def test_a_fixed_schedule_is_planned_on_the_forecast_and_paid_the_real_price():
    # Forecast 10 then 100: buy 1 MWh, sell 0.81.  The day comes out the other way
    # round, 100 then 10: -100 + 0.81 x 10 - 0.81 x 8 of wear = -98.38.
    _, earned = BT.fixed(berlin_days([10.0, 100.0]), berlin_days([100.0, 10.0]))
    assert earned.sum() == pytest.approx(-98.38, abs=1e-6)


def test_settlement_refuses_an_hour_with_no_price():
    prices = berlin_days([10.0, 100.0])
    schedule = BT.walk(prices)
    with pytest.raises(ValueError, match="no price"):
        BT.settle(schedule, prices.iloc[:1])


def test_nothing_beats_the_ceiling_on_any_day():
    # 24/25 December in miniature.  The forecast thinks power is paid for at 22:00 and
    # 23:00 on day 1; really it costs 50, and day 2 opens at 200.  Free to end full, the
    # forecast plan would buy 2 MWh, sell 1 at 200 on day 2 and beat the ceiling, which
    # starts day 2 empty.  Held to empty, it buys 1 and sells 0.81 the same evening:
    # -50 + 0.81 x 50 - 0.81 x 8 = -15.98 on day 1, nothing on day 2.
    day_2 = [200.0] + [50.0] * 23
    truth = berlin_days([50.0] * 24, day_2)
    guess = berlin_days([50.0] * 22 + [-60.0, -60.0], day_2)
    _, best = BT.ceiling(truth)
    other = BT.settle(BT.walk(guess), truth)
    by_day = lambda earned: earned.groupby(BT.delivery_days(earned.index)).sum()
    assert (by_day(other) <= by_day(best) + 1e-6).all()
    assert by_day(other).to_numpy() == pytest.approx([-15.98, 0.0], abs=1e-6)


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


def test_the_fixed_command_plans_on_the_stored_forecast_and_pays_real_prices(monkeypatch, capsys):
    """Runs `just backtest fixed` on a stand-in cache and a stand-in stored run.
    A forecast equal to the real prices must score exactly 100 %; one that gets
    every price backwards must score less; and 1 January 2024 is never read."""
    from scripts import backtest as SB
    from src import data, tracking as TR

    rng = np.random.default_rng(3)
    edges = [berlin_days(*(list(rng.normal(80, 60, 24)) for _ in range(3)), start=start)
             for start in ("2022-12-31", "2023-12-30")]
    cache = pd.concat(edges)
    cache[BT.delivery_days(cache.index) == pd.Timestamp("2024-01-01", tz="Europe/Berlin")] = 5000.0
    monkeypatch.setattr(data, "load", lambda key: cache.to_frame("day_ahead_price"))
    slots = data.to_slots(SB.actual_prices().to_frame("actual"))["actual"]
    table = pd.DataFrame({"actual": slots + 50.0,                     # wrong on purpose: never paid
                          "lear": slots, "naive_field": 160.0 - slots})   # perfect, and backwards
    monkeypatch.setattr(TR, "latest", lambda **where: "run" if where == SB.LEAR_RUN else None)
    monkeypatch.setattr(TR, "read", lambda run: ({"commit": "abc1234"}, table))

    assert SB.main(["fixed"]) == 0
    out = capsys.readouterr().out
    assert "run at abc1234" in out
    _, got = SB.capture(SB.actual_prices())
    assert got["LEAR"]["earned"] == pytest.approx(got["ceiling"]["earned"], abs=1e-6)
    assert got["naive (field)"]["earned"] < got["ceiling"]["earned"]
    assert got["ceiling"]["earned"] < 1000 * 4                    # 5,000 EUR never seen


def test_the_fixed_command_names_the_run_it_needs(monkeypatch):
    from scripts import backtest as SB
    from src import tracking as TR

    monkeypatch.setattr(TR, "latest", lambda **where: None)
    with pytest.raises(LookupError, match="just train daily"):
        SB.forecasts(pd.DatetimeIndex([], tz="UTC"))
