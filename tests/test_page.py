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
    assert len(axes) >= 2                                       # prices above, battery below
    assert all(len(set(axis)) == len(axis) == hours for axis in axes)


# ── What a visitor can do and see ─────────────────────────────────────────────

def test_a_real_day_button_opens_that_day():
    page = _run()
    label = page.button[0].label                                # "Big miss, kept 100%: 11 Dec 2024"
    page.button[0].click().run()
    shown = pd.Timestamp(page.date_input[0].value)
    assert shown.strftime("%b %Y") in label and f"{shown.day} " in label.split(": ")[1]


def test_every_chart_with_a_legend_has_room_to_draw():
    for spec in _specs(_run()):
        if '"orient": "top"' in json.dumps(spec):
            assert spec.get("height", 0) >= LEGEND_ROOM, spec.get("height")
