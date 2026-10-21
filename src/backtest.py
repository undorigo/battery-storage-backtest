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
    lower = np.concatenate([np.zeros(2 * T), np.full(T, E * battery.soc_min), np.zeros(T)])
    integral = np.concatenate([np.zeros(3 * T), np.ones(T)])     # only the switch is whole

    result = milp(cost, constraints=constraints, bounds=Bounds(lower, upper),
                  integrality=integral)
    if not result.success:
        raise RuntimeError(f"no plan found: {result.message}")
    x = result.x
    return Plan(charge=x[:T], discharge=x[T:2 * T], level=x[2 * T:3 * T])


# ── Walking forward a day at a time ───────────────────────────────────────────
# Each delivery day is planned on its own prices alone, and the stored level is
# carried over midnight (Contract 4).  One day, not two, because at 12:00 on D-1
# nobody has a forecast for D+1: the TSO forecasts it would need come out a day
# later.  Measured on 2023 (21 October 2026): seeing tomorrow is worth 482 EUR a
# year even on real prices, and every stand-in for it tried — a copy of today,
# last week, LEAR's next-day forecast — earned less than leaving it out.
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


# ── The perfect-foresight ceiling ─────────────────────────────────────────────
# The battery planned on the very prices it is paid at: the 100 % every capture
# rate divides by.  It is the best plan for each day *given the charge it starts
# with*.  A plan made from a forecast that ends a day holding charge starts the
# next one with energy the ceiling does not have, and can beat it that day.

def ceiling(actual: pd.Series, start_mwh: float = 0.0,
            battery: cfg.Battery = cfg.BATTERY) -> tuple[pd.DataFrame, pd.Series]:
    """The schedule planned on real prices, and what it earned at them."""
    schedule = walk(actual, start_mwh, battery)
    return schedule, settle(schedule, actual, battery)
