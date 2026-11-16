"""The four-week trial's evening: when it runs, and what it tries again.

`scripts/trial.py` is the one piece of the schedule that makes decisions, so it is
tested here with a fake evening that only records how it was called and answers
with the exit codes a real one gives.  No network, no clock, no cache.
"""

from __future__ import annotations

import pandas as pd
import pytest

from scripts import trial as TR
from scripts.tomorrow import NOT_YET

PULL_FAILED = 2                                             # what `just tomorrow` returns when the pull fails


class Evening:
    """A stand-in for one try of `just tomorrow`: answers in turn, notes each call."""

    def __init__(self, *answers: int):
        self.answers, self.calls, self.waits = list(answers), [], []

    def run(self, pay_only: bool, last_try: bool, pull: bool) -> int:
        self.calls.append((pay_only, last_try, pull))
        return self.answers.pop(0)

    def wait(self, seconds: float) -> None:
        self.waits.append(seconds)


def _evening(day: str, *answers: int, written: set[str] = frozenset()) -> tuple[int, Evening]:
    fake = Evening(*answers)
    code = TR.evening(pd.Timestamp(day), fake.run, fake.wait, written)
    return code, fake


# ── The end date ──────────────────────────────────────────────────────────────
# Four weeks from 16 November: the last forecast is written on 13 December, for the
# 14th.  The evening of the 14th pays that day and forecasts nothing, so no row is
# left unpaid; every evening after it does nothing at all.

def test_the_last_forecast_is_written_on_13_december():
    code, fake = _evening("2026-12-13", 0)
    assert code == 0
    assert fake.calls == [(False, False, True)]             # a full evening: pay, then forecast


def test_14_december_is_paid_and_nothing_is_forecast():
    code, fake = _evening("2026-12-14", 0)
    assert code == 0
    assert fake.calls == [(True, False, True)]              # pay only


def test_after_14_december_the_job_does_nothing():
    for day in ("2026-12-15", "2027-01-31"):
        code, fake = _evening(day)
        assert code == 0
        assert fake.calls == []


# ── A day already written ─────────────────────────────────────────────────────
# Tonight's first evening is started by hand and the schedule fires at 19:07 as
# well.  The second run must stop at once, not forecast for 8 minutes and then
# fail on "already written".

def test_an_evening_whose_tomorrow_is_written_does_nothing():
    code, fake = _evening("2026-11-16", written={"2026-11-17"})
    assert code == 0
    assert fake.calls == []


def test_only_tomorrow_counts_as_written():
    code, fake = _evening("2026-11-16", 0, written={"2026-11-16"})   # today's own rows, from last night
    assert fake.calls == [(False, False, True)]


# ── The retry rule ────────────────────────────────────────────────────────────
# Hourly from 19:00 to 22:00: four tries, three waits of an hour.  "Not yet" (3) and
# "the pull failed" (2) are tried again; the fourth try sends what it has, and if
# its pull fails too, it runs once more on the cache as it stands.  Anything else
# is a fault in the code, and trying again an hour later would only hide it.

def test_not_yet_is_tried_each_hour_and_sent_at_the_fourth():
    code, fake = _evening("2026-11-20", NOT_YET, NOT_YET, NOT_YET, 0)
    assert code == 0
    assert [last for _, last, _ in fake.calls] == [False, False, False, True]
    assert fake.waits == [3600, 3600, 3600]


def test_an_answer_stops_the_tries():
    code, fake = _evening("2026-11-20", NOT_YET, 0)
    assert code == 0
    assert len(fake.calls) == 2 and fake.waits == [3600]


def test_a_failed_pull_is_tried_again_and_the_last_try_falls_back_on_the_cache():
    code, fake = _evening("2026-11-20", PULL_FAILED, PULL_FAILED, PULL_FAILED, PULL_FAILED, 0)
    assert code == 0
    assert fake.calls[3] == (False, True, True)             # 22:00: last try, still pulling
    assert fake.calls[4] == (False, True, False)            # then the cache as it stands
    assert fake.waits == [3600, 3600, 3600]


def test_the_last_evening_falls_back_on_the_cache_too():
    code, fake = _evening("2026-12-14", PULL_FAILED, PULL_FAILED, PULL_FAILED, PULL_FAILED, 0)
    assert fake.calls[-1] == (True, True, False)


@pytest.mark.parametrize("fault", [1, 4])
def test_a_fault_is_not_tried_again(fault):
    code, fake = _evening("2026-11-20", fault)
    assert code == fault
    assert len(fake.calls) == 1 and fake.waits == []


# ── One try, for real ─────────────────────────────────────────────────────────
# The pay-only try runs once, on 14 December, so a fault in it would show only as
# the trial's last day left unpaid.  Its wiring is checked here with the pull and
# the record replaced.  The pull asks for the three series the forecast reads and
# no others: a revised actual must not cost an evening an hour (decided 16 Nov).

def _once(monkeypatch, pulled: bool, pay_only: bool) -> tuple[int, list[str]]:
    steps = []
    monkeypatch.setattr(TR, "fetch_recent", lambda: steps.append("pull") or pulled)
    monkeypatch.setattr(TR.data, "load", lambda key: pd.DataFrame({"price": [1.0]}))
    monkeypatch.setattr(TR.T, "pay", lambda actual: steps.append("pay") or (None, ["2026-12-14"]))
    monkeypatch.setattr(TR.T, "main", lambda argv: steps.append(" ".join(argv)) or 0)
    return TR.once(pay_only=pay_only, last_try=True, pull=True), steps


def test_the_last_evening_pulls_then_pays(monkeypatch):
    assert _once(monkeypatch, pulled=True, pay_only=True) == (0, ["pull", "pay"])


def test_the_last_evening_waits_when_the_pull_fails(monkeypatch):
    assert _once(monkeypatch, pulled=False, pay_only=True) == (PULL_FAILED, ["pull"])


def test_a_full_evening_pulls_once_then_runs_tomorrow_on_that_cache(monkeypatch):
    assert _once(monkeypatch, pulled=True, pay_only=False) == (0, ["pull", "--no-pull --last-try"])


def test_the_pull_asks_for_the_forecasts_three_series_alone(monkeypatch):
    from src import features as F

    asked = {}
    monkeypatch.setattr(TR.data, "pull", lambda keys, recent: asked.update(keys=keys, recent=recent) or [])
    assert TR.fetch_recent() is True
    assert asked == {"keys": list(F.SOURCES), "recent": True}
