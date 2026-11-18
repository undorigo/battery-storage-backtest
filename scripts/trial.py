"""The four-week trial: one evening of `just tomorrow`, tried again until it answers.

Run:  python -m scripts.trial      (by `.github/workflows/trial.yml`, every hour)

GitHub starts this each evening.  It decides four things and leaves the rest to
`scripts/tomorrow.py`: whether the trial is still on, whether it is the evening at
all, whether tomorrow is already written, and when to try again.  The decisions are
in `evening`, which takes the evening itself as an argument, so `tests/test_trial.py`
can check them with a fake.
"""

from __future__ import annotations

import sys
import time

import pandas as pd

from scripts import tomorrow as T
from src import config as cfg
from src import data
from src import features as F

# ── The four weeks ────────────────────────────────────────────────────────────
# Four weeks from the first evening, 18 November 2026 (decided the 16th as "four
# weeks from tonight"; GitHub's schedules fired too late on the 16th and 17th).  The
# last forecast is written on 15 December for the 16th.  The evening of the 16th
# pays it and forecasts nothing, so the trial leaves no row unpaid.  After that the job still
# fires each evening and does nothing, until the workflow is switched off.

LAST_DAY = pd.Timestamp("2026-12-16")                       # the last delivery day forecast

# ── The evening window ────────────────────────────────────────────────────────
# GitHub fired its first three schedules 6¾ to 7¾ hours late.  Started at 02:50, the run's
# "tomorrow" was a day whose wind and solar forecast was 15 hours away, and its
# fourth try would have sent the simple rule's plan, which then stands.  So only a
# start between 18:00 and 19:59 Berlin runs, and the day it forecasts is fixed at
# the start, so a long evening cannot slide into the next day's forecast.  The
# workflow fires every hour, so whichever fire lands in the window runs.

FIRST_HOUR, LAST_HOUR = 18, 19                              # a start from 18:00 to 19:59

# ── Trying again ──────────────────────────────────────────────────────────────
# Hourly, four tries.  Two answers mean "later": an input still short (3), and the
# pull failed (2), which an ENTSO-E outage and a revised value both cause.  The
# fourth try sends what it has; if even its pull fails, it runs on the cache as it
# stands, so the evening still ends with a row.  Any other code is a fault in the
# code, and an hour's wait would only hide it.

TRIES = 4                                                   # from 18:07: 18, 19, 20 and 21:00
HOUR = 3600                                                 # seconds between tries
PULL_FAILED = 2                                             # `just tomorrow`'s code when the pull fails
LATER = (T.NOT_YET, PULL_FAILED)


def evening(now: pd.Timestamp, run, wait, written: set[str]) -> int:
    """One evening started at `now` (Berlin wall clock).  `run(day, pay_only, last_try, pull)` is one try."""
    today = now.normalize()
    if today > LAST_DAY:
        print(f"The trial ended with {LAST_DAY:%d %B %Y}: nothing to do.")
        return 0
    if not FIRST_HOUR <= now.hour <= LAST_HOUR:
        print(f"Started at {now:%H:%M}, outside 18:00-19:59 Berlin: nothing to do.")
        return 0
    day = today + pd.Timedelta(days=1)                      # naive dates: a calendar step, not 24 h
    pay_only = today == LAST_DAY                            # nothing left to forecast
    if not pay_only and f"{day:%Y-%m-%d}" in written:
        print("Tomorrow is already written: the plan sent stands.")
        return 0

    for n in range(1, TRIES + 1):
        last = n == TRIES
        code = run(day, pay_only, last, True)
        if code == PULL_FAILED and last:
            print("The pull failed at the last try: running on the cache as it stands.", flush=True)
            code = run(day, pay_only, last, False)
        if code not in LATER or last:
            return code
        print(f"Try {n} of {TRIES} answered {code}: again in an hour.", flush=True)
        wait(HOUR)
    return code


# ── One try, for real ─────────────────────────────────────────────────────────
# The pull is made here and asks for the three series the forecast reads, nothing
# else (decided 16 November 2026): ENTSO-E revised both actuals on the one recent
# pull after a gap, and a revision is an hour's wait.  `just tomorrow` by hand still
# pulls all five.  The last evening only pays, which `tomorrow.py` has no flag for.

def fetch_recent() -> bool:
    """The last two weeks of the forecast's series.  False if it failed or revised."""
    try:
        results = data.pull(keys=list(F.SOURCES), recent=True)
    except Exception as exc:                                # outage, network, no token
        print(f"Pull failed: {exc}", flush=True)
        return False
    for r in results:
        print(f"  {r.key:<22}{r.outcome:<11}{r.detail}", flush=True)
    return not any(r.needs_attention for r in results)     # revised: the old copy archived


def once(day: pd.Timestamp, pay_only: bool, last_try: bool, pull: bool) -> int:
    if pull and not fetch_recent():
        return PULL_FAILED
    if not pay_only:
        return T.evening(day, last_try)                     # the day fixed at the start, not the clock
    _, paid = T.pay(data.load("day_ahead_price").iloc[:, 0])
    print("Paid: " + (", ".join(paid) if paid else "nothing new"))
    return 0


def main() -> int:
    now = pd.Timestamp.now(tz=cfg.TZ_MARKET).tz_localize(None)   # Berlin wall clock
    written = set(T.read()["day"]) if cfg.DAILY.exists() else set()
    return evening(now, once, time.sleep, written)


if __name__ == "__main__":
    sys.exit(main())
