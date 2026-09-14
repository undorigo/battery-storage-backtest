"""Contract 1, as far as it can be checked without the network.

These tests do not prove a series is a forecast — only measurement does that, and
scripts/verify_forecast_series.py is where it happens. What they do is keep the
catalog internally honest: every entry callable, the forbidden item still
forbidden, and the target never mistaken for a feature.

The expensive check runs once per series. This one runs in milliseconds, every
time, which is what makes it the permanent guard.
"""

import pytest
from entsoe import EntsoePandasClient

from src.sources import entsoe as cat


# ── The catalog must be callable ──────────────────────────────────────────────
# Methods are referenced by name so the catalog stays plain data, which costs the
# import-time failure a direct reference would give. This test buys it back.

@pytest.mark.parametrize("key", sorted(cat.CATALOG))
def test_every_query_resolves_to_a_real_method(key):
    item = cat.CATALOG[key]
    assert hasattr(EntsoePandasClient, item.query), (
        f"{key!r} names {item.query!r}, which entsoe-py does not provide"
    )
    assert callable(getattr(EntsoePandasClient, item.query))


@pytest.mark.parametrize("key", sorted(cat.CATALOG))
def test_key_matches_its_dict_entry(key):
    """A record filed under the wrong key would cache to the wrong directory."""
    assert cat.CATALOG[key].key == key


def test_no_two_items_share_a_query_method():
    """The leak, in the form it would actually take.

    `hasattr` only asks whether a method exists, so pointing load_forecast at
    query_load — the actuals — satisfies it perfectly. Two items resolving to the
    same call means one of them is fetching the other's data, which is precisely
    the mistake Contract 1 exists to prevent, and it is invisible otherwise.
    """
    queries = [item.query for item in cat.CATALOG.values()]
    duplicated = {q for q in queries if queries.count(q) > 1}
    assert not duplicated, f"more than one catalog item fetches via {duplicated}"


# ── Contract 1 ────────────────────────────────────────────────────────────────
# The two that must never be feature-eligible, named individually rather than
# counted, so that adding a series cannot quietly flip one of them.

def test_actual_generation_is_never_feature_eligible():
    """The hindsight series. A model given this scores beautifully and is worthless."""
    assert cat.CATALOG["actual_generation"].known_before_gate_closure is False
    assert "actual_generation" not in cat.FEATURE_ELIGIBLE


def test_the_target_is_not_feature_eligible():
    """Day D's price is what we predict, and it clears after gate closure has passed.

    Lagged prices are legitimate and are features.py's business — the lag is what
    makes the value old enough to have been public at the decision point.
    """
    assert cat.TARGET.key == "day_ahead_price"
    assert cat.TARGET.known_before_gate_closure is False


def test_feature_eligible_holds_exactly_the_two_forecasts():
    assert set(cat.FEATURE_ELIGIBLE) == {"load_forecast", "wind_solar_forecast"}


@pytest.mark.parametrize("key", sorted(cat.CATALOG))
def test_every_item_states_when_it_becomes_public(key):
    """A boolean with no stated reason cannot be reviewed, only trusted."""
    item = cat.CATALOG[key]
    assert item.publication.strip(), f"{key} does not say when it is published"
    assert len(item.why.strip()) > 40, f"{key} does not explain itself"


# ── The audit trail ───────────────────────────────────────────────────────────
# A01 against A16 is the leak. The code never reads these, so nothing else would
# notice if one drifted.

def test_forecast_items_declare_the_day_ahead_process_type():
    for key in ("load_forecast", "wind_solar_forecast"):
        assert cat.CATALOG[key].process_type == "A01", (
            f"{key} must be the day-ahead process type, not a realised one"
        )


def test_actual_generation_declares_the_realised_process_type():
    assert cat.CATALOG["actual_generation"].process_type == "A16"


def test_the_document_and_process_pair_is_unique_per_item():
    """It is the pair that identifies a series, not the document type alone.

    Load forecast and actual load are both A65; only the process type separates
    them, A01 against A16. An earlier version of this test asserted that document
    types alone were distinct, which is simply untrue of ENTSO-E's model — and it
    passed only because the forbidden twin was missing from the catalog.
    """
    pairs = [(i.document_type, i.process_type) for i in cat.CATALOG.values()]
    assert len(pairs) == len(set(pairs))


def test_each_forecast_has_its_forbidden_twin_catalogued():
    """The pairs the verification script compares, and the pairs a mistake swaps."""
    for forecast, actual in (("load_forecast", "actual_load"),
                             ("wind_solar_forecast", "actual_generation")):
        assert cat.CATALOG[forecast].known_before_gate_closure is True
        assert cat.CATALOG[actual].known_before_gate_closure is False


# ── Lookup ────────────────────────────────────────────────────────────────────

def test_get_returns_the_item():
    assert cat.get("day_ahead_price") is cat.CATALOG["day_ahead_price"]


def test_get_raises_on_a_typo_rather_than_returning_none():
    with pytest.raises(KeyError, match="Unknown data item"):
        cat.get("day_ahead_prices")          # the plural is the natural mistake
