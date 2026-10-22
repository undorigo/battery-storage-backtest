"""What could the battery have earned on 2023? — stage 4, in one command.

`just backtest ceiling` plans the battery on the prices that actually cleared
and settles it at the same prices: the most the battery could have earned under
the project's convention, and the 100 % every capture rate divides by.
`just backtest fixed` plans on LEAR's stored 2023 forecasts instead, the field's
naive rule beside it, and settles both at real prices: the capture rate.

Nothing here decides anything.  `backtest.py` holds the planner and settlement;
this file puts them in order and prints what came out.

**The test years are unreachable from here**: only 2023 is handed to the walk,
and each day is planned on its own prices, so 31 December never reads 1 January 2024.
"""

from __future__ import annotations

import argparse
import time

import pandas as pd

from scripts.train import git_commit
from src import backtest as BT
from src import config as cfg
from src import data
from src import tracking as TR


# ── The prices that cleared ───────────────────────────────────────────────────
# Real hours, as the battery is paid: 8,760 in 2023, the clock-change days at 23
# and 25.  Checked on 20 October 2026: no hour missing in any split, so the walk's
# hour-after-hour balance never joins two hours that are not neighbours.

def actual_prices() -> pd.Series:
    """2023's day-ahead prices, EUR/MWh, on real hours in UTC."""
    price = data.load("day_ahead_price").iloc[:, 0]
    return cfg.split(price)[1]                                   # validation year only


# ── The ceiling, and what to read off it ──────────────────────────────────────
# Equivalent full cycles count energy out of the cells against capacity: what
# reached the grid, divided by the discharge efficiency, then by 2 MWh.  It says
# how hard the plan works the battery, which the wear figure assumes.

def ceiling(actual: pd.Series) -> dict:
    """Earnings and effort of the perfect-foresight plan over these prices."""
    schedule, earned = BT.ceiling(actual)
    per_day = earned.groupby(BT.delivery_days(earned.index)).sum()
    b = cfg.BATTERY
    return {"days": len(per_day), "hours": len(earned), "earned": earned.sum(),
            "median_day": per_day.median(), "best_day": per_day.max(),
            "worst_day": per_day.min(),
            "cycles": schedule.discharge.sum() / b.efficiency_discharge / b.capacity_mwh}


# ── The forecasts a fixed schedule is planned on ──────────────────────────────
# Read back from the stored run, not refitted: LEAR walked through 2023 one day at
# a time, each forecast made from what was known at 12:00 the day before.  The run
# keeps the field's naive forecast beside LEAR's, so both come from one file.  Its
# `actual` column is not used: it sits on the 24-slot grid, where the two autumn
# 02:00 prices are averaged, and the battery is paid the real ones.

LEAR_RUN = {"model": "lear", "refit": "daily", "lear_window": "1092", "split": "valid"}
PLANNED_ON = {"LEAR": "lear", "naive (field)": "naive_field"}


def forecasts(hours: pd.DatetimeIndex) -> tuple[str, dict[str, pd.Series]]:
    """The stored run's commit, and each forecast laid onto these real hours."""
    run = TR.latest(**LEAR_RUN)
    if run is None:
        raise LookupError("no stored 2023 LEAR run: run `just train daily` first")
    params, table = TR.read(run)
    return params["commit"], {name: data.from_slots(table[col], hours)
                              for name, col in PLANNED_ON.items()}


def capture(actual: pd.Series) -> tuple[str, dict]:
    """Earnings per run, the ceiling first, and the days a run beat it."""
    commit, planned = forecasts(actual.index)
    _, best = BT.ceiling(actual)
    best_day = best.groupby(BT.delivery_days(best.index)).sum()
    got = {"ceiling": {"earned": best.sum(), "days_above": 0, "above_eur": 0.0}}
    for name, forecast in planned.items():
        _, earned = BT.fixed(forecast, actual)
        gap = earned.groupby(BT.delivery_days(earned.index)).sum() - best_day
        above = gap[gap > 1e-6]                                  # days above the ceiling: a bug if any
        got[name] = {"earned": earned.sum(), "days_above": len(above), "above_eur": above.sum()}
    return commit, got


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan, settle and score the battery on 2023.")
    parser.add_argument("what", choices=["ceiling", "fixed"])
    what = parser.parse_args(argv).what

    started = time.time()
    if what == "fixed":
        run_commit, got = capture(actual_prices())
        ceiling_eur = got["ceiling"]["earned"]
        print(f"Fixed schedule, 2023, at {git_commit()}: forecasts from the run at {run_commit}, "
              f"settled at real prices, {time.time() - started:.1f} s")
        for name, row in got.items():
            print(f"  {name:<14} {row['earned']:>10,.0f} EUR  {row['earned'] / ceiling_eur:6.1%}"
                  + (f"   beat the ceiling on {row['days_above']} days, by {row['above_eur']:,.0f} EUR"
                     if name != "ceiling" else ""))
        return 0

    got = ceiling(actual_prices())
    print(f"Perfect-foresight ceiling, 2023, at {git_commit()}: {got['days']} days, "
          f"{got['hours']} hours, {time.time() - started:.1f} s")
    print(f"  earned      {got['earned']:>10,.0f} EUR  (1 MW / 2 MWh, wear included)")
    print(f"  per day     median {got['median_day']:,.0f}, best {got['best_day']:,.0f}, "
          f"worst {got['worst_day']:,.0f} EUR")
    print(f"  full cycles {got['cycles']:>10,.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
