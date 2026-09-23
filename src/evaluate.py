"""How good was it? — the scores that let one forecast be compared with another.

Nothing here knows what a model is.  It takes two columns of numbers, one predicted
and one that actually happened, and returns a figure.  That separation is on
purpose: a scoring rule that knows which model it is scoring is a scoring rule that
can flatter one of them.

Two functions carry the ideas and are yours to write.  The rest is plumbing.

Run `just test` while you work — `tests/test_evaluate.py` fails until they are right,
and each failure says what it expected.
"""

from __future__ import annotations

import pandas as pd


# ── Lining the two columns up ─────────────────────────────────────────────────
# Every score below compares two series hour by hour.  If they cover different
# hours, pandas will happily line them up and put a blank in the gaps — and a
# blank quietly drops out of an average, so the score comes back looking fine and
# is computed on fewer hours than you think.
#
# So the comparison is made explicit once, here, and every score starts with it.

def aligned(predicted: pd.Series, actual: pd.Series) -> tuple[pd.Series, pd.Series]:
    """The hours both series actually cover, in the same order, with no blanks."""
    both = pd.concat([predicted.rename("p"), actual.rename("a")], axis=1, join="inner")
    both = both.dropna()
    if both.empty:
        raise ValueError("predicted and actual share no hours — check the index and timezone")
    return both["p"], both["a"]


# ── Mean absolute error ───────────────────────────────────────────────────────
# The average size of a miss, in euros per megawatt-hour, ignoring whether the
# miss was high or low.  Being 10 too expensive and 10 too cheap both count as 10.
#
# Why this rather than the other usual choices.  Squaring the errors first (*root
# mean squared error*) lets a handful of wild hours dominate the score, and this
# market has hours at 900 and at minus 500.  Dividing by the true price (*mean
# absolute percentage error*) is worse still: our prices pass through zero, and
# dividing by something near zero produces a meaningless number.
#
# So: plain average of the absolute misses.
#
# YOUR TURN.  Three steps:
#   1. line the two series up with `aligned` above
#   2. take the difference, then the absolute value of it
#   3. return the mean, as a plain float

def mae(predicted: pd.Series, actual: pd.Series) -> float:
    """Average size of a miss, in EUR/MWh. Lower is better; zero is perfect."""
    raise NotImplementedError("mae: see the notes above this line")


# ── Relative mean absolute error ──────────────────────────────────────────────
# A bare MAE cannot be judged.  Is 15 EUR/MWh good?  Against 2019 prices it is
# poor; against 2022 prices it is excellent.  The number has no scale of its own,
# and it changes meaning as the market changes — which is fatal here, because this
# market changed three times in seven years.
#
# So every score is divided by what a rule with no modelling in it achieves:
#
#       rMAE  =  the model's MAE  /  the benchmark's MAE
#
#   below 1  the model beats doing nothing clever
#   exactly 1  it matched it
#   above 1  it is worse than doing nothing clever, which does happen
#
# The benchmark is the denominator, which is why it gets built first.  Build the
# model first and you have a numerator with nothing underneath it — and a strong
# pull towards choosing a denominator that flatters it.
#
# YOUR TURN.  Two steps:
#   1. work out the MAE of the model and the MAE of the benchmark, on the *same*
#      actual prices, using the function you just wrote
#   2. return the first divided by the second

def rmae(predicted: pd.Series, benchmark: pd.Series, actual: pd.Series) -> float:
    """The model's error as a fraction of the benchmark's. Below 1 is a win."""
    raise NotImplementedError("rmae: see the notes above this line")


# ── Reporting ─────────────────────────────────────────────────────────────────
# Plumbing, already written.  One row per forecast per split, so a table can be
# printed, pasted into the work log, and compared against the next run.
#
# `n` is carried deliberately.  Two scores computed on different numbers of hours
# are not comparable, and the count is the only way to notice that has happened.

def score(name: str, split: str, predicted: pd.Series, benchmark: pd.Series,
          actual: pd.Series) -> dict:
    """One row: what was forecast, on which split, and how it did."""
    p, a = aligned(predicted, actual)
    return {
        "model": name,
        "split": split,
        "n": len(p),
        "mae": mae(predicted, actual),
        "rmae": rmae(predicted, benchmark, actual),
    }


def table(rows: list[dict]) -> str:
    """Render scored rows as markdown, ready to paste into the work log."""
    head = ["Model", "Split", "Hours", "MAE", "rMAE"]
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        out.append(f"| {r['model']} | {r['split']} | {r['n']:,} | "
                   f"{r['mae']:.2f} | {r['rmae']:.3f} |")
    return "\n".join(out)
