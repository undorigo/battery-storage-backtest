"""The web page opens, shows the record's money, and draws every chart it promises.

Streamlit's headless runner executes `streamlit_app.py` as a visitor's browser would ask
for it, with no server.  It reads the charts' specifications, not their pixels, so what
it can pin is what a specification states: which numbers, which hours, how tall.

Two failures happened and are pinned here.  A 25-hour clock-change day repeats 02:00,
which collapsed two hours into one on a chart keyed by clock time.  And Streamlit fits
a chart's title and legend inside the height it is given: at 150 pixels the battery
chart's drawing area shrank to nothing on the hosted page (2 November 2026).  The
height test is a stand-in for looking; the page is still checked in a browser.
"""

from __future__ import annotations

import json
import re
from datetime import date

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src import config as cfg

APP = str(cfg.ROOT / "streamlit_app.py")        # AppTest resolves against the caller, not cwd
LEGEND_ROOM = 250                               # pixels a chart with a legend on top needs


def _run(day: date | None = None) -> AppTest:
    page = AppTest.from_file(APP, default_timeout=60).run()
    if day is not None:
        page.date_input[0].set_value(day).run()
    assert not page.exception, [e.message for e in page.exception]
    return page


def _specs(page: AppTest) -> list[dict]:
    return [json.loads(chart.proto.spec) for chart in page.get("vega_lite_chart")]


def _text(page: AppTest) -> str:
    return " ".join(m.value for m in page.markdown)


# ── The money, against the record ─────────────────────────────────────────────

def test_page_leads_with_the_recorded_euros():
    record = pd.read_csv(cfg.CAPTURE_SCORES)
    first = record.loc[(record.split == "test") & (record.commit == record.commit.iloc[0])]
    euros = dict(zip(first.run, first.earned / 2))            # 2024 and 2025: two years
    tiles = {m.label: m.value for m in _run().metric[:3]}     # the headline row
    assert tiles == {"The maximum": f"{euros['ceiling']:,.0f} €",
                     "Our forecast": f"{euros['bids strict']:,.0f} €",
                     "No forecast": f"{euros['naive (field)']:,.0f} €"}


# ── Every hour of a clock-change day ──────────────────────────────────────────

def _hour_axes(spec: dict | list) -> list[list[str]]:
    """Every hour-of-day axis in a chart: the order list of each `slot` x encoding."""
    found = []
    if isinstance(spec, dict):
        if spec.get("field") == "slot" and isinstance(spec.get("sort"), list):
            found.append(spec["sort"])
        for value in spec.values():
            found += _hour_axes(value)
    elif isinstance(spec, list):
        for value in spec:
            found += _hour_axes(value)
    return found


@pytest.mark.parametrize("day, hours", [(date(2025, 3, 30), 23), (date(2025, 10, 26), 25)])
def test_page_draws_every_hour_of_a_clock_change_day(day, hours):
    page = _run(day)
    assert f"{day.day} {day.strftime('%B %Y')}" in _text(page)
    axes = [axis for spec in _specs(page) for axis in _hour_axes(spec)]
    assert all(len(set(axis)) == len(axis) for axis in axes)    # no hour drawn over another
    assert sum(len(axis) == hours for axis in axes) >= 2        # the day's prices and battery


# ── What a visitor can do and see ─────────────────────────────────────────────

def test_the_example_days_open_in_explore_a_day():
    page = _run()
    named = next(m.value for m in page.markdown if "Off by" in m.value and "right places" in m.value)
    page.get("button_group")[1].set_value("Big miss, order right").run()
    shown = pd.Timestamp(page.date_input[0].value)
    assert f"{shown.day} {shown.strftime('%B %Y')}" in named          # the day Part 2 describes


def test_no_sentence_names_the_same_share_twice():
    assert not re.search(r"(\d+%) (?:to|and) \1", _text(_run()))    # "97% to 97%"


def test_every_chart_with_a_legend_has_room_to_draw():
    for spec in _specs(_run()):
        if '"orient": "top"' in json.dumps(spec):
            assert spec.get("height", 0) >= LEGEND_ROOM, spec.get("height")


# ── Part 2's claim, held to the data ──────────────────────────────────────────
# Part 2 opens with a fixed sentence: the order of the hours moves the money, the
# size of the miss barely does.  The four numbers under it are recomputed from the
# file, so this keeps the sentence true if the file is ever rebuilt.

@pytest.mark.parametrize("period", ["2024–25: the test years", "2023: the practice year"])
def test_the_order_moves_the_money_and_the_miss_does_not(period):
    page = _run()
    page.get("button_group")[0].set_value(period).run()
    table = next(m.value for m in page.markdown if m.value.startswith("| |"))
    (a, b), (c, d) = [[int(v) for v in re.findall(r"\*\*(\d+)%\*\*", line)]
                      for line in table.splitlines()[2:]]              # rows: in order, less
    by_order = (a + b) / 2 - (c + d) / 2                               # down a column
    by_miss = abs((a + c) / 2 - (b + d) / 2)                           # across a row
    assert by_order > 0 and by_order > 2 * by_miss, (a, b, c, d)
