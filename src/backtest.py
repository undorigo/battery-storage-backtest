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
