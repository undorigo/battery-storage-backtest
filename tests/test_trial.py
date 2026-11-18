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
        self.answers, self.calls, self.waits, self.days = list(answers), [], [], []

    def run(self, day: pd.Timestamp, pay_only: bool, last_try: bool, pull: bool) -> int:
        self.days.append(day)
        self.calls.append((pay_only, last_try, pull))
        return self.answers.pop(0)

    def wait(self, seconds: float) -> None:
        self.waits.append(seconds)


def _evening(start: str, *answers: int, written: set[str] = frozenset()) -> tuple[int, Evening]:
    """One evening started at `start`, Berlin wall clock; 19:07 unless a time is given."""
    fake = Evening(*answers)
    now = pd.Timestamp(start if " " in start else f"{start} 19:07")
    code = TR.evening(now, fake.run, fake.wait, written)
    return code, fake


# ── The end date ──────────────────────────────────────────────────────────────
# Four weeks from the first evening, 18 November: the last forecast is written on
# 15 December, for the 16th.  The evening of the 16th pays that day and forecasts
# nothing, so no row is left unpaid; every evening after it does nothing at all.

def test_the_last_forecast_is_written_on_15_december():
    code, fake = _evening("2026-12-15", 0)
    assert code == 0
    assert fake.calls == [(False, False, True)]             # a full evening: pay, then forecast
    assert fake.days == [pd.Timestamp("2026-12-16")]


def test_16_december_is_paid_and_nothing_is_forecast():
    code, fake = _evening("2026-12-16", 0)
    assert code == 0
    assert fake.calls == [(True, False, True)]              # pay only


def test_after_16_december_the_job_does_nothing():
    for day in ("2026-12-17", "2027-01-31"):
        code, fake = _evening(day)
        assert code == 0
        assert fake.calls == []


# ── The evening window ────────────────────────────────────────────────────────
# GitHub fired its first three schedules 6¾ to 7¾ hours late (17–18 November).  Started
# then, "tomorrow" is the day after, whose wind and solar forecast is 15 hours
# away: the fourth try would have sent the simple rule's plan, and the plan sent
# stands.  So a start outside 18:00–19:59 Berlin does nothing.

@pytest.mark.parametrize("start", ["2026-11-18 02:50", "2026-11-17 17:59", "2026-11-17 20:00"])
def test_a_start_outside_the_evening_does_nothing(start):
    code, fake = _evening(start)
    assert code == 0
    assert fake.calls == []


@pytest.mark.parametrize("start", ["2026-11-17 18:00", "2026-11-17 19:59"])
def test_a_start_inside_the_evening_runs(start):
    code, fake = _evening(start, 0)
    assert fake.days == [pd.Timestamp("2026-11-18")]


def test_every_try_forecasts_the_day_fixed_when_the_evening_began():
    code, fake = _evening("2026-11-17 19:59", NOT_YET, NOT_YET, NOT_YET, 0)
    assert fake.days == [pd.Timestamp("2026-11-18")] * 4    # 22:59 or later: still the 18th


# ── A day already written ─────────────────────────────────────────────────────
# Tonight's first evening is started by hand and the schedule fires at 19:07 as
# well.  The second run must stop at once, not forecast for 8 minutes and then
# fail on "already written".

def test_an_evening_whose_tomorrow_is_written_does_nothing():
    code, fake = _evening("2026-11-17", written={"2026-11-18"})
    assert code == 0
    assert fake.calls == []


def test_only_tomorrow_counts_as_written():
    code, fake = _evening("2026-11-17", 0, written={"2026-11-17"})   # today's own rows, from last night
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
    code, fake = _evening("2026-12-16", PULL_FAILED, PULL_FAILED, PULL_FAILED, PULL_FAILED, 0)
    assert fake.calls[-1] == (True, True, False)


@pytest.mark.parametrize("fault", [1, 4])
def test_a_fault_is_not_tried_again(fault):
    code, fake = _evening("2026-11-20", fault)
    assert code == fault
    assert len(fake.calls) == 1 and fake.waits == []


# ── One try, for real ─────────────────────────────────────────────────────────
# The pay-only try runs once, on 16 December, so a fault in it would show only as
# the trial's last day left unpaid.  Its wiring is checked here with the pull and
# the record replaced.  The pull asks for the three series the forecast reads and
# no others: a revised actual must not cost an evening an hour (decided 16 Nov).

def _once(monkeypatch, pulled: bool, pay_only: bool) -> tuple[int, list[str]]:
    steps = []
    monkeypatch.setattr(TR, "fetch_recent", lambda: steps.append("pull") or pulled)
    monkeypatch.setattr(TR.data, "load", lambda key: pd.DataFrame({"price": [1.0]}))
    monkeypatch.setattr(TR.T, "pay", lambda actual: steps.append("pay") or (None, ["2026-12-16"]))
    monkeypatch.setattr(TR.T, "evening", lambda day, last_try: steps.append(f"{day:%Y-%m-%d} {last_try}") or 0)
    return TR.once(pd.Timestamp("2026-12-01"), pay_only=pay_only, last_try=True, pull=True), steps


def test_the_last_evening_pulls_then_pays(monkeypatch):
    assert _once(monkeypatch, pulled=True, pay_only=True) == (0, ["pull", "pay"])


def test_the_last_evening_waits_when_the_pull_fails(monkeypatch):
    assert _once(monkeypatch, pulled=False, pay_only=True) == (PULL_FAILED, ["pull"])


def test_a_full_evening_pulls_once_then_forecasts_the_day_it_was_given(monkeypatch):
    assert _once(monkeypatch, pulled=True, pay_only=False) == (0, ["pull", "2026-12-01 True"])


def test_the_pull_asks_for_the_forecasts_three_series_alone(monkeypatch):
    from src import features as F

    asked = {}
    monkeypatch.setattr(TR.data, "pull", lambda keys, recent: asked.update(keys=keys, recent=recent) or [])
    assert TR.fetch_recent() is True
    assert asked == {"keys": list(F.SOURCES), "recent": True}
