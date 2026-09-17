"""Describe seven years of German day-ahead prices.

Run:  just explore

Produces the two numbers stage 0 asks for — negative-price hours per year and the
average daily spread — and the figures the README refers to.  Every figure quoted
anywhere in this project comes from here, so a number and its picture cannot drift
apart, and both regenerate from a clean clone with one command.

Grouping is by *market-local* day and year throughout.  A delivery day is a Berlin
calendar day, the auction clears it as a block, and a battery's cycle lives inside
one.  Grouping by UTC day would cut each of them two hours early.
"""

from __future__ import annotations

import sys

import matplotlib
matplotlib.use("Agg")                               # write files, never open a window
import matplotlib.pyplot as plt
import pandas as pd

from src import config as cfg
from src import data

FLOOR = -500.0                                      # EPEX SPOT's minimum bid, for context


def local(series: pd.Series) -> pd.Series:
    """Re-index onto the market clock and clip to the project's window.

    The clip matters.  A request is half-open at its lower end but the client
    truncates inclusively at the upper, so the price series carries one hour past
    the end of 2025 — 00:00 on 1 January in market time.  Left alone it becomes a
    one-day "2026" in every table, with a daily spread of zero.
    """
    out = series.set_axis(series.index.tz_convert(cfg.TZ_MARKET))
    first = pd.Timestamp(cfg.HISTORY_START, tz=cfg.TZ_MARKET)
    last = pd.Timestamp(cfg.TEST_END, tz=cfg.TZ_MARKET) + pd.DateOffset(days=1)
    return out[(out.index >= first) & (out.index < last)]


# ── The two headline numbers ──────────────────────────────────────────────────
# Negative hours say how often the system had more power than it could use.  The
# daily spread says how much there was to earn by moving energy within a day —
# which is the only thing a battery is paid for.

def negative_hours(price: pd.Series) -> pd.DataFrame:
    """How many hours each year cleared below zero, and how far below."""
    by_year = price.groupby(price.index.year)
    return pd.DataFrame({
        "hours": by_year.apply(lambda s: int((s < 0).sum())),
        "share": by_year.apply(lambda s: (s < 0).mean() * 100),
        "deepest": by_year.min(),
        "at_floor": by_year.apply(lambda s: int((s <= FLOOR).sum())),
    })


def daily_spread(price: pd.Series) -> pd.DataFrame:
    """Highest minus lowest price within each delivery day, averaged per year."""
    day = price.groupby(price.index.normalize())       # local calendar days
    spread = day.max() - day.min()
    by_year = spread.groupby(spread.index.year)
    return pd.DataFrame({
        "mean": by_year.mean(),
        "median": by_year.median(),
        "widest": by_year.max(),
        "days": by_year.size(),
    })


def as_markdown(df: pd.DataFrame, headers: list[str], fmts: list[str]) -> str:
    """Render a table ready to paste into the README, so the two cannot disagree."""
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for year, row in df.iterrows():
        cells = [str(year)] + [f.format(v) for f, v in zip(fmts, row)]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


# ── The figures ───────────────────────────────────────────────────────────────
# Named README_* because .gitignore excludes generated figures except that prefix:
# a picture the README points at has to survive a clean clone, and everything else
# is rebuilt on demand.

def figure_history(price: pd.Series, path):
    """Monthly average against the range it was drawn from."""
    monthly = price.resample("MS")
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.fill_between(monthly.mean().index, monthly.min(), monthly.max(),
                    alpha=0.18, color="#4a6fa5", linewidth=0, label="monthly range")
    ax.plot(monthly.mean().index, monthly.mean(), color="#1f3a5f", lw=1.6, label="monthly mean")
    ax.axhline(0, color="#b4433a", lw=0.9, ls="--", label="zero")
    ax.set_ylabel("EUR/MWh")
    ax.set_title("DE-LU day-ahead price, Oct 2018 – Dec 2025", loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


def figure_trends(neg: pd.DataFrame, spread: pd.DataFrame, path):
    """The two headline numbers side by side, because the question is whether they move."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 3.8))
    a.bar(neg.index, neg["hours"], color="#b4433a", width=0.62)
    a.set_title("Hours cleared below zero", loc="left", fontsize=10)
    a.set_ylabel("hours per year")
    b.bar(spread.index, spread["mean"], color="#1f3a5f", width=0.62)
    b.set_title("Average daily spread (highest − lowest)", loc="left", fontsize=10)
    b.set_ylabel("EUR/MWh")
    for ax in (a, b):
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xticks(neg.index)
        ax.tick_params(labelsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


def figure_residual(path) -> str:
    """Price against what thermal plants must cover — the mechanism behind the rest.

    Residual load is demand minus wind and solar, built entirely from forecasts
    published before gate closure.  It is the single strongest driver of the price
    and the reason no weather source is needed.
    """
    load = data.load("load_forecast").iloc[:, 0]
    ws = data.load("wind_solar_forecast")
    price = data.load("day_ahead_price").iloc[:, 0]

    residual = load - ws["Wind Onshore"] - ws["Wind Offshore"] - ws["Solar"]
    both = pd.concat([local(residual).rename("residual"), local(price).rename("price")],
                     axis=1, join="inner").dropna()

    # Coloured by year on purpose.  Pooling seven years hides the finding: the same
    # residual load cleared near 40 EUR/MWh in 2019 and near 300 in 2022, so the
    # cloud is several relationships stacked rather than one scattered.
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    years = sorted(both.index.year.unique())
    colours = plt.cm.viridis([i / max(len(years) - 1, 1) for i in range(len(years))])
    for colour, year in zip(colours, years):
        part = both[both.index.year == year]
        ax.scatter(part.residual / 1000, part.price, s=1.6, alpha=0.10,
                   color=colour, edgecolors="none", rasterized=True, label=str(year))
    ax.axhline(0, color="#b4433a", lw=0.9, ls="--")
    ax.set_xlabel("residual load (GW)  =  demand − wind − solar")
    ax.set_ylabel("day-ahead price (EUR/MWh)")
    ax.set_title("What thermal plants must cover, against what it cost", loc="left", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    leg = ax.legend(frameon=False, fontsize=8, markerscale=6, loc="upper left")
    for handle in leg.legend_handles:
        handle.set_alpha(1)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)

    per_year = both.groupby(both.index.year).apply(
        lambda d: d.residual.corr(d.price), include_groups=False
    )
    return both, per_year


def main() -> int:
    try:
        price = local(data.load("day_ahead_price").iloc[:, 0]).dropna()
    except FileNotFoundError as exc:
        print(exc)
        return 2

    neg, spread = negative_hours(price), daily_spread(price)

    print(f"DE-LU day-ahead price — {len(price):,} hours, "
          f"{price.index.min():%Y-%m-%d} to {price.index.max():%Y-%m-%d}\n")

    print("Negative-price hours\n")
    print(as_markdown(neg, ["Year", "Hours below zero", "Share", "Deepest", "At the -500 floor"],
                      ["{:,.0f}", "{:.1f} %", "{:,.2f}", "{:,.0f}"]))

    print("\n\nAverage daily spread\n")
    print(as_markdown(spread, ["Year", "Mean spread", "Median", "Widest day", "Days"],
                      ["{:,.1f}", "{:,.1f}", "{:,.1f}", "{:,.0f}"]))

    cfg.FIGURES.mkdir(parents=True, exist_ok=True)
    figure_history(price, cfg.FIGURES / "README_price_history.png")
    figure_trends(neg, spread, cfg.FIGURES / "README_negative_hours_and_spread.png")
    both, per_year = figure_residual(cfg.FIGURES / "README_residual_load_vs_price.png")

    print("\n\nResidual load against price\n")
    print(f"pooled over all {len(both):,} hours: {both.residual.corr(both.price):.3f}")
    print("within each year:")
    for year, corr in per_year.items():
        print(f"   {year}   {corr:.3f}")
    print("\nThe pooled figure is the weaker one, and that is the finding: the same")
    print("residual load cleared at very different prices in different years, so a")
    print("model fitted across the whole record is fitting several relationships.")

    print(f"\nFigures written to {cfg.FIGURES.relative_to(cfg.ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
