"""Prove that the series we treat as forecasts are forecasts, not actuals.

Run:  python -m scripts.verify_forecast_series

Contract 1 says every feature must have been knowable at 12:00 on D-1.  The API
cannot answer that question: it indexes values by the hour they describe, never by
the moment they were published.  Ask it for "wind on 1 June 2024" and it will
answer whether you wanted the forecast or the outcome — the two differ only by a
couple of request parameters, and both come back as megawatts on the same index.

Pull the wrong one and nothing breaks.  The split stays clean, the target is still
withheld, no test fails.  The model simply knows what actually happened, scores
beautifully, and would lose money in production.

So this compares each forecast against its own actual.  A forecast tracks reality
closely and is never equal to it.  Actuals are equal to themselves.  A mean
absolute error of exactly zero means the same series was pulled twice.

This is a one-off check per series, re-run only when a source, a parameter or the
client library changes.  The cheap permanent guard is the request parameters
themselves, asserted offline in the test suite.
"""

from __future__ import annotations

import os
import sys

import pandas as pd
from dotenv import load_dotenv

from src import config as cfg

# ── Window ────────────────────────────────────────────────────────────────────
# Deliberately inside the training period.  Contract 2 keeps the test years for a
# single evaluation at the end of a stage, and there is no reason to spend any of
# that budget on a provenance check that any fortnight answers equally well.

START = pd.Timestamp("2022-06-01", tz=cfg.TZ_MARKET)
END = pd.Timestamp("2022-06-15", tz=cfg.TZ_MARKET)

IDENTICAL_TOL = 1e-9        # below this, two series are the same series


def _compare(name: str, forecast: pd.Series, actual: pd.Series) -> bool:
    """Report one pair and return True if it behaves like a forecast."""
    both = pd.concat(
        [forecast.rename("f"), actual.rename("a")], axis=1, join="inner"
    ).dropna()                                          # align on timestamp, not position

    if both.empty:
        print(f"  {name:<16} NO OVERLAP — cannot verify")
        return False

    err = both.f - both.a
    is_identical = bool((err.abs() < IDENTICAL_TOL).all())   # the failure we are hunting
    verdict = "!! IDENTICAL — LEAK" if is_identical else "forecast"
    print(
        f"  {name:<16}{len(both):>7}{both.f.corr(both.a):>9.4f}"
        f"{err.abs().mean():>11,.0f}{err.mean():>+11,.0f}   {verdict}"
    )
    return not is_identical


def _actual_column(df: pd.DataFrame, tech: str) -> pd.Series:
    """Pick one technology's generation out of the actuals frame.

    Actual generation arrives with MultiIndex columns because a technology can both
    generate and consume — pumped storage does each in different hours.  Flattening
    to the first level would collide those two, so the pair is addressed in full.
    """
    if isinstance(df.columns, pd.MultiIndex):
        return df[(tech, "Actual Aggregated")]
    return df[tech]


def main() -> int:
    load_dotenv(cfg.ROOT / ".env")                      # token never enters the repo
    token = os.getenv("ENTSOE_API_KEY")
    if not token:
        print("ENTSOE_API_KEY missing — copy .env.example to .env and fill it in")
        return 2

    from entsoe import EntsoePandasClient                # imported late so --help stays fast

    client = EntsoePandasClient(api_key=token, timeout=90)   # platform can be slow
    print(f"Window: {START.date()} to {END.date()} (training period)\n")
    print(f"  {'series':<16}{'hours':>7}{'corr':>9}{'MAE (MW)':>11}{'bias (MW)':>11}   verdict")
    print("  " + "-" * 72)

    ok = []

    # ── Load ──────────────────────────────────────────────────────────────────
    # The day-ahead load forecast is published by the TSOs well before gate
    # closure; actual load is only known after the hour has passed.
    forecast = client.query_load_forecast(cfg.BIDDING_ZONE, start=START, end=END).iloc[:, 0]
    actual = client.query_load(cfg.BIDDING_ZONE, start=START, end=END).iloc[:, 0]
    ok.append(_compare("Load", forecast, actual))

    # ── Wind and solar ────────────────────────────────────────────────────────
    # One request returns all three technologies as columns.  Each is checked
    # separately, because a mistake could affect one series and not the others.
    ws_forecast = client.query_wind_and_solar_forecast(cfg.BIDDING_ZONE, start=START, end=END)
    ws_actual = client.query_generation(cfg.BIDDING_ZONE, start=START, end=END)

    for tech in ("Solar", "Wind Onshore", "Wind Offshore"):
        try:
            ok.append(_compare(tech, ws_forecast[tech], _actual_column(ws_actual, tech)))
        except KeyError:
            print(f"  {tech:<16} column absent from the response")
            ok.append(False)

    failed = ok.count(False)
    print()
    if failed:
        print(f"{failed} series did not verify. Treat them as hindsight until resolved.")
        return 1
    print("All series behave like forecasts: correlated with reality, never equal to it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
