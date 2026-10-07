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

import subprocess
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


# ── One row per forecast ──────────────────────────────────────────────────────
# Three forecasts get scored, and the order they are built in is not cosmetic.
#
# The benchmark comes first because it is the denominator: every rMAE here is a
# model's error divided by the benchmark's.  Build a model first and you have a
# numerator with nothing underneath it — and a quiet pull towards choosing the
# denominator that flatters it.
#
# The two models are fitted on the training years only, and never refitted.  That is
# the stricter test, because the model never sees a single validation row, and it
# keeps the stage 1 question clean: any win belongs to the model rather than to the
# refitting.  Walking the fit forward through the year is stage 2 work, and it is
# measured against this number rather than instead of it.
#
# The benchmark is also scored against itself, which looks redundant and is not.  That
# row has to read exactly 1.000, and it is a free check on everything underneath: if it
# does not, the lining-up or the scoring is wrong, and every other row in the table is
# wrong with it.
#
# The hourly forecasts are handed back beside the scores.  A score is one number per
# model; the significance test compares two models hour by hour, so it needs the
# 8,759 values each score was computed from, not a second set made afterwards.

def run(train: pd.DataFrame, valid: pd.DataFrame) -> tuple[list[dict], pd.DataFrame]:
    """Fit, forecast and score. Score rows, benchmark first, and the hourly forecasts."""
    benchmark = M.naive_forecast(valid)                  # a lookup, not a fit: no training needed
    actual = valid[F.TARGET]                             # the prices that actually happened
    forecasts = pd.DataFrame({"actual": actual, "naive": benchmark})   # one column per forecast

    rows = [E.score("naive", "valid", benchmark, benchmark, actual)]   # must come out at 1.000
    for name, estimator in (("linear", M.linear()), ("gbm", M.gbm())):
        model = M.fit(estimator, train)                  # the training years only, never refitted
        forecasts[name] = M.forecast(model, valid)       # one price per hour of 2023
        rows.append(E.score(name, "valid", forecasts[name], benchmark, actual))

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

def main() -> int:
    try:
        train, valid = data()
    except FileNotFoundError as exc:
        print(exc)
        print("\nNo cached data. Run `just pull` first.")
        return 2

    days = valid.index                                   # grid labels: Berlin delivery hours
    print(f"Train {len(train):,} rows  ·  validate {len(valid):,} rows  "
          f"({days.min():%Y-%m-%d} to {days.max():%Y-%m-%d})\n")

    rows, forecasts = run(train, valid)
    print(E.table(rows))

    history = record(rows)
    print(f"\nAppended {len(rows)} rows to {SCORES.relative_to(cfg.ROOT)} "
          f"— {len(history):,} recorded in total.")

    params = {"refit": "once",                           # stage 1 recipe: fitted once, never again
              "train_start": f"{train.index.min():%Y-%m-%d %H:%M}",
              "train_end": f"{train.index.max():%Y-%m-%d %H:%M}",
              "commit": git_commit()}
    ids = TR.log(rows, forecasts, params)
    print(f"Logged {len(ids)} runs to MLflow: "
          + ", ".join(f"{model} {run[:8]}" for model, run in ids.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
