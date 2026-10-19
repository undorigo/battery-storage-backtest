"""Stage 3's script: which days LEAR walks, and what each range row scores.

LEAR, QRA and conformal are tested in `test_models.py`.  What is tested here is the
wiring around them: that the walk starts early enough for 2023's first window and
stops before the test years, and that each row describes the hours it was handed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts import quantiles as Q
from src import evaluate as E
from src import features as F


# ── Which days LEAR walks ─────────────────────────────────────────────────────
# A day table named like the real one, from January 2022 into February 2024, so
# both edges have days on the wrong side to wrongly include.  One clue is blanked
# on 9 September 2022: LEAR cannot forecast that day, so the walk must skip it.

GAP = pd.Timestamp("2022-09-09")


def day_table() -> pd.DataFrame:
    days = pd.date_range("2022-01-01", "2024-02-01", freq="D")    # naive: Berlin days
    rng = np.random.default_rng(5)
    table = pd.DataFrame(index=days)
    for h in range(24):
        table[f"price_d0_h{h:02d}"] = 100 * h + rng.uniform(0, 1, len(days))   # hour readable
        table[f"price_d1_h{h:02d}"] = table[f"price_d0_h{h:02d}"].shift(1)
    table["weekday_0"] = (days.dayofweek == 0).astype(float)
    table.loc[GAP, "price_d1_h05"] = np.nan
    return table.iloc[1:]


def test_lear_walks_from_182_days_before_2023_to_the_end_of_it():
    days = Q.walk_days(day_table())
    assert days.min() == pd.Timestamp("2022-07-03")      # 1 January's window starts here
    assert (days < pd.Timestamp("2023-01-01")).sum() == 182 - 1   # less the one gap
    assert days.max() == pd.Timestamp("2023-12-31")      # never a test-year day
    assert GAP not in days


def test_prices_land_on_the_hour_their_column_names():
    table = day_table()
    actual = Q.prices(table)
    day = pd.Timestamp("2023-03-14")
    assert actual[day + pd.Timedelta(hours=18)] == table.loc[day, "price_d0_h18"]
    assert len(actual) == 24 * len(table)


# ── What each row scores ──────────────────────────────────────────────────────
# Made-up LEAR forecasts and prices, two scored days, a short window and seven
# percentiles: enough for every coverage band, quick enough for the suite.

LEVELS = (5, 10, 25, 50, 75, 90, 95)


@pytest.fixture(scope="module")
def scored():
    idx = pd.date_range("2023-01-01", periods=40 * 24, freq="h")
    rng = np.random.default_rng(6)
    lear = pd.Series(rng.uniform(20, 200, len(idx)), index=idx)
    actual = lear + rng.normal(0, 1, len(idx)) * 0.2 * lear
    days = pd.DatetimeIndex(["2023-02-08", "2023-02-09"])
    [(_, rows, kept)] = Q.runs(lear, actual, days, [30], levels=LEVELS)   # one window: no average
    return rows, kept, days


def test_both_methods_are_scored_on_the_scored_hours_only(scored):
    rows, kept, days = scored
    hours = pd.date_range(days[0], periods=48, freq="h")
    assert [r["method"] for r in rows] == ["qra", "conformal"]
    for row in rows:
        assert row["n"] == 48 and row["window"] == 30 and row["split"] == "valid"
        assert kept[row["method"]].index.equals(hours)


def test_each_row_reproduces_from_the_table_it_keeps(scored):
    """The kept table is what MLflow stores, so it must be what was scored."""
    rows, kept, _ = scored
    for row in rows:
        q = kept[row["method"]][list(LEVELS)]
        assert E.pinball(q, kept[row["method"]]["actual"]) == row["pinball"]
        assert E.coverage(q, kept[row["method"]]["actual"], 80) == row["cover80"]


def test_kept_lines_are_in_order_and_conformal_never_crosses(scored):
    rows, kept, _ = scored
    for method, table in kept.items():
        q = table[list(LEVELS)].to_numpy()
        assert (np.diff(q, axis=1) >= 0).all(), f"{method} kept crossed lines"
    assert rows[1]["crossed"] == 0                       # widths grow with the level


def test_the_table_prints_one_line_per_method(scored):
    rows, _, _ = scored
    out = Q.table(rows)
    assert out.count("\n") == 3 and "| qra |" in out and "| conformal |" in out


def test_the_conformal_row_holds_the_symmetric_band_and_the_qra_row_does_not(scored):
    """Each row reproducing from its own table cannot show the tables were swapped:
    a swapped pair still agrees with itself.  Conformal's band is the one centred on
    LEAR, so that is checked from outside the row."""
    _, kept, _ = scored
    c, q = kept["conformal"], kept["qra"]
    np.testing.assert_allclose(c[95] - c["lear"], c["lear"] - c[5])
    assert not np.allclose(q[95] - q["lear"], q["lear"] - q[5])


# ── The average of several windows ────────────────────────────────────────────
# Three windows on the same made-up data.  The average is checked against the
# windows' own tables averaged here by hand, and its crossed hours against the
# raw lines fitted again outside the script, so neither check can agree with a
# mistake inside `runs`.

WINDOWS = [10, 20, 30]


@pytest.fixture(scope="module")
def several():
    idx = pd.date_range("2023-01-01", periods=40 * 24, freq="h")
    rng = np.random.default_rng(7)
    lear = pd.Series(rng.uniform(20, 200, len(idx)), index=idx)
    actual = lear + rng.normal(0, 1, len(idx)) * 0.2 * lear
    days = pd.DatetimeIndex(["2023-02-08", "2023-02-09"])
    return lear, actual, days, list(Q.runs(lear, actual, days, WINDOWS, levels=LEVELS))


def test_each_window_comes_first_then_their_average(several):
    *_, out = several
    assert [label for label, _, _ in out] == [10, 20, 30, "10+20+30"]
    for label, rows, _ in out:
        assert [r["window"] for r in rows] == [label, label]


def test_two_windows_are_enough_for_an_average(several):
    lear, actual, days, _ = several
    labels = [label for label, _, _ in Q.runs(lear, actual, days, [10, 20], levels=LEVELS)]
    assert labels == [10, 20, "10+20"]


def test_the_average_is_the_windows_lines_averaged(several):
    *_, out = several
    (_, _, k10), (_, _, k20), (_, _, k30), (_, rows, avg) = out
    for method in ("qra", "conformal"):
        by_hand = (k10[method][list(LEVELS)] + k20[method][list(LEVELS)]
                   + k30[method][list(LEVELS)]) / 3
        np.testing.assert_allclose(avg[method][list(LEVELS)], by_hand)
    assert rows[0]["pinball"] == E.pinball(avg["qra"][list(LEVELS)], avg["qra"]["actual"])


def test_an_averaged_hour_counts_as_crossed_if_any_window_crossed(several):
    from src import models as M

    lear, actual, days, out = several
    raw = [M.qra(lear, actual, days, w, LEVELS).to_numpy() for w in WINDOWS]
    each = [(np.sort(r, axis=1) != r).any(axis=1) for r in raw]
    assert len({int(e.sum()) for e in each}) > 1         # the windows differ, so "any" is tested
    assert out[-1][1][0]["crossed"] == int(np.logical_or.reduce(each).sum())


# ── Which windows a run scores ────────────────────────────────────────────────

def test_with_no_window_named_the_run_is_the_182_day_one():
    assert Q.windows([]) == [182]


def test_several_windows_are_scored_in_the_order_named():
    assert Q.windows(["28", "56", "91"]) == [28, 56, 91]


@pytest.mark.parametrize("window", ["183", "364", "0"])
def test_a_window_the_walk_cannot_fill_is_refused(window):
    """LEAR walks 182 days before 2023; a longer window would be short in early 2023."""
    with pytest.raises(SystemExit):
        Q.windows(["28", window])
