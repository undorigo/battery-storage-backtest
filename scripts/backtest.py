"""What could the battery have earned on 2023? — stage 4, in one command.

`just backtest ceiling` plans the battery on the prices that actually cleared
and settles it at the same prices: the most the battery could have earned under
the project's convention, and the 100 % every capture rate will divide by.
Later runs (`fixed`, `bids`) will plan on forecasts and come through the same door.

Nothing here decides anything.  `backtest.py` holds the planner and settlement;
this file puts them in order and prints what came out.

**The test years are unreachable from here**: only 2023 is handed to the walk,
so its last day plans alone rather than reading 1 January 2024.
"""

from __future__ import annotations

import argparse
import time

import pandas as pd

from scripts.train import git_commit
from src import backtest as BT
from src import config as cfg
from src import data


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan, settle and score the battery on 2023.")
    parser.add_argument("what", choices=["ceiling"])
    parser.parse_args(argv)

    started = time.time()
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
