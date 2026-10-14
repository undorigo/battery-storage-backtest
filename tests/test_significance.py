"""The p-value command must read the runs it names and score both on one exam.

Two runs are logged to a temporary MLflow store, the second one day shorter, so a
comparison that scored each run on its own hours would come out different from one
that scores the shared hours.  Expected values come from `evaluate` directly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts import significance as S
from src import evaluate as E
from src import tracking as TR


# ── The fixture ───────────────────────────────────────────────────────────────
# A week of hours.  The monthly line is closer than the once line by a varying
# amount, so the test has something to detect; it is missing the last day, and on
# that day it would have been far off, so leaving it in would move its score.

ONCE = {"model": "linear", "refit": "once"}
MONTHLY = {"model": "linear", "refit": "monthly"}


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    where = tmp_path_factory.mktemp("mlflow")
    hours = pd.date_range("2023-03-13 00:00", periods=7 * 24, freq="h")
    n = np.arange(len(hours), dtype=float)
    actual = pd.Series(80 + 20 * np.sin(n / 4), index=hours)
    naive = actual.shift(24).bfill()
    once = actual + 6 + 2 * np.cos(n)
    monthly = actual + 3 + 2 * np.sin(n / 3)
    monthly.iloc[-24:] = actual.iloc[-24:] + 90                 # a bad day, then trimmed away
    for refit, forecast in (("once", once), ("monthly", monthly.iloc[:-24])):
        frame = pd.DataFrame({"actual": actual, "naive": naive, "linear": forecast}).dropna()
        rows = [E.score("linear", "valid", frame["linear"], frame["naive"], frame["actual"])]
        TR.log(rows, frame, {"refit": refit, "commit": f"c-{refit}"},
               db=where / "mlflow.db", store=where / "mlruns")
    shared = hours[:-24]
    expected = (once[shared], monthly[shared], naive[shared], actual[shared])
    return {"db": where / "mlflow.db"}, expected


def test_both_sides_are_scored_on_the_shared_hours(store):
    where, (a, b, naive, actual) = store
    r = S.compare(ONCE, MONTHLY, **where)
    assert r["hours"] == 6 * 24
    assert r["first"] == pytest.approx(E.rmae(a, naive, actual))
    assert r["second"] == pytest.approx(E.rmae(b, naive, actual))


def test_the_p_values_point_the_stated_way(store):
    where, (a, b, _, actual) = store
    r = S.compare(ONCE, MONTHLY, **where)
    assert r["p_second_better"] == pytest.approx(E.dm(a, b, actual))   # monthly closer: small
    assert r["p_first_better"] == pytest.approx(E.dm(b, a, actual))
    assert r["p_second_better"] < 0.05 < r["p_first_better"]
    assert r["commits"] == "c-once / c-monthly"


def test_a_missing_run_names_the_command_that_makes_it(store):
    where, _ = store
    with pytest.raises(LookupError, match="just train daily all"):
        S.compare(ONCE, {"model": "lear_all", "refit": "daily", "lear_window": "all"}, **where)
