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
   (published before gate closure)      (decision)          (actual prices)
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

| Stage | What it delivers | Headline number | Status |
|-------|-----------------|-----------------|--------|
| 0 | Reproducible data pull, split locked | negative-price hours, daily spread | done 17 Sep 2026 |
| 1 | First model against naive benchmark | **rMAE 0.532** | done 30 Sep 2026 |
| 2 | Recalibration, LEAR, one model per delivery hour | rMAE per variant, DM significance | next |
| 3 | Quantile forecasts | pinball loss, coverage | |
| 4 | MILP optimiser, revenue | capture rate | |
| 5 | Drift monitoring, scheduled run | reproducibility | |

Stage 2 led with "model craft" until 30 September. It now leads with **recalibration**, because
refitting monthly rather than once moved the tree from 0.488 to 0.440 on validation — a larger
gain than any choice of algorithm produced. Expanding beat rolling, so the lever is *refit more
often*, not *forget the crisis*.

**CatBoost and Random Forest are parked until stage 4**, not dropped. Both are reported to trade
well despite worse error scores, so capture rate may not rank models the way rMAE does. Ranking
more algorithms on the wrong metric is wasted effort; stage 4 settles whether the two agree.

The full plan, with what stage 1 found and roughly when the rest lands, is in the README under
**Where this is going** — that is the canonical version and this table follows it.

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
features(published before gate closure) → forecast → schedule → settle(actual prices) → capture rate
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

### Standing Protocol — Align Before Building

Ask before building, whenever a change needs alignment or clarification. A question costs
a minute. The wrong abstraction costs a day, and is harder to remove later than it was to
add.

Use the ask-a-question prompt rather than prose whenever:

- a plan changes materially, or a stage's scope moves
- a decision has more than one defensible answer
- a new file, directory, dependency or tool is being proposed
- something is being built to guard against a risk that has not actually been observed

**"I can imagine a case where this breaks" is not a requirement.** Build for the failure
that happened, or that the data shows will happen. A hypothetical justifies a note in the
work log, not a module.

Scaffolding is the easiest thing to add and the hardest to notice. When the line count
grows faster than the results, stop and say so.

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
# Every column here must have been published before the auction closed.  That
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

### Standing Protocol — Build Evidence, Not Volume

This repository is read by two audiences: the person building it, and whoever is deciding
whether to hire them. The second audience does not change what gets built. It changes the
tiebreaker when a choice is genuinely open.

**The tiebreaker:** prefer the option a reader can check.

That is not the same as the option that looks more impressive. A polished repository with a
leaked feature is worth less than nothing, because it demonstrates exactly the failure the
work is supposed to guard against.

**What counts as evidence.** Not the number of models, features, markets or lines of code.
The things that cannot be faked by adding more:

- a backtest whose information boundary holds when someone goes looking
- a number that regenerates from a clean clone by a documented command
- a decision recorded with the alternatives that were rejected, and why
- a bug caught by a test written to catch it, verified by reintroducing the bug
- a limit stated plainly instead of hidden — including "this dataset cannot answer that"

**What this does not license.** More scope, more sources, more architectures. The Second Law
still governs. A project that sprawls in order to look substantial is the failure this
protocol exists to prevent, not a use of it.

**The one-line version:** the differentiator is judgement, and judgement is only visible when
the reasoning is written down next to the result.

### Standing Protocol — Teach While Building

The first goal is learning, which changes how code arrives rather than what gets built.

**Explain the reasoning before producing code.** Where there is a genuine choice between two
approaches, name both and say which you would pick and why. Generate in pieces that can be
followed, not finished modules that have to be reverse-engineered — a pipeline that appears
fully formed defeats the point of building it.

**Expect pushback on vague claims, and expect it to be right.** Two corrections from the
planning conversation set the standard: a proposed weather dataset would have leaked
hindsight, and an earlier plan put the optimiser before the modelling. Both came from
outside the work, and both improved it. The pattern has held since — a question about where
missing rows sit, rather than how many there are, found an annual data hole in the held-back
years; a question about refitting produced the two-recipe design that revealed stage 1's
ranking reversal.

**So if something has not been verified, say so rather than smoothing over it.** An
unverified claim stated plainly is useful. The same claim stated confidently costs more to
undo than it ever saved.

### Standing Protocol — Learning Notes in Plain Language

This project has two goals and the first one is learning. Something understood is worth
more than something merely built, so what is learned gets written down — in language a
reader from outside this field would follow on the first pass.

**The daily recap.** A working session opens with an interview on the previous one: a
handful of questions across market knowledge, the code, and how the work is done. Answers
are corrected in writing. What comes out of it is appended to `docs/learnings.md` — one
entry per idea, dated, never rewritten. That file is personal study material and is not
committed.

**The language.** Write the way Ginny Redish teaches. Short sentences. Everyday words.
The point first.

Never let a technical term do the explaining. Say the thing in plain words, then put the
term in brackets, so the reader can look it up *once they already know what it means*.

| Instead of | Write |
|---|---|
| Subsidy structures keep plants running below zero | Some plants earn per unit produced, so stopping costs them money (*subsidy structures*) |
| `curveType A03` forward-fills absent positions | A missing row means "same as the row above", not "no data" (*curveType A03*) |
| Fit the scaler on train only, to avoid leakage | Work out the average from the training years alone. Using every year lets the model peek at the future (*data leakage*) |

**This is the default for explanation everywhere**, not only for what gets written to disk:
`docs/learnings.md`, the work log, the README, and any explanation given during a working
session. If a concept is being explained rather than used, it is explained this way without
being asked.

It does **not** govern code comments — those follow the protocol above, and may name a term
directly, because their reader is already inside the file. Nor does it govern a term already
established earlier in the same session: plain language is for the first encounter, and
repeating the scaffolding after that is its own kind of noise.

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

### Standing Protocol — Early Warning Signs

The leakage check above asks a question about a specific change. These are about the work
itself, and each one has the same remedy: **go back to the last completed stage.**

| Sign | What it usually means |
|---|---|
| The backtest looks suspiciously good | go hunting for hindsight before celebrating |
| You cannot say which change caused which improvement | too many at once; undo until you can |
| The error improves and the money does not | the gains are landing in hours that do not matter |
| More than two days spent cleaning data | cut scope, not care |
| Days of reading without a commit | reading is a stage's work, not a substitute for it |

Two of these have already fired on this project, which is why they are written down rather
than implied.

**The backtest looked suspiciously good** on 14 September, when a check was handed actual
load instead of the forecast: correlation 1.0000, error 0. That was deliberate — it proved the
check could fail — but it is exactly what a real leak looks like from the inside.

**The error improved and the ranking did not hold.** Stage 1 chose a gradient-boosted tree on
the validation year by 0.044 of rMAE, and on the held-back years the straight-line model beat
it. The gap had been measured as a near coin toss two days earlier and was not acted on.

The third sign is the one with no instrument yet. Until stage 4 exists there is no capture
rate to compare an error improvement against — so a forecast that improves on paper cannot
yet be shown to improve a decision. **That is a stated limit of every number before stage 4,
not a detail.**

### Meta-Law — Conflict Resolution

Laws are ordered. When they conflict, state the conflict, justify the resolution, and
resolve in hierarchy order.

---

## INTEGRATION CONTRACTS

Five shared interfaces where a change in one place breaks another.

### Contract 1 — Feature Availability (HIGHEST RISK)

**Owner:** `src/features.py`
**Dependents:** everything downstream

Every feature must have been published **before the auction closed** — 12:00 on day D−1 for
this market. This is not a style preference; it is what separates a valid backtest from a
worthless one.

Lead with the constraint rather than the clock, because two different deadlines are easy to
collapse into one number:

| | What it is | Who sets it |
|---|---|---|
| **Information boundary** | what the market could have known: anything published before the book closed | the market — a fact |
| Operational deadline | when your own pipeline must be finished, leaving room to run the model, run the optimiser, submit and recover | you — a choice |

**Only the first governs a backtest.** The question is whether the market could have known a
value, not whether a pipeline would have finished in time. An earlier internal cut-off makes a
backtest more conservative without making it more correct, and discards legitimate information.
The operational deadline belongs in the README's note on what production would add.

**Neither is checkable from this data.** ENTSO-E indexes values by the hour they describe, never
by the moment they were published, which is why `scripts/verify_forecast_series.py` has to prove
provenance by comparing a forecast against its own actual instead of reading a timestamp.

So the boundary is enforced **structurally, with no clock anywhere**. `MIN_PRICE_LAG_HOURS` is 24
for a reason worth following once: for delivery hour 23:00 on day D, a 12-hour lag reaches back
to 11:00 **on day D itself**, which nobody knew at the decision point. Twenty-four hours is the
smallest fixed lag that is safe for all 24 delivery hours, and a fixed row offset needs no date
comparison to be right.

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
| `src/sources/` | Transport only: parameters in, tidy frame out. One module per source, so swapping SMARD for ENTSO-E never edits the file that owns Contract 5. Nothing outside imports these |
| `src/sources/entsoe.py` | The data-item catalog: request parameters, and the Contract 1 claim per series as a field a test can read |
| `src/data.py` | Caching and normalisation; the public `load_*()` API everything else calls |
| `src/features.py` | Feature construction; enforces the availability contract the catalog declares |
| `src/models.py` | Training, benchmarks, quantile models |
| `src/backtest.py` | Dispatch optimiser and settlement |
| `src/evaluate.py` | rMAE, Diebold-Mariano, pinball loss, capture rate |
