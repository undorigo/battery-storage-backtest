"""The number a stage ends on — read once, from years nothing has been tuned against.

`train.py` runs as often as you like, because the validation year exists to be looked at.
This does not. Contract 2 allows the held-back years to be scored **once per stage**, and
the reason is not ceremony: every time results are read and something is changed in
response, those results stop being a fair exam. Read them repeatedly and the final number
quietly becomes the best of several attempts rather than an honest one.

So this lives in its own file, with its own command, and `train.py` has no path to the
years it reads. That separation is the enforcement — a promise in a docstring would not
survive a hurried afternoon.

**Stage 2's recipe, and stage 1's beside it, in one reading.** Contract 2 limits how often
the held-back years are looked at, not how many forecasts are scored in a single look:

- line, tree and LEAR refitted every day, walking forward through 2024-25 exactly as
  `train.py` walks through 2023 — the recipe stage 2 chose, and the one that would run
- line and tree fitted once on every year before 2024 and then frozen — stage 1's headline
  recipe, kept so the reading shows on untouched years what daily refitting bought

A daily refit learns from held-back days once they are in the past, as a live run would
on 5 March 2025 with 4 March in hand. What it never sees is the day it forecasts.
"""

from __future__ import annotations

import time

import pandas as pd

from scripts.train import git_commit, lear_days, record   # same stamping, same rules
from src import config as cfg
from src import evaluate as E
from src import features as F
from src import models as M
from src import tracking as TR

SPLIT = "test"                                       # what every row produced here is labelled


# ── The three blocks, unchanged ───────────────────────────────────────────────
# Thin on purpose. `cfg.split` owns the boundary arithmetic and every script goes through
# it rather than slicing on its own, which is what keeps Contract 2 in one file. The only
# job here is to drop incomplete rows first, so every recipe below is fitted and scored on
# the same hours.

def data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """The training years, the validation year, and the years held back."""
    return cfg.split(F.complete_rows(F.build()))     # complete rows only, then split


def day_rows() -> pd.DataFrame:
    """LEAR's day table up to the last held-back day, through the same split."""
    return pd.concat(cfg.split(F.day_table()))       # nothing after the test years


# ── Naming a recipe after the years it saw ────────────────────────────────────
# The label is derived from the data rather than written as a string. A hardcoded
# "2018-2022" would be a second copy of the split dates, and Contract 2 says those live in
# `config.py` alone — change a boundary and a hardcoded label would quietly start lying.

def label(name: str, history: pd.DataFrame) -> str:
    """A model name carrying the span it learned from, e.g. `gbm 2018-2023`."""
    years = history.index                            # grid labels are Berlin, so the years read right
    return f"{name} {years.min():%Y}-{years.max():%Y}"


# ── The scored rows ───────────────────────────────────────────────────────────
# The benchmark comes first because it is the denominator every other row divides by, and
# it is built from the held-back years alone — a week-old lookup needs no training at all.
#
# The daily rows walk forward over the whole history, held-back years included, because
# `walk_forward` only ever hands a refit the hours before the day it forecasts.  The frozen
# rows are fitted once on every year before 2024.  Then the same-exam rule from `train.py`:
# every forecast is scored on the hours all of them cover, LEAR's skipped days included.

def run(train: pd.DataFrame, valid: pd.DataFrame, holdout: pd.DataFrame,
        table: pd.DataFrame | None = None) -> tuple[list[dict], pd.DataFrame]:
    """Score rows, benchmark first, and the hourly forecasts. Without `table`, no LEAR."""
    benchmark = M.naive_forecast(holdout)            # a lookup, not a fit
    forecasts = pd.DataFrame({"actual": holdout[F.TARGET], "naive": benchmark})

    history = pd.concat([train, valid, holdout])     # a refit takes only the days before its own
    for name, make in (("linear", M.linear), ("gbm", M.gbm)):
        forecasts[f"{name} daily"] = M.walk_forward(make, history, holdout, "D")
    if table is not None:
        lear = M.lear_walk_forward(table, lear_days(table, holdout))   # one fresh LEAR per day
        forecasts["lear daily"] = lear.reindex(forecasts.index)        # blank where LEAR skipped

    known = pd.concat([train, valid])                # every year before the first held-back day
    for name, make in (("linear", M.linear), ("gbm", M.gbm)):
        forecasts[label(name, known)] = M.forecast(M.fit(make(), known), holdout)   # then frozen

    forecasts = forecasts.dropna()                   # the hours every forecast covers
    rows = [E.score(name, SPLIT, forecasts[name], forecasts["naive"], forecasts["actual"])
            for name in forecasts.columns.drop("actual")]   # naive first: must come out at 1.000
    return rows, forecasts


# ── Saying whether this was the first look ────────────────────────────────────
# Not a lock. There are honest reasons to run this again — a bug in this very script is
# one. But a second reading of the held-back years should never happen without anyone
# noticing that it happened.
#
# The stamped record is the evidence; this sentence is what a person actually reads. It is
# a separate function only so it can be tested, because an enforcement message that
# quietly says the wrong thing is worse than none at all.

def reading_note(recorded: pd.DataFrame, just_written: int) -> str:
    """Whether the held-back years had been read before this run."""
    already = int((recorded["split"] == SPLIT).sum())     # every test row ever recorded
    if already == just_written:
        return f"{already} held-back rows recorded. This is the first reading."
    return (f"{already} held-back rows recorded, {just_written} of them from this run. "
            f"The held-back years have been read before — check the commit column.")


# ── Running it ────────────────────────────────────────────────────────────────

def main() -> int:
    try:
        train, valid, holdout = data()
    except FileNotFoundError as exc:
        print(exc)
        print("\nNo cached data. Run `just pull` first.")
        return 2

    days = holdout.index                             # grid labels: Berlin delivery hours
    print(f"Histories of {len(train):,} and {len(train) + len(valid):,} rows  ·  "
          f"scoring {len(holdout):,} held-back rows "
          f"({days.min():%Y-%m-%d} to {days.max():%Y-%m-%d})\n")

    started = time.perf_counter()
    rows, forecasts = run(train, valid, holdout, day_rows())
    print(f"Ran in {time.perf_counter() - started:.0f} s\n")
    print(E.table(rows))
    print("\n" + reading_note(record(rows), len(rows)))

    # Two batches, so each run states its own schedule and `just significance` can find it.
    commit = git_commit()
    daily = [r for r in rows if r["model"] == "naive" or r["model"].endswith(" daily")]
    frozen = [r for r in rows if r not in daily]                  # "gbm 2018-2023"
    ids = {**TR.log(daily, forecasts, {"refit": "daily", "lear_window": M.WINDOW_DAYS,
                                       "commit": commit}),
           **TR.log(frozen, forecasts, {"refit": "once", "commit": commit})}
    print(f"Logged {len(ids)} runs to MLflow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
