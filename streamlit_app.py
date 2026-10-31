"""The web page: what a day-ahead price forecast is worth to a battery, in money first.

Reads one committed file, `reports/page.parquet` (`just page-data`), and nothing else,
so a clean clone and the hosted page show the same numbers the README states.  Nothing
is fitted, planned or settled here: every euro was computed by the code that produced
the record, and a test holds the file to it.

The page tells one story in three parts.  First the money: how much of the best
possible each approach kept.  Then one day, because the money is explained there: the
battery is paid for knowing which hours are cheap and dear, not the exact price.  Then
every day at once, error against money, which is the project's main finding.

Run it with `just page`.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src import config as cfg

st.set_page_config(page_title="Battery day-ahead backtest", page_icon="🔋", layout="centered")


# ── Names and colours ─────────────────────────────────────────────────────────
# Plain names for the record's run labels, because a visitor has not read the README.
# Colour follows the entity, never its rank: the average is blue everywhere, LEAR
# orange everywhere, the best possible is dark ink and dashed, everything else grey.
# Blue and orange pass the colour-vision checks in both themes (validated 31 Oct).

NAMES = {
    "ceiling": "Best possible (prices known)",
    "average": "Average of three forecasts",
    "bids strict": "LEAR, bids with price limits",
    "bids pair": "LEAR, bids, lenient fill rule",
    "LEAR": "LEAR, plan without limits",
    "straight line": "Plain linear model",
    "tree": "Gradient-boosted tree",
    "naive (field)": "No forecast",
}

LIGHT = {"ink": "#0b0b0b", "soft": "#52514e", "muted": "#898781", "average": "#2a78d6",
         "lear": "#eb6834", "grid": "#e1e0d9"}
DARK = {"ink": "#ffffff", "soft": "#c3c2b7", "muted": "#898781", "average": "#3987e5",
        "lear": "#d95926", "grid": "#2c2c2a"}
theme = getattr(st.context, "theme", None)
C = DARK if theme is not None and theme.type == "dark" else LIGHT   # the viewer's own theme

FOCUS = ["ceiling", "average", "bids strict", "naive (field)"]     # the four the story follows
FOCUS_COLOURS = [C["ink"], C["average"], C["lear"], C["muted"]]
SHORT = {"ceiling": "Best possible", "average": "Average", "bids strict": "LEAR's bids",
         "naive (field)": "No forecast"}                        # labels at the line ends
MIN_CEILING = 25.0          # EUR: below this, a day's share of the best possible is noise


# ── The data ──────────────────────────────────────────────────────────────────
# Stored in UTC like every series in the project; shown on the Berlin clock, the
# market's.  A delivery day is a Berlin date, so a clock-change day has 23 or 25 rows.

@st.cache_data
def load() -> pd.DataFrame:
    page = pd.read_parquet(cfg.PAGE_DATA)
    local = page.index.tz_convert(cfg.TZ_MARKET)
    page["day"] = local.tz_localize(None).normalize()           # the delivery day, Berlin
    page["clock"] = local.strftime("%H:%M")
    return page


@st.cache_data
def days(page: pd.DataFrame) -> pd.DataFrame:
    """One row per delivery day: euros per run, the average's miss, its share kept."""
    per_day = page.filter(like="earned:").groupby(page.day).sum()
    per_day.columns = per_day.columns.str.removeprefix("earned:")
    miss = (page["forecast:average"] - page.price).abs()
    per_day["miss"] = miss.groupby(page.day).mean()             # EUR/MWh, hour by hour
    per_day["share"] = per_day.average / per_day.ceiling
    per_day["split"] = page.split.groupby(page.day).first()
    return per_day


page = load()
daily = days(page)


def years(split: str) -> int:
    return daily.loc[daily.split == split].index.year.nunique()


def totals(split: str) -> pd.Series:
    return daily.loc[daily.split == split, list(NAMES)].sum()


# ── Opening ───────────────────────────────────────────────────────────────────

st.title("What is a price forecast worth to a battery?")
st.markdown(
    "A battery in Germany's day-ahead market must commit tomorrow's plan **by noon "
    "today**, before tomorrow's prices are known. We forecast those prices, plan the "
    "battery on the forecast, and pay it at the prices that really happened. "
    "**The score is the share of the best possible money it kept**: what the same "
    "battery would have earned had it known tomorrow's prices.")
st.caption("A 1 MW / 2 MWh battery, 81 % round trip, wear charged, each day planned on its "
           "own. Gross trading margin before fees. Hourly prices, German–Luxembourg zone.")


# ── Part 1: the money ─────────────────────────────────────────────────────────
# Four numbers, not a chart: a few headline figures read faster as tiles.  They are
# always the held-back years, because that is where the headline was fixed.

st.header("1 · The money")
held = totals("test")
share = held / held.ceiling
tiles = st.columns(4)
tiles[0].metric("Headline", f"{share['bids strict']:.1%}", help=NAMES["bids strict"])
tiles[1].metric("Average of three", f"{share['average']:.1%}")
tiles[2].metric("No forecast", f"{share['naive (field)']:.1%}")
tiles[3].metric("Best possible", f"{held.ceiling / years('test'):,.0f} €",
                help="per year, prices known in advance")
st.markdown(
    "Shares of the best possible over **2024 and 2025**, years kept out of every model "
    "choice. **Why the headline is not the biggest number:** LEAR's bids were chosen as "
    "the headline *before* those years were looked at. The average was chosen to send "
    "each day *after*, so it is reported beside the headline, not in its place.")

PERIODS = {"2024–25, held back": "test", "2023, the practice year": "valid"}
label = st.segmented_control("Look closer at", list(PERIODS), default=list(PERIODS)[0])
split = PERIODS[label or list(PERIODS)[0]]
period = daily.loc[daily.split == split]
kept = totals(split)
n_years = years(split)

# Chart 1: every approach as a share of the best possible.  Bars start at zero, so
# the differences look as large as they are; the exact share is written on each.

per_year = (kept.average - kept["naive (field)"]) / n_years
lear_year = (kept.LEAR - kept["naive (field)"]) / n_years
st.subheader("How much of the best possible each approach kept")
st.markdown(f"Sent without limits, the average of three forecasts earned **{per_year:,.0f} € a "
            f"year** more than no forecast; LEAR alone {lear_year:,.0f} €. No forecast means "
            "assuming tomorrow repeats yesterday (last week on Saturdays to Mondays).")

bars = pd.DataFrame({"run": [NAMES[r] for r in kept.index if r != "ceiling"],
                     "share": [kept[r] / kept.ceiling for r in kept.index if r != "ceiling"],
                     "euros": [kept[r] for r in kept.index if r != "ceiling"],
                     "key": [r for r in kept.index if r != "ceiling"]})
bars = bars.sort_values("share", ascending=False)
bars["tone"] = bars.key.map({"average": "average", "bids strict": "lear"}).fillna("other")
bar = alt.Chart(bars).encode(
    y=alt.Y("run:N", sort=list(bars.run), title=None),
    x=alt.X("share:Q", title="share of the best possible", axis=alt.Axis(format="%"),
            scale=alt.Scale(domain=[0, 1])),
    tooltip=[alt.Tooltip("run:N", title="approach"), alt.Tooltip("share:Q", format=".1%"),
             alt.Tooltip("euros:Q", title="earned, €", format=",.0f")])
chart1 = (bar.mark_bar(cornerRadiusEnd=4, height=16).encode(
              color=alt.Color("tone:N", legend=None, scale=alt.Scale(
                  domain=["average", "lear", "other"],
                  range=[C["average"], C["lear"], C["muted"]])))
          + bar.mark_text(align="right", dx=-6, color="white", fontWeight="bold").encode(
              text=alt.Text("share:Q", format=".1%")))
st.altair_chart(chart1, width="stretch")

# Chart 2: the euros adding up.  The dashed line is the best possible; the distance
# below it is money left on the table, and the month that left most is named.

lost = (period.ceiling - period.average).groupby(period.index.to_period("M")).sum()
worst = lost.idxmax()
month = page.loc[(page.split == split) & (page.day.dt.to_period("M") == worst), "price"]
st.subheader("When the money was earned, and where it was lost")
st.markdown(f"Euros adding up over the period. The gap to the dashed line is money left on the "
            f"table. The average left most in **{worst.strftime('%B %Y')}** "
            f"({lost.max():,.0f} €). Prices averaged {month.mean():.0f} €/MWh that month, "
            f"against {page.loc[page.split == split, 'price'].mean():.0f} over the period.")

running = period[FOCUS].cumsum().reset_index().melt("day", var_name="key", value_name="euros")
running["run"] = running.key.map(NAMES)
order = [NAMES[r] for r in FOCUS]
lines = alt.Chart(running).encode(
    x=alt.X("day:T", title=None),
    y=alt.Y("euros:Q", title="earned so far, €", axis=alt.Axis(format=",.0f")),
    color=alt.Color("run:N", sort=order, title=None, legend=alt.Legend(orient="top"),
                    scale=alt.Scale(domain=order, range=FOCUS_COLOURS)),
    strokeDash=alt.StrokeDash("run:N", sort=order, legend=None,
                              scale=alt.Scale(domain=order, range=[[6, 4], [1, 0], [1, 0], [1, 0]])))
hover = alt.selection_point(fields=["day"], nearest=True, on="pointerover", empty=False)
chart2 = alt.layer(
    lines.mark_line(strokeWidth=2),
    lines.mark_point(size=60, filled=True).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0)),
        tooltip=[alt.Tooltip("day:T", title="day", format="%d %b %Y"),
                 alt.Tooltip("run:N", title="approach"),
                 alt.Tooltip("euros:Q", title="earned so far, €", format=",.0f")]
    ).add_params(hover),
    alt.Chart(running.loc[running.day == running.day.max()].assign(
        short=lambda f: f.key.map(SHORT))).mark_text(align="left", dx=6).encode(
        x="day:T", y="euros:Q", text="short:N",
        color=alt.Color("run:N", sort=order, legend=None,
                        scale=alt.Scale(domain=order, range=FOCUS_COLOURS))),
).properties(height=340, padding={"left": 5, "top": 5, "bottom": 5, "right": 95})
st.altair_chart(chart2, width="stretch")


# ── Part 2: one day ───────────────────────────────────────────────────────────
# Where the money is explained.  Examples are picked from the data, so they stay
# true if the file is rebuilt; keying the date box on the example resets it when
# a different example is chosen.

st.header("2 · Why: one day at a time")
st.markdown("The battery is **not paid for guessing the price exactly**. It is paid for knowing "
            "which hours are cheap and which are dear: buy in the cheap ones, sell in the dear "
            "ones. Pick a day and compare the forecast's plan with the best possible one.")

sized = period.loc[period.ceiling >= MIN_CEILING]
prices = page.loc[page.split == split]
EXAMPLES = {
    "An ordinary day": (sized.share - sized.share.median()).abs().idxmin(),
    "The forecast's best day": sized.share.idxmax(),
    "Its costliest day": (period.ceiling - period.average).idxmax(),
    "Prices below zero": prices.day[prices.price.idxmin()],
}
example = st.segmented_control("Start from", list(EXAMPLES), default="An ordinary day")
start = EXAMPLES[example or "An ordinary day"]
day = pd.Timestamp(st.date_input("or pick any day", value=start.date(),
                                 min_value=period.index.min().date(),
                                 max_value=period.index.max().date(),
                                 key=f"day-{split}-{example}", format="DD.MM.YYYY"))

one = page.loc[page.day == day].copy()
row = daily.loc[day]
# A 25-hour day repeats 02:00; the second one is marked so the axis keeps both.
one["slot"] = one.clock.where(~one.clock.duplicated(), one.clock + "′")

money = st.columns(4)
money[0].metric("Best possible", f"{row.ceiling:,.0f} €")
for col, key in zip(money[1:], ["average", "bids strict", "naive (field)"]):
    kept_day = f"{row[key] / row.ceiling:.0%} kept" if row.ceiling >= MIN_CEILING else None
    col.metric(NAMES[key].split(",")[0] if key != "bids strict" else "LEAR's bids",
               f"{row[key]:,.0f} €", kept_day, delta_color="off")

charge = lambda run: set(one.slot[one[f"net:{run}"] < -1e-6])       # hours the plan buys in
sell = lambda run: set(one.slot[one[f"net:{run}"] > 1e-6])          # hours it sells in
best_buy, best_sell = charge("ceiling"), sell("ceiling")
same_buy = len(best_buy & charge("average"))
same_sell = len(best_sell & sell("average"))
share_text = (f"kept **{row.share:.0%}** of the best possible" if row.ceiling >= MIN_CEILING
              else f"earned {row.average:,.0f} € of a best possible {row.ceiling:,.0f} €")
st.markdown(f"On **{day.strftime('%A %d %B %Y')}** the average forecast missed by "
            f"**{row.miss:.0f} €/MWh** per hour and {share_text}. It bought in "
            f"{same_buy} of the {len(best_buy)} hours the best plan bought in, and sold in "
            f"{same_sell} of its {len(best_sell)}.")

# Two panels on one shared clock, never one chart with two scales: prices above,
# the battery's hours below (selling up, buying down).  The shaded range is LEAR's,
# so it is drawn with LEAR's line and labelled as LEAR's.

x = alt.X("slot:N", sort=list(one.slot), title=None, axis=alt.Axis(labelAngle=0, labelOverlap=True))
Y_AXIS = dict(minExtent=56, maxExtent=56)                       # same width, so the clocks line up
curves = one.melt(id_vars="slot", value_vars=["price", "forecast:average", "forecast:LEAR"],
                  var_name="what", value_name="eur")
curves["what"] = curves.what.map({"price": "Real price", "forecast:average": "Average forecast",
                                  "forecast:LEAR": "LEAR forecast"})
kinds = ["Real price", "Average forecast", "LEAR forecast"]
band = alt.Chart(one).mark_area(opacity=0.18, color=C["lear"]).encode(
    x=x, y=alt.Y("p10:Q", title="€/MWh", axis=alt.Axis(**Y_AXIS)), y2="p90:Q",
    tooltip=[alt.Tooltip("slot:N", title="hour"), alt.Tooltip("p10:Q", title="LEAR p10", format=".1f"),
             alt.Tooltip("p90:Q", title="LEAR p90", format=".1f")])
price_lines = alt.Chart(curves).mark_line(point=alt.OverlayMarkDef(size=20)).encode(
    x=x, y=alt.Y("eur:Q", title="€/MWh", axis=alt.Axis(**Y_AXIS)),
    color=alt.Color("what:N", sort=kinds, title=None, legend=alt.Legend(orient="top"),
                    scale=alt.Scale(domain=kinds, range=[C["ink"], C["average"], C["lear"]])),
    strokeWidth=alt.StrokeWidth("what:N", sort=kinds, legend=None,
                                scale=alt.Scale(domain=kinds, range=[2.5, 2, 1.2])),
    tooltip=[alt.Tooltip("slot:N", title="hour"), alt.Tooltip("what:N", title=" "),
             alt.Tooltip("eur:Q", title="€/MWh", format=".1f")])
top = (band + price_lines).properties(height=260,
                                      title="Prices · shaded: LEAR's 80 % range")

plans = one.melt(id_vars="slot", value_vars=["net:ceiling", "net:average"],
                 var_name="plan", value_name="mw")
plans["plan"] = plans.plan.map({"net:ceiling": "Best possible plan", "net:average": "Average's plan"})
plan_kinds = ["Best possible plan", "Average's plan"]
bottom = alt.Chart(plans).mark_bar(cornerRadius=2).encode(
    x=x, xOffset=alt.XOffset("plan:N", sort=plan_kinds),
    y=alt.Y("mw:Q", title="MW · sell ↑ buy ↓", scale=alt.Scale(domain=[-1.15, 1.15]),
            axis=alt.Axis(**Y_AXIS)),
    color=alt.Color("plan:N", sort=plan_kinds, title=None, legend=alt.Legend(orient="top"),
                    scale=alt.Scale(domain=plan_kinds, range=[C["soft"], C["average"]])),
    tooltip=[alt.Tooltip("slot:N", title="hour"), alt.Tooltip("plan:N", title=" "),
             alt.Tooltip("mw:Q", title="MW", format=".2f")]
).properties(height=150, title="The battery's hours")
st.altair_chart(top, width="stretch")
st.altair_chart(bottom, width="stretch")


# ── Part 3: error against money ───────────────────────────────────────────────
# Every day as one dot.  The wording is chosen from the measured correlation, so a
# rebuilt file cannot leave a sentence behind that the dots no longer support.

st.header("3 · A closer forecast is not a richer one")
rho = sized.miss.corr(sized.share, method="spearman")
link = "no link" if abs(rho) < 0.1 else "a weak link" if abs(rho) < 0.3 else "a clear link"
st.markdown(f"Each dot is a day: across, how far the average forecast missed; up, the share of "
            f"the best possible it kept. **There is {link}** (rank correlation {rho:.2f}). "
            "Days with large misses kept as much as days with small ones, because a forecast "
            "can be wrong about the level of every hour and still right about their order. "
            f"Left out: {len(period) - len(sized)} days when even the best plan earned under "
            f"{MIN_CEILING:.0f} €, where a share is noise. The ringed dot is the day above.")

dots = sized.reset_index()[["day", "miss", "share", "average", "ceiling"]]
base = alt.Chart(dots).encode(
    x=alt.X("miss:Q", title="average miss that day, €/MWh"),
    y=alt.Y("share:Q", title="share of the best possible kept", axis=alt.Axis(format="%"),
            scale=alt.Scale(domainMax=1.02, nice=False)))
chosen = dots.loc[dots.day == day]
chart3 = alt.layer(
    base.mark_circle(size=34, opacity=0.45, color=C["average"]).encode(
        tooltip=[alt.Tooltip("day:T", format="%d %b %Y"),
                 alt.Tooltip("miss:Q", title="miss, €/MWh", format=".1f"),
                 alt.Tooltip("share:Q", title="kept", format=".1%"),
                 alt.Tooltip("average:Q", title="earned, €", format=",.0f"),
                 alt.Tooltip("ceiling:Q", title="best possible, €", format=",.0f")]),
    alt.Chart(chosen).mark_point(size=160, strokeWidth=2, color=C["ink"]).encode(
        x="miss:Q", y="share:Q"),
).properties(height=340)
st.altair_chart(chart3, width="stretch")


# ── Close ─────────────────────────────────────────────────────────────────────

st.header("What this does not show")
st.markdown(
    "- **One market only.** Published 2024 figures for German batteries across every market "
    "run two to three times this best possible, mostly from grid reserve.\n"
    "- **Gross margin.** Before grid fees, taxes and the cost of the battery.\n"
    "- **A backtest.** Every forecast here was made as if at noon the day before, from data "
    "published by then, but computed later. A daily live run is being built next.\n\n"
    "Every number on this page regenerates from a clean copy of the "
    "[repository](https://github.com/undorigo/battery-storage-backtest) by the commands in "
    "its README, *Reproduce it*.")
