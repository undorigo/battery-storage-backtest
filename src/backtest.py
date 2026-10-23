"""What would the battery have done, and what would it have earned?

Three objects stay apart here, because mixing them is how a capture rate passes
100 % (Contract 3): the prices a plan is made from, the plan itself, and the
prices it is paid at.  `plan` takes prices as a plain argument and does not know
where they came from.  The perfect-foresight ceiling hands it real prices; the
model runs will hand it forecasts.  Settlement always uses real prices.

Everything runs on real hours, as the battery is paid: 23 in March, 25 in October.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

from src import config as cfg


# ── One plan over a window of hours ───────────────────────────────────────────
# A mixed-integer program, not a plain linear one, for a reason the data shows:
# without an on/off switch per hour, the cheapest plan at a very negative price
# charges and discharges in the same hour, collects money for burning energy as
# losses, and leaves the stored level unchanged.  No battery can do that.  It pays
# below about -34 EUR/MWh, and 2023 had 27 such hours.  The switch `u` allows
# charging when 1 and discharging when 0, never both.
#
# Charge and discharge are measured at the grid, where the power limit and the
# price apply; the losses sit between the grid and the cells.  Wear is charged per
# MWh delivered to the grid, as `Battery.cycle_cost_eur_per_mwh` is defined.
#
# The window's last hour ends empty (Contract 4): every trade a day makes is sold
# again inside that day's auction, where one loop block can hold it.

@dataclass(frozen=True)
class Plan:
    """Hour by hour, in MWh: bought from the grid, sold to it, stored at the hour's end."""

    charge: np.ndarray
    discharge: np.ndarray
    level: np.ndarray


def plan(prices: np.ndarray, start_mwh: float,
         battery: cfg.Battery = cfg.BATTERY) -> Plan:
    """The schedule that earns most over these hours, starting from `start_mwh` stored."""
    p = np.asarray(prices, dtype=float)
    T = len(p)
    P, E = battery.power_mw, battery.capacity_mwh                # one hour, so MW = MWh
    ec, ed = battery.efficiency_charge, battery.efficiency_discharge
    I, Z = np.eye(T), np.zeros((T, T))
    earlier = np.eye(T, k=-1)                                    # picks the hour before

    # Variables side by side: charge, discharge, level, switch — T of each.
    # milp minimises, so earnings enter with the sign turned.
    cost = np.concatenate([p, -p + battery.cycle_cost_eur_per_mwh, np.zeros(T), np.zeros(T)])

    # Stored level: last hour's, plus 90 % of what was bought, minus what was sold / 90 %.
    balance = np.hstack([-ec * I, I / ed, I - earlier, Z])
    first = np.zeros(T)
    first[0] = start_mwh                                         # the hour before the window
    # The switch: charge only when u = 1, discharge only when u = 0.
    charge_needs_u = np.hstack([I, Z, Z, -P * I])                # c - P·u <= 0
    discharge_needs_not_u = np.hstack([Z, I, Z, P * I])          # d + P·u <= P

    constraints = [
        LinearConstraint(balance, first, first),
        LinearConstraint(charge_needs_u, -np.inf, 0),
        LinearConstraint(discharge_needs_not_u, -np.inf, P),
    ]
    upper = np.concatenate([np.full(T, P), np.full(T, P),
                            np.full(T, E * battery.soc_max), np.ones(T)])
    upper[3 * T - 1] = E * battery.soc_min                       # the last hour's level: empty
    lower = np.concatenate([np.zeros(2 * T), np.full(T, E * battery.soc_min), np.zeros(T)])
    integral = np.concatenate([np.zeros(3 * T), np.ones(T)])     # only the switch is whole

    result = milp(cost, constraints=constraints, bounds=Bounds(lower, upper),
                  integrality=integral)
    if not result.success:
        raise RuntimeError(f"no plan found: {result.message}")
    x = result.x
    return Plan(charge=x[:T], discharge=x[T:2 * T], level=x[2 * T:3 * T])


# ── Walking forward a day at a time ───────────────────────────────────────────
# Each delivery day is planned on its own prices alone, and ends empty (Contract 4).
# One day, not two, because at 12:00 on D-1 nobody has a forecast for D+1: the TSO
# forecasts it would need come out a day later.  Empty, because charge held over
# midnight is a trade split across two auctions, which no loop block can hold;
# on 2023 it also earned less (22 October 2026: ceiling -14 EUR, LEAR -42 EUR).
#
# So a plan reads only its own day's prices.  A whole year of forecasts can be
# handed over at once without the plan for D seeing the forecast made for D+1.

def delivery_days(index: pd.DatetimeIndex) -> pd.Index:
    """The Berlin calendar day each hour is delivered on."""
    if index.tz is None:
        raise ValueError("prices need a time zone: a naive hour is ambiguous twice a year")
    return index.tz_convert(cfg.TZ_MARKET).normalize()


def walk(prices: pd.Series, start_mwh: float = 0.0,
         battery: cfg.Battery = cfg.BATTERY) -> pd.DataFrame:
    """Hour by hour over every day in `prices`: charge, discharge and level, in MWh."""
    day = delivery_days(prices.index)                            # 23, 24 or 25 hours each
    level, kept = start_mwh, []
    for d in day.unique():
        today = day == d
        got = plan(prices[today].to_numpy(), level, battery)
        kept.append(pd.DataFrame({"charge": got.charge, "discharge": got.discharge,
                                  "level": got.level}, index=prices.index[today]))
        level = got.level[-1]                                    # where tomorrow starts
    return pd.concat(kept)


# ── Settlement: what the plan earned at the prices that happened ──────────────
# The one place real prices meet a schedule (Contract 3).  Every hour of the
# schedule must have a price: lining the two up by timestamp would drop an
# unpriced hour silently, and the total would describe fewer hours than were run.
# Wear is paid per MWh sold, so a schedule that cycles for nothing loses money here.

def settle(schedule: pd.DataFrame, actual: pd.Series,
           battery: cfg.Battery = cfg.BATTERY) -> pd.Series:
    """Hour by hour, in EUR: sold minus bought at the real price, minus wear."""
    missing = schedule.index.difference(actual.index)
    if len(missing):
        raise ValueError(f"{len(missing)} scheduled hours have no price, first {missing[0]}")
    price = actual.reindex(schedule.index)
    return (price * (schedule.discharge - schedule.charge)
            - battery.cycle_cost_eur_per_mwh * schedule.discharge).rename("earned")


# ── The fixed schedule: planned on one set of prices, paid at another ─────────
# The decision and the settlement take separate arguments, so nothing a plan
# reads can be the price it is paid (Contract 3).  Every run comes through here —
# the model's forecast, the naive rule's, and the ceiling's real prices — so all
# of them share one walk (Contract 4).

def fixed(forecast: pd.Series, actual: pd.Series, start_mwh: float = 0.0,
          battery: cfg.Battery = cfg.BATTERY) -> tuple[pd.DataFrame, pd.Series]:
    """The schedule planned on `forecast`, and what it earned at `actual`."""
    schedule = walk(forecast, start_mwh, battery)
    return schedule, settle(schedule, actual, battery)


# ── The perfect-foresight ceiling ─────────────────────────────────────────────
# The battery planned on the very prices it is paid at: the 100 % every capture
# rate divides by.  Every run starts each day empty, as the ceiling does, so the
# ceiling is the best plan for every single day: a day above it is a bug.

def ceiling(actual: pd.Series, start_mwh: float = 0.0,
            battery: cfg.Battery = cfg.BATTERY) -> tuple[pd.DataFrame, pd.Series]:
    """The schedule planned on real prices, and what it earned at them."""
    return fixed(actual, actual, start_mwh, battery)


# ── Cutting a schedule into rounds ────────────────────────────────────────────
# A bid goes out as one loop block per buy-then-sell round (decided 22 October
# 2026), so the schedule must first be cut into rounds.  The cut falls where the
# battery is empty again, not at a time of day: two rounds that share energy then
# stay one round by themselves, and every round starts and ends empty, so any mix
# of filled and failed rounds is something a real battery could have done.

TRADING = 1e-6                                                   # MWh below this is solver noise

def rounds(schedule: pd.DataFrame) -> pd.Series:
    """Each hour's round, numbered from 0 in order; -1 for an empty hour with no trade."""
    trading = (schedule.charge > TRADING) | (schedule.discharge > TRADING)
    empty = schedule.level < TRADING
    closes = trading & empty                                     # this hour's trade empties it
    label = closes.shift(fill_value=False).cumsum()              # rounds closed before this hour
    return label.where(trading | ~empty, -1).rename("round")


# ── A loop per round: filled or not, then paid ────────────────────────────────
# Each round goes out as a loop: a buy block over its charging hours, a sell block
# over its selling hours, each with one limit, filled whole or not at all.  The
# exchange judges a block in euros, its *surplus*: how far the real prices beat
# the limit, times the volume.  Which surpluses must hold is not settled for the
# German day-ahead (EPEX writes the pair rule for its GB auction only), so both:
# "strict", each block on its own, leads; "pair", the two together, sits beside it.
#
# Real prices decide the fill and the pay, and nothing here returns to a plan
# (Contract 3).  Where the limits come from is the caller's: one row per round.

RULES = ("strict", "pair")

def bid(schedule: pd.DataFrame, actual: pd.Series, limits: pd.DataFrame,
        rule: str = "strict", battery: cfg.Battery = cfg.BATTERY) -> tuple[pd.DataFrame, pd.Series]:
    """The trades whose loop went through under `rule`, and what they earned at `actual`."""
    if rule not in RULES:
        raise ValueError(f"rule must be one of {RULES}, not {rule!r}")
    label = rounds(schedule)
    held = label[label >= 0]
    unpriced = pd.Index(held.unique()).difference(limits.dropna().index)
    if len(unpriced):                                            # NaN fails every test: a silent "no"
        raise ValueError(f"{len(unpriced)} rounds have no limits, first round {unpriced[0]}")
    settle(schedule, actual, battery)                            # refuses an unpriced hour first
    price = actual.reindex(held.index)
    hours = schedule.loc[held.index]
    buy = (hours.charge * (limits.buy.reindex(held).to_numpy() - price)).groupby(held).sum()
    sell = (hours.discharge * (price - limits.sell.reindex(held).to_numpy())).groupby(held).sum()
    went = (buy >= 0) & (sell >= 0) if rule == "strict" else (buy + sell >= 0)
    kept = label.isin(went.index[went])                          # hours of a filled round
    traded = schedule.copy()
    traded.loc[~kept, ["charge", "discharge", "level"]] = 0.0    # a failed round never happened
    return traded, settle(traded, actual, battery)
