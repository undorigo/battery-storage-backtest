# Work log — Battery Storage Backtest

Running record of what was done, what was decided, and what was found. Newest session
last. Written for a reader who was not present: what changed, and why it changed.
Decisions belong here with their reasoning; `CLAUDE.md` holds the standing rules and
`HANDOVER.md` the decisions settled before any code existed.

## Contents

One row per working day. Follow the date link for the detail.

| Date | What was done |
|---|---|
| [8 Sep 2026](#d20260908) | Repository initialised. Environment rebuilt off the pyenv global into a project venv. Two `.gitignore` bugs found. Split boundary bug demonstrated and fixed in `config.py`. |
| [9 Sep 2026](#d20260909) | Cycle cost set to 8 EUR/MWh. ENTSO-E API outage diagnosed, then recovered. First authenticated pull. SMARD cross-validated to the cent. Raw XML read — two silent traps found. Python 3.11.14, editor settings, 15 contract tests. |
| [14 Sep 2026](#d20260914) | Platform recovered, sub-second. All four forecast series verified against their actuals by measurement. Catalog written — Contract 1 becomes a testable field. Code review found five issues, two of them wrong assumptions in the tests themselves. |
| [15 Sep 2026](#d20260915) | `just` replaced ad-hoc invocation. A proposal built on a hypothetical was dropped, and a protocol added to stop and ask instead. Eight open questions settled, including what finishes stage 0. |
| [16 Sep 2026](#d20260916) | Daily recap ritual and plain-language protocol added. `main()` read, empty package marker dropped, repository map written. `src/data.py` and `just pull` built: the first real market data on disk. |

[Commits](#commits) · [Open items](#open-items) · [Next](#next)

*Anchors are explicit `<a id="dYYYYMMDD">` tags on each day heading, so the links keep
working when a heading is reworded.*

---

## Stage 0 — Data · from 8 September 2026

**Stage goal:** a reproducible data pull with the split locked.
**Checkpoint:** runs twice identically; coverage counted.
**Status:** groundwork, `config.py`, forecast provenance, the catalog and the command menu
complete. The bulk pull, the coverage count, the figures and the data-quality note remain —
roughly two and a half hours.
**Done means:** pull runs twice identically · coverage counted · negative-price hours and
daily spread in the README · first figures · a written data-quality note.

---

<a id="d20260908"></a>
### 8 September 2026 — repository, environment, and the split

Opened with `README.md`, `CLAUDE.md`, `HANDOVER.md`, `.gitignore` and `LICENSE` already
in place from the planning session. No code, no environment, no dependencies.

#### Commit message corrected on an already-pushed commit

The `CLAUDE.md` commit carried a typo — "ontext" for "context". Because it had already
been pushed to `origin/main`, fixing it meant rewriting published history: `git commit
--amend` followed by `git push --force-with-lease`. `dc43e9a` became `c9ba760`.
`--force-with-lease` rather than `--force`, so the push would abort if the remote had
moved in the meantime.

#### The environment was not the project's

`VIRTUAL_ENV` pointed at `/Users/…/.pyenv/versions/3.11.3` — the pyenv **global**
interpreter directory, which is not a virtualenv at all (no `pyvenv.cfg`). VS Code's
Python extension had selected it for the workspace and was exporting the variable to
match. That directory carries catboost, celery, evidently, boto3, alembic and aiohttp
from unrelated coursework.

Two consequences, both fatal to the Third Law before a line of code existed. A
`pip freeze` would have emitted hundreds of packages unrelated to this project, hiding
which libraries were actually chosen. And a clean clone would have reproduced nothing,
because the environment was a machine-level accident rather than a project artefact.

Replaced with a project-local `.venv` on Python 3.11.3, and a hand-curated
`requirements.txt` — never `pip freeze` — pinned exactly:

```
entsoe-py==0.8.1   pandas==3.0.5   pyarrow==25.0.1
python-dotenv==1.2.3   matplotlib==3.11.1
```

Pinned exactly rather than with `>=`, because `entsoe-py` declares only `pandas>=2.2` and
pip resolved **pandas 3.0.5** — a major version the library never claims to support. That
combination was smoke-tested rather than assumed: the import works, and a tz-aware frame
survives a parquet round-trip with its UTC index intact.

#### Two `.gitignore` bugs, same root cause

Both instances of one rule: **git never descends into an excluded directory, so a
negation inside one can never fire.**

| Pattern | Intent | Actual behaviour |
|---|---|---|
| `data/` + `!data/**/.gitkeep` | keep the directory skeleton | skeleton silently absent from a clean clone — **fixed** |
| `.vscode/` + `!.vscode/settings.json` | commit the editor's interpreter choice | `settings.json` cannot be staged — **still open** |

Fixed for `data/` by excluding the *contents* (`data/**`) and re-including directories and
markers. Verified both directions with `git add --dry-run`: `.gitkeep` files stage, real
`.parquet` and `.csv` files stay ignored. An attempted trailing comment on a pattern line
was caught and removed — `.gitignore` only treats `#` as a comment at the start of a line,
so the comment would have become part of the pattern.

#### `.env.example` written, `.env` created

`.gitignore` promised an `.env.example` documenting the required keys; it did not exist.
Added, holding `ENTSOE_API_KEY` empty. The name is not arbitrary — `entsoe-py` reads that
exact variable from the environment on its own, so no mapping code is needed.

#### The split boundary bug — demonstrated, not assumed

Contract 2 states the split as bare dates (`TRAIN_END = "2022-12-31"`). Sliced against a
UTC index that is wrong twice over: the date is off by the UTC offset, and `pandas.loc`
is inclusive at **both** ends. Reproduced live — `2022-12-31 22:00+00:00` appeared in the
training set *and* the validation set. No error, no warning, and no metric would expose
one contaminated hour.

`src/config.py` resolves it by keeping the dates verbatim as the readable contract and
deriving half-open, DST-aware UTC boundaries that code actually touches. It also exports
`split(df)`, so the boundary arithmetic exists once rather than in every script — a
correct constant used with `.loc[:X]` in five places would satisfy the letter of Contract
2 while scattering exactly what it warns about.

Verified:

- `TRAIN_END_UTC = 2022-12-31 22:00+00:00` (= 23:00 Berlin, the last delivery hour)
- validation ends exactly one hour before test begins — no gap, no overlap
- clock-change days resolve correctly: 23 h (2023-03-26), 25 h (2023-10-29), 24 h normal.
  Derived as "next local midnight minus one hour", never a hard-coded 23:00
- a timezone-naive index is rejected rather than silently mis-sliced
- 2023 validates at exactly 8760 hours

#### Design decisions taken

| Decision | Choice | Reasoning |
|---|---|---|
| Transport layer | Wrap `entsoe-py`; own everything above it | The learning goal is forecasting, not XML parsing. Caching, provenance and normalisation are precisely what the library does *not* do. |
| Storage timezone | UTC index; calendar features derived in `Europe/Berlin` | UTC has 24 hours every day and no ambiguous timestamps, so joins never break on a clock change. Load and solar follow the local clock, so hour-of-day must be local. |
| Quarter-hour aggregation | Mean of the four quarters, from 2025-10-01 | The price a flat 1 MW block across the hour would settle at. Known cost: intra-hour spread is lost, so the revenue ceiling is understated after that date. |
| Split exposure | Contract 2 strings **and** a `split()` helper | See the boundary bug above. |
| Repository layout | Add `src/sources/` | Separates transport from normalisation, so the planned SMARD→ENTSO-E switch never edits the file that owns Contract 5. Extends CLAUDE.md's Quick Reference; to be recorded there with the first file placed in it. |

#### Facts verified against live sources, not memory

- `Area['DE_LU'].code == 10Y1001A1001A82H`; `Area['DE_AT_LU'].code == 10Y1001A1001A63L`
  — both match CLAUDE.md, checked against the library
- `entsoe-py` hard-codes `QUARTER_MTU_SDAC_GOLIVE = 2025-10-01` and returns a **mixed
  resolution** series across it: hourly before, 15-minute after, concatenated and **not**
  aggregated. The Danger Zone is real and lands inside the test period.
- `entsoe-py` ships `retry_count=3, retry_delay=10` and range-chunking decorators
  (`year_limited`, `day_limited`, `documents_limited`), so per-request range caps are
  already handled
- Rate limit is 400 requests/minute **per token**. A full seven-year backfill of four
  series chunked yearly is roughly 30 requests, so no throttle will be built — that would
  be Second Law sprawl.

---

<a id="d20260909"></a>
### 9 September 2026 — degradation cost, and a live API outage

#### Cycle degradation cost set to 8.0 EUR/MWh discharged

Previously zero, which is not a neutral placeholder: at zero the optimiser chases any
spread above round-trip losses, overstating both cycle count and revenue.

Derived as cell replacement cost over lifetime throughput — 70 EUR/kWh of LFP cells
across 8000 equivalent full cycles ≈ 8.75 EUR/MWh — and cross-checked against Montel's
published framework for a 50 MW two-hour GB battery, which uses GBP 7/MWh ≈ EUR 8. Two
independent routes within 10 % of each other.

The convention is stated explicitly in the code, because some sources count charge and
discharge together, which would halve the figure.

Effect on dispatch, charging at 50 EUR/MWh: the break-even spread rises from
**11.73 → 19.73 EUR/MWh**, a 68 % wider gap before cycling is worthwhile. Stage 4 reports
a sensitivity at 4 / 8 / 16 rather than resting on the point estimate.

#### ENTSO-E API outage — diagnosed, not guessed

The token is in `.env`: 36 characters, UUID-shaped. It could not be verified end to end
because the API is down. Each hypothesis was eliminated in turn:

| Probe | Result | Rules out |
|---|---|---|
| `entsoe-py` day-ahead request | `ReadTimeout` after 30 s | — |
| `curl`, token as header | TCP connect 40 ms, empty reply after 60 s | DNS, TLS, firewall |
| `curl`, **no token at all** | identical hang | **the token** — a bad one returns `401` at once |
| `transparency.entsoe.eu` | `200` in 0.4 s | general ENTSO-E outage, local network |
| `curl`, `securityToken` query param | **HTTP 599** `uu-gateway-router/connectTimeout` — *"Unable to access service within time limit"* | everything else |

The last probe is ENTSO-E's own gateway reporting it cannot reach its own backend.
Server-side, unrelated to the token or the local setup.

The platform's own dashboard corroborated this from the other side. *Web API Access*
showed the security token **Generated** and the integration channel **ACTIVE**, and
*Integration Channels Monitoring* logged **Last Activity 10:46:30 UTC** with a file count
of 6 — matching the six probes made that morning. So the requests arrived, were
attributed to the account and counted, and only then failed. Both directions agreed the
credentials were fine.

The documented error surface confirmed it too. Every failure ENTSO-E documents — missing
or duplicate parameters, no data found, range over one year, too many documents, bad
characters — returns an `Acknowledgement_MarketDocument` XML carrying a `<Reason><code>`.
Ours returned JSON from `uu-gateway-router`. The request never reached the API
application at all.

(The Zendesk articles are readable through the Help Center JSON API at
`/api/v2/help_center/en-us/articles/{id}.json`, which is not behind the bot wall that
returns 403 to the HTML pages. Worth remembering.)

**Recovered at 11:42:30 UTC**, roughly 70 minutes after first observation, caught by a
10-minute poller. Two useful limits harvested from the documentation meanwhile: a
**one-year maximum range per request**, and a document-count cap — though the two
articles disagree, one saying 100 and the other 200, so it needs pinning down before
chunking is built.

Documentation was also unreachable: `transparencyplatform.zendesk.com` returns 403 to
non-browser clients, so the API contract in use was reconstructed from the `entsoe-py`
source and secondary sources rather than the official sitemap.

#### Fallback routes established and tested

| Route | Status | Notes |
|---|---|---|
| **SMARD chart-data API** | **working** — verified live | No key, no registration. Day-ahead price filter `4169`, 415 weekly buckets, first at `2018-09-30 22:00 UTC` = `2018-10-01 00:00` Berlin, exactly the DE-LU zone start. One week pulled: 168 rows, hourly UTC, 6 negative-price hours, mean 77.95 EUR/MWh. |
| **ENTSO-E File Library** | reachable — `200` | Bulk CSV extracts on `transparency.entsoe.eu`, which is up. Replaced the SFTP server, discontinued end of September 2025. Authoritative and clearly labelled. |
| ENTSO-E REST API | down | The intended route; blocked. |

**Caveat on SMARD, and it is a Contract 1 risk.** The `chart_data` responses carry no
series names — `meta_data` holds only `version` and `created`. The filter IDs are magic
numbers, and the download-centre page is JavaScript-rendered, so the mapping cannot be
scraped. Prices (`4169`) are confirmed by plausible values, but using SMARD for the
day-ahead *forecast* series would mean guessing which ID is a forecast and which is an
actual. Mislabelling one as the other injects silent hindsight — precisely the failure
mode Contract 1 exists to prevent. Forecast series therefore come from the ENTSO-E File
Library or the API, never from an unverified SMARD ID.

#### First authenticated pull — and three findings

Once the API returned, the token verified end to end through `entsoe-py`: 49 rows of
DE-LU day-ahead prices for 1–3 June 2024. Three things surfaced that shape the client:

1. **`entsoe-py` returns a `Europe/Berlin` index, not UTC.** Contract 5's conversion is
   required at the source boundary, exactly as designed — not an optional tidy-up.
2. **The endpoint is inclusive at both ends.** A request for 1 June to 3 June returned
   **49** hours, not 48. The same off-by-one class as the split boundary bug, now known
   about before it can cause a silent duplicate.
3. **The platform is slow while recovering.** A 30-second timeout failed; 120 seconds
   succeeded, and `entsoe-py`'s built-in retry fired twice before the call went through.
   Timeouts must be generous, and the library's `retry_count=3, retry_delay=10` is doing
   real work rather than sitting idle.

#### SMARD validated against ENTSO-E — filter 4169 confirmed

The open risk from the fallback work was that SMARD's filter IDs are undocumented magic
numbers, so using one for a *forecast* series could silently inject hindsight. That risk
is now resolved for prices, by measurement rather than assumption.

Both sources were pulled for the same window and compared hour by hour after converting
each to UTC:

```
overlapping hours compared : 49
max absolute difference    : 0.000000 EUR/MWh
hours differing by > 0.01  : 0
```

Exact agreement on every hour. This establishes three things at once: SMARD filter `4169`
**is** the DE-LU day-ahead price; the timezone handling is correct on both paths, since
independently-converted indices align to the hour; and there is now a reproducible
cross-source check to re-run whenever either feed is touched.

The caveat still stands for every **other** SMARD filter. Forecast series remain
unverified and must not be used until each is validated the same way — against ENTSO-E,
or from the File Library's labelled extracts.

#### Environment and tests

Interpreter moved from **3.11.3 to 3.11.14** — eleven patch releases had accumulated.
3.11 was kept rather than moving to 3.13 after checking that every current and planned
dependency (`pandas`, `pyarrow`, `statsmodels`, `lightgbm`, `evidently`, `pulp`) supports
3.11 through 3.14, so compatibility does not discriminate between the lines. Portability
comes from the project-local `.venv`, the exact pins and `.python-version`, not from the
minor version. All five pinned packages resolved to identical versions on the rebuilt venv.

The second `.gitignore` bug is fixed: `.vscode/*` instead of `.vscode/`, so the promised
`!.vscode/settings.json` negation can finally fire. `settings.json` now pins the
interpreter path and enables pytest, while personal editor state stays ignored.

**15 contract tests** added, scoped to Contracts 2 and 5 rather than general coverage.
They were mutation-tested rather than merely run: reintroducing the `.loc` inclusive
slicing bug failed exactly three of them, with the validation set showing 8761 rows
instead of 8760 — the duplicated boundary hour caught. A test that has never been seen to
fail is not yet evidence of anything.

#### Reading a raw response — two traps that fail silently

One real A44 response was read element by element before any library touched it, and
saved as `tests/fixtures/sample_A44_dayahead_price.xml`. It turned out to contain two
things no amount of planning would have anticipated. Both are invisible failures.

**1. The same hours arrive twice, at two resolutions.** A request for two days returned
**four** `TimeSeries` blocks — each period once at `PT15M` and once at `PT60M`. This is
June 2024, more than a year before quarter-hourly products went live. The only field
separating them is `classificationSequence_AttributeInstanceComponent.position`: `1` is
hourly, `2` is quarter-hourly. Domain, currency, business type, auction type, contract
type and curve type are identical across all four. Select on anything else and a
different series comes back, with no error.

**2. Under `curveType A03`, an absent position is not missing data.** One block held 95
points with a highest position of 96 — position 54 simply absent. A03 means
"variable-sized block": a gap repeats the previous value. Position 53 was `0` and
position 55 was `-16.75`, so the true value at 54 is `0`. Reindexing without a forward
fill would invent a hole, and any later imputation would land near `-16.75` — a
different price, and for a battery a different decision.

`entsoe-py` handles both (`parsers.py`: *"Handle curveType A03: forward fill missing
positions"*). A hand-written parser written for comparison reproduced its values exactly,
which is the clearest argument yet for wrapping the library rather than writing one.

Points carry no timestamp, only a 1-based `position`; the time is reconstructed as
`period_start + (position - 1) x resolution`. Every tag is namespaced under an IEC URN,
so searching for the bare tag name finds nothing.

#### Leakage — scope clarified

A loose phrase during discussion ("tomorrow's weather") caused confusion and was wrong.
No weather data is used anywhere; that decision is unchanged. The actual risk is narrower
and closer to home: ENTSO-E publishes the day-ahead generation **forecast** (`A69`/`A01`)
and the **actual** generation (`A75`/`A16`) in the same units and the same shape,
separated only by request parameters. Pull the wrong one and the split stays clean, the
target is still withheld, nothing errors — and the model has been handed what actually
happened.

Withholding the target and Contract 1 therefore cover different things: the first protects
the label, the second protects the features. Only the two forecast series carry real risk;
prices and calendar features have nothing to confuse them with.

**Proposed:** verify each forecast series empirically once — pull the forecast and the
actual for the same days and confirm they differ the way a forecast differs from reality —
then keep a fast assertion on the request parameters thereafter. Adopted and carried out
on 14 September; see below.

#### Housekeeping

Work log moved from `logfiles/` to `docs/`, and `logfiles/` deleted — it was an empty
leftover, and `.gitignore` already covers `logs/` and `*.log` for stage 5 runtime output.
A work log is documentation, not runtime output, so it belongs in version control. A
table of contents was added, then cut back to one row per day once it began reproducing
the whole document above itself.

The planning artifact was brought up to date: stage 0 marked part-done, the schedule
corrected to show where the slippage went, an internal `2019` / `October 2018` slip fixed,
and the degradation cost and the two XML traps folded in.

A weekly routine (`trig_0113rBvXLa9eZa46byKszxZi`, Tuesdays 09:00 Berlin) probes the API
and drafts an outage email if it fails. Now that the platform is back it is redundant, but
harmless, and useful if the migration causes further instability.

---

<a id="d20260914"></a>
### 14 September 2026 — forecast provenance, the catalog, and a review

#### The platform has fully recovered

An unauthenticated probe returned `401` in **0.16 s**, against 34.8 s or an outright
timeout five days earlier. An authenticated pull completed in **1.90 s** with no retries,
where the same call previously needed a 120-second timeout and two internal retries.

The values came back identical to the 9 September pull — same minimum of −19.58 and
maximum of 109.01 EUR/MWh for the same window. Not proof that ENTSO-E never revises, but
the first datapoint against it, and free.

#### Forecast series verified by measurement, not by trust

Contract 1's hazard is that the API indexes values by the hour they describe and never by
when they were published. Ask for wind on a past day and it answers whether you wanted the
forecast or the outcome — the two differ only by request parameters, and both arrive as
megawatts on the same index. Pull the wrong one and the split stays clean, the target is
still withheld, no test fails, and the model quietly knows what happened.

So each forecast was compared against its own actual over a fortnight in the **training**
period — the test years are not spent on a provenance check that any fortnight answers
equally well.

| Series | Hours | Correlation | MAE | Bias | Verdict |
|---|---|---|---|---|---|
| Load | 1344 | 0.9914 | 936 MW | +195 MW | forecast |
| Solar | 1344 | 0.9967 | 681 MW | −421 MW | forecast |
| Wind Onshore | 1344 | 0.9716 | 769 MW | −128 MW | forecast |
| Wind Offshore | 1344 | 0.9343 | 393 MW | −161 MW | forecast |

All four track reality closely and none equals it, which is what a forecast looks like and
what actuals never look like. Two details corroborate rather than merely pass: the
predictability ordering is physically sensible — solar highest, offshore wind lowest — and
load carries a consistent positive bias while all three renewables carry negative ones,
matching the known tendency of TSO publications to over-forecast demand and under-forecast
renewables.

**The check was then shown to fail when it should.** Feeding actual load in place of the
forecast produced correlation 1.0000, MAE 0, and the LEAK verdict. A check that has never
been seen to fail is not yet evidence of anything.

Kept as `scripts/verify_forecast_series.py`, exiting non-zero on failure so it can gate a
pipeline later. It needs the network and a token, so it stays out of the offline test
suite; the permanent guard there will be an assertion on the catalog's request parameters.

#### The catalog — Contract 1 becomes a field

`src/sources/entsoe.py` holds one record per series: how to fetch it, what comes back, and
whether the model may see it. Adding a sixth series should be an entry here and nothing
else.

The field that carries the contract needed more care than expected. A plain
`feature_eligible` flag broke on the price: day D's price is the **target**, and the
auction publishes it at roughly 12:45 on D-1 — forty-five minutes after gate closure — yet
*lagged* prices are entirely legitimate features. So the field became
`known_before_gate_closure`, meaning precisely: may the value for delivery period t be used
to predict period t? For the price, no. Lags are `features.py`'s business, because the lag
is what makes a value old enough to have been public.

Five records, arranged as pairs: the target, two forecasts, and the two hindsight twins
those forecasts would be confused with. The forbidden series are listed rather than omitted
— a prohibition is only testable if the trap has a record to point at.

#### Review of the three modules, and what it found

Reading the code back rather than admiring it turned up five issues, all fixed:

1. **The verification script named its own query methods**, so the catalog and the thing it
   audits were free to drift apart, each looking correct alone. It now resolves every call
   through `cat.get()`.
2. **`actual_load` had no record**, though the script fetched it. The catalog claimed
   completeness it did not have.
3. **`expected_resolution` was described as "checked"** when nothing checked it. Comment
   corrected rather than the claim quietly left standing.
4. `_DE_AT_LU_EIC` was private yet reached into by a test. Made public — a named hazard is
   easier to check against than a hidden one.
5. `GATE_CLOSURE_LOCAL` was a bare string, now a `datetime.time`, since the lag arithmetic
   will compare against it rather than print it.

**Fixing (2) exposed two wrong assumptions.** A test asserted that document types uniquely
identify a series; load forecast and actual load are both `A65`, and only the process type
separates them. It had passed only because the forbidden twin was missing. And a mutation
pointing `load_forecast` at `query_load` — the actuals — **passed every offline test**,
because `hasattr` asks only whether a method exists. The precise leak Contract 1 exists to
prevent walked through the fast guard untouched.

Both are now tested, and the defence is layered:

| Layer | Cost | Caught the mislabel |
|---|---|---|
| Offline test suite | 0.26 s | `test_no_two_items_share_a_query_method` |
| Live provenance check | ~40 s, network | `corr 1.0000, MAE 0, exact 1344 — LEAK` |

The refactored script returns numbers identical to before — 0.9914 / 936 / +195 on load —
which is the First Law check that a refactor did not quietly become a change.

#### Walkthrough of `config.py` and the catalog

Read line by line rather than summarised. Two things worth recording because they are easy
to get wrong and produce no error when you do.

`DateOffset(days=1)` means *the same clock time tomorrow*; `Timedelta(days=1)` means
*exactly 24 hours later*. On the 25-hour October day the second lands back inside the same
day, silently losing its final hour. `_last_delivery_hour` uses the former.

`df.loc[mask]` and `df.loc[start:end]` are different operations. Only the boolean mask can
express "strictly greater than" — label slicing is inclusive at both ends, which is the
original split bug.

A stale comment was found during the walkthrough itself: the catalog still said "four
items" after `actual_load` was added.

---

<a id="d20260915"></a>
### 15 September 2026 — a command menu, and a deliberate stop

#### `just` replaced the ad-hoc invocation

Three pieces of knowledge lived only in conversation: use `.venv/bin/python`, run scripts
as modules rather than file paths, and be in the repository root. Three of four plausible
invocations failed, each with a `ModuleNotFoundError` rather than a hint.

A Makefile was written first and then replaced within the hour. `just` searches parent
directories and runs recipes from the directory holding the file, so a command works from
anywhere in the project — which is the one fragility make could not fix and which had been
papered over with editor tasks. `--list` is also built in, where make needed a grep-and-awk
incantation for the same menu.

The objection to `just` had been that a clean clone must install it. That was weaker than
it looked: the clone already creates a venv and installs pinned dependencies, so this is
one more documented line rather than a new kind of burden. It belongs in the README now
and in the Dockerfile from stage 5 — not in `requirements.txt`, which is for Python
imports. (The `just` package on PyPI is an unrelated file-reading library; installing it
would be a genuine trap.)

#### Stopped adding, after being told to

A proposal to send `process_type` explicitly rather than rely on `entsoe-py`'s default was
dropped. The risk it defended against — a library default changing on an upgrade, for a
method this project never calls — had not been observed. The Second Law already forbade
it; what was missing was the instinct to stop and ask instead of reasoning onward.

A new standing protocol, **Align Before Building**, now says so explicitly: a hypothetical
justifies a note here, not a module. And when the line count grows faster than the results,
say so. At this point the count was 664 lines of Python, 40 tests, and **zero rows of
market data**.

#### Eight decisions, settled so they are not re-litigated

| Question | Decision |
|---|---|
| Learning or portfolio, when they conflict | **Both, sequenced.** Learning drives stages 1–3; portfolio polish is one pass at the end |
| How much testing | **Contracts, plus a regression test for every real bug.** Nothing for code that fails loudly |
| SMARD, now the API works | **Cross-check only.** No source module; keep the comparison for re-validating prices |
| What the first pull fetches | **Everything in the catalog, full history**, 2018-10 to 2025-12 |
| Actual generation, which stage 1 does not need | **Include it.** One pass over the API is cheaper than two |
| The empty `notebooks/` directory | **Exploration only, never a source of truth.** Anything producing a reported number moves to `src/` or `scripts/` |
| What finishes stage 0 | Pull runs twice identically · coverage counted · negative-price hours and daily spread in the README · first figures · a written data-quality note |
| The 16 October end date | **Provisional.** Re-plan after stage 1, which is the first stage with a real deliverable and therefore the first honest measure of pace |

Note on the pull scope: all five catalog items are cached, not four. `actual_load` and
`actual_generation` are symmetric — both forbidden twins kept for the same reason — and
"everything in the catalog" is a rule that needs no exception to explain.

---

### Commits

| SHA | Date | Summary |
|---|---|---|
| `c9ba760` | 08 Sep | Create CLAUDE.md to provide project context & engineering laws *(amended from `dc43e9a`)* |
| `5b5dcda` | 08 Sep | Fix data/ ignore rule so the directory skeleton survives a clone |
| `7beaa76` | 08 Sep | Pin stage 0 dependencies and document the required API token |
| `e7c23c3` | 08 Sep | Add config.py as the single source of truth for split and market |
| `5dec185` | 09 Sep | Set battery cycle degradation cost to 8 EUR per MWh discharged |
| `d73e0ef` | 09 Sep | Add a work log recording decisions and their reasoning |
| `4dac141` | 09 Sep | Add a table of contents to the work log |
| `b7302d7` | 09 Sep | Pin the interpreter and share the editor's environment setting |
| `bdb5923` | 09 Sep | Add contract tests for the split and market constants |
| `9800277` | 09 Sep | Record the API recovery and the SMARD cross-validation |
| `3eee18b` | 09 Sep | Reduce the work log contents to one row per day |
| `f736ad2` | 09 Sep | Record a real A44 response as a parser fixture |
| `9c8666e` | 09 Sep | Record the raw response findings and clarify the leakage scope |
| `27044a4` | 14 Sep | Verify the forecast series are forecasts and not actuals |
| `92d6997` | 14 Sep | Report resolution and coincidence count in the provenance check |
| `97db7ae` | 14 Sep | Add the ENTSO-E data-item catalog and its contract tests |
| `03e4503` | 14 Sep | Name the wrong-market EIC publicly and type gate closure as a time |
| `dec837e` | 14 Sep | Make the catalog load-bearing rather than merely descriptive |
| `7fc4858` | 14 Sep | Correct the catalog's item count and name the pairing |
| `40f64f1` | 14 Sep | Record the catalog, the review findings, and two wrong test assumptions |
| `37cdfd6` | 15 Sep | Add a Makefile and editor tasks as the project's command menu |
| `8473e76` | 15 Sep | Replace the Makefile with a justfile |
| `3902e02` | 15 Sep | Add a standing protocol to align before building |

---

### Open items

1. **SMARD filter IDs beyond `4169` remain unverified.** Prices are confirmed against
   ENTSO-E to the cent; every other filter is still an undocumented magic number and must
   not be used for a forecast series until validated the same way.
2. **Document-count cap unknown.** ENTSO-E's own articles disagree — one says 100 matching
   documents, the other 200. Needs pinning down before request chunking is built.
3. **Coverage uncounted** (HANDOVER open question 1): gaps in DE-LU 2018–2025 unknown,
   because no bulk data has been pulled yet.
4. **Revision behaviour untested** (HANDOVER open question 2): whether ENTSO-E overwrites
   published day-ahead values. The immutable cache answers this by construction once two
   pulls of the same period exist.
5. **Platform stability** — resolved as of 14 September: sub-second responses, no retries.
   Keep generous timeouts and SMARD as a fallback anyway; the outage cost half a day once.
6. **The 23/25-hour delivery day** contradicts CLAUDE.md's "24 values per run". Storing in
   UTC keeps joins safe but does not settle it. Needs an explicit rule at stage 2, when the
   model layout is chosen.
7. **`expected_resolution` is declared but unchecked.** The normaliser should compare it
   against what actually arrives; until it does, the October 2025 style of surprise would
   pass unnoticed.
8. **Half of `config.py` is not yet used** — the path constants, `RESOLUTION`,
   `QUARTER_HOUR_GOLIVE` and `GATE_CLOSURE_LOCAL` are waiting for the pull and the
   normaliser. Declared early on purpose, but they are promises until something reads them.

### Next

Stage 0 has roughly two and a half hours left. In order:

1. **`main()` in `verify_forecast_series.py`** — the last unread 45 lines, and the three
   patterns the pull will reuse: loading the token, resolving through the catalog, and
   returning an exit code.
2. **A file map** — what exists and what depends on what, drawn before adding to it.
3. **Fetch and cache** — immutable timestamped pulls plus `manifest.jsonl`, which also
   supplies the incremental retrieval an MLOps loop needs, and answers open item 6 by
   letting two pulls be diffed.
3. **Normalisation** — the single Contract 5 choke point: UTC, hourly, the two-resolution
   selection, `curveType A03`, and gap counting.
4. **First figures** — negative-price hours per year, average daily spread, residual load
   against price. This closes the stage 0 checkpoint.

The `src/sources/` split has already earned itself: for most of 9 September SMARD worked
and the API did not, and the layer above will neither know nor care which supplied the
bytes.
