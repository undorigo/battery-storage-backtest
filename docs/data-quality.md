# What is in the data, and what is missing from it

Written after the first full pull, 17 September 2026. Covers DE-LU, 1 October 2018 to
31 December 2025, as cached in `data/raw/`.

Regenerate any figure here with `just pull`, then read the series with `src.data.load()`.

---

## Coverage

63,578 hours lie between the first and last delivery hour. Against that:

| Series | Hourly rows | Missing | Feature-eligible |
|---|---|---|---|
| `day_ahead_price` | 63,578 | **0** | no — it is the target |
| `load_forecast` | 63,575 | **890** | **yes** |
| `wind_solar_forecast` | 63,577 | 0 | **yes** |
| `actual_load` | 63,576 | 3 | no |
| `actual_generation` | 63,577 | 0 | no |

Both series a model is allowed to use are listed in bold. One of them is complete; the
other is the subject of most of this note.

---

## Seven hours we lost ourselves

The price series first came back with seven hours missing — one on 29 September of each
year from 2019 to 2025. Same date, same hour, seven years running.

The day-ahead auction has cleared every hour since the market opened, so that was never
market behaviour. It was **our own pull dropping data**, and the cause is a defect in the
`entsoe-py` library:

> The library splits any request longer than a year into blocks. It then removes each
> block's first timestamp, expecting it to be a duplicate of the previous block's last one.
> The API returns half-open windows, so the previous block never held that timestamp — and
> removing it deletes the only copy.

Every one of the seven was returned when asked for in a narrow request. They are now
recovered and the series is complete:

```
2019-09-29 22:00      5.07 EUR/MWh        2023-09-29 22:00     90.95
2020-09-29 22:00     41.70               2024-09-29 22:00     19.00
2021-09-29 22:00     70.30               2025-09-29 22:00    101.10
2022-09-29 22:00    349.44
```

**What this cost us in time was worth it.** Seven hours out of 63,578 changes no headline
figure. But the loss was *systematic* and *silent*, and nothing would ever have reported
it. It was found only because coverage was counted rather than assumed.

`src/data.py` now checks every series against its own spacing after fetching, and re-fetches
anything that is missing. The check works from the data rather than from the library's
block arithmetic, so it is not tied to the one defect that prompted it. A re-fetch that
recovers nothing is also useful — it is the difference between *we failed to fetch this*
and *this was never published*.

---

## The load forecast: 37 whole days, and 2 single hours

890 hours sounds like a scattered-holes problem. It is not.

| When | Missing | Shape |
|---|---|---|
| Oct–Dec 2018 | 840 h | ~35 whole delivery days |
| 22 Feb 2022 | 24 h | one whole day |
| 24 Mar 2022 | 24 h | one whole day |
| 29 Oct 2023 | 1 h | first hour of the day |
| 27 Oct 2024 | 1 h | first hour of the day |

Almost all of it is the market's opening quarter, when publication was evidently still
settling down. The rest is two isolated days and two isolated hours in seven years.

### ENTSO-E genuinely does not have it

Four checks, the last of which is conclusive:

1. **Re-fetched all 25 gaps** during the pull, in narrow windows. Nothing came back — which,
   after the price bug above, is a meaningful negative result rather than an assumption.
2. **Checked SMARD**, the German regulator's platform. It carries actual consumption,
   residual load and forecast *generation* — but **no consumption forecast at all**. Twenty
   filters were correlated against the ENTSO-E series; the closest was filter 410 at 0.9932
   and 1,090 MW mean error, which is almost exactly the forecast error measured in
   September. That identifies it as *actual* load, not the forecast.
3. **Asked ENTSO-E's REST API directly**, bypassing the client library entirely. The reply
   is explicit:

   > `Acknowledgement_MarketDocument` — *"No matching data found for Data item
   > DAY_AHEAD_TOTAL_LOAD_FORECAST_R3 [6.1.B]"*

   For the identical window, *actual* load returned 384 points. ENTSO-E has the outcome and
   not the expectation.

4. The control window either side returns 192 points normally, so this is the data and not
   the request.

---

## The days are available elsewhere — deferred, not dismissed

**Energy-Charts (Fraunhofer ISE) has them.** This was checked rather than assumed, and it
changes what "missing" means: the data is absent from *our source*, not from the world.

### It is the same series

| Check | Result |
|---|---|
| Does it cover the gaps? | **yes** — 480 quarter-hourly values across 2018-10-02..06 |
| `de` alone against ENTSO-E | **549 MW short**, every hour — that is Luxembourg |
| **`de` + `lu` against ENTSO-E DE-LU** | **MAE 0.025 MW**, worst deviation 0.1 MW |

On a 55,000 MW series that is rounding error. Same data item, established the same way the
SMARD price filter was established.

### It behaves like a forecast, not like hindsight

The gap-day values were put through the same test `scripts/verify_forecast_series.py`
applies to ENTSO-E, comparing them against what actually happened:

| Window | corr | MAE | **exact matches** |
|---|---|---|---|
| 2018-10-02..06 *(gap)* | 0.9740 | 781 MW | **0** |
| 2022-02-22..24 *(gap)* | 0.9702 | 1,440 MW | **0** |
| 2019-03-04..11 *(control)* | 0.9896 | 2,755 MW | **0** |
| *ENTSO-E's own forecast, control week* | 0.9895 | 2,748 MW | 0 |

A reconstruction from actuals would show near-zero error and match at every point. Not one
point matches, and the error sits in the normal range for a load forecast. The control week
tracks ENTSO-E's own figures to within 7 MW, which points to the same publication chain
rather than a re-derivation.

**What remains unprovable:** that Energy-Charts archived these before gate closure rather
than obtaining them from the TSOs later. That is equally unprovable for ENTSO-E's own
history, and the evidence above is as far as this can be taken without asking Fraunhofer.

### Decision: drop the days for now, and revisit after stage 1

**This is a deferral, not a dismissal.** The days are droppable *and* recoverable, and the
question of which is better is one the model can answer better than an argument can.

| | |
|---|---|
| **Now** | Drop the ~37 affected delivery days from training |
| **Revisit** | End of stage 1, once there is a measured rMAE |
| **Trigger** | Errors concentrated in early data, or a training set that feels short |
| **If we act** | Add `src/sources/energy_charts.py`; roughly an hour, validation already done |

The reasoning for dropping in the meantime is unchanged: the gaps are whole days, so
dropping leaves no interpolation seam, and it costs about 37 of roughly 1,550 training days
— under 2.5 %, from the market's least representative quarter.

The reasoning for recording this so carefully is that **the difference between "we dropped
data" and "we dropped data knowing exactly how to get it back" is the difference between an
oversight and a decision.**

### The recipe, so acting on it later is cheap

```
GET https://api.energy-charts.info/v2/public_power_forecast
      ?country=de        (and again with lu, then sum)
      &production_type=load
      &forecast_type=day-ahead
      &start=YYYY-MM-DD&end=YYYY-MM-DD

Response: data[].timestamp (local, tz-aware) and data[].values.load, MW, PT15M
Rate limited — HTTP 429 on rapid successive calls, so pace them.
Validate any new window the same way: de+lu against ENTSO-E where both exist,
then the forecast-versus-actual test above.
```

**Interpolate the two single hours in 2023 and 2024.**

Different reasoning, because these fall in the validation and test years. Removing an hour
from a period being *measured* changes what the number means; removing one from a period
being *learned from* only changes what the model saw. Two hours out of 26,000, with known
neighbours on both sides of a smooth series, distort less by being filled than by being cut.

Both fall on the last Sunday of October, when the clocks go back. That looked like a pattern
worth chasing, but the other six clock-change days in the record are complete, so it is a
coincidence rather than a rule.

---

## What the gap check cannot see

The check finds holes **between** timestamps. It cannot see data missing from the start or
the end of a series, because there is no step to be wider than.

Three hours sit in that blind spot, all at the very beginning of the record:

| Series | Starts | Late by |
|---|---|---|
| `load_forecast` | 2018-10-01 00:00 UTC | **2 hours** |
| `actual_load` | 2018-09-30 23:00 UTC | **1 hour** |

Both were checked by hand with a narrow request, and both are genuinely absent — the same
answer as every other 2018 gap. So the blind spot has cost nothing so far.

It is worth knowing about anyway. The end of a series is exactly where a future pull extends
it, and that is the one place this check would not notice a value being dropped.

---

## Actual load: three hours

8 October, 28 October and 30 October 2018 — one hour each, scattered, in the opening weeks.
Not recovered by re-fetching, so genuinely absent.

No decision needed yet. `actual_load` is not feature-eligible; it exists so that the
prohibition on using it is testable, and so the forecast has something to be checked against.

---

## The resolution change

German day-ahead products went from hourly to quarter-hourly on 1 October 2025, in the
middle of the test period. The price series therefore holds 70,205 rows across 63,578 hours
— the extra 6,627 are the last quarter of 2025 arriving four times as often.

This needed no special handling. `to_hourly()` averages whatever falls inside each hour, so
four values collapse as readily as one, and a series that changes resolution partway through
comes out hourly throughout.

Averaging is the right operation for both kinds of series here. A megawatt figure averaged
over an hour is the energy delivered in it; and the revenue from four quarter-hour products
at 1 MW is the mean price times 1 MWh, not the sum.

---

## Summary of decisions

| Finding | Decision |
|---|---|
| 7 price hours dropped by the library | **Recovered.** Check is permanent, in `src/data.py` |
| ~37 load-forecast days absent from ENTSO-E | **Drop for now — revisit after stage 1.** Available from Energy-Charts, validated to 0.03 MW, provenance tested |
| 2 load-forecast hours in 2023 and 2024 | **Interpolate.** They fall in the measured period |
| 3 actual-load hours, Oct 2018 | No action. Not a feature |
| 3 leading hours, start of record | No action. Absent at source |
| Quarter-hourly from Oct 2025 | Averaged to hourly at load time. No special case |

---

## One thing to carry into stage 2

The load forecast's bias is **not stable over time**. It is not a fixed offset to be
subtracted once:

| Week | Mean error, forecast minus actual |
|---|---|
| March 2019 | **−2,748 MW** — under-forecast in every single hour |
| June 2022 | **+195 MW** |

Something changed between those dates — the forecasting method, or the definition of what
the actual figure counts. Either way, a model trained across the boundary sees two different
relationships wearing the same column name. Worth understanding before stage 2 chooses a
layout, and worth remembering if early-period errors turn out to be large.
