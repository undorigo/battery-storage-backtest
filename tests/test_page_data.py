"""The web page shows the record, not a second version of it.

`reports/page.parquet` is committed so a clean clone and the hosted page can draw every
hour without MLflow.  That makes it a copy, and a copy can drift: a rebuilt plan, a
settlement path touched, a split mislabelled.  These tests read the committed file
against the committed record, offline, so the page cannot quietly disagree with the
README.

The test that carries the weight is `test_held_back_totals_equal_the_record`: a plan
settled at anything but the real prices lands in the totals, and the totals are held
to the cent.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src import backtest as BT
from src import config as cfg

HOURS = {"valid": 8_760, "test": 17_544}               # 2023; 2024-25, both on real hours


@pytest.fixture(scope="module")
def page() -> pd.DataFrame:
    return pd.read_parquet(cfg.PAGE_DATA)


def _earned(page: pd.DataFrame, split: str) -> pd.Series:
    totals = page.loc[page.split == split].filter(like="earned:").sum()
    return totals.rename(lambda c: c.removeprefix("earned:"))


# ── Against the record ────────────────────────────────────────────────────────
# 2024-25 has rows in `capture_scores.csv`, stamped with the reading that wrote them;
# the first reading is the one the README states.  2023 has no rows file, so its
# shares are held to the figures `docs/decisions.md` states, to the decimal shown.

def test_held_back_totals_equal_the_record(page):
    record = pd.read_csv(cfg.CAPTURE_SCORES)
    first = record.loc[(record.split == "test") & (record.commit == record.commit.iloc[0])]
    got = _earned(page, "test")
    for run, earned in zip(first.run, first.earned):
        assert got[run] == pytest.approx(earned, abs=0.01), run


STATED_2023 = {"LEAR": 0.910, "tree": 0.907, "straight line": 0.916, "average": 0.939,
               "naive (field)": 0.795, "bids strict": 0.810, "bids pair": 0.922}

def test_2023_shares_equal_the_stated_ones(page):
    got = _earned(page, "valid")
    assert round(got["ceiling"]) == 50_557
    for run, share in STATED_2023.items():
        assert round(got[run] / got["ceiling"], 3) == share, run


# ── What the page can rely on ─────────────────────────────────────────────────
# Every hour present and complete, so a chart never draws a gap the data does not
# have, and no day above the ceiling: two runs beat it by about a cent, the
# solver's tolerance (27 October), so a few cents are allowed and nothing more.

def test_every_hour_is_complete(page):
    assert page.split.value_counts().to_dict() == HOURS
    assert page.index.is_unique and str(page.index.tz) == "UTC"
    assert not page.drop(columns="split").isna().any().any()
    assert (page.p10 <= page.p90).all()


def test_no_day_beats_the_ceiling(page):
    per_day = page.filter(like="earned:").groupby(BT.delivery_days(page.index)).sum()
    above = per_day.sub(per_day["earned:ceiling"], axis=0)
    assert above.max().max() < 0.05
