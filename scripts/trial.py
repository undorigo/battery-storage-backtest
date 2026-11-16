"""The four-week trial: one evening of `just tomorrow`, tried again until it answers.

Run:  python -m scripts.trial      (by `.github/workflows/trial.yml`, at 19:07 Berlin)

GitHub starts this once an evening.  It decides three things and leaves the rest
to `scripts/tomorrow.py`: whether the trial is still on, whether tomorrow is already
written, and when to try again.  The decisions are in `evening`, which takes the
evening itself as an argument, so `tests/test_trial.py` can check them with a fake.
"""

from __future__ import annotations

import sys
import time

import pandas as pd

from scripts import tomorrow as T
from src import config as cfg
from src import data

# ── The four weeks ────────────────────────────────────────────────────────────
# Decided 16 November 2026: the first evening is that one, so the last forecast is
# written on 13 December for the 14th.  The evening of the 14th pays it and
# forecasts nothing, so the trial leaves no row unpaid.  After that the job still
# fires each evening and does nothing, until the workflow is switched off.

LAST_DAY = pd.Timestamp("2026-12-14")                       # the last delivery day forecast

# ── Trying again ──────────────────────────────────────────────────────────────
# Hourly from 19:00 to 22:00.  Two answers mean "later": an input still short (3),
# and the pull failed (2), which an ENTSO-E outage and a revised value both cause.
# The fourth try sends what it has; if even its pull fails, it runs on the cache
# as it stands, so the evening still ends with a row.  Any other code is a fault in
# the code, and an hour's wait would only hide it.

TRIES = 4                                                   # 19, 20, 21 and 22:00
HOUR = 3600                                                 # seconds between tries
PULL_FAILED = 2                                             # `just tomorrow`'s code when the pull fails
LATER = (T.NOT_YET, PULL_FAILED)


def evening(today: pd.Timestamp, run, wait, written: set[str]) -> int:
    """One evening of the trial.  `run(pay_only, last_try, pull)` is one try."""
    if today > LAST_DAY:
        print(f"The trial ended with {LAST_DAY:%d %B %Y}: nothing to do.")
        return 0
    pay_only = today == LAST_DAY                            # nothing left to forecast
    if not pay_only and f"{today + pd.Timedelta(days=1):%Y-%m-%d}" in written:
        print("Tomorrow is already written: the plan sent stands.")
        return 0

    for n in range(1, TRIES + 1):
        last = n == TRIES
        code = run(pay_only, last, True)
        if code == PULL_FAILED and last:
            print("The pull failed at the last try: running on the cache as it stands.", flush=True)
            code = run(pay_only, last, False)
        if code not in LATER or last:
            return code
        print(f"Try {n} of {TRIES} answered {code}: again in an hour.", flush=True)
        wait(HOUR)
    return code


# ── One try, for real ─────────────────────────────────────────────────────────
# A full evening is `just tomorrow` with its flags.  The last evening only pays,
# which `tomorrow.py` has no flag for, so it is spelled out here with the same two
# calls the full evening makes first: the pull, then `pay`.

def once(pay_only: bool, last_try: bool, pull: bool) -> int:
    if not pay_only:
        return T.main(["--last-try"] * last_try + ["--no-pull"] * (not pull))
    if pull:
        from scripts import pull as P                       # network and a token
        if P.main(["recent"]) != 0:
            return PULL_FAILED
    _, paid = T.pay(data.load("day_ahead_price").iloc[:, 0])
    print("Paid: " + (", ".join(paid) if paid else "nothing new"))
    return 0


def main() -> int:
    today = pd.Timestamp.now(tz=cfg.TZ_MARKET).normalize().tz_localize(None)   # Berlin date, grid label
    written = set(T.read()["day"]) if cfg.DAILY.exists() else set()
    return evening(today, once, time.sleep, written)


if __name__ == "__main__":
    sys.exit(main())
