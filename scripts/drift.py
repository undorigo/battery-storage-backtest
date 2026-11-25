"""The drift checks (stage 5, step 9): is the trial still forecasting as 2023 did?

Run:  just drift match      (does the trial's code rebuild 2023's stored forecasts?)

Two signals, each over 28 days, flag when they leave the range 2023 showed: the share
of real prices inside LEAR's 80 % band, and the average's error against the field's
rule (decided 17 and 18 November 2026).  A flag is a message; nothing switches.
`trial.py` and the forecasting code stay frozen: this file only reads them.

`match` comes first, because a threshold is only as good as the forecasts it was set
on: 2023's were stored in October by `just train daily`, and the trial makes its own
with `tomorrow._models`.  If the two recipes disagree, the error signal watches LEAR.
"""

from __future__ import annotations

import argparse
import time

import pandas as pd

from scripts import backtest as B
from scripts import tomorrow as T
from scripts.train import git_commit
from src import config as cfg
from src import models as M
from src import tracking as TR

MEMBERS = ("LEAR", "tree", "straight line")                 # the average's three, in order


# ── Rebuilding 2023 with the trial's own models ───────────────────────────────
# The forecasting step behind tomorrow's arrival check, called one day at a time.
# The check itself is skipped: it counts quarter-hours, and 2023's prices came
# hourly (24 a day, not 96), so it would answer "not yet" for every day of the year.
# A day any model could not forecast is an error, so a match is never claimed on
# fewer days than it names.

def rebuild(days: pd.DatetimeIndex, given: T.Inputs,
            lear_window: int | None = M.WINDOW_DAYS) -> dict[str, pd.Series]:
    """Each forecast the trial would make for these days, on the 24-slot grid."""
    made = {name: [] for name in MEMBERS}
    for day in days:
        rows = given.frame[given.frame.index.normalize() == day]   # the day's 24 slots
        got, stopped, _ = T._models(day, given, rows, lear_window)
        if stopped:
            raise ValueError(f"{day:%Y-%m-%d}: " + "; ".join(stopped))
        for name in MEMBERS:
            made[name].append(got[name])
    joined = {name: pd.concat(parts) for name, parts in made.items()}
    joined["average"] = sum(joined[name] for name in MEMBERS) / len(MEMBERS)   # hour by hour
    return joined


# ── How far the rebuild lands from what was stored ────────────────────────────
# The largest difference within each day, so one hour off shows at full size.  A
# cent per MWh is the line: day-ahead prices clear in whole cents, so a gap below
# it is rounding, and a gap at it is a price a reader could see.

TOLERANCE = 0.01                                            # EUR/MWh: one cent, a price's last digit


def gaps(rebuilt: dict[str, pd.Series], stored: dict[str, pd.Series]) -> pd.DataFrame:
    """Per day, the largest gap in EUR/MWh between rebuilt and stored, one column per forecast."""
    out = {}
    for name, new in rebuilt.items():
        old = stored[name].reindex(new.index)               # by label, never by position
        if old.isna().any():
            raise ValueError(f"{name}: nothing stored for {old.index[old.isna()][0]:%Y-%m-%d}")
        out[name] = (new - old).abs().groupby(new.index.normalize()).max()
    return pd.DataFrame(out)


def matches(per_day: pd.DataFrame) -> bool:
    return bool((per_day < TOLERANCE).all().all())


def stored_2023() -> tuple[str, dict[str, pd.Series]]:
    """The commit and slots of `just train daily`'s 2023 runs, the average beside them."""
    stored, commits = {}, set()
    for name, model in B.MODELS.items():
        params, table = TR.read(TR.latest(model=model, **B.DAILY))
        stored[name] = table[model]
        commits.add(params["commit"])
    stored["average"] = sum(stored[name] for name in MEMBERS) / len(MEMBERS)
    return ", ".join(sorted(commits)), stored


def match() -> int:
    started = time.time()
    days = pd.date_range(pd.Timestamp(cfg.TRAIN_END) + pd.Timedelta(days=1), cfg.VALID_END)
    commit, stored = stored_2023()
    per_day = gaps(rebuild(days, T.inputs()), stored)
    print(f"2023 rebuilt at {git_commit()} against the runs at {commit}: {len(per_day)} days, "
          f"{time.time() - started:.0f} s")
    for name, gap in per_day.items():
        print(f"  {name:<14} largest gap {gap.max():.2e} EUR/MWh, days at {TOLERANCE} or more: "
              f"{int((gap >= TOLERANCE).sum())}")
    print("Match: the error signal watches the average." if matches(per_day)
          else "No match: the error signal watches LEAR.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The drift checks.")
    parser.add_argument("what", choices=["match"])
    parser.parse_args(argv)
    return match()


if __name__ == "__main__":
    raise SystemExit(main())
