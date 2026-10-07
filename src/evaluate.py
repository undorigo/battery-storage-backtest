"""How good was it? — the scores that let one forecast be compared with another.

Nothing here knows what a model is.  It takes two columns of numbers, one predicted
and one that actually happened, and returns a figure.  That separation is on
purpose: a scoring rule that knows which model it is scoring is a scoring rule that
can flatter one of them.

The one rule that governs all of it: a model and the benchmark it is judged against
must be scored on the same hours.  `aligned` is where that is enforced, which is why
every function here starts by calling it.
"""

from __future__ import annotations

import math

import pandas as pd


# ── Lining the two columns up ─────────────────────────────────────────────────
# Every score below compares two series hour by hour.  If they cover different
# hours, pandas matches them by timestamp and puts a blank in the gaps — and a
# blank quietly drops out of an average, so the score comes back looking correct
# and is computed over fewer hours than you think.  Nothing errors.
#
# The inner join is the part that earns its place today: a forecast scoped to one
# split, compared against the whole price history, is an easy mistake and a silent
# one.  The empty check catches a timezone or index bug that leaves no overlap at
# all.  The `dropna` is precaution — measured on 23 September, no forecast on the
# scored rows carries a blank — kept because it costs one line and the models do
# not agree on what they can reach: a gradient-boosted tree predicts happily
# through missing features where a linear fit refuses.

def aligned(*series: pd.Series) -> tuple[pd.Series, ...]:
    """Every series passed in, trimmed to the hours all of them cover.

    Takes two or three.  Two for a plain error, three when a model and a benchmark
    are being compared — and in that case all three have to be trimmed *together*,
    or the two errors end up measured over different hours and the ratio between
    them describes nothing.

    Returns one series per argument, in the order given.
    """
    if len(series) < 2:
        raise ValueError("aligned needs at least two series to line up")

    # `inner` is not load-bearing: an outer join followed by `dropna` leaves exactly
    # the same rows, because a timestamp only one series carries arrives as a blank
    # and is dropped anyway.  Kept for the smaller intermediate frame, and because
    # it states the intent — mutating it to `outer` changes nothing, verified.
    named = [s.rename(str(i)) for i, s in enumerate(series)]    # positions, so names cannot clash
    frame = pd.concat(named, axis=1, join="inner").dropna()
    if frame.empty:
        raise ValueError("predicted and actual share no hours — check the index and timezone")
    return tuple(frame[str(i)] for i in range(len(series)))


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
# Two details that are easy to get wrong.  The absolute value matters because a
# miss of 10 too high and a miss of 10 too low are both misses of 10, and adding
# them signed would cancel to nothing.  And the trim has to come first, or pandas
# matches the two by timestamp, blanks the hours only one of them covers, and the
# average quietly runs over fewer hours than you think.

def mae(predicted: pd.Series, actual: pd.Series) -> float:
    """Average size of a miss, in EUR/MWh. Lower is better; zero is perfect."""
    p, a = aligned(predicted, actual)
    return float((p - a).abs().mean())


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
# Note what this does *not* divide by.  Dividing each miss by the price it missed
# (*mean absolute percentage error*) breaks here, because our prices pass through
# zero.  This divides one average miss by another, and an average of absolute
# values is never negative — so negative prices cannot reach the denominator.
#
# All three series are trimmed together, and that is the whole point of the
# function.  Score the model and the benchmark separately and each is measured on
# whatever hours it happens to reach: the naive rule has a value for the opening
# week where a fitted model has none, so it would collect a free, easy hour and
# the ratio would move without either forecast changing.

def rmae(predicted: pd.Series, benchmark: pd.Series, actual: pd.Series) -> float:
    """The model's error as a fraction of the benchmark's. Below 1 is a win."""
    p, b, a = aligned(predicted, benchmark, actual)     # one trim, so one set of hours
    return mae(p, a) / mae(b, a)


# ── Is the gap real? — Diebold-Mariano ───────────────────────────────────────
# A lower rMAE is not evidence on its own: in 2023 the tree beat the line by 1.65
# EUR/MWh a day on average, while the daily gap swung by about 9.6.  The test asks
# whether the average stands out from the swing.
#
# Days, not hours, are the evidence.  All 24 hours of a day are forecast at once,
# so one hour's gap predicts the next (0.79 in 2023), and 8,759 hours would pretend
# to far more evidence than there is.  As in the field's reference code
# (epftoolbox, Lago et al. 2021) each day collapses to one number: the first
# forecast's average miss minus the second's.  One-sided, as there: a small p says
# the second forecast is more accurate.  A large p means *cannot tell*, not *same*.
#
# One departure, measured rather than assumed.  epftoolbox treats days as
# unconnected; in 2023 one day's gap echoes into the next (0.25, gone by day four),
# which makes the plain test too confident.  So the spread is widened by the echo
# over the past `lags` days (*Newey-West*).  `lags=0` is epftoolbox exactly.

def dm(first: pd.Series, second: pd.Series, actual: pd.Series, lags: int = 7) -> float:
    """One-sided p-value that `second` is more accurate than `first`, from daily gaps."""
    f, s, a = aligned(first, second, actual)            # one set of hours for both
    hourly = (f - a).abs() - (s - a).abs()              # positive where second missed less
    d = hourly.groupby(hourly.index.normalize()).mean().to_numpy()   # one number per day
    n = len(d)
    c = d - d.mean()
    var = c @ c / n                                     # the plain spread, as epftoolbox
    for k in range(1, lags + 1):
        echo = c[k:] @ c[:-k] / n                       # how gaps k days apart move together
        var += 2 * (1 - k / (lags + 1)) * echo          # weight fades with distance
    stat = d.mean() / math.sqrt(var / n)
    return 0.5 * math.erfc(stat / math.sqrt(2))         # upper tail of the normal curve


# ── Reporting ─────────────────────────────────────────────────────────────────
# Plumbing, already written.  One row per forecast per split, so a table can be
# printed, pasted into the work log, and compared against the next run.
#
# `n` is carried deliberately.  Two scores computed on different numbers of hours
# are not comparable, and the count is the only way to notice that has happened.
#
# The trim happens once, here, and the trimmed series are what get scored — so the
# three numbers in a row all describe the same hours.  Without that, `n` would be
# auditing a different set than the `rmae` beside it, which is worse than having no
# audit at all.

def score(name: str, split: str, predicted: pd.Series, benchmark: pd.Series,
          actual: pd.Series) -> dict:
    """One row: what was forecast, on which split, and how it did."""
    p, b, a = aligned(predicted, benchmark, actual)
    return {
        "model": name,
        "split": split,
        "n": len(p),
        "mae": mae(p, a),
        "rmae": rmae(p, b, a),                          # already trimmed; the second trim is a no-op
    }


def table(rows: list[dict]) -> str:
    """Render scored rows as markdown, ready to paste into the work log."""
    head = ["Model", "Split", "Hours", "MAE", "rMAE"]
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        out.append(f"| {r['model']} | {r['split']} | {r['n']:,} | "
                   f"{r['mae']:.2f} | {r['rmae']:.3f} |")
    return "\n".join(out)
