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


# ── The band: the trial's own `tomorrow.band`, handed one day's LEAR ──────────
# A fake stands in for it.  Each call must see that day's 24 slots of LEAR alone,
# as an evening does, and the window asked for.  A day without a band is an error.

class FakeBand:
    """`tomorrow.band`: p10 at LEAR minus 10, p90 at LEAR plus 10."""

    def __init__(self, none_on: pd.Timestamp | None = None):
        self.calls, self.none_on = [], none_on

    def __call__(self, got, given, lear_window):
        self.calls.append((got.day, list(got.forecasts.index), lear_window))
        if got.day == self.none_on:
            return None
        lear = got.forecasts["LEAR"]
        return pd.DataFrame({10: lear - 10, 90: lear + 10})


def _lear() -> pd.Series:
    return pd.Series(range(len(SLOTS)), index=SLOTS, dtype=float)


def test_each_band_is_asked_for_with_its_own_days_lear_alone(monkeypatch):
    fake = FakeBand()
    monkeypatch.setattr(T, "band", fake)
    D.rebuild_band(DAYS, _given(), _lear(), lear_window=300)
    assert fake.calls == [(day, list(pd.date_range(day, periods=24, freq="h")), 300) for day in DAYS]


def test_the_bands_are_joined_by_percentile_in_order(monkeypatch):
    monkeypatch.setattr(T, "band", FakeBand())
    got = D.rebuild_band(DAYS, _given(), _lear(), lear_window=300)
    pd.testing.assert_series_equal(got["p90"], _lear() + 10, check_names=False)
    assert set(got) == {"p10", "p90"}


def test_a_day_without_a_band_is_an_error_not_a_skip(monkeypatch):
    monkeypatch.setattr(T, "band", FakeBand(none_on=DAYS[2]))
    with pytest.raises(ValueError, match="2023-03-03.*no band"):
        D.rebuild_band(DAYS, _given(), _lear(), lear_window=300)


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


# ── A reading: the last 28 days with rows, two numbers ────────────────────────
# Coverage is the share of hours whose price landed inside p10 to p90, the edges
# counting as inside (as `evaluate.coverage` counts them).  The error is the
# average's mean absolute error over the field rule's, the project's rMAE.  A day
# with no rows is skipped, not counted as a day: the trial's record has a hole.

def _hourly(days: int, start: str = "2023-01-01") -> pd.DataFrame:
    """Every hour: price 100 on the band's lower edge (100 to 110), the average 5 off, the rule 10 off."""
    idx = pd.date_range(start, periods=24 * days, freq="h")
    return pd.DataFrame({"actual": 100.0, "average": 105.0, "naive": 90.0,
                         "p10": 100.0, "p90": 110.0}, index=idx)


def test_a_reading_needs_28_days_with_rows():
    assert D.readings(_hourly(27)).empty
    got = D.readings(_hourly(30))
    assert list(got.index) == list(pd.date_range("2023-01-28", "2023-01-30"))   # labelled by its last day


def test_every_price_inside_reads_full_coverage_and_the_rmae_is_the_error_ratio():
    got = D.readings(_hourly(28))
    assert got.coverage.tolist() == [1.0]                   # on p10, the edge: inside
    assert got.rmae.tolist() == [0.5]                       # 5 off against 10 off


def test_the_rmae_is_the_windows_errors_summed_not_its_days_ratios_averaged():
    hourly = _hourly(28)
    hourly["average"], hourly["naive"] = 101.0, 101.0       # every day: 1 off, ratio 1
    first = hourly.index[:24]
    hourly.loc[first, "average"], hourly.loc[first, "naive"] = 110.0, 120.0   # day 1: 10 off, 20 off
    got = D.readings(hourly)
    assert got.rmae.iloc[0] == pytest.approx(37 / 47)       # not (0.5 + 27) / 28


def test_coverage_counts_hours_outside_in_its_own_window_only():
    hourly = _hourly(29)
    hourly.loc[hourly.index[:24], "actual"] = 200.0         # the first day: every price above p90
    got = D.readings(hourly)
    assert got.coverage.tolist() == [27 / 28, 1.0]          # gone once the window has moved on


def test_a_day_without_rows_is_skipped_not_counted():
    hourly = _hourly(29)
    hourly = hourly[hourly.index.normalize() != pd.Timestamp("2023-01-10")]
    got = D.readings(hourly)
    assert list(got.index) == [pd.Timestamp("2023-01-29")]  # 28 days with rows, over 29 on the calendar


# ── The thresholds: where 2023's readings rarely went ─────────────────────────
# Coverage flags below the 5th percentile of 2023's readings, the error above the
# 95th: on 2023 itself each line is crossed in about one reading in twenty.

def test_the_lines_are_2023s_5th_and_95th_percentiles():
    read = pd.DataFrame({"coverage": range(101), "rmae": range(101)}, dtype=float)
    assert D.thresholds(read) == {"coverage_below": 5.0, "rmae_above": 95.0}


def test_a_reading_flags_below_the_coverage_line_or_above_the_error_line():
    lines = {"coverage_below": 0.7, "rmae_above": 0.6}
    read = pd.DataFrame({"coverage": [0.8, 0.69, 0.8, 0.7], "rmae": [0.5, 0.5, 0.61, 0.6]})
    got = D.flags(read, lines)
    assert got.coverage.tolist() == [False, True, False, False]   # on the line is not below it
    assert got.rmae.tolist() == [False, False, True, False]


# ── The 2026 replay, exported once for GitHub ─────────────────────────────────
# The replay's hourly table lives in MLflow on one machine, and the trial's first
# readings reach back into it.  The export keeps what the two signals read, and
# never writes over a file that disagrees: the replay was read once, so a second
# run in MLflow is a change to be looked at, not a newer copy to take.

REPLAY_SLOTS = pd.date_range("2026-10-30", periods=48, freq="h")   # grid labels, naive


def _kept(shift: float = 0.0) -> pd.DataFrame:
    """The replay run's table: price, five forecasts, percentile k valued k."""
    kept = pd.DataFrame({"actual": 42.394999999999996 + shift,   # pandas' fast parser reads 42.395
                         "LEAR": 1.0, "tree": 2.0,
                         "straight line": 3.0, "average": 2.0, "naive (field)": 4.0},
                        index=REPLAY_SLOTS)
    for level in range(1, 100):
        kept[level] = float(level)
    return kept


@pytest.fixture
def stored_replay(monkeypatch):
    """A fake MLflow: `latest` names the run, `read_range` hands back its table."""
    held = {"kept": _kept()}
    monkeypatch.setattr(D.TR, "latest", lambda **params: "run123" if params else None)
    monkeypatch.setattr(D.TR, "read_range",
                        lambda run: ({"commit": "abc1234", "split": "2026"}, held["kept"]))
    return held


def test_the_export_keeps_the_price_the_five_forecasts_and_the_bands_edges():
    got = D.replay_table(_kept())
    assert list(got.columns) == ["actual", "LEAR", "tree", "straight line", "average",
                                 "naive (field)", "p10", "p90"]
    assert (got.p10 == 10).all() and (got.p90 == 90).all()  # each edge from its own percentile


def test_the_exported_file_reads_back_exactly(stored_replay, tmp_path):
    path = tmp_path / "replay.csv"
    assert D.export(path) == 0
    pd.testing.assert_frame_equal(D.read_replay(path), D.replay_table(_kept()),
                                  check_exact=True, check_freq=False)


def test_a_second_export_that_agrees_leaves_the_file_alone(stored_replay, tmp_path):
    path = tmp_path / "replay.csv"
    D.export(path)
    before = path.stat().st_mtime_ns
    assert D.export(path) == 0
    assert path.stat().st_mtime_ns == before


def test_an_export_that_disagrees_is_refused_and_the_file_kept(stored_replay, tmp_path):
    path = tmp_path / "replay.csv"
    D.export(path)
    written = path.read_bytes()
    stored_replay["kept"] = _kept(shift=0.01)                # a different replay in MLflow
    assert D.export(path) == 1
    assert path.read_bytes() == written


def test_the_committed_replay_holds_every_hour_of_its_ten_months():
    got = D.read_replay()                                    # the committed file: no MLflow needed
    expected = pd.date_range("2026-01-01", "2026-10-31 23:00", freq="h")   # 304 days on the grid
    assert list(got.index) == list(expected)
    assert not got.isna().any().any()
    assert (got.p10 <= got.p90).all()                        # the edges not swapped
