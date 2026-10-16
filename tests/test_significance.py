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
    naive = actual.shift(48).bfill()                            # last week's, as a stand-in
    field = actual.shift(24).bfill()                            # the field's: a different miss
    once = actual + 6 + 2 * np.cos(n)
    monthly = actual + 3 + 2 * np.sin(n / 3)
    monthly.iloc[-24:] = actual.iloc[-24:] + 90                 # a bad day, then trimmed away
    for refit, forecast in (("once", once), ("monthly", monthly.iloc[:-24])):
        frame = pd.DataFrame({"actual": actual, "naive": naive, "naive_field": field,
                              "linear": forecast}).dropna()
        rows = [E.score("linear", "valid", frame["linear"], frame["naive"], frame["actual"],
                        field=frame["naive_field"])]
        TR.log(rows, frame, {"refit": refit, "commit": f"c-{refit}"},
               db=where / "mlflow.db", store=where / "mlruns")
    shared = hours[:-24]
    expected = (once[shared], monthly[shared], field[shared], actual[shared], naive[shared])
    return {"db": where / "mlflow.db"}, expected


def test_both_sides_are_scored_on_the_shared_hours_against_the_field(store):
    where, (a, b, field, actual, _) = store
    r = S.compare(ONCE, MONTHLY, **where)
    assert r["hours"] == 6 * 24
    assert r["divided_by"] == "field"
    assert r["first"] == pytest.approx(E.rmae(a, field, actual))
    assert r["second"] == pytest.approx(E.rmae(b, field, actual))


def test_a_run_from_before_the_revision_is_divided_by_last_week_and_says_so(store, monkeypatch):
    """Runs pinned to old commits never stored the field's benchmark.  Their ratio falls
    back to last week's, and the row must say so rather than pass as a new one."""
    where, (a, b, _, actual, naive) = store
    stored = TR.read
    monkeypatch.setattr(TR, "read", lambda run, **kw: (lambda p, f: (p, f.drop(columns="naive_field")))(
        *stored(run, **kw)))                                      # as an old run looks
    r = S.compare(ONCE, MONTHLY, **where)
    assert r["divided_by"] == "last week"
    assert r["first"] == pytest.approx(E.rmae(a, naive, actual))
    assert r["second"] == pytest.approx(E.rmae(b, naive, actual))


def test_the_p_values_point_the_stated_way(store):
    where, (a, b, _, actual, _) = store
    r = S.compare(ONCE, MONTHLY, **where)
    assert r["p_second_better"] == pytest.approx(E.dm(a, b, actual))   # monthly closer: small
    assert r["p_first_better"] == pytest.approx(E.dm(b, a, actual))
    assert r["p_second_better"] < 0.05 < r["p_first_better"]
    assert r["commits"] == "c-once / c-monthly"


def test_a_missing_run_names_the_command_that_makes_it(store):
    where, _ = store
    with pytest.raises(LookupError, match="just train daily all"):
        S.compare(ONCE, {"model": "lear_all", "refit": "daily", "lear_window": "all"}, **where)


def test_a_held_back_run_is_never_read_for_a_validation_claim(tmp_path):
    """A newer run on the same model and schedule, but scored on 2024-25."""
    hours = pd.date_range("2023-03-13 00:00", periods=48, freq="h")
    frame = pd.DataFrame({"actual": 50.0 + np.arange(48), "naive": 40.0, "naive_field": 45.0,
                          "linear": 55.0}, index=hours)
    runs = (("once", "valid", "c-once", 52.0), ("monthly", "valid", "c-valid", 55.0),
            ("monthly", "test", "c-test", 55.0))                                 # test is newest
    for refit, split, commit, level in runs:
        frame["linear"] = level + np.sin(np.arange(48))
        rows = [E.score("linear", split, frame["linear"], frame["naive"], frame["actual"],
                        field=frame["naive_field"])]
        TR.log(rows, frame, {"refit": refit, "commit": commit},
               db=tmp_path / "mlflow.db", store=tmp_path / "mlruns")
    for _, first, second in S.COMPARISONS[:4]:              # the 2023 refit claims
        assert first["split"] == second["split"] == "valid"
    r = S.compare({**ONCE, "split": "valid"}, {**MONTHLY, "split": "valid"}, db=tmp_path / "mlflow.db")
    assert r["commits"] == "c-once / c-valid"


def test_a_pinned_run_is_read_from_its_commit_only(store):
    where, _ = store
    assert S.compare(ONCE, {**MONTHLY, "commit": "c-monthly"}, **where)["commits"] == "c-once / c-monthly"
    with pytest.raises(LookupError, match="git checkout c-later"):
        S.compare(ONCE, {**MONTHLY, "commit": "c-later"}, **where)


# ── The range comparison ──────────────────────────────────────────────────────
# Two range runs as `just quantiles` logs them.  QRA's band is the closer one but
# misses the last day, where it would have been far off, so scoring each run on
# its own hours would move its pinball.

CONFORMAL = {"model": "conformal", "window": "182", "split": "valid"}
QRA = {"model": "qra", "window": "182", "split": "valid"}


@pytest.fixture(scope="module")
def ranges(tmp_path_factory):
    where = tmp_path_factory.mktemp("mlflow")
    hours = pd.date_range("2023-03-13 00:00", periods=7 * 24, freq="h")
    n = np.arange(len(hours), dtype=float)
    actual = pd.Series(80 + 20 * np.sin(n / 4), index=hours)
    centre = {"conformal": actual + 6 * np.cos(n), "qra": actual + 2 * np.sin(n / 3)}
    centre["qra"].iloc[-24:] += 90                              # a bad day, then trimmed away
    kept = {}
    for method, mid in centre.items():
        frame = pd.DataFrame({"actual": actual, "lear": actual + 12, 10: mid - 8, 50: mid, 90: mid + 8})
        if method == "qra":
            frame = frame.iloc[:-24]
        row = {"method": method, "split": "valid", "n": len(frame),
               "pinball": E.pinball(frame[[10, 50, 90]], frame["actual"]), "window": 182}
        TR.log_range(row, frame, {"window": 182, "commit": f"c-{method}"},
                     db=where / "mlflow.db", store=where / "mlruns")
        kept[method] = frame
    return {"db": where / "mlflow.db"}, kept


def test_ranges_are_scored_on_the_hours_both_cover(ranges):
    where, kept = ranges
    shared = kept["qra"].index
    r = S.compare_ranges(CONFORMAL, QRA, **where)
    assert r["hours"] == 6 * 24
    c = kept["conformal"].loc[shared]
    assert r["first"] == pytest.approx(E.pinball(c[[10, 50, 90]], c["actual"]))
    assert r["second"] == pytest.approx(E.pinball(kept["qra"][[10, 50, 90]], kept["qra"]["actual"]))


def test_the_range_p_values_point_the_stated_way(ranges):
    where, kept = ranges
    c, q = kept["conformal"].loc[kept["qra"].index], kept["qra"]
    r = S.compare_ranges(CONFORMAL, QRA, **where)
    assert r["p_second_better"] == pytest.approx(E.dm_pinball(c[[10, 50, 90]], q[[10, 50, 90]], q["actual"]))
    assert r["p_first_better"] == pytest.approx(E.dm_pinball(q[[10, 50, 90]], c[[10, 50, 90]], q["actual"]))
    assert r["p_second_better"] < 0.05 < r["p_first_better"]  # QRA closer: small
    assert r["commits"] == "c-conformal / c-qra"


def test_a_missing_range_run_names_just_quantiles(tmp_path):
    with pytest.raises(LookupError, match="just quantiles"):
        S.compare_ranges(CONFORMAL, QRA, db=tmp_path / "mlflow.db")
