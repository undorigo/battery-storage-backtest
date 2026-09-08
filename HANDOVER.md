# Handover — Battery Storage Backtest

Context for the assistant picking this project up in VS Code. `CLAUDE.md` holds the
standing rules and the technical spec; this file holds the state of play and the reasoning
behind decisions already made, so they do not get relitigated.

Written 8 September 2026, before the first commit.

---

## How to work on this project

**Ivo is learning, not outsourcing.** The explicit purpose is to practise time series
forecasting properly — chronological validation, real benchmarks, uncertainty, drift.
A pipeline that appears fully formed defeats the point.

So: explain the reasoning before producing code. When there is a choice between two
approaches, name both and say which you would pick and why. Generate in pieces he can
follow, not in complete modules he has to reverse-engineer.

**He pushes back on vague claims, and he is usually right to.** Two examples from the
planning conversation: he caught that a proposed weather dataset would have leaked
hindsight, and he rejected an earlier plan that put the optimiser before the modelling.
Both corrections improved the project. Assume the same standard applies to anything you
assert — if something has not been verified, say so rather than smoothing over it.

**Prefer the smallest thing that works.** This project has a standing tendency to sprawl.
The scope boundaries below were argued through once already.

---

## Where things stand

Nothing is built yet. The repository is being initialised today with `README.md`,
`CLAUDE.md`, `.gitignore`, `LICENSE` (MIT), and this file.

**Blocked on:** the ENTSO-E API token. The request could not be sent yet — the platform
was under maintenance on 8 September. It goes out first thing, and access takes up to
three working days.

**Workaround in place:** SMARD.de offers CSV downloads without registration, so stages 0
and 1 can proceed on SMARD data and switch to the API when the token arrives.

---

## Settled decisions — do not reopen without a reason

| Decision | Reasoning |
|---|---|
| **Day-ahead price, not intraday** | Drivers are published before gate closure, which makes it tractable in weeks. Intraday needs order book data behind a licence wall. |
| **Hourly resolution** | Quarter-hourly products started 30 Sept 2025, mid-test-period. Aggregating up keeps one consistent series. |
| **Window starts Oct 2018** | DE-LU did not exist as a bidding zone before then; earlier data is the DE-AT-LU zone under a different EIC code. Splicing them joins two markets. |
| **Train ≤2022 / validate 2023 / test 2024–25** | ~37k training rows is ample. Two-year test follows the EPF literature. |
| **No weather data in v1** | The ENTSO-E day-ahead wind and solar *generation* forecast already contains the weather forecast, converted onto the real installed fleet — and it is what the market saw. |
| **No fuel or CO₂ prices in v1** | A lagged price level (most recent daily mean available at the decision point) carries the fuel signal for free. Whether real TTF and EUA beat it is a stage 2 experiment. |
| **No outage data** | Heavily revised after publication; pulling it today returns a corrected version, not what was known at gate closure. |
| **Modelling first, optimiser at stage 4** | The learning goal is forecasting. A greedy revenue rule at stage 1 provides a euro figure to steer by until the real optimiser exists. |
| **SoC carries over midnight** | Realistic. Handled with an overlapping horizon: optimise 48 h, implement 24 h, carry forward. Avoids the end-of-horizon dump. |
| **Battery: 1 MW / 2 MWh, 90 % each way, cycle penalty** | Standard two-hour asset. Round-trip ≈ 81 %. |

---

## Explicitly rejected — and why

- **Building the optimiser first.** Was the original plan; overruled because the learning
  goal is modelling and three weeks of MILP plumbing at the start risks the whole project.
- **open-meteo Historical Forecast API.** Sounds like a forecast archive; is not. It
  stitches the first hours of successive model runs, which is close to an analysis of what
  actually happened. If weather is ever needed, the Previous Runs API is the correct one.
- **Multiple countries, quarter-hourly modelling, balancing reserve co-optimisation.**
  Each doubles the work without changing what the project demonstrates.
- **More model architectures, deep learning, heavy hyperparameter tuning.** No interview
  value. The differentiators are clean validation, a real benchmark, and revenue framing.

---

## Open questions

These are genuinely unresolved and will be answered by doing, not by discussion:

1. **Coverage.** Are there gaps in DE-LU series across 2018–2025? Unverified. Stage 0
   counts missing periods rather than assuming.
2. **Revisions.** Does ENTSO-E overwrite a published day-ahead forecast value? Structurally
   it should not — day-ahead and intraday are separate series — but this is untested.
   Mitigation: timestamp every pull.
3. **Training window.** Does full history from 2018 beat 2023-onwards only? More data
   against better regime match. Stage 2 experiment, roughly an hour.
4. **Fuel prices.** Do real TTF and EUA beat the lagged price level? Stage 2 experiment.

---

## Immediate next actions

**Tuesday 8 Sept — 4 h**
1. ENTSO-E account, then token request to `transparency@entsoe.eu`, subject "RESTful API access"
2. Repository, environment, first commit
3. Day-ahead prices from SMARD, loaded and normalised
4. First plots: price history, negative-price hours per year, average daily spread

**Wednesday 9 Sept — 4 h**
1. Load, wind and solar forecasts; derive residual load
2. Scatter residual load against price — the merit order should become visible
3. `src/config.py` with the split dates and EIC code as constants
4. README updated with the first figure, committed

**The one thing to get right on day one:** timezone handling. Clock-change days have 23 or
25 hours. Convert once at load, stay timezone-aware throughout. Getting this wrong produces
silently shifted series that surface weeks later.

**The second thing:** `src/config.py` before any modelling code. It makes the locked test
period a constant rather than an intention.

---

## Stage plan and checkpoints

Each stage is gated. The checkpoint is a genuine stop condition, not a formality — at
20 hours a week the temptation to skip ahead is the main risk to the project.

| Stage | Dates | Delivers | Checkpoint |
|---|---|---|---|
| 0 Data | 8–9 Sept | Reproducible pull, split locked | Runs twice identically; coverage counted |
| 1 First model | 14–16 Sept | LightGBM vs naive rule | rMAE < 1, and no hindsight in features |
| — Compass | 16 Sept | Greedy revenue rule | A euro figure exists beside every metric |
| 2 Model craft | 17–30 Sept | LEAR, model layout, decomposition, extrapolation, training window | Can you *explain* why a variant wins? |
| 3 Uncertainty | 1–8 Oct | Quantile regression | Are the intervals calibrated? |
| 4 Revenue | 9–14 Oct | MILP optimiser, capture rate | Same horizon convention across all three runs |
| 5 Operations | 15–16 Oct | Drift, scheduled run, dashboard | Clone and reproduce in under ten minutes |

**Stage 2 is the core** — it carries the most hours and the most learning. Stage 2's end
is also the first publishable state.

---

## The framing that should survive to the README

Two things worth keeping in view while building:

**Accuracy only pays where it changes a decision.** If two forecasts produce the same
schedule, the more accurate one earned nothing. The interesting result at the end is not
the error metric but the point where better forecasts stop converting into money.

**This is not a novel problem.** Every optimiser runs a better version. The project
demonstrates competence, not a new result — and saying so plainly reads as judgement
rather than weakness.

---

## Reference

The full plan, with reasoning, sits at the artifact produced during planning. Key external
references:

- ENTSO-E Transparency Platform — data items 12.1.D (prices), 6.1.B (load forecast),
  14.1.D (wind/solar generation forecast), 16.1.B&C (actual generation)
- `entsoe-py` — Python client, returns pandas objects
- `epftoolbox` (Lago & Weron, *Applied Energy* 2021) — LEAR benchmark and evaluation
  methodology including the Diebold-Mariano test
- SMARD.de — cross-check and no-registration fallback
