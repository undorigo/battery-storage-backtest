"""The web page opens, and shows the record's headline.

Streamlit's headless runner executes `streamlit_app.py` as a visitor's browser would ask
for it, with no server.  Two things are worth pinning: that the page runs at all on the
committed file, and that it runs on the days whose shape differs.  A clock-change day has
23 or 25 hours, and the 25-hour day repeats 02:00, which would collapse two bars into one
on a chart keyed by clock time.
"""

from __future__ import annotations

import json
from datetime import date

import pytest
from streamlit.testing.v1 import AppTest

from src import config as cfg

APP = str(cfg.ROOT / "streamlit_app.py")        # AppTest resolves against the caller, not cwd


def _run(day: date | None = None) -> AppTest:
    page = AppTest.from_file(APP, default_timeout=60).run()
    if day is not None:
        page.date_input[0].set_value(day).run()
    assert not page.exception, [e.message for e in page.exception]
    return page


def test_page_shows_the_headline_from_the_record():
    tiles = {m.label: m.value for m in _run().metric[:4]}     # the headline row; the day row repeats labels
    assert tiles["Headline"] == "90.1%"
    assert tiles["Average of three"] == "94.4%"
    assert tiles["No forecast"] == "84.9%"


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
    assert day.strftime("%d %B %Y") in " ".join(m.value for m in page.markdown)
    axes = [axis for chart in page.get("vega_lite_chart")
            for axis in _hour_axes(json.loads(chart.proto.spec))]
    assert len(axes) >= 2                                       # prices above, battery below
    assert all(len(set(axis)) == len(axis) == hours for axis in axes)
