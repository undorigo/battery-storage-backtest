"""How far might tomorrow's price land from LEAR's forecast? — stage 3, in one command.

Walks LEAR forward from mid-2022 so every day of 2023 has 182 real forecasts behind
it, turns LEAR's one number per hour into 99 percentiles two ways (QRA, conformal),
and scores both ranges on 2023 by pinball loss and coverage.  Given several
windows, it also scores their average, the range stage 3 chose.

Nothing here decides anything.  `models.py` holds LEAR, QRA and conformal;
`evaluate.py` the scores.  This file puts them in order and writes down what came out.

**The test years are unreachable from here**, as from `train.py`: they are dropped at
the first step, and a range for 2024–25 belongs to the reading that closes the stage.
"""

from __future__ import annotations

import argparse
import time

import pandas as pd

from scripts.train import data, day_rows, git_commit, record   # same rows, same stamping
from src import config as cfg
from src import evaluate as E
from src import features as F
from src import models as M
from src import tracking as TR


# ── The days LEAR must forecast first ─────────────────────────────────────────
# QRA learns how far LEAR misses, so its dots must be forecasts LEAR really made.
# For 1 January 2023 to have a full window, LEAR has to walk the 182 days before
# it as well: 3 July to 31 December 2022.  Those are training days, forecast each
# from the days before it, so no validation day is learned from early.
#
# A day is forecast only if all its clues are present.  On 16 October 2026 every
# day from 3 July 2022 to the end of 2023 was; a gap would leave a window short.

START = pd.Timestamp(cfg.TRAIN_END) - pd.Timedelta(days=M.QRA_WINDOW - 1)   # 2022-07-03


def walk_days(table: pd.DataFrame, start: pd.Timestamp = START,
              end: str = cfg.VALID_END) -> pd.DatetimeIndex:
    """The days LEAR forecasts: 182 before 2023, then 2023 (unless told), clues complete."""
    days = table.loc[(table.index >= start) & (table.index <= pd.Timestamp(end))]
    ready = days[F.day_feature_columns(table)].notna().all(axis=1)
    return days.index[ready]


def prices(table: pd.DataFrame) -> pd.Series:
    """The real prices, on the grid, read from the day table LEAR learnt from."""
    answers = table[F.day_answer_columns(table)]
    return F.unfold(answers.set_axis([int(c[-2:]) for c in answers.columns], axis=1))


# ── Two ranges, scored on the same hours ──────────────────────────────────────
# QRA and conformal see the same LEAR forecasts, prices and window, so their
# scores differ only by method.  QRA's crossed lines are sorted before scoring
# and counted; conformal cannot cross, so its count is a check that reads 0.
#
# Each row carries its window, because the record's header is fixed once written
# and a later comparison of shorter windows must be told apart from this one.
#
# Fitting and scoring are separate steps so that several windows' lines can be
# averaged before anything is scored.  The average's window reads "28+56+91+182",
# and an hour counts as crossed in it if any window's lines crossed there.

SHARES = (50, 80, 90)                                    # central bands whose coverage is reported
METHODS = {"qra": M.qra, "conformal": M.conformal}


def lines(lear: pd.Series, actual: pd.Series, days: pd.DatetimeIndex, window: int,
          levels: tuple[int, ...] = M.PERCENTILES) -> dict[str, tuple[pd.DataFrame, pd.Series]]:
    """Each method's lines on `days`, sorted, and which hours had crossed."""
    return {method: M.untangle(make(lear, actual, days, window, levels))
            for method, make in METHODS.items()}


def averaged(per_window: list[dict]) -> dict[str, tuple[pd.DataFrame, pd.Series]]:
    """Each method's lines averaged over the windows; crossed where any window crossed."""
    return {method: (M.average([found[method][0] for found in per_window]),
                     pd.concat([found[method][1] for found in per_window], axis=1).any(axis=1))
            for method in METHODS}


def score(found: dict, lear: pd.Series, actual: pd.Series, window: int | str,
          split: str = "valid") -> tuple[list[dict], dict[str, pd.DataFrame]]:
    """One row per method, and each method's hourly table as scored."""
    rows, kept = [], {}
    for method, (q, crossed) in found.items():
        row = {"method": method, "split": split, "n": len(q),
               "pinball": E.pinball(q, actual)}
        row.update({f"cover{s}": E.coverage(q, actual, s) for s in SHARES})
        row.update({"crossed": int(crossed.sum()), "window": window})
        rows.append(row)
        kept[method] = pd.concat([actual.rename("actual"), lear.rename("lear"), q],
                                 axis=1, join="inner")   # the scored hours only
    return rows, kept


def runs(lear: pd.Series, actual: pd.Series, days: pd.DatetimeIndex, windows: list[int],
         levels: tuple[int, ...] = M.PERCENTILES):
    """Each window's (label, rows, tables) as it finishes, then their average if several."""
    per_window = []
    for window in windows:
        per_window.append(lines(lear, actual, days, window, levels))
        yield window, *score(per_window[-1], lear, actual, window)   # recorded before the next
    if len(windows) > 1:
        yield named(windows), *score(averaged(per_window), lear, actual, named(windows))


def named(windows: list[int]) -> str:
    """An average's window, as recorded: "28+56+91+182"."""
    return "+".join(str(w) for w in windows)


def table(rows: list[dict]) -> str:
    """Render the rows as markdown, ready for the work log."""
    head = ["Method", "Hours", "Pinball", "50 %", "80 %", "90 %", "Crossed", "Window"]
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        out.append(f"| {r['method']} | {r['n']:,} | {r['pinball']:.3f} | {r['cover50']:.3f} | "
                   f"{r['cover80']:.3f} | {r['cover90']:.3f} | {r['crossed']:,} | {r['window']} |")
    return "\n".join(out)


# ── Running it ────────────────────────────────────────────────────────────────
# LEAR's 2023 forecasts here come from the same model on the same days as `just
# train daily`, and LEAR is deterministic, so its rMAE is printed as a check:
# it must read what `scores.csv` already holds for that run (0.504, last week's
# 0.429).  Printed, not recorded, because that row is already in the record.
#
# Several windows can share one LEAR walk, the slow half.  None may exceed 182:
# the walk starts 182 days before 2023, so a longer window would quietly be short
# through early 2023 and its scores would describe a different window.

def windows(argv: list[str] | None = None) -> list[int]:
    """The window lengths asked for, 182 if none; refuses any the walk cannot fill."""
    parser = argparse.ArgumentParser(description="Score QRA and conformal ranges on 2023.")
    parser.add_argument("windows", nargs="*", type=int, default=[M.QRA_WINDOW],
                        help="days of dots per fit, at most 182")
    asked = parser.parse_args(argv).windows
    if any(not 1 <= w <= M.QRA_WINDOW for w in asked):
        parser.error(f"windows run from 1 to {M.QRA_WINDOW} days: LEAR's walk starts "
                     f"{M.QRA_WINDOW} days before 2023")
    return asked


def main(argv: list[str] | None = None) -> int:
    asked = windows(argv)
    try:
        history = day_rows()                             # training and validation days only
        _, valid = data()                                # hourly 2023, for the benchmarks
    except FileNotFoundError as exc:
        print(exc)
        print("\nNo cached data. Run `just pull` first.")
        return 2

    days = walk_days(history)
    scored = days[days > pd.Timestamp(cfg.TRAIN_END)]    # 2023: the days the ranges are scored on
    print(f"LEAR walks {len(days)} days ({days.min():%Y-%m-%d} to {days.max():%Y-%m-%d}); "
          f"ranges scored on {len(scored)}\n")

    started = time.perf_counter()
    lear = M.lear_walk_forward(history, days)
    print(f"LEAR: {time.perf_counter() - started:.0f} s")
    actual = prices(history)
    check = E.score("lear", "valid", lear, M.naive_forecast(valid), actual,
                    field=M.field_naive(valid))
    print(f"LEAR on 2023, the check: rMAE {check['rmae_field']:.3f} "
          f"(last week's {check['rmae']:.3f}), {check['n']:,} hours\n")

    started = time.perf_counter()
    for window, rows, kept in runs(lear, actual, scored, asked):   # each window, the same LEAR
        print(f"Ranges, {window} days: {time.perf_counter() - started:.0f} s\n")
        print(table(rows))

        recorded = record(rows, cfg.QUANTILE_SCORES)
        print(f"\nAppended {len(rows)} rows to {cfg.QUANTILE_SCORES.relative_to(cfg.ROOT)} "
              f"— {len(recorded):,} recorded in total.")

        params = {"window": window, "levels": "1-99", "lear_window": M.WINDOW_DAYS,
                  "lear_from": f"{days.min():%Y-%m-%d}", "commit": git_commit()}
        ids = {row["method"]: TR.log_range(row, kept[row["method"]], params) for row in rows}
        print("Logged to MLflow: " + ", ".join(f"{m} {r[:8]}" for m, r in ids.items()) + "\n")
        started = time.perf_counter()                    # the next window's clock
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
