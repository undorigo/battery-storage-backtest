"""The drift checks: first, that the trial forecasts as 2023 was forecast.

The thresholds are set on 2023's stored forecasts and then compared with the
trial's, so the two must come from one recipe.  `rebuild` asks the trial's own
models for each day, and `gaps` says how far that lands from what was stored.
Both run here on small synthetic series; no cache and no MLflow are read.
"""

from __future__ import annotations

import pandas as pd
import pytest

from scripts import drift as D
from scripts import tomorrow as T

DAYS = pd.date_range("2023-03-01", periods=3)               # grid labels: Berlin days, naive
SLOTS = pd.date_range(DAYS[0], periods=24 * len(DAYS), freq="h")


def _flat(value: float, index: pd.DatetimeIndex = SLOTS) -> pd.Series:
    return pd.Series(value, index=index, dtype=float)


# ── Rebuilding: the trial's own models, one day at a time ─────────────────────
# A fake stands in for `tomorrow._models`, so the test shows the check runs the
# trial's code rather than a copy of it, and is quick.  A day a model could not
# forecast is an error: skipping it would let a match pass on fewer days than claimed.

class FakeModels:
    """`tomorrow._models` on 24 slots: LEAR 30, the tree 60, the line 90."""

    def __init__(self, stop_on: pd.Timestamp | None = None):
        self.calls, self.stop_on = [], stop_on

    def __call__(self, day, given, rows, lear_window):
        self.calls.append((day, lear_window))
        slots = pd.date_range(day, periods=24, freq="h")
        if day == self.stop_on:
            return {"tree": _flat(60, slots)}, ["LEAR: clue missing, first renew_d1_h00"], {}
        return {"LEAR": _flat(30, slots), "tree": _flat(60, slots),
                "straight line": _flat(90, slots)}, [], {}


def _given() -> T.Inputs:
    frame = pd.DataFrame({"price": 0.0}, index=SLOTS)
    return T.Inputs(raw={}, frame=frame, table=pd.DataFrame())


def test_rebuilding_asks_the_trials_models_for_each_day_in_order(monkeypatch):
    fake = FakeModels()
    monkeypatch.setattr(T, "_models", fake)
    D.rebuild(DAYS, _given(), lear_window=300)              # not the default, so it must be passed on
    assert fake.calls == [(day, 300) for day in DAYS]


def test_the_rebuilt_average_is_the_three_models_hour_by_hour(monkeypatch):
    monkeypatch.setattr(T, "_models", FakeModels())
    got = D.rebuild(DAYS, _given(), lear_window=1092)
    pd.testing.assert_series_equal(got["average"], _flat(60.0), check_names=False)
    assert list(got["LEAR"].index) == list(SLOTS)           # every day, joined in order


def test_a_day_a_model_could_not_forecast_is_an_error_not_a_skip(monkeypatch):
    monkeypatch.setattr(T, "_models", FakeModels(stop_on=DAYS[1]))
    with pytest.raises(ValueError, match="2023-03-02.*LEAR: clue missing"):
        D.rebuild(DAYS, _given(), lear_window=1092)


# ── The gaps: how far the rebuild lands from what was stored ──────────────────
# The largest difference in each day, in EUR/MWh, so one hour off shows at full
# size rather than averaged away.  Lined up by label: a stored series missing a
# day is refused, never compared with whatever day sits in its place.

def test_identical_forecasts_have_no_gap():
    same = {"LEAR": _flat(30), "average": _flat(60)}
    got = D.gaps(same, {name: s.copy() for name, s in same.items()})
    assert list(got.index) == list(DAYS)
    assert (got == 0).all().all()


def test_one_hour_off_shows_at_full_size_on_its_own_day():
    stored = _flat(60)
    stored.iloc[24 + 7] += 5                                # the second day, 07:00
    got = D.gaps({"average": _flat(60)}, {"average": stored})
    assert got["average"].tolist() == [0, 5, 0]


def test_a_stored_series_missing_a_day_is_refused():
    stored = _flat(60)[24:]                                 # the first day never stored
    with pytest.raises(ValueError, match="2023-03-01"):
        D.gaps({"average": _flat(60)}, {"average": stored})


def test_a_match_allows_no_gap_a_price_could_show():
    assert D.matches(pd.DataFrame({"average": [0.0, 0.004]}))
    assert not D.matches(pd.DataFrame({"average": [0.0, 0.01]}))   # a cent per MWh: prices show it
