"""What could the battery have earned on 2023? — stage 4, in one command.

`just backtest ceiling` plans the battery on the prices that actually cleared
and settles it at the same prices: the most the battery could have earned under
the project's convention, and the 100 % every capture rate divides by.
`just backtest fixed` plans on the stored 2023 forecasts instead (LEAR, the tree,
the straight line, their average, the field's naive rule) and settles each at
real prices: the capture rate.
`just backtest bids` sends LEAR's plan as one loop per round, with limits from
QRA's stored range, and settles what went through under each fill rule.

Nothing here decides anything.  `backtest.py` holds the planner and settlement;
this file puts them in order and prints what came out.

**The test years are unreachable from this command**: only 2023 is handed to the
walk, and each day is planned on its own prices, so 31 December never reads 1 January
2024.  The functions take the split as an argument for one caller only: `just
final-score battery`, stage 4's one reading of 2024-25, which runs this same code.
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from scripts.train import git_commit
from src import backtest as BT
from src import config as cfg
from src import data
from src import evaluate as E
from src import tracking as TR


# ── The prices that cleared ───────────────────────────────────────────────────
# Real hours, as the battery is paid: 8,760 in 2023, the clock-change days at 23
# and 25.  Checked on 20 October 2026: no hour missing in any split, so the walk's
# hour-after-hour balance never joins two hours that are not neighbours.

PART = {"valid": 1, "test": 2}                                   # which of `cfg.split`'s three


def actual_prices(split: str = "valid") -> pd.Series:
    """One split's day-ahead prices, EUR/MWh, on real hours in UTC: 2023 by default."""
    price = data.load("day_ahead_price").iloc[:, 0]
    return cfg.split(price)[PART[split]]                         # that split only


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
# Read back from the stored runs, not refitted: each model walked through 2023 one
# day at a time, each forecast made from what was known at 12:00 the day before.
# All three come from one `just train daily` batch.  LEAR's run keeps the field's
# naive forecast beside its own.  The `actual` columns are not used: they sit on the
# 24-slot grid, where the two autumn 02:00 prices are averaged, and the battery is
# paid the real ones.
#
# The average of the three is a candidate since 26 October 2026: on 2023 it kept
# 93.9 % against LEAR's 91.0 %, because the money is in the day's shape and the
# three miss the shape partly in different hours.  Equal weights, as the field
# averages (Lago et al. 2021), so nothing is tuned on the year it is scored on.
#
# The held-back runs carry their recipe in the name (`lear daily`), because `just
# final-score` stores a frozen tree and line beside the daily ones; 2023's do not.

DAILY = {"refit": "daily", "lear_window": "1092", "split": "valid"}
MODELS = {"LEAR": "lear", "tree": "gbm", "straight line": "linear"}
NEEDS = {"valid": ("2023", "`just train daily`"), "test": ("2024-25", "`just final-score`")}


def forecasts(hours: pd.DatetimeIndex, split: str = "valid") -> tuple[str, dict[str, pd.Series]]:
    """The stored runs' commits, and each forecast laid onto these real hours."""
    slots, commits = {}, set()
    for name, model in MODELS.items():
        stored = model if split == "valid" else f"{model} daily"   # the held-back run's name
        run = TR.latest(model=stored, **{**DAILY, "split": split})
        if run is None:
            years, command = NEEDS[split]
            raise LookupError(f"no stored {years} {name} run: run {command} first")
        params, table = TR.read(run)
        slots[name] = table[stored]
        commits.add(params["commit"])
        if model == "lear":
            naive = table["naive_field"]                         # the benchmark rides in LEAR's run
    slots["average"] = sum(slots[name] for name in MODELS) / len(MODELS)   # hour by hour
    slots["naive (field)"] = naive
    return ", ".join(sorted(commits)), {name: data.from_slots(f, hours) for name, f in slots.items()}


# A lead is one year's total, so it is tested day by day: Diebold-Mariano on daily
# earnings, the test behind every p-value on this project.  One year can only see
# gaps above about 1.5 points between the models (26 October 2026), so a p-value
# above 0.05 here reads "cannot tell", never "the same".

LEADS = [("LEAR", "naive (field)"), ("average", "LEAR"),
         ("tree", "LEAR"), ("straight line", "LEAR")]             # each: did the first earn more?

def capture(actual: pd.Series, split: str = "valid") -> tuple[str, dict]:
    """Earnings per run, the ceiling first, the days a run beat it, and its daily totals."""
    commit, planned = forecasts(actual.index, split)
    _, best = BT.ceiling(actual)
    best_day = best.groupby(BT.delivery_days(best.index)).sum()
    got = {"ceiling": {"earned": best.sum(), "days_above": 0, "above_eur": 0.0}}
    for name, forecast in planned.items():
        _, earned = BT.fixed(forecast, actual)
        gap = earned.groupby(BT.delivery_days(earned.index)).sum() - best_day
        above = gap[gap > 1e-6]                                  # days above the ceiling: a bug if any
        got[name] = {"earned": earned.sum(), "days_above": len(above), "above_eur": above.sum(),
                     "per_day": earned.groupby(BT.delivery_days(earned.index)).sum()}
    return commit, got


# ── The range the limits come from ────────────────────────────────────────────
# QRA's stored 2023 range, the four windows averaged (stage 3's choice).  The plan
# and its limits must rest on one forecast, so the range is refused unless it was
# built on the very LEAR forecasts the plan reads.  Buy below p75, sell above p25:
# Nitka & Weron's (2023) best band, taken from the paper rather than tuned on 2023.
# The band only splits the room between the two sides: `BT.limits` then moves both
# to break-even, and under the pair rule the split makes no difference at all.

QRA_RUN = {"model": "qra", "split": "valid", "window": "28+56+91+182"}
QRA_NEEDS = {"valid": ("2023", "`just quantiles 28 56 91 182`"),
             "test": ("2024-25", "`just final-score ranges`")}
BAND = (75, 25)                                                  # buy below p75, sell above p25


def ranges(hours: pd.DatetimeIndex, lear: pd.Series,
           split: str = "valid") -> tuple[str, pd.Series, pd.Series]:
    """The range run's commit, and its buy and sell percentiles on these real hours."""
    run = TR.latest(**{**QRA_RUN, "split": split})
    if run is None:
        years, command = QRA_NEEDS[split]
        raise LookupError(f"no stored {years} QRA range: run {command} first")
    params, table = TR.read_range(run)
    if not np.allclose(data.from_slots(table["lear"], hours), lear):
        raise ValueError("the stored range was built on another LEAR forecast than the plan's")
    buy, sell = BAND
    return params["commit"], data.from_slots(table[buy], hours), data.from_slots(table[sell], hours)


# ── The bids: LEAR's plan, sent as loops ──────────────────────────────────────
# The fixed schedule is the same plan sent without limits, so the gap between them
# is what the limits did.  A round that went through and lost money is counted,
# because the limits promise 0: any such round is a bug, as a day above the ceiling is.

def bids(actual: pd.Series, split: str = "valid") -> tuple[str, str, dict]:
    """Earnings of the ceiling, the fixed schedule and each fill rule, and what filled."""
    commit, planned = forecasts(actual.index, split)
    range_commit, buy_at, sell_at = ranges(actual.index, planned["LEAR"], split)
    schedule, fixed_earned = BT.fixed(planned["LEAR"], actual)
    limits = BT.limits(schedule, buy_at, sell_at)
    label = BT.rounds(schedule)
    got = {"ceiling": {"earned": BT.ceiling(actual)[1].sum()},
           "fixed (LEAR)": {"earned": fixed_earned.sum()}}
    for rule in BT.RULES:
        traded, earned = BT.bid(schedule, actual, limits, rule)
        went = label[(traded.charge + traded.discharge) > BT.TRADING].unique()
        per_round = earned.groupby(label).sum()[went]
        got[rule] = {"earned": earned.sum(), "filled": len(went), "rounds": len(limits),
                     "lost": int((per_round < -1e-9).sum())}
    return commit, range_commit, got


# ── Printing what came out ────────────────────────────────────────────────────
# Shared with `just final-score battery`, so the held-back reading prints exactly
# what the 2023 commands print, and nothing a reader could mistake for more.

def show_fixed(got: dict) -> None:
    """Each run's share of the ceiling, then each lead tested day by day."""
    ceiling_eur = got["ceiling"]["earned"]
    for name, row in got.items():
        print(f"  {name:<14} {row['earned']:>10,.0f} EUR  {row['earned'] / ceiling_eur:6.1%}"
              + (f"   beat the ceiling on {row['days_above']} days, by {row['above_eur']:,.0f} EUR"
                 if name != "ceiling" else ""))
    print("  Day by day (Diebold-Mariano on daily earnings, one-sided p that the first earned more):")
    for first, second in LEADS:
        a, b = got[first]["per_day"], got[second]["per_day"]
        gap = a - b
        print(f"    {first} against {second}: ahead on {(gap > 1e-6).sum()} days, behind on "
              f"{(gap < -1e-6).sum()}, {gap.mean():+,.2f} EUR a day; p {E.dm_earnings(b, a):.2g}")


def show_bids(got: dict) -> None:
    """Each fill rule's share of the ceiling, the rounds that went through and lost."""
    ceiling_eur = got["ceiling"]["earned"]
    for name, row in got.items():
        print(f"  {name:<14} {row['earned']:>10,.0f} EUR  {row['earned'] / ceiling_eur:6.1%}"
              + (f"   {row['filled']} of {row['rounds']} rounds went through, "
                 f"{row['lost']} lost money" if "filled" in row else "")
              + ("   <- headline" if name == "strict" else ""))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan, settle and score the battery on 2023.")
    parser.add_argument("what", choices=["ceiling", "fixed", "bids"])
    what = parser.parse_args(argv).what

    started = time.time()
    if what == "bids":
        run_commit, range_commit, got = bids(actual_prices())
        print(f"Bids, 2023, at {git_commit()}: LEAR's plan from the runs at {run_commit}, limits "
              f"from QRA p{BAND[0]}/p{BAND[1]} at {range_commit}, moved to break-even, "
              f"{time.time() - started:.1f} s")
        show_bids(got)
        return 0
    if what == "fixed":
        run_commit, got = capture(actual_prices())
        print(f"Fixed schedule, 2023, at {git_commit()}: forecasts from the runs at {run_commit}, "
              f"settled at real prices, {time.time() - started:.1f} s")
        show_fixed(got)
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
