# Battery Storage Backtest — Day-Ahead Price Forecasting

## Project Context & Engineering Laws

---

## WHAT THIS PROJECT IS

Forecast the German day-ahead electricity price for tomorrow, use that forecast to
schedule a battery, and measure how much of the theoretically achievable revenue the
forecast captured.

The chain, end to end:

```
ENTSO-E data → features → price forecast → dispatch optimiser → settlement → capture rate
   (known at 11:00 on D-1)              (decision)          (actual prices)
```

**Two goals, in this order.** First, practise time series forecasting properly on real
market data. Second, produce portfolio evidence of energy-domain and data work in one
piece. When a design decision is unclear, ask which of the two it serves.

### The decision being modelled

The day-ahead auction closes at 12:00 on day D−1 and covers all delivery periods of
day D. A battery operator must commit a schedule before that deadline, without knowing
tomorrow's prices. The commitment is binding.

So the forecast horizon is 12 to 36 hours, and the decision point is fixed at 12:00 on D−1.
Everything in this repository is downstream of that single fact.

### Target and split

| | |
|---|---|
| Target | Day-ahead clearing price, DE-LU bidding zone, €/MWh |
| Bidding zone EIC | `10Y1001A1001A82H` |
| Resolution | Hourly (quarter-hours after 30 Sept 2025 aggregated up) |
| Output | 24 values per run, one per delivery hour of day D |
| Train | Oct 2018 – Dec 2022 |
| Validate | 2023 |
| Test | 2024 – 2025 |

The window starts in October 2018 because the DE-LU bidding zone did not exist before
then — Germany, Austria and Luxembourg shared one zone and one price under a different
EIC code. Splicing across that boundary joins two different markets.

### Battery being modelled

1 MW power, 2 MWh capacity, 90 % efficiency each direction, state of charge 0–100 %,
a cost penalty per cycle for degradation. State of charge carries over midnight, handled
by an overlapping horizon: optimise 48 hours, implement the first 24, carry forward.

### Stage plan

| Stage | What it delivers | Headline number |
|-------|-----------------|-----------------|
| 0 | Reproducible data pull, split locked | negative-price hours, daily spread |
| 1 | First model against naive benchmark | rMAE |
| 2 | Model craft: LEAR, layout, decomposition, extrapolation | rMAE per variant, DM significance |
| 3 | Quantile forecasts | pinball loss, coverage |
| 4 | MILP optimiser, revenue | capture rate |
| 5 | Drift monitoring, scheduled run | reproducibility |

---

## THE LAWS

These govern every change made to this codebase — by humans and AI assistants alike.

### Zeroth Law — Intent Fidelity

Preserve the developer's intent. When a change is ambiguous or touches an Integration
Contract, surface the risk before executing.

Never make irreversible changes — altering a split date, overwriting a cached data pull,
changing a settlement convention — without stating the downstream effect first. Any of
these silently invalidates every result produced before the change.

### First Law — Outcome Integrity

Every change must leave the evaluation chain intact:

```
features(known at 11:00 D-1) → forecast → schedule → settle(actual prices) → capture rate
```

A change is not complete if the chain is broken, even if the edited file passes its own
tests. Correctness means the full evaluation runs end to end and the numbers are still
comparable to the previous run.

**If a change makes new results incomparable to old ones, say so explicitly.**

### Second Law — Elegant Sufficiency

Use the simplest change that satisfies the First Law. Complexity must be justified by a
specific requirement.

This project has a standing tendency to sprawl: more model architectures, more markets,
more countries, more features. None of that is in scope. Do not add abstraction layers,
config files, or dependencies unless the First Law cannot be satisfied without them.

### Third Law — Reproducibility

Any result stated in the README must be reproducible from a clean clone by running a
documented command. If a number cannot be regenerated, it does not go in the README.

Data pulls are cached and timestamped. A cached pull is never silently overwritten —
ENTSO-E revises history, and an overwrite would rewrite the training data underneath
results that were already published.

### Standing Protocol — Transparency

Before any change touching an Integration Contract, state:
1. Which contract is affected
2. Which other files depend on it
3. Whether those files are updated in the same change
4. Whether previously produced results remain valid

### Standing Protocol — Educational Comments

This repository exists to be read. Every file written or edited carries two layers.

**Layer 1 — Section header (one per logical block).** A short prose paragraph above each
section explaining WHY the block exists: what problem it solves, what the reader needs to
know first, any non-obvious constraint. Lead with the most important sentence. Three to
five lines maximum — if more is needed, the section is too large.

```python
# ── Build the feature frame ───────────────────────────────────────────────────
# Every column here must have existed at 11:00 on D-1, before gate closure.  That
# is why we use the published TSO wind forecast rather than actual generation —
# the actuals are freely available today but were unknown when the decision was
# made, and using them would inflate every result downstream.
```

**Layer 2 — Inline comment (one per meaningful line).** A short phrase to the right of
each non-obvious line, in plain words, 5–10 words. Skip lines that already read like
English.

```python
df = load_parquet(RAW / "prices.parquet")   # DE-LU day-ahead prices, hourly, from 2018-10
df = df.tz_convert("Europe/Berlin")         # keep one timezone convention everywhere
df["residual_load"] = df.load - df.wind - df.solar   # what thermal plants must cover
```

**Do not comment:** lines whose names already explain them, restatements that add nothing,
or implementation details that belong in the commit message.

### Standing Protocol — Commit & Push After Every Change

Every completed change is committed and pushed immediately. Do not batch.

```
<imperative summary, max 72 chars>

<one or two sentences on WHY: what problem this solves or what it enables>

Co-Authored-By: Claude <noreply@anthropic.com>
```

Summary uses an imperative verb. The body answers WHY — the diff shows what. Never
reference the current task or session; write for a reader who has only `git log`.

One logical change = one commit.

### Standing Protocol — Dependency Check

Before committing: a new `import` means the package is in `requirements.txt`, in the same
commit as the code that needs it. From stage 5 onwards, a new CLI call means the binary is
in the Dockerfile.

### Standing Protocol — Leakage Check

Before committing any change to features, splits, or evaluation, answer in writing:

1. Was every input to this feature published before 12:00 on D−1?
2. Was any statistic (scaler, encoder, imputation value) fitted on data outside the
   training period?
3. Does the settlement path touch forecast prices anywhere?

If capture rate exceeds 100 %, or rMAE drops implausibly, assume leakage before assuming
success.

### Meta-Law — Conflict Resolution

Laws are ordered. When they conflict, state the conflict, justify the resolution, and
resolve in hierarchy order.

---

## INTEGRATION CONTRACTS

Five shared interfaces where a change in one place breaks another.

### Contract 1 — Feature Availability (HIGHEST RISK)

**Owner:** `src/features.py`
**Dependents:** everything downstream

Every feature must have been knowable at 12:00 on day D−1. This is not a style preference;
it is what separates a valid backtest from a worthless one.

| Allowed | Not allowed |
|---------|-------------|
| Published day-ahead load forecast | Actual load |
| Published day-ahead wind/solar generation forecast | Actual generation |
| Prices of days ≤ D−1 | Prices of day D |
| Calendar features | Anything revised after publication |
| Installed capacity as of D−1 | — |

**The failure mode is silent.** A leaked feature produces excellent metrics and a model
that would lose money in production. Nothing errors.

### Contract 2 — The Split

**Owner:** `src/config.py`
**Dependents:** every training, evaluation and backtest script

```python
TRAIN_END = "2022-12-31"
VALID_END = "2023-12-31"
TEST_START = "2024-01-01"
TEST_END   = "2025-12-31"
```

These are constants in one file, not literals scattered across notebooks. Changing any of
them invalidates every previously reported number.

**The test period is evaluated once, at the end of a stage.** Repeated evaluation with
adjustment in between turns it into a second validation set and the final number becomes
optimistic.

### Contract 3 — Settlement Convention

**Owner:** `src/backtest.py`
**Dependents:** every reported revenue figure

Three objects stay strictly separate:

```
features_at_decision_time  →  schedule (decided)  →  actual_prices (settlement)
```

Decisions use forecasts. Settlement uses actuals. The third must never flow into the first.
Mixing them is the single most common way a capture rate exceeds 100 %.

### Contract 4 — Horizon Convention

**Owner:** `src/backtest.py`
**Dependents:** ceiling run, model runs, naive run

All three comparison runs — perfect foresight, model, naive — must use the identical
horizon and state-of-charge convention (48-hour optimisation, 24-hour implementation,
charge carried forward).

If they differ, the capture rate measures the convention rather than the forecast.

### Contract 5 — Time and Resolution

**Owner:** `src/data.py`
**Dependents:** everything

One timezone convention throughout, applied at load time. Clock-change days have 23 or 25
hours; quarter-hourly data after 30 Sept 2025 is aggregated to hourly at the same point.

Handle both in one place. Handling them per-script produces series that silently disagree
by an hour.

---

## DANGER ZONES

- **Timezone handling.** Naive timestamps anywhere in the pipeline. Convert once at load,
  keep tz-aware everywhere after.
- **The Oct 2025 resolution change.** A series that switches from 24 to 96 periods
  mid-test-set breaks aggregation that assumes a fixed shape.
- **Wrong bidding zone code.** `10Y1001A1001A82H` is DE-LU. `10Y1001A1001A63L` is the old
  DE-AT-LU. They are different markets, not different names.
- **Scaler fitted on full data.** Fit on training only, transform everywhere.
- **open-meteo Historical Forecast API.** Not a forecast archive — it stitches the first
  hours of successive model runs, which is close to an analysis of what actually happened.
  If weather is ever needed, use the Previous Runs API.
- **ENTSO-E outage data.** Heavily revised after publication. Pulling it today returns the
  corrected version, not what was known before gate closure. Out of scope for now.
- **Capture rate above 100 %.** Always a bug, never a result.

---

## PRE-CHANGE CHECKLIST

| Change type | Check |
|-------------|-------|
| Add or edit a feature | Available at 12:00 D−1? Fitted on training only? |
| Touch `config.py` | Which published results become invalid? |
| Edit the optimiser | Do ceiling, model and naive runs still share a convention? |
| Edit settlement | Do actual prices flow anywhere near the decision path? |
| Change data loading | Timezone applied once? Resolution change handled? |
| New import | In `requirements.txt`, same commit? |
| Report a new number | Reproducible from a clean clone by a documented command? |

---

## QUICK REFERENCE

| File | Role |
|------|------|
| `src/config.py` | Split dates, EIC codes, paths, battery parameters — single source of truth |
| `src/data.py` | ENTSO-E and SMARD pulls, timezone and resolution normalisation |
| `src/features.py` | Feature construction; owns the availability contract |
| `src/models.py` | Training, benchmarks, quantile models |
| `src/backtest.py` | Dispatch optimiser and settlement |
| `src/evaluate.py` | rMAE, Diebold-Mariano, pinball loss, capture rate |
