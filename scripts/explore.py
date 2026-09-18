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
    """Highest minus lowest price within each delivery day, averaged per year.

    The last column asks a blunter question: was the day worth cycling at all?  A
    battery gets back 81 % of what it stores and pays for the wear, so the day's
    best hour has to beat its cheapest hour by more than those two together.  Days
    that fail the test are days where the right answer was to do nothing.
    """
    day = price.groupby(price.index.normalize())       # local calendar days
    low, high = day.min(), day.max()
    spread = high - low
    breakeven = low / cfg.BATTERY.round_trip_efficiency + cfg.BATTERY.cycle_cost_eur_per_mwh
    idle = high <= breakeven                           # nothing to earn, even knowing the day
    by_year = spread.groupby(spread.index.year)
    return pd.DataFrame({
        "mean": by_year.mean(),
        "median": by_year.median(),
        "widest": by_year.max(),
        "days": by_year.size(),
        "idle": idle.groupby(idle.index.year).sum(),
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
    """The two headline numbers side by side, because the question is whether they move.

    The first bar is a quarter, not a year — the bidding zone only began in October
    2018 — so it is hatched and faded.  A footnote alone is not enough: a chart gets
    screenshotted away from its caption, and a short bar next to seven full ones
    reads as a low year rather than a partial one.
    """
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 3.8))
    panels = ((a, neg["hours"], "#b4433a", "Hours cleared below zero", "hours per year"),
              (b, spread["mean"], "#1f3a5f", "Average daily spread (highest − lowest)", "EUR/MWh"))
    partial = neg.index.min()                       # the only year not covered in full
    for ax, values, colour, title, ylabel in panels:
        bars = ax.bar(values.index, values, color=colour, width=0.62)
        bars[0].set(alpha=0.45, hatch="///", edgecolor="white")   # October-December only
        ax.set_title(title, loc="left", fontsize=10)
        ax.set_ylabel(ylabel)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xticks(neg.index)
        ax.tick_params(labelsize=8)
    fig.tight_layout(rect=(0, 0.06, 1, 1))          # leave a strip for the footnote
    fig.text(0.008, 0.02, f"{partial} covers October–December only, and is not comparable "
             f"to the full years beside it", fontsize=7.5, color="#666666")
    fig.savefig(path, dpi=140); plt.close(fig)


def residual_frame() -> pd.DataFrame:
    """Residual load beside the price it cleared at, in GW and EUR/MWh.

    Residual load is demand minus wind and solar, built entirely from forecasts
    published before gate closure — so this frame would have been available at the
    decision point, and nothing downstream of it leaks.
    """
    load = data.load("load_forecast").iloc[:, 0]
    ws = data.load("wind_solar_forecast")
    price = data.load("day_ahead_price").iloc[:, 0]

    residual = load - ws["Wind Onshore"] - ws["Wind Offshore"] - ws["Solar"]
    return pd.concat([local(residual).rename("residual") / 1000,      # MW to GW, once, here
                      local(price).rename("price")],
                     axis=1, join="inner").dropna()


def fit(part: pd.DataFrame) -> tuple[float, float]:
    """Slope and intercept of the least-squares line through one year.

    Written out rather than imported: for a single predictor the slope is just
    covariance over variance, and that is not worth a dependency.  The slope is the
    number a forecaster cares about — how many EUR/MWh one GW of error is worth.
    """
    slope = part.residual.cov(part.price) / part.residual.var()
    return slope, part.price.mean() - slope * part.residual.mean()


# ── Residual load against price ───────────────────────────────────────────────
# The one figure that says why a model must not be fitted across all seven years at
# once.  Each year gets its own colour and its own fitted line, so the claim — that
# this is several relationships stacked, not one scattered — is something a reader
# can check instead of taking on trust.  The price window is clipped because 26 of
# 63,000 hours would otherwise stretch the axis over empty space and squash the
# region where almost every hour actually sits.

PRICE_WINDOW = (-150.0, 600.0)                      # the band nearly every hour falls in


def figure_residual(both: pd.DataFrame, path) -> pd.DataFrame:
    fig, ax = plt.subplots(figsize=(7.8, 5.0))
    years = sorted(both.index.year.unique())
    colours = plt.cm.viridis([i / max(len(years) - 1, 1) for i in range(len(years))])

    rows = {}
    for colour, year in zip(colours, years):
        part = both[both.index.year == year]
        ax.scatter(part.residual, part.price, s=1.6, alpha=0.10,
                   color=colour, edgecolors="none", rasterized=True, label=str(year))
        slope, intercept = fit(part)
        span = part.residual.quantile([0.01, 0.99])          # never draw where no data is
        ax.plot(span, intercept + slope * span, color=colour, lw=2.0,
                solid_capstyle="round", zorder=3)
        rows[year] = {"slope": slope, "corr": part.residual.corr(part.price), "hours": len(part)}

    ax.axhline(0, color="#b4433a", lw=0.9, ls="--")
    ax.set_ylim(*PRICE_WINDOW)
    ax.set_xlabel("residual load (GW)  =  demand − wind − solar forecast")
    ax.set_ylabel("day-ahead price (EUR/MWh)")
    ax.set_title("The same residual load cleared at very different prices",
                 loc="left", fontsize=10.5)
    ax.spines[["top", "right"]].set_visible(False)
    leg = ax.legend(frameon=False, fontsize=8, markerscale=6, loc="upper left",
                    title="line = least squares fit for that year", title_fontsize=7.5)
    leg._legend_box.align = "left"
    for handle in leg.legend_handles:
        handle.set_alpha(1)

    outside = int(((both.price < PRICE_WINDOW[0]) | (both.price > PRICE_WINDOW[1])).sum())
    ax.text(0.995, 0.015, f"{outside} of {len(both):,} hours fall outside this price window",
            transform=ax.transAxes, ha="right", fontsize=7, color="#777777")
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)

    return pd.DataFrame(rows).T


def negative_price_mechanism(both: pd.DataFrame) -> dict:
    """Do prices only go below zero once wind and solar exceed demand?

    They do not, and the gap is the finding.  Four fifths of negative hours still
    needed several GW from something else, so the surplus is not the whole story —
    but this dataset holds no plant-level costs and cannot say what the rest is.
    """
    neg = both[both.price < 0]
    return {
        "hours": len(neg),
        "with_surplus": int((neg.residual < 0).sum()),   # wind and solar alone beat demand
        "median_residual": neg.residual.median(),        # still positive, and that is the point
    }


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
    print(as_markdown(spread, ["Year", "Mean spread", "Median", "Widest day", "Days",
                               "Days not worth cycling"],
                      ["{:,.1f}", "{:,.1f}", "{:,.1f}", "{:,.0f}", "{:,.0f}"]))

    cfg.FIGURES.mkdir(parents=True, exist_ok=True)
    figure_history(price, cfg.FIGURES / "README_price_history.png")
    figure_trends(neg, spread, cfg.FIGURES / "README_negative_hours_and_spread.png")

    both = residual_frame()
    per_year = figure_residual(both, cfg.FIGURES / "README_residual_load_vs_price.png")

    print("\n\nResidual load against price\n")
    print(as_markdown(per_year, ["Year", "Slope (EUR/MWh per GW)", "Correlation", "Hours"],
                      ["{:,.2f}", "{:.3f}", "{:,.0f}"]))
    print(f"\npooled across all {len(both):,} hours: "
          f"{both.residual.corr(both.price):.3f}")
    print("\nThe pooled correlation is the weaker one, and that is the finding: the same")
    print("residual load cleared at very different prices in different years, so a model")
    print("fitted across the whole record is fitting several relationships at once.")
    print("The slope is the part that moved — one GW is worth roughly three times what")
    print("it was in 2019, so the same forecast error now costs three times as much.")

    # A claim worth checking rather than assuming: negative prices are usually read
    # as "wind and solar made more than the country needed".  Mostly they are not.
    mech = negative_price_mechanism(both)
    print(f"\nOf {mech['hours']:,} negative-price hours, {mech['with_surplus']:,} "
          f"({mech['with_surplus'] / mech['hours'] * 100:.0f} %) had residual load below zero.")
    print(f"The median negative-price hour still needed {mech['median_residual']:.1f} GW "
          f"from something other than wind and solar.")

    print(f"\nFigures written to {cfg.FIGURES.relative_to(cfg.ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
