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

**Stage 3's reading is `just final-score ranges`**, a separate run of this file so that
reading the ranges does not read stage 2's forecasts a second time.  **Stage 4's is `just
final-score battery`**: the battery planned on what those two readings stored.

**`just final-score 2026` reads the ten months after the test years**, which no model and
no decision has seen: every day forecast through `scripts/tomorrow.py`, the code the
evening run calls, then planned and settled on stage 4's list, once.
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from scripts import backtest as SB                         # stage 4's battery, same code as on 2023
from scripts import quantiles as Q                         # stage 3's ranges, same code as on 2023
from scripts import tomorrow as T                          # one day's forecast, as the evening run makes it
from scripts.train import git_commit, lear_days, record   # same stamping, same rules
from src import backtest as BT
from src import config as cfg
from src import data as D
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
# The benchmarks come first because they are the denominators every other row divides by,
# and they are lookups of earlier prices — a benchmark needs no training at all.
#
# The daily rows walk forward over the whole history, held-back years included, because
# `walk_forward` only ever hands a refit the hours before the day it forecasts.  The frozen
# rows are fitted once on every year before 2024.  Then the same-exam rule from `train.py`:
# every forecast is scored on the hours all of them cover, LEAR's skipped days included.

def run(train: pd.DataFrame, valid: pd.DataFrame, holdout: pd.DataFrame,
        table: pd.DataFrame | None = None) -> tuple[list[dict], pd.DataFrame]:
    """Score rows, benchmark first, and the hourly forecasts. Without `table`, no LEAR."""
    forecasts = pd.DataFrame({"actual": holdout[F.TARGET],
                              "naive": M.naive_forecast(holdout),      # lookups, not fits
                              "naive_field": M.field_naive(holdout)})

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
    rows = [E.score(name, SPLIT, forecasts[name], forecasts["naive"], forecasts["actual"],
                    field=forecasts["naive_field"])
            for name in forecasts.columns.drop("actual")]   # each benchmark reads 1.000 on its own ratio
    return rows, forecasts


# ── Saying whether this was the first look ────────────────────────────────────
# Not a lock. There are honest reasons to run this again — a bug in this very script is
# one. But a second reading of the held-back years should never happen without anyone
# noticing that it happened.
#
# The stamped record is the evidence; this sentence is what a person actually reads. It is
# a separate function only so it can be tested, because an enforcement message that
# quietly says the wrong thing is worse than none at all.

def reading_note(recorded: pd.DataFrame, just_written: int, split: str = SPLIT) -> str:
    """Whether these years, the held-back ones unless told, had been read before this run."""
    already = int((recorded["split"].astype(str) == split).sum())   # a CSV of only 2026 reads it as a number
    name, years = ("held-back", "The held-back years have") if split == SPLIT else (split, f"{split} has")
    if already == just_written:
        return f"{already} {name} rows recorded. This is the first reading."
    return (f"{already} {name} rows recorded, {just_written} of them from this run. "
            f"{years} been read before — check the commit column.")


# ── Stage 3: the ranges, read once ────────────────────────────────────────────
# The range chosen on 2023 (19 Oct 2026): QRA and conformal around LEAR, each averaged
# over four windows.  LEAR walks from 182 days before 2024, so the first held-back day's
# longest window holds forecasts LEAR really made, as `just quantiles` does for 2023.
#
# Only the two averages are scored.  Each window's own held-back score would invite
# choosing the window again on the years held back, which is the choice 2023 was for.
# Every range at D learns from days before D, held-back days included once past.

RANGE_WINDOWS = [28, 56, 91, 182]                    # chosen on 2023: the field's average
RANGE_START = pd.Timestamp(cfg.VALID_END) - pd.Timedelta(days=max(RANGE_WINDOWS) - 1)   # 2023-07-03


def range_walk(table: pd.DataFrame) -> tuple[pd.DatetimeIndex, pd.Series]:
    """The days LEAR walks for the ranges, and its forecast for each."""
    days = Q.walk_days(table, RANGE_START, cfg.TEST_END)
    return days, M.lear_walk_forward(table, days)


def ranges(lear: pd.Series, actual: pd.Series, days: pd.DatetimeIndex,
           windows: list[int] = RANGE_WINDOWS,
           levels: tuple[int, ...] = M.PERCENTILES) -> tuple[list[dict], dict[str, pd.DataFrame]]:
    """Both methods' averaged ranges on the held-back days of `days`, scored."""
    scored = days[days > pd.Timestamp(cfg.VALID_END)]    # the held-back days only
    per_window = []
    for window in windows:
        started = time.perf_counter()
        per_window.append(Q.lines(lear, actual, scored, window, levels))
        print(f"Ranges, {window} days: {time.perf_counter() - started:.0f} s", flush=True)
    return Q.score(Q.averaged(per_window), lear, actual, Q.named(windows), SPLIT)


def read_ranges() -> int:
    try:
        _, _, holdout = data()                       # hourly 2024-25, for the benchmarks
        table = day_rows()
    except FileNotFoundError as exc:
        print(exc)
        print("\nNo cached data. Run `just pull` first.")
        return 2

    started = time.perf_counter()
    days, lear = range_walk(table)
    print(f"LEAR walks {len(days)} days ({days.min():%Y-%m-%d} to {days.max():%Y-%m-%d}): "
          f"{time.perf_counter() - started:.0f} s", flush=True)
    actual = Q.prices(table)
    # LEAR is deterministic, so this must read what stage 2's reading holds for `lear daily`.
    check = E.score("lear", SPLIT, lear, M.naive_forecast(holdout), actual,
                    field=M.field_naive(holdout))
    print(f"LEAR on 2024-25, the check: MAE {check['mae']:.3f}, rMAE {check['rmae_field']:.3f} "
          f"(last week's {check['rmae']:.3f}), {check['n']:,} hours\n", flush=True)

    rows, kept = ranges(lear, actual, days)
    print("\n" + Q.table(rows))
    print("\n" + reading_note(record(rows, cfg.QUANTILE_SCORES), len(rows)))

    params = {"window": Q.named(RANGE_WINDOWS), "levels": "1-99", "lear_window": M.WINDOW_DAYS,
              "lear_from": f"{days.min():%Y-%m-%d}", "commit": git_commit()}
    ids = {row["method"]: TR.log_range(row, kept[row["method"]], params) for row in rows}
    print("Logged to MLflow: " + ", ".join(f"{m} {r[:8]}" for m, r in ids.items()))
    return 0


# ── Stage 4: the battery, read once ───────────────────────────────────────────
# The list was fixed on 26 October 2026, before looking: the ceiling; LEAR, the
# average, the tree and the line as fixed schedules, naive beside them; the bids on
# LEAR, strict the headline, pair beside it; each lead tested day by day.  Nothing
# is refitted: the forecasts and the range are the ones stages 2 and 3 stored from
# their own readings, and the code is `just backtest`'s, handed 2024-25.

def capture_rows(fixed: dict, bid: dict, days: int, split: str = SPLIT) -> list[dict]:
    """One row per run: what it earned and its share of the ceiling."""
    ceiling_eur = fixed["ceiling"]["earned"]
    rows = [{"run": name, "split": split, "days": days, "earned": row["earned"],
             "capture": row["earned"] / ceiling_eur, "days_above": row["days_above"]}
            for name, row in fixed.items()]
    rows += [{"run": f"bids {rule}", "split": split, "days": days, "earned": bid[rule]["earned"],
              "capture": bid[rule]["earned"] / ceiling_eur, "rounds": bid[rule]["rounds"],
              "filled": bid[rule]["filled"], "lost": bid[rule]["lost"]}
             for rule in BT.RULES]                    # the ceiling and fixed LEAR: once, above
    return rows


def read_battery() -> int:
    try:
        actual = SB.actual_prices(SPLIT)             # real hours, as the battery is paid
    except FileNotFoundError as exc:
        print(exc)
        print("\nNo cached data. Run `just pull` first.")
        return 2

    started = time.perf_counter()
    run_commit, fixed = SB.capture(actual, SPLIT)
    _, range_commit, bid = SB.bids(actual, SPLIT)    # refuses a range on another LEAR forecast
    days = BT.delivery_days(actual.index).nunique()
    print(f"The battery on 2024-25, {days} days: forecasts from the runs at {run_commit}, limits "
          f"from QRA p{SB.BAND[0]}/p{SB.BAND[1]} at {range_commit}, moved to break-even, "
          f"{time.perf_counter() - started:.0f} s\n")
    print("Fixed schedules, settled at real prices:")
    SB.show_fixed(fixed)
    print("\nBids on LEAR, one loop per round:")
    SB.show_bids(bid)

    rows = capture_rows(fixed, bid, days)
    print("\n" + reading_note(record(rows, cfg.CAPTURE_SCORES), len(rows)))
    return 0


# ── 2026: the replay, read once ───────────────────────────────────────────────
# Stage 4's list, fixed on 31 October 2026 before looking, on ten months no model has
# seen: the ceiling; the average, LEAR, the tree, the line and naive as fixed plans;
# LEAR's bids under both rules; each lead tested day by day.  Every day goes through
# `forecast_day` with the cache as it stands, so the replay is also its test.  A day
# that fell back stops the reading (decided 9 November): none does in 2026.

LIVE = "2026"                                        # what every 2026 row is labelled


def live_days() -> pd.DatetimeIndex:
    """The replayed delivery days, as grid labels: LIVE_START to REPLAY_END."""
    return pd.date_range(cfg.LIVE_START, cfg.REPLAY_END, freq="D")


def replay(given: T.Inputs, days: pd.DatetimeIndex,
           lear_window: int) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    """Each day's five forecasts, the plan `forecast_day` sends, and seconds per part."""
    forecasts, sent, seconds = [], [], {}
    for day in days:
        got = T.forecast_day(day, given, lear_window)
        if got.why:                                  # nothing is scored around a fallback
            raise ValueError(f"{day:%Y-%m-%d} fell back ({got.why}): nothing scored")
        forecasts.append(got.forecasts)
        sent.append(got.schedule)
        for part, took in got.seconds.items():
            seconds[part] = seconds.get(part, 0.0) + took
    return pd.concat(forecasts), pd.concat(sent), seconds


# ── 2026's range: LEAR's half year before it, first ───────────────────────────
# QRA's dots must be forecasts LEAR really made, so for 1 January's 182-day window LEAR
# walks 3 July to 31 December 2025 first, as the 2024-25 reading walked the half year
# before 2024.  Stage 2's reading stored a forecast for each of those days; the walk
# must match it, or the range rests on a LEAR the record never scored.  Then QRA alone
# (the bids read nothing else), its 99 lines, each window sorted, the four averaged.

def warm_up_days(table: pd.DataFrame, windows: list[int]) -> pd.DatetimeIndex:
    """The days before LIVE_START that the longest window reaches back over."""
    first = pd.Timestamp(cfg.LIVE_START)
    return Q.walk_days(table, first - pd.Timedelta(days=max(windows)), first - pd.Timedelta(days=1))


def matches_stored(lear: pd.Series) -> str:
    """Says the walk matches stage 2's stored LEAR, or stops the reading."""
    run = TR.latest(**{**SB.DAILY, "split": SPLIT, "model": "lear daily"})
    if run is None:
        return "no stored 2024-25 LEAR to check it against"
    _, stored = TR.read(run)
    were = stored["lear daily"].reindex(lear.index)  # the same hours, as stage 2 stored them
    if were.isna().any() or not np.allclose(were, lear):
        raise ValueError("LEAR's walk of late 2025 differs from stage 2's stored reading: nothing scored")
    return f"the same as stage 2's stored reading on all {len(lear) // 24} days"


def live_range(lear: pd.Series, actual: pd.Series, days: pd.DatetimeIndex,
               windows: list[int], levels: tuple[int, ...]) -> pd.DataFrame:
    """QRA's lines on `days`, each window's sorted, then averaged percentile by percentile."""
    per_window = []
    for window in windows:
        started = time.perf_counter()
        per_window.append(M.untangle(M.qra(lear, actual, days, window, levels))[0])
        print(f"QRA, {window} days: {time.perf_counter() - started:.0f} s", flush=True)
    return M.average(per_window)


# ── 2026: forecast, range, plans, settlement ──────────────────────────────────
# One function computes and nothing here prints a score, so a test can plant a price
# and compare two replays.  Settlement is the same code 2024-25 went through, on the
# real hours of the replayed days only: the cache runs past them and nothing may read on.

def replay_2026(windows: list[int] = RANGE_WINDOWS, levels: tuple[int, ...] = M.PERCENTILES,
                lear_window: int = M.WINDOW_DAYS) -> dict:
    """The replay: forecasts, the plans sent, LEAR's walk, the range, and what each run earned."""
    clock = {}
    started = time.perf_counter()
    given = T.inputs()                               # the cache, read once for every day
    clock["inputs"] = time.perf_counter() - started

    days, started = live_days(), time.perf_counter()
    forecasts, sent, parts = replay(given, days, lear_window)
    clock["days"] = time.perf_counter() - started
    print(f"{len(days)} days through forecast_day, none fell back: {clock['days']:.0f} s ("
          + ", ".join(f"{part} {took:.0f}" for part, took in parts.items()) + ")", flush=True)

    warm, started = warm_up_days(given.table, windows), time.perf_counter()
    before = M.lear_walk_forward(given.table, warm, lear_window)
    clock["lear before"] = time.perf_counter() - started
    print(f"LEAR on the {len(warm)} days before ({warm.min():%Y-%m-%d} to {warm.max():%Y-%m-%d}): "
          f"{clock['lear before']:.0f} s, {matches_stored(before)}", flush=True)

    lear = pd.concat([before, forecasts["LEAR"]])    # every forecast LEAR made, in day order
    on_grid = Q.prices(given.table)                  # real prices on the grid: the dots' answers
    started = time.perf_counter()
    band = live_range(lear, on_grid, days, windows, levels)
    clock["range"] = time.perf_counter() - started

    started = time.perf_counter()
    actual = cfg.replayed(D.load("day_ahead_price").iloc[:, 0])     # real hours, as the battery is paid
    planned = {name: D.from_slots(forecasts[name], actual.index) for name in forecasts.columns}
    buy, sell = SB.BAND
    fixed = SB.fixed_plans(planned, actual)
    bid = SB.bid_plans(planned["LEAR"], D.from_slots(band[buy], actual.index),
                       D.from_slots(band[sell], actual.index), actual)
    clock["battery"] = time.perf_counter() - started

    kept = pd.concat([on_grid.reindex(forecasts.index).rename("actual"), forecasts, band], axis=1)
    return {"days": days, "forecasts": forecasts, "sent": sent, "lear": lear, "range": band,
            "actual": actual, "fixed": fixed, "bid": bid, "kept": kept, "seconds": clock}


def read_2026(windows: list[int] = RANGE_WINDOWS, levels: tuple[int, ...] = M.PERCENTILES,
              lear_window: int = M.WINDOW_DAYS) -> int:
    started = time.perf_counter()
    try:
        got = replay_2026(windows, levels, lear_window)
    except FileNotFoundError as exc:
        print(exc)
        print("\nNo cached data. Run `just pull` first.")
        return 2

    days = got["days"]
    print(f"\nThe battery on {days.min():%Y-%m-%d} to {days.max():%Y-%m-%d}, {len(days)} days: "
          f"limits from QRA p{SB.BAND[0]}/p{SB.BAND[1]}, moved to break-even\n")
    print("Fixed schedules, settled at real prices:")
    SB.show_fixed(got["fixed"])
    print("\nBids on LEAR, one loop per round:")
    SB.show_bids(got["bid"])

    rows = capture_rows(got["fixed"], got["bid"], len(days), LIVE)
    print("\n" + reading_note(record(rows, cfg.CAPTURE_SCORES), len(rows), LIVE))
    params = {"window": Q.named(windows), "levels": f"{min(levels)}-{max(levels)}",
              "lear_window": lear_window, "days": f"{days.min():%Y-%m-%d} to {days.max():%Y-%m-%d}",
              "commit": git_commit()}
    run = TR.log_replay(rows, got["kept"], params)
    took = ", ".join(f"{part} {s:.0f}" for part, s in got["seconds"].items())
    print(f"Logged to MLflow: replay {run[:8]}. Ran in {time.perf_counter() - started:.0f} s ({took}).")
    return 0


# ── Running it ────────────────────────────────────────────────────────────────
# Four readings: `points` is stage 2's forecasts, the default because it came first;
# `ranges` is stage 3's; `battery` is stage 4's; `2026` is stage 5's replay.

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read the held-back years, once per stage.")
    parser.add_argument("what", nargs="?", choices=["points", "ranges", "battery", LIVE],
                        default="points")
    what = parser.parse_args(argv).what
    if what == LIVE:
        return read_2026()
    if what == "ranges":
        return read_ranges()
    if what == "battery":
        return read_battery()

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
    daily = [r for r in rows if r["model"].startswith("naive") or r["model"].endswith(" daily")]
    frozen = [r for r in rows if r not in daily]                  # "gbm 2018-2023"
    ids = {**TR.log(daily, forecasts, {"refit": "daily", "lear_window": M.WINDOW_DAYS,
                                       "commit": commit}),
           **TR.log(frozen, forecasts, {"refit": "once", "commit": commit})}
    print(f"Logged {len(ids)} runs to MLflow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
