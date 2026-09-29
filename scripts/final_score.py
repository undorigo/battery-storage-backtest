"""The number a stage ends on — read once, from years nothing has been tuned against.

`train.py` runs as often as you like, because validation exists to be looked at. This
does not. Contract 2 allows the held-back years to be scored **once per stage**, and the
reason is not ceremony: every time results are read and something is changed in response,
those results stop being a fair exam. Read them repeatedly and the final number quietly
becomes the best of several attempts rather than an honest one.

So this lives in its own file, with its own command, and `train.py` has no path to the
years it reads. That separation is the enforcement — a promise in a docstring would not
survive a hurried afternoon.

**What the models learn from here is deliberately not what they learned from in
`train.py`.** There the fit stopped at the end of 2022 so that validation stayed unseen.
Here validation has already done its job — it chose between the models — so holding it
out would waste a year for nothing. Every 2023 price was public long before any 2024
delivery hour, so Contract 1 is untouched.

One consequence, stated rather than buried: the number this produces comes from a
different recipe than the validation number, so the two are not directly comparable.
"""

from __future__ import annotations

import pandas as pd

from scripts.train import record                     # same file, same stamping, same rules
from src import config as cfg
from src import evaluate as E
from src import features as F
from src import models as M

SPLIT = "test"                                       # what every row produced here is labelled


# ── Everything knowable, and the years held back ──────────────────────────────
# `cfg.split` returns three frames. Here the first two are joined rather than one being
# discarded, which is the whole difference from `train.py` — and it is the line worth
# reading twice, because joining the wrong pair is how a held-back year leaks into a fit.
#
# The join is in time order and the frames never overlap, so no row can appear twice.

def data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Everything published before 2024, and the held-back years themselves."""
    frame = F.complete_rows(F.build())               # drop any row with a blank anywhere
    train, valid, holdout = cfg.split(frame)
    return pd.concat([train, valid]), holdout        # history to learn from, years to be judged on


# ── The scored rows ───────────────────────────────────────────────────────────
# Identical in shape to `train.py`, deliberately: the same benchmark, the same order, the
# same scoring call. If the two disagreed about how a score is built, the two numbers
# could not be set beside each other at all — and comparing them is most of the point.

def run(history: pd.DataFrame, holdout: pd.DataFrame) -> list[dict]:
    """Fit on everything knowable, forecast the held-back years, score. Benchmark first."""
    benchmark = M.naive_forecast(holdout)            # a lookup, not a fit: no history needed
    actual = holdout[F.TARGET]                       # the prices that actually cleared

    rows = [E.score("naive", SPLIT, benchmark, benchmark, actual)]   # must come out at 1.000
    for name, estimator in (("linear", M.linear()), ("gbm", M.gbm())):
        model = M.fit(estimator, history)            # 2018 through 2023, all of it
        rows.append(E.score(name, SPLIT, M.forecast(model, holdout), benchmark, actual))

    return rows


# ── Running it ────────────────────────────────────────────────────────────────
# Prints how many held-back rows the file already carries. Not a lock — there are honest
# reasons to run this again, such as a bug in this very script. But a second reading of
# the held-back years should never happen without anyone noticing it happened, and the
# stamped record is what makes that visible rather than deniable.

def main() -> int:
    try:
        history, holdout = data()
    except FileNotFoundError as exc:
        print(exc)
        print("\nNo cached data. Run `just pull` first.")
        return 2

    days = holdout.index.tz_convert(cfg.TZ_MARKET)   # delivery days are market-local
    print(f"Fitted on {len(history):,} rows through 2023  ·  "
          f"scoring {len(holdout):,} held-back rows "
          f"({days.min():%Y-%m-%d} to {days.max():%Y-%m-%d})\n")

    rows = run(history, holdout)
    print(E.table(rows))

    recorded = record(rows)
    already = int((recorded["split"] == SPLIT).sum())
    note = ("This is the first reading." if already == len(rows)
            else "The held-back years have been read before — check the commit column.")
    print(f"\n{already} held-back rows now recorded. {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
