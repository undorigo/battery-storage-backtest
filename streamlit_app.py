"""The web page: what a day-ahead price forecast is worth to a battery, in money first.

Reads one committed file, `reports/page.parquet` (`just page-data`), and nothing else,
so a clean clone and the hosted page show the same numbers the README states.  Nothing
is fitted, planned or settled here: every euro was computed by the code that produced
the record, and a test holds the file to it.

The page tells one story in three parts, for a visitor who has not read the README.
First the money, in euros.  Then what earns it: the order of the hours, not the exact
price, shown across every day.  Then one day to explore, where that can be seen.
Words follow the plain-language rule: the everyday word first, the term in brackets.

Run it with `just page`.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src import config as cfg

st.set_page_config(page_title="Battery day-ahead backtest", page_icon="🔋", layout="centered")


# ── Names and colours ─────────────────────────────────────────────────────────
# Plain names for the record's run labels, the technical name kept for the full
# table.  Colour follows the entity, never its rank: our forecast (LEAR) is orange
# everywhere, the three averaged blue, the maximum dark ink and dashed, no forecast
# grey.  Blue and orange pass the colour-vision checks in both themes (31 Oct).

NAMES = {
    "ceiling": "The maximum (prices known in advance)",
    "bids strict": "Our forecast, with price limits",
    "average": "Three forecasts averaged, no limits",
    "naive (field)": "No forecast (tomorrow = yesterday)",
    "bids pair": "Our forecast, with price limits, lenient exchange rule",
    "LEAR": "Our forecast, no price limits",
    "straight line": "A plain straight-line model",
    "tree": "A decision-tree model",
}
TECHNICAL = {"ceiling": "perfect-foresight ceiling", "bids strict": "LEAR, loop bids, strict fill",
             "average": "mean of LEAR, tree and line", "naive (field)": "naive benchmark (Lago et al.)",
             "bids pair": "LEAR, loop bids, pair fill", "LEAR": "LEAR, fixed schedule",
             "straight line": "linear regression", "tree": "gradient-boosted trees"}
SHORT = {"ceiling": "The maximum", "bids strict": "Our forecast", "average": "Three averaged",
         "naive (field)": "No forecast"}

LIGHT = {"ink": "#0b0b0b", "soft": "#52514e", "muted": "#898781", "average": "#2a78d6",
         "lear": "#eb6834"}
DARK = {"ink": "#ffffff", "soft": "#c3c2b7", "muted": "#898781", "average": "#3987e5",
        "lear": "#d95926"}
theme = getattr(st.context, "theme", None)
C = DARK if theme is not None and theme.type == "dark" else LIGHT   # the viewer's own theme

FOCUS = ["ceiling", "bids strict", "average", "naive (field)"]     # the four the story follows
TONE = {"ceiling": C["ink"], "bids strict": C["lear"], "average": C["average"],
        "naive (field)": C["muted"]}
MIN_CEILING = 25.0          # EUR: below this, a day's share of the maximum is noise


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


def per_year(split: str) -> pd.Series:
    """Euros a year per run, over one period."""
    period = daily.loc[daily.split == split]
    return period[list(NAMES)].sum() / period.index.year.nunique()


def eur(x: float) -> str:
    return f"{x:,.0f} €"


def date_text(day: pd.Timestamp, short: bool = False) -> str:
    return f"{day.day} {day.strftime('%b %Y' if short else '%B %Y')}"   # "9 July 2024", no zero


def hundreds(x: float) -> str:
    return f"{round(x, -2):,.0f} €"                             # for prose: "about 60,400 €"


# ── Opening ───────────────────────────────────────────────────────────────────

st.title("What is a price forecast worth to a battery?")
st.markdown(
    "A battery earns money by buying electricity when it is cheap and selling it when it "
    "is dear. In Germany it must fix tomorrow's plan **by noon today**, before tomorrow's "
    "prices are known. So it needs a forecast. We forecast the prices, plan the battery on "
    "the forecast, and pay it at the prices that really happened.")
st.caption("A grid battery that can charge or discharge 1 MW for 2 hours. About a fifth of "
           "the energy is lost between buying and selling, and wear is charged on every use. "
           "Prices: the German day-ahead auction, hour by hour. Money before fees and taxes.")


# ── Part 1: the money ─────────────────────────────────────────────────────────
# Euros first, because a share means nothing until the reader knows what it is a
# share of.  Always the test years: that is where the main number was fixed.  The
# second number gets its own box, so the reason for it is read, not hovered over.

st.header("1 · The money")
test = per_year("test")
kept = test / test.ceiling
st.markdown(
    f"**Over 2024 and 2025, our forecast earned the battery about {hundreds(test['bids strict'])} "
    f"a year.** That is {kept['bids strict']:.0%} of the most it could have earned: "
    f"{hundreds(test.ceiling)} a year if it had known every price in advance. We call that "
    f"**the maximum**. No forecast can reach it. With no forecast at all, assuming tomorrow's "
    f"prices repeat yesterday's, the battery would have earned {hundreds(test['naive (field)'])}.")

tiles = st.columns(3)
for col, key, note in zip(tiles, ["ceiling", "bids strict", "naive (field)"],
                          ["a year, prices known in advance",
                           f"a year · {kept['bids strict']:.1%} of the maximum",
                           f"a year · {kept['naive (field)']:.1%} of the maximum"]):
    col.metric(SHORT[key], eur(test[key]))
    col.caption(note)

with st.container(border=True):
    st.markdown(f"**Why {kept['bids strict']:.0%} and not {kept['average']:.0%}?**")
    st.markdown(
        "We later found a way to earn more: average three different forecasts, and send "
        f"the plan without price limits. On the same two years it kept {kept['average']:.1%}. "
        "But we found it **after** seeing those years' results. A method picked after seeing "
        "the results usually looks better than it will do later. So the main number stays "
        "the one we fixed **before** looking. From now on the daily run uses the better way, "
        "and that will test it on new days.")

PERIODS = {"2024–25: the test years": "test", "2023: the practice year": "valid"}
label = st.segmented_control("Look closer at", list(PERIODS), default=list(PERIODS)[0])
split = PERIODS[label or list(PERIODS)[0]]
st.caption("We built and tuned the forecasts on the years up to 2023. 2024 and 2025 were kept "
           "aside and used once, as the final test.")
period = daily.loc[daily.split == split]
yearly = per_year(split)

# Chart 1: three ways as a share of the maximum.  Bars start at zero, so the
# differences look as large as they are.  The other ways sit in a table below,
# technical names beside the plain ones.

st.subheader("How much of the maximum each way kept")
st.markdown("Each bar is one way of planning the battery. The longer the bar, the more of the "
            "maximum it earned.")
three = [k for k in FOCUS if k != "ceiling"]
bars = pd.DataFrame({"key": three, "way": [NAMES[k] for k in three],
                     "share": [yearly[k] / yearly.ceiling for k in three],
                     "euros": [yearly[k] for k in three]})
bar = alt.Chart(bars).encode(
    y=alt.Y("way:N", sort=[NAMES[k] for k in three], title=None,
            axis=alt.Axis(labelLimit=260)),
    x=alt.X("share:Q", title="share of the maximum", axis=alt.Axis(format="%"),
            scale=alt.Scale(domain=[0, 1])),
    tooltip=[alt.Tooltip("way:N", title="way"), alt.Tooltip("share:Q", format=".1%"),
             alt.Tooltip("euros:Q", title="€ a year", format=",.0f")])
chart1 = alt.layer(
    bar.mark_bar(cornerRadiusEnd=4, height=22).encode(
        color=alt.Color("key:N", legend=None, scale=alt.Scale(
            domain=three, range=[TONE[k] for k in three]))),
    bar.mark_text(align="right", dx=-8, color="white", fontWeight="bold").encode(
        text=alt.Text("share:Q", format=".1%")),
).properties(height=150)
st.altair_chart(chart1, width="stretch")

with st.expander("All eight ways we tried, with their technical names"):
    table = pd.DataFrame({"Way": [NAMES[k] for k in NAMES],
                          "€ a year": [eur(yearly[k]) for k in NAMES],
                          "Share of the maximum": [f"{yearly[k] / yearly.ceiling:.1%}" for k in NAMES],
                          "Technical name": [TECHNICAL[k] for k in NAMES]})
    st.dataframe(table, hide_index=True, width="stretch")

# Chart 2: the euros adding up.  The dashed line is the maximum; the space below it
# is money left on the table, and the month that left most is named, with its prices.

lost = (period.ceiling - period.average).groupby(period.index.to_period("M")).sum()
worst = lost.idxmax()
prices_all = page.loc[page.split == split, "price"]
month = page.loc[(page.split == split) & (page.day.dt.to_period("M") == worst), "price"]
st.subheader("Money adding up, day by day")
st.markdown(f"The dashed line is the maximum. The space between it and a coloured line is money "
            f"that way left on the table. The three averaged left most in "
            f"**{worst.strftime('%B %Y')}** ({lost.max():,.0f} €). Prices that month averaged "
            f"{month.mean():.0f} € per MWh, against {prices_all.mean():.0f} over the whole period.")

running = period[FOCUS].cumsum().reset_index().melt("day", var_name="key", value_name="euros")
running["way"] = running.key.map(SHORT)
order = [SHORT[k] for k in FOCUS]
colours = alt.Scale(domain=order, range=[TONE[k] for k in FOCUS])
lines = alt.Chart(running).encode(
    x=alt.X("day:T", title=None),
    y=alt.Y("euros:Q", title="earned so far, €", axis=alt.Axis(format=",.0f")),
    color=alt.Color("way:N", sort=order, title=None, legend=alt.Legend(orient="top"),
                    scale=colours),
    strokeDash=alt.StrokeDash("way:N", sort=order, legend=None,
                              scale=alt.Scale(domain=order, range=[[6, 4], [1, 0], [1, 0], [1, 0]])))
hover = alt.selection_point(fields=["day"], nearest=True, on="pointerover", empty=False)
chart2 = alt.layer(
    lines.mark_line(strokeWidth=2),
    lines.mark_point(size=60, filled=True).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0)),
        tooltip=[alt.Tooltip("day:T", title="day", format="%d %b %Y"),
                 alt.Tooltip("way:N", title="way"),
                 alt.Tooltip("euros:Q", title="earned so far, €", format=",.0f")]
    ).add_params(hover),
    alt.Chart(running.loc[running.day == running.day.max()]).mark_text(align="left", dx=6).encode(
        x="day:T", y="euros:Q", text="way:N",
        color=alt.Color("way:N", sort=order, legend=None, scale=colours)),
).properties(height=380, padding={"left": 5, "top": 5, "bottom": 5, "right": 100})
st.altair_chart(chart2, width="stretch")


# ── Part 2: what earns the money ──────────────────────────────────────────────
# The project's main finding, shown on every day at once.  Days are cut into four
# equal groups by how far off the forecast was, and each bar is the typical day of
# its group (the median), the thin line the middle half.  Medians, because a few
# days with a loss would drag an average around.  The two example days are found
# by rule, so they stay true if the file is rebuilt.

st.header("2 · What earns the money")
st.markdown("**The battery does not need the exact price.** It needs to know which hours will "
            "be cheapest and which dearest: it buys in the first and sells in the second. A "
            "forecast can be wrong about every price and still right about their order.")

sized = period.loc[period.ceiling >= MIN_CEILING].copy()
sized["group"] = pd.qcut(sized.miss, 4)
edges = sized.group.cat.categories
names = [f"{c.left:.0f}–{c.right:.0f} €" for c in edges]
names[0], names[-1] = f"least off\n{names[0]}", f"most off\n{names[-1]}"
groups = sized.groupby("group", observed=True).share.agg(
    typical="median", low=lambda s: s.quantile(0.25), high=lambda s: s.quantile(0.75),
    count="size").reset_index(drop=True)
groups["group"] = names

low, high = f"{groups.typical.min():.0%}", f"{groups.typical.max():.0%}"
spread = f"about {low}" if low == high else f"between {low} and {high}"
st.markdown("Here every day is sorted by how far off the forecast was, then cut into four "
            "groups of equal size. Each bar shows how much of that day's maximum the battery "
            f"kept on a typical day of the group. **The bars are almost the same height:** a "
            f"typical day kept {spread} in every group, however far off the forecast was.")
st.caption("Forecast: the three averaged, the way the daily run uses them. How far off: the "
           "average gap between forecast and real price over the day's hours. Thin line: where "
           f"the middle half of the group's days fell. Left out: {len(period) - len(sized)} days "
           f"when even the maximum was under {MIN_CEILING:.0f} €, where a share means little.")

g = alt.Chart(groups).encode(
    x=alt.X("group:N", sort=names, title="How far off the forecast was (€ per MWh)",
            axis=alt.Axis(labelAngle=0, labelExpr="split(datum.label, '\\n')")),
    tooltip=[alt.Tooltip("group:N", title="off by"),
             alt.Tooltip("typical:Q", title="typical day", format=".1%"),
             alt.Tooltip("low:Q", title="middle half from", format=".1%"),
             alt.Tooltip("high:Q", title="to", format=".1%"), alt.Tooltip("count:Q", title="days")])
chart3 = alt.layer(
    g.mark_bar(cornerRadiusEnd=4, width=56, color=C["average"]).encode(
        y=alt.Y("typical:Q", title="money kept on a typical day", axis=alt.Axis(format="%"),
                scale=alt.Scale(domain=[0, 1]))),
    g.mark_rule(strokeWidth=1.5, color=C["ink"]).encode(y="low:Q", y2="high:Q"),
    g.mark_text(dy=-10, color=C["ink"]).encode(y="high:Q", text=alt.Text("typical:Q", format=".0%")),
).properties(height=300)
st.altair_chart(chart3, width="stretch")

# Two real days make the point concrete: a large miss that kept everything, and a
# small miss that kept least.  Only days worth at least 100 EUR, so neither is a
# day with nothing to earn.

worth = sized.loc[sized.ceiling >= 100]
big = worth.loc[worth.share >= 0.99].miss.idxmax()
small = worth.loc[worth.miss <= edges[0].right].share.idxmin()
beaten = int((sized.miss < sized.miss[big]).mean() * 100)   # floored: never "100 in 100"


def show(day: pd.Timestamp) -> None:
    st.session_state.day = day.date()                           # Part 3 opens on this day
    st.session_state.start = None


st.markdown(f"**Two real days.** On {date_text(big)} the forecast was off by "
            f"{sized.miss[big]:.0f} € per MWh, more than on {beaten} days in 100, and the "
            f"battery still kept {sized.share[big]:.0%} ({eur(sized.average[big])}). On "
            f"{date_text(small)} it was off by only {sized.miss[small]:.1f} € and "
            f"kept {sized.share[small]:.0%}. Open either one below.")
pick = st.columns(2)
pick[0].button(f"Big miss, kept {sized.share[big]:.0%}: {date_text(big, short=True)}",
               on_click=show, args=(big,), width="stretch")
pick[1].button(f"Small miss, kept {sized.share[small]:.0%}: {date_text(small, short=True)}",
               on_click=show, args=(small,), width="stretch")

with st.expander("Show every day as a dot"):
    dots = sized.reset_index()[["day", "miss", "share", "average", "ceiling"]]
    st.altair_chart(alt.Chart(dots).mark_circle(size=34, opacity=0.45, color=C["average"]).encode(
        x=alt.X("miss:Q", title="How far off the forecast was (€ per MWh)"),
        y=alt.Y("share:Q", title="money kept that day", axis=alt.Axis(format="%"),
                scale=alt.Scale(domainMax=1.02, nice=False)),
        tooltip=[alt.Tooltip("day:T", format="%d %b %Y"),
                 alt.Tooltip("miss:Q", title="off by, €/MWh", format=".1f"),
                 alt.Tooltip("share:Q", title="kept", format=".1%"),
                 alt.Tooltip("average:Q", title="earned, €", format=",.0f"),
                 alt.Tooltip("ceiling:Q", title="the maximum, €", format=",.0f")]
    ).properties(height=320), width="stretch")
    st.caption("Below zero: on a few days the plan lost money. It bought in hours it expected "
               "to be cheap, and they were not.")


# ── Part 3: explore a day ─────────────────────────────────────────────────────
# The playground.  The chosen day lives in session state, so the buttons above and
# the examples here can both set it; a day outside the chosen period is reset to an
# ordinary one, because the date box refuses a value outside its range.

st.header("3 · Explore a day")
st.markdown("Pick a day. Compare the hours the battery bought and sold in with the hours it "
            "should have.")

prices = page.loc[page.split == split]
EXAMPLES = {
    "An ordinary day": (sized.share - sized.share.median()).abs().idxmin(),
    "The forecast's best day": sized.share.idxmax(),
    "Its costliest day": (period.ceiling - period.average).idxmax(),
    "Prices below zero": prices.day[prices.price.idxmin()],
}
first, last = period.index.min().date(), period.index.max().date()
if not first <= st.session_state.get("day", first - pd.Timedelta(days=1)) <= last:
    st.session_state.day = EXAMPLES["An ordinary day"].date()


def start_from(examples: dict) -> None:
    if st.session_state.start:
        st.session_state.day = examples[st.session_state.start].date()


st.segmented_control("Start from", list(EXAMPLES), key="start", on_change=start_from,
                     args=(EXAMPLES,))
day = pd.Timestamp(st.date_input("or pick any day", min_value=first, max_value=last,
                                 key="day", format="DD.MM.YYYY"))

one = page.loc[page.day == day].copy()
row = daily.loc[day]
# A 25-hour day repeats 02:00; the second one is marked so the axis keeps both.
one["slot"] = one.clock.where(~one.clock.duplicated(), one.clock + "′")

money = st.columns(4)
for col, key in zip(money, ["ceiling", "average", "bids strict", "naive (field)"]):
    col.metric(SHORT[key], eur(row[key]))
    if key != "ceiling" and row.ceiling >= MIN_CEILING:
        col.caption(f"{row[key] / row.ceiling:.0%} of the maximum")

charge = lambda run: set(one.slot[one[f"net:{run}"] < -1e-6])       # hours the plan buys in
sell = lambda run: set(one.slot[one[f"net:{run}"] > 1e-6])          # hours it sells in
best_buy, best_sell = charge("ceiling"), sell("ceiling")
same_buy, same_sell = len(best_buy & charge("average")), len(best_sell & sell("average"))
kept_text = (f"kept **{row.share:.0%}** of the maximum" if row.ceiling >= MIN_CEILING
             else f"earned {eur(row.average)} of a maximum of {eur(row.ceiling)}")
st.markdown(f"On **{day.strftime('%A')} {date_text(day)}** the three averaged were off by "
            f"**{row.miss:.0f} € per MWh** on average and {kept_text}. The battery bought in "
            f"{same_buy} of the {len(best_buy)} hours the best plan bought in, and sold in "
            f"{same_sell} of its {len(best_sell)}.")

# Two charts on one clock, never one chart with two scales: prices above, the
# battery's hours below.  Heights leave room for title and legend, which Streamlit
# counts inside the height.  The range is our forecast's (LEAR's), so it is only
# drawn together with that forecast's own line.

x = alt.X("slot:N", sort=list(one.slot), title=None, axis=alt.Axis(labelAngle=0, labelOverlap=True))
y_axis = dict(minExtent=56, maxExtent=56)                       # same width, so the clocks line up
extra = st.toggle("Also show our forecast (LEAR) and the range it expects prices to fall in")
shown = ["price", "forecast:average"] + (["forecast:LEAR"] if extra else [])
kinds = {"price": "Real price", "forecast:average": "Three averaged", "forecast:LEAR": "Our forecast"}
curves = one.melt(id_vars="slot", value_vars=shown, var_name="what", value_name="eur")
curves["what"] = curves.what.map(kinds)
order = [kinds[k] for k in shown]
price_lines = alt.Chart(curves).mark_line(point=alt.OverlayMarkDef(size=20)).encode(
    x=x, y=alt.Y("eur:Q", title="€ per MWh", axis=alt.Axis(**y_axis)),
    color=alt.Color("what:N", sort=order, title=None, legend=alt.Legend(orient="top"),
                    scale=alt.Scale(domain=order,
                                    range=[C["ink"], C["average"], C["lear"]][:len(order)])),
    tooltip=[alt.Tooltip("slot:N", title="hour"), alt.Tooltip("what:N", title=" "),
             alt.Tooltip("eur:Q", title="€ per MWh", format=".1f")])
layers = [price_lines]
if extra:
    layers.insert(0, alt.Chart(one).mark_area(opacity=0.18, color=C["lear"]).encode(
        x=x, y=alt.Y("p10:Q", title="€ per MWh", axis=alt.Axis(**y_axis)), y2="p90:Q",
        tooltip=[alt.Tooltip("slot:N", title="hour"),
                 alt.Tooltip("p10:Q", title="range from", format=".1f"),
                 alt.Tooltip("p90:Q", title="to", format=".1f")]))
st.markdown("**Prices.**" + (" Shaded: the range our forecast expects 8 prices in 10 to fall in."
                             if extra else ""))
st.altair_chart(alt.layer(*layers).properties(height=320), width="stretch")

plans = one.melt(id_vars="slot", value_vars=["net:ceiling", "net:average"],
                 var_name="plan", value_name="mw")
plan_kinds = ["Best plan (prices known)", "Plan on the three averaged"]
plans["plan"] = plans.plan.map(dict(zip(["net:ceiling", "net:average"], plan_kinds)))
st.markdown("**The battery's hours.** Bars above the line: the battery sells. Below: it buys "
            "(charges). Where the two colours sit in the same hours, the forecast got the order "
            "right.")
st.altair_chart(alt.Chart(plans).mark_bar(cornerRadius=2).encode(
    x=x, xOffset=alt.XOffset("plan:N", sort=plan_kinds),
    y=alt.Y("mw:Q", title="MW · sell ↑ buy ↓", scale=alt.Scale(domain=[-1.1, 1.1]),
            axis=alt.Axis(**y_axis)),
    color=alt.Color("plan:N", sort=plan_kinds, title=None, legend=alt.Legend(orient="top"),
                    scale=alt.Scale(domain=plan_kinds, range=[C["soft"], C["average"]])),
    tooltip=[alt.Tooltip("slot:N", title="hour"), alt.Tooltip("plan:N", title=" "),
             alt.Tooltip("mw:Q", title="MW", format=".2f")]
).properties(height=280), width="stretch")


# ── Close ─────────────────────────────────────────────────────────────────────

st.header("What this does not show")
st.markdown(
    "- **One market only.** Batteries in Germany also earn by standing ready to balance the "
    "grid (*reserve markets*). Published figures for 2024 across every market are two to three "
    "times this maximum.\n"
    "- **Money before costs.** Before grid fees, taxes and the price of the battery.\n"
    "- **A replay.** Every forecast here was made as if at noon the day before, from data "
    "published by then, but it was computed later. A daily live run is being built next.\n\n"
    "Every number on this page can be rebuilt from a fresh copy of the "
    "[repository](https://github.com/undorigo/battery-storage-backtest), with the commands in "
    "its README under *Reproduce it*.")
