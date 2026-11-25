"""The drift checks (stage 5, step 9): is the trial still forecasting as 2023 did?

Run:  just drift match      (does the trial's code rebuild 2023's stored forecasts and band?)

Two signals, each over 28 days, flag when they leave the range 2023 showed: the share
of real prices inside LEAR's 80 % band, and the average's error against the field's
rule (decided 17 and 18 November 2026).  A flag is a message; nothing switches.
`trial.py` and the forecasting code stay frozen: this file only reads them.

`match` comes first, because a threshold is only as good as the forecasts it was set
on: 2023's were stored in October by `just train daily`, and the trial makes its own
with `tomorrow._models`.  If the two recipes disagree, the error signal watches LEAR.
The band is checked the same way, on twelve days: stage 3 stored 2023's, the trial
builds its own with `tomorrow.band`.
"""

from __future__ import annotations

import argparse
import time
from types import SimpleNamespace

import pandas as pd

from scripts import backtest as B
from scripts import tomorrow as T
from scripts.train import git_commit
from src import config as cfg
from src import models as M
from src import tracking as TR

MEMBERS = ("LEAR", "tree", "straight line")                 # the average's three, in order


# ── Rebuilding 2023 with the trial's own models ───────────────────────────────
# The forecasting step behind tomorrow's arrival check, called one day at a time.
# The check itself is skipped: it counts quarter-hours, and 2023's prices came
# hourly (24 a day, not 96), so it would answer "not yet" for every day of the year.
# A day any model could not forecast is an error, so a match is never claimed on
# fewer days than it names.

def rebuild(days: pd.DatetimeIndex, given: T.Inputs,
            lear_window: int | None = M.WINDOW_DAYS) -> dict[str, pd.Series]:
    """Each forecast the trial would make for these days, on the 24-slot grid."""
    made = {name: [] for name in MEMBERS}
    for day in days:
        rows = given.frame[given.frame.index.normalize() == day]   # the day's 24 slots
        got, stopped, _ = T._models(day, given, rows, lear_window)
        if stopped:
            raise ValueError(f"{day:%Y-%m-%d}: " + "; ".join(stopped))
        for name in MEMBERS:
            made[name].append(got[name])
    joined = {name: pd.concat(parts) for name, parts in made.items()}
    joined["average"] = sum(joined[name] for name in MEMBERS) / len(MEMBERS)   # hour by hour
    return joined


# ── Rebuilding 2023's band with the trial's own `tomorrow.band` ───────────────
# The band signal is set on stage 3's stored range, and the trial builds its own each
# evening, so it needs the same check.  One band costs about 8 minutes (LEAR's 182
# days before the day, re-forecast), so the check takes the 1st of each month
# (decided 25 November 2026), from 1 January, whose windows reach back into 2022.
# `band` reads only the day and its LEAR forecast, so that is all it is handed.

BAND_DAYS = pd.date_range("2023-01-01", periods=12, freq="MS")   # the 1st of each month


def rebuild_band(days: pd.DatetimeIndex, given: T.Inputs, lear: pd.Series,
                 lear_window: int | None = M.WINDOW_DAYS) -> dict[str, pd.Series]:
    """The trial's band for these days, one series per percentile (`p10`, ...)."""
    parts = []
    for day in days:
        own = lear[lear.index.normalize() == day]               # that day's 24 slots, as an evening has
        got = SimpleNamespace(day=day, forecasts=pd.DataFrame({"LEAR": own}))
        band = T.band(got, given, lear_window)
        if band is None:
            raise ValueError(f"{day:%Y-%m-%d}: no band")
        parts.append(band)
    joined = pd.concat(parts)
    return {f"p{level}": joined[level] for level in joined.columns}


# ── How far the rebuild lands from what was stored ────────────────────────────
# The largest difference within each day, so one hour off shows at full size.  A
# cent per MWh is the line: day-ahead prices clear in whole cents, so a gap below
# it is rounding, and a gap at it is a price a reader could see.

TOLERANCE = 0.01                                            # EUR/MWh: one cent, a price's last digit


def gaps(rebuilt: dict[str, pd.Series], stored: dict[str, pd.Series]) -> pd.DataFrame:
    """Per day, the largest gap in EUR/MWh between rebuilt and stored, one column per forecast."""
    out = {}
    for name, new in rebuilt.items():
        old = stored[name].reindex(new.index)               # by label, never by position
        if old.isna().any():
            raise ValueError(f"{name}: nothing stored for {old.index[old.isna()][0]:%Y-%m-%d}")
        out[name] = (new - old).abs().groupby(new.index.normalize()).max()
    return pd.DataFrame(out)


def matches(per_day: pd.DataFrame) -> bool:
    return bool((per_day < TOLERANCE).all().all())


def stored_2023() -> tuple[str, dict[str, pd.Series]]:
    """The commit and slots of `just train daily`'s 2023 runs, the average beside them."""
    stored, commits = {}, set()
    for name, model in B.MODELS.items():
        params, table = TR.read(TR.latest(model=model, **B.DAILY))
        stored[name] = table[model]
        commits.add(params["commit"])
    stored["average"] = sum(stored[name] for name in MEMBERS) / len(MEMBERS)
    return ", ".join(sorted(commits)), stored


def stored_band() -> tuple[str, dict[str, pd.Series]]:
    """The commit and percentiles of stage 3's 2023 range, the four windows averaged."""
    params, table = TR.read_range(TR.latest(**B.QRA_RUN))
    return params["commit"], {f"p{level}": table[level] for level in M.PERCENTILES}


def _show(per_day: pd.DataFrame) -> None:
    for name, gap in per_day.items():
        print(f"  {name:<14} largest gap {gap.max():.2e} EUR/MWh, days at {TOLERANCE} or more: "
              f"{int((gap >= TOLERANCE).sum())}")


def match() -> int:
    started = time.time()
    given = T.inputs()
    days = pd.date_range(pd.Timestamp(cfg.TRAIN_END) + pd.Timedelta(days=1), cfg.VALID_END)
    commit, stored = stored_2023()
    rebuilt = rebuild(days, given)
    per_day = gaps(rebuilt, stored)
    print(f"2023 rebuilt at {git_commit()} against the runs at {commit}: {len(per_day)} days, "
          f"{time.time() - started:.0f} s", flush=True)
    _show(per_day)
    print("Match: the error signal watches the average." if matches(per_day)
          else "No match: the error signal watches LEAR.", flush=True)

    started = time.time()
    commit, stored = stored_band()
    band = gaps(rebuild_band(BAND_DAYS, given, rebuilt["LEAR"]), stored)
    band = pd.DataFrame({"band": band.max(axis=1)})        # the widest gap of the 99 percentiles
    print(f"\nBands of {len(band)} days rebuilt against the range at {commit}, "
          f"{time.time() - started:.0f} s")
    _show(band)
    print("Match: the band signal is set on the band the trial builds." if matches(band)
          else "No match: the band's thresholds would rest on another recipe.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The drift checks.")
    parser.add_argument("what", choices=["match"])
    parser.parse_args(argv)
    return match()


if __name__ == "__main__":
    raise SystemExit(main())
