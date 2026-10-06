"""The number a stage ends on — read once, from years nothing has been tuned against.

`train.py` runs as often as you like, because the validation year exists to be looked at.
This does not. Contract 2 allows the held-back years to be scored **once per stage**, and
the reason is not ceremony: every time results are read and something is changed in
response, those results stop being a fair exam. Read them repeatedly and the final number
quietly becomes the best of several attempts rather than an honest one.

So this lives in its own file, with its own command, and `train.py` has no path to the
years it reads. That separation is the enforcement — a promise in a docstring would not
survive a hurried afternoon.

**Two recipes are scored, in one reading.** Contract 2 limits how often the held-back
years are looked at, not how many models are scored in a single look, so scoring both
costs nothing and answers two different questions:

- fitted to the end of 2022 — the same recipe that produced the validation scores, so the
  two sit side by side and the only thing that differs is which years are being forecast
- fitted to the end of 2023 — the model that would actually be run, because anyone
  forecasting 2024 had every 2023 price in hand

The second is the headline. The first is what keeps the comparison honest, and the gap
between them is what one more year of history bought.

Nothing about the second is a boundary violation. Holding 2023 out of a fit was needed
only while 2023 was the thing being scored; here the thing being scored is 2024-25, and
2023 is simply history.
"""

from __future__ import annotations

import pandas as pd

from scripts.train import record                     # same file, same stamping, same rules
from src import config as cfg
from src import evaluate as E
from src import features as F
from src import models as M

SPLIT = "test"                                       # what every row produced here is labelled


# ── The three blocks, unchanged ───────────────────────────────────────────────
# Thin on purpose. `cfg.split` owns the boundary arithmetic and every script goes through
# it rather than slicing on its own, which is what keeps Contract 2 in one file. The only
# job here is to drop incomplete rows first, so every recipe below is fitted and scored on
# the same hours.

def data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """The training years, the validation year, and the years held back."""
    return cfg.split(F.complete_rows(F.build()))     # complete rows only, then split


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
# Then the same two estimators are fitted over each of the two histories. They are built
# inside the loop rather than outside it, which makes no difference to the result —
# `M.fit` hands back the object it was given, and each row is scored before the next fit
# replaces it. Verified by sharing them: every test still passed.

def run(train: pd.DataFrame, valid: pd.DataFrame,
        holdout: pd.DataFrame) -> list[dict]:
    """Five rows: the benchmark, then each estimator over each history."""
    benchmark = M.naive_forecast(holdout)            # a lookup, not a fit
    actual = holdout[F.TARGET]                       # the prices that actually cleared

    rows = [E.score("naive", SPLIT, benchmark, benchmark, actual)]   # must come out at 1.000
    for history in (train, pd.concat([train, valid])):
        for name, estimator in (("linear", M.linear()), ("gbm", M.gbm())):
            model = M.fit(estimator, history)
            rows.append(E.score(label(name, history), SPLIT,
                                M.forecast(model, holdout), benchmark, actual))

    return rows


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

    rows = run(train, valid, holdout)
    print(E.table(rows))
    print(f"\nHeadline: {rows[-1]['model']} at rMAE {rows[-1]['rmae']:.3f} — "
          f"the recipe that uses every year available before delivery.")

    print("\n" + reading_note(record(rows), len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
