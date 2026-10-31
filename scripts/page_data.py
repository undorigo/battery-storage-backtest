"""The web page's data: one small file, rebuilt from what stages 2 to 4 stored.

The page must show the same numbers the record states, from a clean clone, with no
MLflow and no data cache.  So everything it draws is written here into one committed
file, `reports/page.parquet`: for every hour of 2023 and 2024-25 the real price, the
five forecasts, LEAR's 80 % range, the battery's plans and what every run earned.

**Nothing here is new.**  The forecasts and the range are the ones `just train daily`,
`just quantiles` and the two `final-score` readings stored; the plans come from the
same functions `just backtest` and `just final-score battery` call.  A test holds the
file's totals to `reports/capture_scores.csv`, so the page cannot drift from the
record.  Rebuilding a plan already scored reads no score anew: nothing is chosen
from it.
"""

from __future__ import annotations

import time

import pandas as pd

from scripts import backtest as SB                     # the same planner calls as both readings
from src import backtest as BT
from src import config as cfg

SPLITS = ("valid", "test")                             # 2023, then the years held back
BAND = (90, 10)                                        # the 80 % range, upper first
SHOWN = ("ceiling", "average", "LEAR", "naive (field)", "bids strict")   # plans the page draws


# ── One split, hour by hour ───────────────────────────────────────────────────
# Columns are named `kind:run` so the page can find a run by name without a
# lookup table: `forecast:LEAR`, `net:ceiling` (MW sold minus bought, so charging
# is negative), `earned:bids strict`.  Every capture-table run keeps its earnings,
# the five the page draws also keep their hour-by-hour plan.  The bids are LEAR's
# plan sent as loops with the limits stage 4 used, the headline's configuration.

def hours(split: str) -> pd.DataFrame:
    """Every hour of one split: price, forecasts, range, plans, earnings."""
    actual = SB.actual_prices(split)                          # real hours, as the battery is paid
    _, planned = SB.forecasts(actual.index, split)
    _, upper, lower = SB.ranges(actual.index, planned["LEAR"], split, band=BAND)

    frame = pd.DataFrame({"split": split, "price": actual}, index=actual.index)
    for name, forecast in planned.items():
        frame[f"forecast:{name}"] = forecast
    frame["p90"], frame["p10"] = upper, lower

    schedules = {"ceiling": BT.ceiling(actual)}
    schedules |= {name: BT.fixed(forecast, actual) for name, forecast in planned.items()}
    _, buy_at, sell_at = SB.ranges(actual.index, planned["LEAR"], split)   # stage 4's p75 / p25
    lear_plan = schedules["LEAR"][0]
    limits = BT.limits(lear_plan, buy_at, sell_at)
    schedules |= {f"bids {rule}": BT.bid(lear_plan, actual, limits, rule) for rule in BT.RULES}

    for run, (schedule, earned) in schedules.items():
        if run in SHOWN:
            frame[f"net:{run}"] = schedule.discharge - schedule.charge
        frame[f"earned:{run}"] = earned
    frame.index.name = "hour"                                 # UTC, as every stored series
    return frame


# ── Writing it, and saying what it holds ──────────────────────────────────────
# Printed as shares of each split's ceiling, so a reader can set them beside the
# README's table at a glance; the test makes the same comparison to the cent.

def main() -> int:
    started = time.perf_counter()
    try:
        frame = pd.concat([hours(split) for split in SPLITS])
    except (FileNotFoundError, LookupError) as exc:
        print(exc)
        print("\nNeeds the data cache (`just pull`) and the stored runs both readings used.")
        return 2

    frame.to_parquet(cfg.PAGE_DATA)
    earned = frame.filter(like="earned:").groupby(frame.split).sum()
    shares = earned.div(earned["earned:ceiling"], axis=0).T
    shares.index = shares.index.str.removeprefix("earned:")
    print(f"{cfg.PAGE_DATA.relative_to(cfg.ROOT)}: {len(frame):,} hours, "
          f"{cfg.PAGE_DATA.stat().st_size / 1e6:.1f} MB, {time.perf_counter() - started:.0f} s\n")
    print("Share of the ceiling:")
    print(shares.map(lambda x: f"{x:.1%}").to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
