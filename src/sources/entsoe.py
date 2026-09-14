"""What this project pulls from ENTSO-E, and what may be done with each item.

Owner of the Contract 1 claim.  Every series has a record here stating when its
value becomes public relative to gate closure, so "was this knowable at 12:00 on
D-1?" is a field a test can read rather than a comment nobody re-reads.

The forbidden series is deliberately listed rather than omitted.  Actual
generation is the hindsight trap this contract exists to prevent, and a test can
only assert that no feature derives from it if it has a record to point at.

Adding a fifth series should be a new entry here and nothing else.
"""

from __future__ import annotations

from dataclasses import dataclass


# ── The record ────────────────────────────────────────────────────────────────
# Two fields carry the contract and the rest is context.  `known_before_gate_closure`
# is the testable one; `publication` says in words what it means, because a bare
# boolean tells a later reader nothing about why it was set that way.

@dataclass(frozen=True)
class DataItem:
    """One ENTSO-E series, and the terms on which this project may use it."""

    key: str                      # our name; becomes the cache directory
    query: str                    # entsoe-py method, resolved by name at call time
    unit: str

    # What the API was observed to return, not what it promises.  Recorded so the
    # normaliser can compare it against what actually arrives and complain if the
    # two diverge — the October 2025 switch would have been caught that way.  That
    # comparison does not exist yet; until it does this is documentation.
    expected_resolution: str
    publication: str              # when the value for delivery period t becomes public
    known_before_gate_closure: bool
    why: str

    # Audit trail.  The code never reads these — entsoe-py builds the request — but
    # A01 against A16 *is* the leak, and these are what a reviewer checks against
    # ENTSO-E's own documentation.  The library does not expose what it actually
    # sends, so treat them as a documented claim, verified separately and
    # empirically by scripts/verify_forecast_series.py.
    document_type: str
    process_type: str | None = None


# ── The catalog ───────────────────────────────────────────────────────────────
# Five items: the target, two features, and the two hindsight twins those features
# would be confused with.  Each forbidden series sits beside the one it shadows.
#
# Note what `known_before_gate_closure` means, because it is narrower than it
# looks: may the value for delivery period t be used to predict period t?  For the
# price the answer is no — it is the target, and the auction publishes it after
# gate closure has already passed.  Lagged prices are a different question and a
# legitimate feature; features.py owns that, because the lag is what makes the
# value old enough to have been public.

CATALOG: dict[str, DataItem] = {
    "day_ahead_price": DataItem(
        key="day_ahead_price",
        query="query_day_ahead_prices",
        unit="EUR/MWh",
        expected_resolution="60min, then 15min from 2025-10-01",
        publication="D-1, shortly after the 12:00 auction closes",
        known_before_gate_closure=False,
        why=(
            "The target. Its value for day D is published only once the auction has "
            "cleared, which is after the moment the schedule had to be committed. "
            "Lagged prices are a different matter and are allowed — the price of D-1 "
            "was public well before gate closure for D."
        ),
        document_type="A44",
    ),
    "load_forecast": DataItem(
        key="load_forecast",
        query="query_load_forecast",
        unit="MW",
        expected_resolution="15min",
        publication="D-1, before gate closure",
        known_before_gate_closure=True,
        why=(
            "The TSOs' own day-ahead expectation of demand, and part of what the "
            "market priced. Actual load is the hindsight twin — same units, same "
            "shape, a different process type."
        ),
        document_type="A65",
        process_type="A01",
    ),
    "wind_solar_forecast": DataItem(
        key="wind_solar_forecast",
        query="query_wind_and_solar_forecast",
        unit="MW",
        expected_resolution="15min",
        publication="D-1, before gate closure",
        known_before_gate_closure=True,
        why=(
            "Solar, wind onshore and wind offshore in one response. This already "
            "contains the weather forecast, converted onto the real installed fleet "
            "by people with turbine-level data, which is why no weather source is "
            "needed. Residual load is derived from this and the load forecast."
        ),
        document_type="A69",
        process_type="A01",
    ),
    "actual_load": DataItem(
        key="actual_load",
        query="query_load",
        unit="MW",
        expected_resolution="15min",
        publication="after delivery",
        known_before_gate_closure=False,
        why=(
            "Forbidden as a feature, and the twin of load_forecast — same units, "
            "same shape, one process type apart. Listed for the same reason as "
            "actual_generation: the prohibition is only testable if the trap has a "
            "record. verify_forecast_series.py compares the load forecast against it."
        ),
        document_type="A65",
        process_type="A16",
    ),
    "actual_generation": DataItem(
        key="actual_generation",
        query="query_generation",
        unit="MW",
        expected_resolution="15min",
        publication="after delivery",
        known_before_gate_closure=False,
        why=(
            "Forbidden as a feature, and present so that the prohibition is testable. "
            "Nobody knew these values when the schedule was committed, and they "
            "predict the price almost directly — a model given them scores beautifully "
            "and would lose money. Kept because verify_forecast_series.py needs "
            "something to compare the forecasts against, and because stage 2 may model "
            "where those forecasts are systematically wrong."
        ),
        document_type="A75",
        process_type="A16",
    ),
}

# Convenience views.  Spelled out rather than filtered at each call site, so the
# distinction that matters most in this project reads as a noun.
FEATURE_ELIGIBLE = {k: v for k, v in CATALOG.items() if v.known_before_gate_closure}
TARGET = CATALOG["day_ahead_price"]


def get(key: str) -> DataItem:
    """Look up one item, failing loudly on a typo rather than returning None."""
    try:
        return CATALOG[key]
    except KeyError:
        raise KeyError(f"Unknown data item {key!r}. Known: {sorted(CATALOG)}") from None
