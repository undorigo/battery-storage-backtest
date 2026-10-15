"""Does modelling beat not-modelling? — the stage 1 answer, in one command.

Reads the cached data, fits two models on the training years, forecasts 2023, and
scores both against a rule with no modelling in it at all.

Nothing here decides anything.  `features.py` chose which columns exist, `models.py`
chose the estimators, `evaluate.py` chose the scores.  This file puts them in order
and writes down what came out — which is why it is thin, and should stay thin.

**The test years are unreachable from here, on purpose.**  Contract 2 allows them to
be scored once, when the stage closes, and that is a different command run once.
"""

from __future__ import annotations

import argparse
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src import config as cfg
from src import evaluate as E
from src import features as F
from src import models as M
from src import tracking as TR


# ── The rows every forecast is scored on ──────────────────────────────────────
# One decision governs this whole file: **every forecast is judged on the same
# hours.**
#
# It has to be decided because the two models disagree about what they can reach.
# Out of 63,575 rows, 939 are missing at least one number.  The tree model fills the
# gap itself and still returns a price; the straight-line model refuses and stops.
# Score each on the rows it can manage and they sit different exams — so any gap
# between their scores would partly measure which rows each one got.
#
# So the incomplete rows go first, for everyone, before anything is split or fitted.
#
# `cfg.split` hands back three frames and this file keeps two.  Binding the third to
# `_` is Contract 2 made checkable in a single character: the test years are visibly
# discarded at the one point they pass through, rather than sitting in scope where a
# later line could reach them by accident.

def data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """The training rows and the validation rows: complete, and never overlapping."""
    frame = F.build()                                    # every feature, every hour
    complete = F.complete_rows(frame)                    # drop any row with a blank anywhere
    train, valid, _ = cfg.split(complete)                # the test years, dropped on purpose
    return train, valid


# LEAR reads the day table, not the hourly frame, so the test years are dropped from
# it the same way.  Its rows are not thinned to complete ones here: which days LEAR
# can forecast, and which it can learn from, are two different questions, answered
# in `lear_days` below and inside `models.lear_walk_forward`.

def day_rows() -> pd.DataFrame:
    """LEAR's day table, training and validation days only."""
    train, valid, _ = cfg.split(F.day_table())           # the test years, dropped on purpose
    return pd.concat([train, valid])


# ── One row per forecast ──────────────────────────────────────────────────────
# Three forecasts get scored, four in the daily run, and the order they are built
# in is not cosmetic.
#
# The benchmarks come first because they are the denominators: every rMAE here is a
# model's error divided by a benchmark's.  Build a model first and you have a
# numerator with nothing underneath it — and a quiet pull towards choosing the
# denominator that flatters it.
#
# How often the models are refitted is the run's one setting.  `once` fits on the
# training years alone and never again: the stage 1 recipe, the strictest test,
# because no validation row is ever learned from.  `monthly` and `daily` walk
# forward through 2023, each period forecast before it joins the training rows.
# All three sit the same exam — the same hours, prices and benchmark — so their
# scores compare directly, and only the model's freshness differs.
#
# LEAR joins the daily run only, because refitting every day is its recipe.  It
# learns from the last 1,092 days, or with `all` from every day before; the second
# is scored as `lear_all`, so the record never mixes the two.  It forecasts whole
# days, so a day with one blank clue is a day it skips, and the exam shrinks to
# the hours *every* forecast covers.  That trim happens after all the fitting:
# removing hours before it would also remove them from what later refits learn
# from, and the line and tree would quietly change.
#
# Each benchmark is also scored against itself, which looks redundant and is not.  Its
# own ratio has to read exactly 1.000, and that is a free check on everything underneath:
# if it does not, the lining-up or the scoring is wrong, and every other row in the table
# is wrong with it.
#
# The hourly forecasts are handed back beside the scores.  A score is one number per
# model; the significance test compares two models hour by hour, so it needs the
# hourly values each score was computed from, not a second set made afterwards.

REFIT = {"once": "Y", "monthly": "M", "daily": "D"}   # schedule → the period refitted on


def lear_days(table: pd.DataFrame, valid: pd.DataFrame) -> pd.DatetimeIndex:
    """The validation days whose 248 clues are all present: the ones LEAR can forecast."""
    days = table.loc[table.index.isin(valid.index.normalize())]   # grid labels: Berlin days
    ready = days[F.day_feature_columns(table)].notna().all(axis=1)
    return days.index[ready]


def run(train: pd.DataFrame, valid: pd.DataFrame, refit: str = "once",
        table: pd.DataFrame | None = None,
        lear_window: int | None = M.WINDOW_DAYS) -> tuple[list[dict], pd.DataFrame]:
    """Fit, forecast and score. Score rows, benchmark first, and the hourly forecasts.

    `table` is LEAR's day table; without it, LEAR is not run.  `lear_window=None`
    gives LEAR every day before, scored as `lear_all`.
    """
    actual = valid[F.TARGET]                             # the prices that actually happened
    forecasts = pd.DataFrame({"actual": actual,          # one column per forecast
                              "naive": M.naive_forecast(valid),        # lookups, not fits
                              "naive_field": M.field_naive(valid)})

    history = pd.concat([train, valid])                  # what a refit may learn from, if it came first
    for name, make in (("linear", M.linear), ("gbm", M.gbm)):
        forecasts[name] = M.walk_forward(make, history, valid, REFIT[refit])   # one per hour of 2023
    if table is not None:
        lear = M.lear_walk_forward(table, lear_days(table, valid), lear_window)   # one per day
        column = "lear" if lear_window is not None else "lear_all"   # two windows, two names
        forecasts[column] = lear.reindex(forecasts.index)              # blank where LEAR skipped

    forecasts = forecasts.dropna()                       # the hours every forecast covers
    rows = [E.score(name, "valid", forecasts[name], forecasts["naive"], forecasts["actual"],
                    field=forecasts["naive_field"])
            for name in forecasts.columns.drop("actual")]   # each benchmark reads 1.000 on its own ratio
    return rows, forecasts


# ── Writing it down — PLUMBING, already written ───────────────────────────────
# Every row carries the moment it was produced and the commit it was produced from.
#
# The commit is the part that earns its place.  The Third Law asks that a number be
# reproducible from a clean clone; a number sitting beside a commit says *which*
# clone.  Without it a row is a claim nobody can check a month later, when the code
# has moved on and the number has not.
#
# The file is appended to and never rewritten, for the same reason the data pulls
# are: a record that can be overwritten is not a record.
#
# Appending never looks at the header, so rows with a column the header lacks are
# written first and only fail when the file is read back — after the row is already
# in the record.  So the columns are checked against the header before anything is
# written, and a mismatch stops the run with the file untouched.

SCORES = cfg.SCORES                                 # the one place paths are named


def git_commit() -> str:
    """The short commit this run came from, or 'unknown' outside a git clone."""
    try:
        done = subprocess.run(["git", "rev-parse", "--short", "HEAD"],     # no shell, fixed args
                              cwd=cfg.ROOT, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return "unknown"                                     # git absent, or not a clone
    return done.stdout.strip() if done.returncode == 0 else "unknown"


def record(rows: list[dict], path: Path = SCORES) -> pd.DataFrame:
    """Append this run's scores, stamped, and return everything recorded so far."""
    stamped = pd.DataFrame(rows)
    stamped.insert(0, "commit", git_commit())                # which code produced these
    stamped.insert(0, "run_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    if path.exists():
        header = path.open().readline().strip().split(",")   # the columns already recorded
        if header != list(stamped.columns):
            raise ValueError(f"{path.name} has columns {header}, these rows have "
                             f"{list(stamped.columns)}: nothing written")
    path.parent.mkdir(parents=True, exist_ok=True)
    stamped.to_csv(path, mode="a", header=not path.exists(), index=False)   # append, never replace
    return pd.read_csv(path)


# ── Running it ────────────────────────────────────────────────────────────────
# Prints the table for the work log, then says how many runs the file now holds, so
# a run that failed to record is noticed at the time rather than a week later.
#
# The same run then goes to MLflow with its hourly forecasts.  The params are the
# facts only this script knows: the models were fitted once, on which span, from
# which commit.

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score the models on the validation year.")
    parser.add_argument("--refit", choices=REFIT, default="once", help="how often to refit")
    parser.add_argument("--lear", choices=["1092", "all"], default="1092",
                        help="LEAR's window, daily run only: 1,092 days or every day before")
    args = parser.parse_args(argv)
    refit = args.refit
    if args.lear != "1092" and refit != "daily":
        parser.error("--lear applies to the daily run only")    # never ignored silently
    lear_window = None if args.lear == "all" else M.WINDOW_DAYS

    try:
        train, valid = data()
    except FileNotFoundError as exc:
        print(exc)
        print("\nNo cached data. Run `just pull` first.")
        return 2

    days = valid.index                                   # grid labels: Berlin delivery hours
    print(f"Train {len(train):,} rows  ·  validate {len(valid):,} rows  "
          f"({days.min():%Y-%m-%d} to {days.max():%Y-%m-%d})\n")

    started = time.perf_counter()
    table = day_rows() if refit == "daily" else None     # LEAR only joins the daily run
    rows, forecasts = run(train, valid, refit, table, lear_window)
    print(f"Refit {refit}: {time.perf_counter() - started:.0f} s\n")   # checks the timing estimate
    print(E.table(rows))

    recorded = record(rows)
    print(f"\nAppended {len(rows)} rows to {SCORES.relative_to(cfg.ROOT)} "
          f"— {len(recorded):,} recorded in total.")

    params = {"refit": refit,                            # once, monthly or daily
              "train_start": f"{train.index.min():%Y-%m-%d %H:%M}",
              "train_end": f"{train.index.max():%Y-%m-%d %H:%M}",
              "commit": git_commit()}
    if table is not None:
        params["lear_window"] = lear_window or "all"     # LEAR learns from its own window
    ids = TR.log(rows, forecasts, params)
    print(f"Logged {len(ids)} runs to MLflow: "
          + ", ".join(f"{model} {run[:8]}" for model, run in ids.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
