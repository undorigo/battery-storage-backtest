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


# ── Rounds and loops ──────────────────────────────────────────────────────────

def by_hand(charge: list[float], discharge: list[float]) -> pd.DataFrame:
    """A schedule written out hour by hour, its level following from 90 % each way."""
    c, d = np.array(charge), np.array(discharge)
    level = np.cumsum(0.9 * c - d / 0.9)
    return pd.DataFrame({"charge": c, "discharge": d, "level": level},
                        index=berlin_days([0.0] * len(c)).index)


# Idle, then round 0: buy 1 at 10 and 0.5 at 30, sell 1 at 120 and the last 0.215 at 100.
# Round 1: buy 1 at 10, sell 0.81 at 100.  Empty after hour 4 and after hour 6.
TWO_ROUNDS = by_hand([0, 1, 0.5, 0, 0, 1, 0], [0, 0, 0, 1, 0.215, 0, 0.81])
TWO_PRICES = berlin_days([50.0, 10.0, 30.0, 120.0, 100.0, 10.0, 100.0])


def test_a_day_is_cut_into_rounds_where_the_battery_is_empty_again():
    assert BT.rounds(TWO_ROUNDS).tolist() == [-1, 0, 0, 0, 0, 1, 1]
    # Buy, sell half, buy again, sell the rest: never empty in between, so one round.
    # Cut at the switch from selling to buying, the second half could fill alone and
    # sell energy the first half never bought.
    shared = by_hand([1, 0, 1, 0], [0, 0.405, 0, 1.215])
    assert BT.rounds(shared).tolist() == [0, 0, 0, 0]


def test_strict_needs_each_block_and_pair_needs_the_two_together():
    # Round 0, buy limit 18: the buy block paid 16.67 a MWh weighted by volume
    # (1 at 10, 0.5 at 30), so its surplus is 1 x 8 - 0.5 x 12 = +2 and it fills.  Its
    # plain average, 20, or its dearest hour, 30, would both say no.  Sell limit 113
    # the same way: 116.46 weighted (1 at 120, 0.215 at 100), surplus 7 - 2.795 = +4.2.
    # Round 1, buy limit 5 at a real 10: -5, made up for by the sell side.
    limits = pd.DataFrame({"buy": [18.0, 5.0], "sell": [113.0, -1e6]})
    traded, earned = BT.bid(TWO_ROUNDS, TWO_PRICES, limits, rule="strict")
    assert earned.to_numpy() == pytest.approx([0, -10, -15, 112, 19.78, 0, 0], abs=1e-6)
    assert traded.iloc[5:].to_numpy() == pytest.approx(np.zeros((2, 3)))   # round 1 never happened
    _, earned = BT.bid(TWO_ROUNDS, TWO_PRICES, limits, rule="pair")
    assert earned.sum() == pytest.approx(106.78 - 10 + 74.52, abs=1e-6)


def test_open_limits_fill_every_round_under_either_rule():
    # Limits nobody could miss: the bids must earn exactly what the fixed schedule does.
    rng = np.random.default_rng(2)
    prices = berlin_days(*(list(rng.normal(80, 60, 24)) for _ in range(5)))
    schedule = BT.walk(prices + rng.normal(0, 30, len(prices)))
    n = BT.rounds(schedule).max() + 1
    wide = pd.DataFrame({"buy": [1e6] * n, "sell": [-1e6] * n})
    for rule in BT.RULES:
        _, earned = BT.bid(schedule, prices, wide, rule)
        pd.testing.assert_series_equal(earned, BT.settle(schedule, prices))


def test_a_round_without_limits_is_refused():
    # A missing limit compares as "no" under both rules, so the round would vanish quietly.
    with pytest.raises(ValueError, match="no limits"):
        BT.bid(TWO_ROUNDS, TWO_PRICES, pd.DataFrame({"buy": [18.0], "sell": [-1e6]}))


# ── Limits from a range ───────────────────────────────────────────────────────

def test_limits_average_by_volume_then_meet_at_break_even():
    # Round 0 buys 1 MWh where the range says 20 and 0.5 where it says 26: 22 by volume
    # (23 plain).  It sells 1 at 110 and 0.215 at 100: 108.23 by volume (105 plain).
    # At those limits it would earn 1.215 x 108.23 - 1.5 x 22 - 8 x 1.215 = 88.78 EUR,
    # shared out over 2.715 MWh: both limits move 32.70 towards each other.
    # Round 1: buy 1 at 20, sell 0.81 at 90, earns 46.42 at them; 1.81 MWh, 25.65 each.
    buy_at = berlin_days([0.0, 20.0, 26.0, 0.0, 0.0, 20.0, 0.0])
    sell_at = berlin_days([0.0, 0.0, 0.0, 110.0, 100.0, 0.0, 90.0])
    got = BT.limits(TWO_ROUNDS, buy_at, sell_at)
    assert got.buy.to_numpy() == pytest.approx([22 + 32.6998, 20 + 25.6464], abs=1e-3)
    assert got.sell.to_numpy() == pytest.approx([108.2305 - 32.6998, 90 - 25.6464], abs=1e-3)


def random_bids(seed: int):
    """Five random days: a plan on a noisy forecast, a range around it, and the real prices."""
    rng = np.random.default_rng(seed)
    prices = berlin_days(*(list(rng.normal(80, 60, 24)) for _ in range(5)))
    forecast = prices + rng.normal(0, 30, len(prices))
    width = rng.uniform(5, 80, len(prices))                       # often wider than the gap traded
    schedule = BT.walk(forecast)
    return schedule, prices, BT.limits(schedule, forecast + width, forecast - width)


def test_the_limits_promise_exactly_nothing():
    for seed in range(5):
        schedule, _, got = random_bids(seed)
        label = BT.rounds(schedule)
        held = label[label >= 0]
        bought = schedule.charge[held.index].groupby(held).sum()
        sold = schedule.discharge[held.index].groupby(held).sum()
        promised = sold * got.sell - bought * got.buy - 8.0 * sold
        assert promised.to_numpy() == pytest.approx(0, abs=1e-9)


def test_no_filled_round_loses_under_either_rule():
    # The guard: limits that promise 0 mean a round that goes through earned at least 0.
    # Checked to bite: the wide ranges here would promise a loss on many rounds unmoved.
    filled = failed = 0
    for seed in range(5):
        schedule, prices, got = random_bids(seed)
        for rule in BT.RULES:
            traded, earned = BT.bid(schedule, prices, got, rule)
            label = BT.rounds(schedule)
            per_round = earned.groupby(label).sum().drop(-1, errors="ignore")
            kept = set(label[(traded.charge + traded.discharge) > BT.TRADING])
            assert (per_round[list(kept)] >= -1e-9).all()
            filled += len(kept)
            failed += label.max() + 1 - len(kept)
    assert filled > 0 and failed > 0                              # neither rule passed everything


def test_a_traded_hour_without_a_range_price_is_refused():
    # A missing price would drop out of the volume average and bend the limit quietly.
    buy_at = berlin_days([0.0, 20.0, 26.0, 0.0, 0.0, 20.0, 0.0]).iloc[:-1]
    with pytest.raises(ValueError, match="buy_at has no price for 1 traded hours"):
        BT.limits(TWO_ROUNDS, buy_at, berlin_days([0.0] * 7))


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


def test_the_fixed_command_plans_on_the_stored_forecasts_and_pays_real_prices(monkeypatch, capsys):
    """Runs `just backtest fixed` on a stand-in cache and stand-in stored runs.
    LEAR and the tree miss the shape one way, the straight line twice as far the
    other, so only their average is exactly right and must score 100 %; a backwards
    naive forecast must score less; and 1 January 2024 is never read."""
    from scripts import backtest as SB
    from src import data, tracking as TR

    rng = np.random.default_rng(3)
    edges = [berlin_days(*(list(rng.normal(80, 60, 24)) for _ in range(3)), start=start)
             for start in ("2022-12-31", "2023-12-30")]
    cache = pd.concat(edges)
    cache[BT.delivery_days(cache.index) == pd.Timestamp("2024-01-01", tz="Europe/Berlin")] = 5000.0
    monkeypatch.setattr(data, "load", lambda key: cache.to_frame("day_ahead_price"))
    slots = data.to_slots(SB.actual_prices().to_frame("actual"))["actual"]
    miss = pd.Series(40 * np.sin(np.arange(len(slots)) * np.pi / 6), index=slots.index)
    table = pd.DataFrame({"actual": slots + 50.0,                     # wrong on purpose: never paid
                          "lear": slots + miss, "gbm": slots + miss, "linear": slots - 2 * miss,
                          "naive_field": 160.0 - slots})               # backwards
    monkeypatch.setattr(TR, "latest", lambda **where: where["model"]
                        if where == {"model": where["model"], **SB.DAILY} else None)
    monkeypatch.setattr(TR, "read", lambda run: ({"commit": "abc1234"}, table))

    assert SB.main(["fixed"]) == 0
    out = capsys.readouterr().out
    assert "runs at abc1234" in out
    lead = out.split("LEAR against naive (field): ")[1].split(" p ")[1].split()[0]
    assert float(lead) < 0.05                                     # a shape miss beats backwards
    average = out.split("average against LEAR: ")[1].split("\n")[0]
    assert average.startswith("ahead on 4 days, behind on 0,")      # right every day, LEAR never
    _, got = SB.capture(SB.actual_prices())
    assert got["average"]["earned"] == pytest.approx(got["ceiling"]["earned"], abs=1e-6)
    for name in ("LEAR", "tree", "straight line", "naive (field)"):
        assert got[name]["earned"] < got["ceiling"]["earned"] - 1
    assert got["ceiling"]["earned"] < 1000 * 4                    # 5,000 EUR never seen


def test_the_fixed_command_names_the_run_it_needs(monkeypatch):
    from scripts import backtest as SB
    from src import tracking as TR

    monkeypatch.setattr(TR, "latest", lambda **where: None)
    with pytest.raises(LookupError, match="just train daily"):
        SB.forecasts(pd.DatetimeIndex([], tz="UTC"))


def stand_in_run(monkeypatch, range_lear_shift: float = 0.0, backwards: bool = False):
    """A stand-in 2023 cache, LEAR run and QRA range, LEAR's forecast exactly right
    (or every price backwards).  The range's p75 and p25 sit on LEAR's forecast."""
    from scripts import backtest as SB
    from src import data, tracking as TR

    rng = np.random.default_rng(4)
    edges = [berlin_days(*(list(rng.normal(80, 60, 24)) for _ in range(3)), start=start)
             for start in ("2022-12-31", "2023-12-30")]
    cache = pd.concat(edges)
    cache[BT.delivery_days(cache.index) == pd.Timestamp("2024-01-01", tz="Europe/Berlin")] = 5000.0
    monkeypatch.setattr(data, "load", lambda key: cache.to_frame("day_ahead_price"))
    slots = data.to_slots(SB.actual_prices().to_frame("actual"))["actual"]
    lear = 160.0 - slots if backwards else slots
    run = pd.DataFrame({"actual": slots, "lear": lear, "gbm": slots, "linear": slots,
                        "naive_field": 160.0 - slots})
    band = pd.DataFrame({"lear": lear + range_lear_shift, 75: lear, 25: lear})
    found = {"lear": "run", "gbm": "run", "linear": "run", "qra": "range"}
    monkeypatch.setattr(TR, "latest", lambda **where: found[where["model"]])
    monkeypatch.setattr(TR, "read", lambda run_id: ({"commit": "abc1234"}, run))
    monkeypatch.setattr(TR, "read_range", lambda run_id: ({"commit": "def5678"}, band))
    return SB


def test_the_bids_command_on_a_perfect_forecast_fills_every_round(monkeypatch, capsys):
    # Right prices and a range of no width: each round's limits sit on its real averages,
    # moved apart by its profit, so both blocks clear under either rule: the ceiling.
    SB = stand_in_run(monkeypatch)
    assert SB.main(["bids"]) == 0
    assert "runs at abc1234" in capsys.readouterr().out
    _, range_commit, got = SB.bids(SB.actual_prices())
    assert range_commit == "def5678"
    for rule in BT.RULES:
        assert got[rule]["filled"] == got[rule]["rounds"] > 0
        assert got[rule]["earned"] == pytest.approx(got["ceiling"]["earned"], abs=1e-6)
    assert got["ceiling"]["earned"] < 1000 * 4                    # 5,000 EUR never seen


def test_the_bids_command_refuses_a_range_built_on_another_forecast(monkeypatch):
    SB = stand_in_run(monkeypatch, range_lear_shift=0.5)
    with pytest.raises(ValueError, match="another LEAR forecast"):
        SB.bids(SB.actual_prices())


def test_the_bids_command_counts_a_filled_round_that_lost(monkeypatch):
    # The count is the alarm for a broken guard, so it must ring when rounds do lose:
    # a backwards forecast sent with open limits fills every round, many at a loss.
    SB = stand_in_run(monkeypatch, backwards=True)
    monkeypatch.setattr(BT, "limits", lambda schedule, buy_at, sell_at: pd.DataFrame(
        {"buy": 1e6, "sell": -1e6}, index=range(BT.rounds(schedule).max() + 1)))
    _, _, got = SB.bids(SB.actual_prices())
    for rule in BT.RULES:
        assert got[rule]["lost"] > 0
