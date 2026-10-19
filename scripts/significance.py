"""Is the gap real? — every p-value the README states, regenerated in one command.

Reads the hourly forecasts that `just train` and `just quantiles` left in MLflow and
runs Diebold-Mariano on each comparison the README makes, on pinball loss for ranges.  Writes nothing: `scores.csv` stays the record,
and this only re-reads what the runs already kept.

**Each side is named by what its run states, not by a run id.**  Ids differ from one
clone to the next; "the newest daily tree" does not.  Newest means a rerun at a later
commit replaces the earlier reading, so each row prints the commits it read, and a
p-value that moved because its run moved is visible rather than silent.
"""

from __future__ import annotations

import pandas as pd

from src import evaluate as E
from src import tracking as TR


# ── The comparisons the README makes ──────────────────────────────────────────
# One line per claim, in the README's order.  Each is (label, first, second), and
# the test asks whether `second` is more accurate than `first`; the reverse is
# printed beside it, because "cannot tell" has to be read in both directions.
#
# A claim about one change pins both sides to their commits, so a later rerun
# cannot quietly stand in for the run the claim was made on.  Every side also names
# its split: the held-back reading logs runs with the same models and schedules, and
# without the split the newest run could silently be a 2024-25 one.

LEAR = {"model": "lear", "refit": "daily", "lear_window": "1092"}

VALIDATION = [
    ("line, once → monthly", {"model": "linear", "refit": "once"},
     {"model": "linear", "refit": "monthly"}),
    ("line, monthly → daily", {"model": "linear", "refit": "monthly"},
     {"model": "linear", "refit": "daily"}),
    ("tree, once → monthly", {"model": "gbm", "refit": "once"},
     {"model": "gbm", "refit": "monthly"}),
    ("tree, monthly → daily", {"model": "gbm", "refit": "monthly"},
     {"model": "gbm", "refit": "daily"}),
    ("daily: tree → LEAR", {"model": "gbm", "refit": "daily"}, LEAR),
    ("daily: line → LEAR", {"model": "linear", "refit": "daily"}, LEAR),
    ("LEAR: every year → 1,092 days",
     {"model": "lear_all", "refit": "daily", "lear_window": "all"}, LEAR),
    *[(f"holidays, {name} {refit}: without → with",
       {"model": model, "refit": refit, "commit": before},
       {"model": model, "refit": refit, "commit": "d1f6252"})
      for name, model in (("line", "linear"), ("tree", "gbm"))
      for refit, before in (("once", "9bb03ff"), ("monthly", "9bb03ff"), ("daily", "e8792c6"))],
    ("holidays, LEAR: without → with", {**LEAR, "commit": "4cfc6b4"},
     {**LEAR, "commit": "d1f6252"}),
]

# Stage 2's one reading of 2024-25: does what 2023 showed hold on untouched years?
HELD_BACK = [
    ("held back: line frozen → daily", {"model": "linear 2018-2023", "refit": "once"},
     {"model": "linear daily", "refit": "daily"}),
    ("held back: tree frozen → daily", {"model": "gbm 2018-2023", "refit": "once"},
     {"model": "gbm daily", "refit": "daily"}),
    ("held back: line → tree, daily", {"model": "linear daily", "refit": "daily"},
     {"model": "gbm daily", "refit": "daily"}),
    ("held back: tree → LEAR, daily", {"model": "gbm daily", "refit": "daily"},
     {"model": "lear daily", "refit": "daily"}),
    ("held back: line → LEAR, daily", {"model": "linear daily", "refit": "daily"},
     {"model": "lear daily", "refit": "daily"}),
]

COMPARISONS = ([(label, {**a, "split": "valid"}, {**b, "split": "valid"})
                for label, a, b in VALIDATION]
               + [(label, {**a, "split": "test"}, {**b, "split": "test"})
                  for label, a, b in HELD_BACK])


def command(side: dict) -> str:
    """The `just` call that produces a run like this one, from its commit if pinned."""
    if side.get("split") == "test":
        return "just final-score"                     # once per stage: think before running it
    call = f"just train {side['refit']}" + (" all" if side.get("lear_window") == "all" else "")
    return f"git checkout {side['commit']} && {call}" if "commit" in side else call


# ── One comparison ────────────────────────────────────────────────────────────
# Two runs may cover different hours (an 8,759-hour run against an 8,760-hour one),
# so both forecasts, the benchmark and the actual are trimmed together first.  Both
# rMAEs are then computed on those shared hours, so the two sides sit one exam and
# the p-value and the scores beside it describe the same thing.
#
# The rMAEs divide by the field's benchmark when the first run stored it, and by
# last week's price otherwise: runs from before the close of stage 2 never kept the
# field's, and a claim pinned to one of them cannot be rerun to add it.  Each row
# says which, so an old ratio is never read as a new one.  The p-value uses no
# benchmark at all, so it is the same either way.

def compare(first: dict, second: dict, **where) -> dict:
    """rMAE of each side, p both ways, and which runs were read. Raises if one is missing."""
    found = []
    for side in (first, second):
        run = TR.latest(**where, **side)
        if run is None:
            raise LookupError(f"no {side['model']} run with refit={side['refit']}: "
                              f"run `{command(side)}`")
        params, forecasts = TR.read(run, **where)
        found.append((params["commit"], forecasts[side["model"]], forecasts))
    (c1, f1, frame), (c2, f2, _) = found
    field = "naive_field" in frame                              # did this run keep the field's?
    a, b, naive, actual = E.aligned(f1, f2, frame["naive_field" if field else "naive"],
                                    frame["actual"])            # one exam
    return {"first": E.rmae(a, naive, actual), "second": E.rmae(b, naive, actual),
            "divided_by": "field" if field else "last week",
            "p_second_better": E.dm(a, b, actual), "p_first_better": E.dm(b, a, actual),
            "hours": len(actual), "commits": f"{c1} / {c2}"}


# ── The range comparison: stage 3 ─────────────────────────────────────────────
# The same question for ranges: does QRA's lower pinball loss stand out from the
# day-to-day swing?  Read from the runs `just quantiles` left, which keep all 99
# percentiles per hour, so the test needs no refit.  Both sides are trimmed to the
# hours both cover and scored there, as `compare` does for point forecasts.

def _range(model: str, window: int | str, split: str = "valid") -> dict:
    return {"model": model, "window": str(window), "split": split}


AVERAGE = "28+56+91+182"                                        # stage 3's chosen range


RANGE_COMPARISONS = [
    ("ranges: conformal → QRA", _range("conformal", 182), _range("qra", 182)),
    # The windows, 16 Oct: does forgetting faster keep the bands in step with the market?
    ("QRA: 182 → 91 days", _range("qra", 182), _range("qra", 91)),
    ("QRA: 56 → 91 days", _range("qra", 56), _range("qra", 91)),
    ("conformal: 182 → 91 days", _range("conformal", 182), _range("conformal", 91)),
    ("91 days: conformal → QRA", _range("conformal", 91), _range("qra", 91)),
    # The average, 19 Oct: the field's recipe against the best single window.
    ("QRA: 91 days → average", _range("qra", 91), _range("qra", AVERAGE)),
    ("average: conformal → QRA", _range("conformal", AVERAGE), _range("qra", AVERAGE)),
    # Stage 3's one reading of 2024-25.
    ("held back, average: conformal → QRA", _range("conformal", AVERAGE, "test"),
     _range("qra", AVERAGE, "test")),
]


def compare_ranges(first: dict, second: dict, **where) -> dict:
    """Pinball of each side on shared hours, p both ways, and which runs were read."""
    found = []
    for side in (first, second):
        run = TR.latest(**where, **side)
        if run is None:
            command = "just final-score ranges" if side["split"] == "test" else "just quantiles"
            raise LookupError(f"no {side['model']} run with window={side['window']}: "
                              f"run `{command}`")
        params, kept = TR.read_range(run, **where)
        found.append((params["commit"], kept))
    (c1, k1), (c2, k2) = found
    hours = k1.index.intersection(k2.index)                     # one exam
    levels = [c for c in k1.columns if isinstance(c, int)]      # the percentile columns
    q1, q2, actual = k1.loc[hours, levels], k2.loc[hours, levels], k1.loc[hours, "actual"]
    return {"first": E.pinball(q1, actual), "second": E.pinball(q2, actual),
            "p_second_better": E.dm_pinball(q1, q2, actual),
            "p_first_better": E.dm_pinball(q2, q1, actual),
            "hours": len(hours), "commits": f"{c1} / {c2}"}


# ── Running it ────────────────────────────────────────────────────────────────

def main() -> int:
    print("| Comparison | rMAE first | rMAE second | Divided by | p second better "
          "| p first better | Hours | Commits |")
    print("|---|---|---|---|---|---|---|---|")
    missing = 0
    for label, first, second in COMPARISONS:
        try:
            r = compare(first, second)
        except LookupError as exc:
            print(f"| {label} | — | — | — | — | — | — | {exc} |")
            missing += 1
            continue
        print(f"| {label} | {r['first']:.3f} | {r['second']:.3f} | {r['divided_by']} "
              f"| {r['p_second_better']:.2g} "
              f"| {r['p_first_better']:.2g} | {r['hours']:,} | {r['commits']} |")

    print("\n| Comparison | Pinball first | Pinball second | p second better "
          "| p first better | Hours | Commits |")
    print("|---|---|---|---|---|---|---|")
    for label, first, second in RANGE_COMPARISONS:
        try:
            r = compare_ranges(first, second)
        except LookupError as exc:
            print(f"| {label} | — | — | — | — | — | {exc} |")
            missing += 1
            continue
        print(f"| {label} | {r['first']:.3f} | {r['second']:.3f} | {r['p_second_better']:.2g} "
              f"| {r['p_first_better']:.2g} | {r['hours']:,} | {r['commits']} |")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
