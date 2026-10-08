# Work log — Battery Storage Backtest

Running record of what was done, what was decided, and what was found. Newest session
last. Written for a reader who was not present: what changed, and why it changed.

**Where to look for what.** Decisions belong here, with their reasoning. `CLAUDE.md` holds
the standing rules and the technical spec. The README's **Where this is going** is the
canonical plan — the six stages, what each delivers, and roughly when. The `Next` section at
the foot of this file is the state of play, rewritten each evening, and is the right place to
start a session.

**The plan page.** The current one is <https://claude.ai/artifact/Mysse8XGB4exGFykeDcmYm>. It mirrors
the README's **Where this is going**; the README is canonical and the page is the shareable form, so
the page is refreshed at every milestone (CLAUDE.md, *Refresh the Plan at Every Milestone*, since
7 October), not only when a stage closes. A plain page cannot be revised in place, which is exactly
how the last one drifted. A collaborative version was tried first and abandoned: the
viewer it needs will not run in this machine's Safari, so an editable document was no use at all. The
version that stood until 2 October is archived unchanged at
<https://claude.ai/code/artifact/9f662615-dd72-4326-8695-6ab1f2151b59>: a dated snapshot from
18 September, kept because it records what the plan looked like before stage 1 revised it, and
explicitly not maintained.

`HANDOVER.md` was dissolved on 2 October. Written on 8 September before the first commit, it
had never been updated, so the half of it that claimed to hold the state of play had been
wrong for three weeks while the other half was still worth keeping. Its working method moved
to `CLAUDE.md` as **Teach While Building**, its framing on when accuracy pays to the README,
and its two surviving open questions to item 11 below. Entries before this date refer to it as
a live file, which it was. An earlier version of this header also pointed at a private page as
the home of the stage plan; that page predates stage 1 and the README supersedes it.

## Contents

One row per working day. Follow the date link for the detail.

| Date | What was done |
|---|---|
| [8 Sep 2026](#d20260908) | Repository initialised. Environment rebuilt off the pyenv global into a project venv. Two `.gitignore` bugs found. Split boundary bug demonstrated and fixed in `config.py`. |
| [9 Sep 2026](#d20260909) | Cycle cost set to 8 EUR/MWh. ENTSO-E API outage diagnosed, then recovered. First authenticated pull. SMARD cross-validated to the cent. Raw XML read — two silent traps found. Python 3.11.14, editor settings, 15 contract tests. |
| [14 Sep 2026](#d20260914) | Platform recovered, sub-second. All four forecast series verified against their actuals by measurement. Catalog written — Contract 1 becomes a testable field. Code review found five issues, two of them wrong assumptions in the tests themselves. |
| [15 Sep 2026](#d20260915) | `just` replaced ad-hoc invocation. A proposal built on a hypothetical was dropped, and a protocol added to stop and ask instead. Eight open questions settled, including what finishes stage 0. |
| [16 Sep 2026](#d20260916) | Daily recap ritual and plain-language protocol added. `main()` read, empty package marker dropped, repository map written. `src/data.py` and `just pull` built: the first real market data on disk. |
| [17 Sep 2026](#d20260917) | SMARD ruled out as a gap filler by measurement. A silent data loss in `entsoe-py` found, traced, fixed — seven price hours recovered. Four mutants survived a green suite; two were dead code. Data-quality note written. Stage 0 closed. |
| [18 Sep 2026](#d20260918) | Residual load measured: mean down 16 %, peak down 2 %. Market analysis — ancillary services are saturating and pushing value onto wholesale, which makes forecast quality the whole competitive surface. Figures read: the slope tripled, a negative-price claim was wrong, and stage 3 rescoped to which hours rather than whether to act. |
| [21 Sep 2026](#d20260921) | Recap interview: two answers wrong, one produced a repo correction. Stage plan given an address in the README. Training window decided by measurement. `features.py` built — Contract 1 enforced rather than declared, 9/9 mutants caught. |
| [22 Sep 2026](#d20260922) | Recap: an answer overturned how the slope finding was framed, in six places. EDA page retitled around its actual result. `notebooks/`, `data/interim/` and `data/processed/` removed unused. Map and README rewritten around the gate. |
| [23 Sep 2026](#d20260923) | Stage 1 scaffolded and half-built: `evaluate.py` written by hand, benchmark in place. Modelling approach aligned — two models not six, MLflow deferred with a stated trigger. Setup ungated from homebrew. |
| [28 Sep 2026](#d20260928) | **The first rMAE: 0.488.** A scoping question found an annual data hole in test data. `models.py` and `train.py` finished. Two mutants exposed real gaps, and the second showed the test fixture was rigged so the benchmark could not be beaten. Leak calibrated on purpose. |
| [29 Sep 2026](#d20260929) | Recap found a claim of mine that did not survive checking: January is the model’s *best* month once normalised, not its worst. Sources cited in the README. Open item 9 closed by measurement rather than by fetching. `final_score.py` built, mutated both ways — and deliberately not run. |
| [30 Sep 2026](#d20260930) | **Stage 1 closed: rMAE 0.532 on the held-back years.** The ranking reversed — the tree won on validation and lost on 2024-25. Two tests found unable to fire. Stage 2 reordered around recalibration; CatBoost and Random Forest parked for stage 4. Split rationale finally written down. |
| [2 Oct 2026](#d20261002) | Housekeeping: `HANDOVER.md` dissolved, plan page replaced, scores moved under `reports/`. Short recap, two answers reversed. **Open item 6 closed:** every day becomes 24 slots, the field's convention, chosen over keeping real hours. Decided, not built. |
| [5 Oct 2026](#d20261005) | Recap: three partial, one forgotten, one reversed for the second time. MLflow adopted for stage 2 on a question the deferral never weighed. The grid's labels checked in the field's code and paper. **`to_slots()` built and mutated.** Split rewritten to sort by Berlin date; position tests added after finding the old ones could not see the cut. Wiring half done, uncommitted. |
| [6 Oct 2026](#d20261006) | Recap: two partial, three wrong, refitting missed for the third session running. **The grid wired in:** split by Berlin date, features on 24 slots, 1 April leak case caught a planted bug. 2023 re-scored, and the tree's 0.005 move traced to instability, not the grid. Significance test moved ahead of recalibration. MLflow begun: forecasts now survive the run. |
| [7 Oct 2026](#d20261007) | Recap: the refitting lesson right, which model won wrong for the fourth time. **MLflow finished** and moved to `reports/mlflow/`; the full path inside it cannot be hidden, only kept out of git. **Diebold-Mariano built**, with the field's daily test plus a correction for the 0.25 day-to-day echo. **Recalibration built and measured:** daily wins for the line, while the tree's monthly → daily gain cannot be told from noise. Daily made the stage 2 schedule. LEAR introduced, not built. |
| [8 Oct 2026](#d20261008) | Recap: two half right, one forgotten; the refitting numbers swapped between models for the fifth time. |

[Commits](#commits) · [Open items](#open-items) · [Next](#next)

*Anchors are explicit `<a id="dYYYYMMDD">` tags on each day heading, so the links keep
working when a heading is reworded.*

---

## Stage 0 — Data · from 8 September 2026

**Stage goal:** a reproducible data pull with the split locked.
**Checkpoint:** runs twice identically; coverage counted.
**Status — COMPLETE, 17 September 2026.** All five criteria met:

| | |
|---|---|
| Pull runs twice identically | five series `unchanged`, identical fingerprints, nothing archived |
| Coverage counted | 63,578 hours; every gap located, explained and decided |
| Negative hours and daily spread in the README | 27 → 576 hours a year; spread ×4 |
| First figures | three, regenerated by `just explore` |
| Written data-quality note | `docs/data-quality.md` |

34 MB on disk, 2018-10-01 to 2025-12-31, five series. 81 tests.

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
| The empty `notebooks/` directory | **Exploration only, never a source of truth.** Anything producing a reported number moves to `src/` or `scripts/` |  *(Reversed 22 September: never used, and superseded — exploration goes through `just explore` and is presented as a page. Directory and its `.gitignore` rules removed.)*
| What finishes stage 0 | Pull runs twice identically · coverage counted · negative-price hours and daily spread in the README · first figures · a written data-quality note |
| The 16 October end date | **Provisional.** Re-plan after stage 1, which is the first stage with a real deliverable and therefore the first honest measure of pace |

Note on the pull scope: all five catalog items are cached, not four. `actual_load` and
`actual_generation` are symmetric — both forbidden twins kept for the same reason — and
"everything in the catalog" is a rule that needs no exception to explain.

---

<a id="d20260916"></a>
### 16 September 2026 — a recap ritual, a map, and the first real data

**A daily recap, and a language rule.** The session opened with an interview on everything
built so far: eight questions across market knowledge, the code, and how the work is done.
Three answers needed rebuilding, and the most important was capture rate — it had been
understood as a comparison of predicted price to actual price. It is a comparison of
*money to money*: revenue from the schedule the forecast chose, over revenue from the
schedule perfect foresight would have chosen, both settled at real prices.

That led somewhere useful. A worked example: a forecast wrong by 40 EUR/MWh on every hour
captures 100 % of the available revenue, while one accurate to 7.7 EUR/MWh captures 86 %.
A constant error shifts every hour equally and changes no comparison; only errors that
*reorder* hours cost money. Which is the whole argument for capture rate as the headline
number, and the reason a model that hedges toward the mean is dangerous here in a way MAE
will never show.

A new standing protocol followed — learnings are written in plain language, technical
terms in brackets rather than doing the explaining — plus `docs/learnings.md`, local and
uncommitted, as the record of what was understood rather than what was done.

**The map came before more code.** Explanation had been running bottom-up: lines before
architecture. `docs/architecture.md` now states the shape — `src/` is the machine,
`scripts/` are the buttons; each file answers exactly one question; downloading and
splitting are different jobs. The README's file list had named seven modules, five of
which had never been written, so it now separates BUILT from PLANNED.

`scripts/__init__.py` was deleted. Removing it and running everything proved it did no
work, and it had claimed `scripts/` was a library when it is the opposite. A stale comment
in the verification script — justifying a late import by a `--help` flag the script does
not have — was corrected in the same session.

**Storage was evaluated before it was designed.** The first estimate assumed weekly pulls
and produced 1.6 GB a year, which was answering the wrong question: this is a backtest, not
a production system, and the realistic figure is about twenty pulls over the project's
whole life. Correcting that inverted the argument for keeping old copies. Rare pulls make a
silent overwrite *worse*, not better — months of published results rest on each one.

The evaluation also exposed the design flaw worth keeping: **appending is not overwriting**.
A pull reaching further forward in time adds rows and rewrites nothing. Without that
distinction every pull would archive a full copy for no reason.

**`src/data.py` and `just pull` built.** Four save outcomes — `created`, `unchanged`,
`extended`, `revised` — with only the last displacing anything. Fetching moved out of the
verification script so one definition serves both commands. 25 new tests, 65 in total, and
five deliberate mutations to check they would actually fail: silent overwrite, `sum` for
`mean`, skipped timezone conversion, NaN mishandled, vanished rows ignored. All five caught.

**The first pull: 21 minutes, 34 MB, five series, 2018-10-01 to 2025-12-31.**

| Series | Raw rows | Arrives | Hourly | Missing hours |
|---|---|---|---|---|
| `day_ahead_price` | 70,198 | 60min → 15min | 63,578 | 7 |
| `load_forecast` | 250,740 | 15min | 63,575 | **890** |
| `wind_solar_forecast` | 254,308 | 15min | 63,577 | 0 |
| `actual_load` | 254,292 | 15min | 63,576 | 3 |
| `actual_generation` | 254,308 | 15min | — | — |

Two findings. **The October 2025 resolution change needed no code of its own** — the price
series carries 6,620 more raw rows than hours, which is Q4 2025 arriving as quarter-hour
products, and resampling rather than reshaping absorbed it. That closes a Danger Zone by
measurement instead of assertion.

And **`load_forecast` is missing 890 hours**, 1.4 % of the record, while also starting two
hours late — 02:00 Berlin on 1 October 2018 rather than midnight.

Where those hours fall settles what to do about them:

| Year | Missing hours | | |
|---|---|---|---|
| **2018** | **840** | 25 separate gaps | median length **24 h**, longest 96 h |
| 2022 | 48 | | |
| 2023 | 1 | | |
| 2024 | 1 | | |

Only two isolated single hours in seven years. This is not 890 scattered holes needing
careful imputation — it is roughly **37 whole delivery days**, almost all in the market's
opening quarter, when TSO publication was evidently still settling down.

That makes dropping them the honest option rather than the lazy one. A day with no
published load forecast is a day this project genuinely could not have made a decision on;
inventing one would be putting a forecast into the record that nobody ever issued. The
decision itself — and in particular whether the two isolated hours inside the validation
and test years get the same treatment as the 2018 days — is for 17 September.

**Checkpoint passed.** A second `just pull`, 24 minutes, exit 0:

```
  day_ahead_price       unchanged  70,198 rows
  load_forecast         unchanged  250,740 rows
  wind_solar_forecast   unchanged  254,308 rows
  actual_load           unchanged  254,292 rows
  actual_generation     unchanged  254,308 rows
```

All five fingerprints in the manifest match their first-pull values exactly, and no archive
directory was created — nothing was displaced because nothing had changed. That is the
Third Law demonstrated rather than asserted, and it also gives the first data point on
open item 4: over one day, ENTSO-E revised nothing in DE-LU 2018–2025. One observation is
not a revision rate, but the mechanism to accumulate one now exists.

---

<a id="d20260917"></a>
### 17 September 2026 — a silent data loss, found by counting

**The question that started it.** Could the 37 missing load-forecast days be filled from
SMARD? Answering it honestly meant checking rather than reasoning, and the check said no.

SMARD carries actual consumption, residual load and forecast *generation* — but no
consumption forecast at all. Twenty filters were correlated against ENTSO-E's load forecast
over a known-good week. The closest, filter 410, scored 0.9932 correlation and **1,090 MW**
mean error — almost exactly the forecast error measured on 14 September, which identifies it
as *actual* load, the thing the forecast is trying to predict.

Asking ENTSO-E directly for 2–6 October 2018 returned **8 rows out of 384**, while
`actual_load` for the identical window returned all 384. The grid operators were publishing
what happened and not what they had expected. The data is absent at source.

There is also a Contract 1 argument that would apply even if a value existed somewhere: it
would have to be shown public before noon on the previous day, and platforms show what they
hold now rather than what they showed then. The same trap the project already avoids with
weather data.

**Then the coverage count paid for itself.** The price series was missing one hour on
29 September of every year from 2019 to 2025 — same date, same hour, seven years running.
The auction has cleared every hour since the market opened, so that was never market
behaviour.

It was our own pull. Traced to `entsoe-py`:

> `year_limited` splits any request longer than a year into blocks, then strips each block's
> first timestamp to avoid duplicating the previous block's last. ENTSO-E returns half-open
> windows, so the previous block never held it — and the strip deletes the only copy.

Demonstrated block by block: block 1 ends at 21:00 and lacks the hour; block 2 begins at
22:00 and has it, then has it masked away by `index > _start`. The predicted boundaries —
`(start − 1 day) + N years`, because the price query pads by a day first — match the seven
losses exactly. Only the price series is affected; the four 15-minute series keep all four
periods at every boundary.

**Repaired generally rather than specifically.** Every series is now checked against its own
spacing after fetching and anything missing is re-fetched. Working from the data rather than
from the library's block arithmetic means the fix is not tied to the defect that prompted
it — and a window that recovers nothing is itself evidence, separating *we failed to fetch*
from *never published*.

Re-run: `day_ahead_price extended +7 rows, 7 recovered`, everything else `unchanged`. The
price series now has **zero** missing hours, and the 25 load-forecast windows recovered
nothing, confirming those days are genuinely absent.

**Mutation testing, and a lesson about it.** 74 tests green, then four deliberate bugs
injected. **All four survived.**

| Mutant | Why it lived |
|---|---|
| Let a gap redefine what is normal | a real missing test — no case had two gaps in a row |
| Backfill overwrites existing values | dead code — an earlier filter already prevented it |
| Backfill keeps duplicates | dead code — same reason |
| Global average step instead of local | equivalent mutant for a regularly-spaced series |

So: the consecutive-gap test was added, the dead deduplication line **deleted**, and the
mutation re-run against the line that actually guards the property. Three of three caught,
75 tests.

The same lesson as the empty `__init__.py` in a different costume — a line that can never
fire is a line nobody can check, which is how it gets trusted without being true. Writing a
test is not the same as having one.

**A design flaw caught by its own test.** The first gap detector compared each step to the
series average. With 61,000 hourly rows and 8,800 quarter-hourly ones, that average
describes neither half, and every hour of one of them looks like a gap. Comparing against
the *preceding* step instead handles a resolution change correctly. The test that failed was
the one written for the October 2025 switch.

**A question that reversed a conclusion.** Asked whether the missing data could be pulled
straight from the API rather than through the library — since the library was the problem
once already. It could not: ENTSO-E's REST endpoint answers *"No matching data found for
Data item DAY_AHEAD_TOTAL_LOAD_FORECAST_R3"* while returning 384 points of actual load for
the same window. The absence is real.

But the same question pointed at Energy-Charts, and **Energy-Charts has the days**. Two
tests before believing it:

- `de` + `lu` reproduces ENTSO-E's DE-LU load forecast to **0.025 MW** mean error. Using
  `de` alone leaves a flat 549 MW shortfall, which is Luxembourg — a reminder that a 0.9999
  correlation says nothing about a constant offset.
- The gap-day values score 0.974 against what actually happened, with 781 MW error and
  **zero exact matches**. A reconstruction from actuals would match everywhere. This does
  not, so it is a real forecast.

**Deferred rather than decided.** The days stay dropped for stage 1, and the question is
revisited once there is a measured rMAE rather than an argument. Open item 9 holds the
trigger; `docs/data-quality.md` holds the evidence and the API recipe, so acting later costs
an hour rather than a fresh investigation.

**A finding for stage 2.** The load forecast's bias is not stable: −2,748 MW in March 2019,
under-forecasting every hour, against +195 MW in June 2022. A model trained across that
boundary sees two different relationships sharing one column name.

**`docs/data-quality.md` written** — coverage per series, every gap located, four independent
checks on the absent days, the Energy-Charts evidence, and the decisions. That is the fourth
of stage 0's five criteria.

**Stage 0 closed.** `just explore` produces both headline numbers and the three README
figures from the cache, so every figure quoted anywhere regenerates with one command.

A prediction was written down before the data was plotted — *negative hours rising, spreads
widening* — and both were right:

| | 2019 | 2022 | 2025 |
|---|---|---|---|
| Hours below zero | 211 | **69** | **576** |
| Mean daily spread, EUR/MWh | 30.1 | **187.0** | 124.1 |

Negative hours have risen roughly twentyfold since the zone opened; by 2025 one hour in
fifteen cleared below zero, and one hour in 2023 reached the −500 EUR/MWh floor. The average
daily spread has roughly quadrupled. Since a battery is paid for the spread and nothing
else, that is the headline: **the opportunity this project measures is several times larger
than it was in 2019.**

Both trends break during 2021–22. Gas set the price in nearly every hour, so surplus power
became rare and negative hours collapsed while the spread reached its record. That
interruption sits in the middle of the training period.

**The finding that matters most for stage 1.** Residual load explains the price at 0.58 to
0.91 within any single year, but only **0.44** pooled across all of them. A pooled
correlation lower than every year inside it is the signature of several relationships
stacked on one another — the same residual load cleared near 40 EUR/MWh in 2019 and above
300 in 2022. The weakest years are 2021 (0.58) and 2022 (0.62) — years in which something
other than residual load was doing most of the work.

**What that something was, this dataset cannot say.** It holds prices, demand and renewable
output, and no fuel or carbon prices at all. The obvious candidate is plausible and untested,
and writing it down as a finding would be importing an explanation rather than measuring one.
Whether to collect the data that would test it is an open scope question, held until the
model shows whether it needs it.

So the training window holds at least two regimes, and the test years resemble neither
exactly. No strategy for this yet, on purpose: stage 1 fits everything with no special
handling, because without that baseline nothing else is measurable. The candidates for stage
2 were already in the plan — a rolling calibration window, and decomposing price into daily
level plus within-day shape. The second is the interesting one, since the regime shift is
largely a *level* shift and the battery needs the *shape*.

**A demo page** was published from the same figures, for an audience who will not run code.
It is a presentation of `just explore` output, never a source of a number.

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
| `0eda6ff` | 15 Sep | Record eight settled decisions and the stop that prompted them |
| `05cafc8` | 15 Sep | Restate stage 0's finish line and the order of what remains |
| `45a7500` | 16 Sep | Record what is understood, not only what is done |
| `56fa937` | 16 Sep | Drop the empty package marker from scripts/ |
| `1e1ed38` | 16 Sep | Correct a comment that described a flag the script lacks |
| `7486057` | 16 Sep | Add a map of the repository for first-time readers |
| `999af24` | 16 Sep | Fetch and cache the catalog without ever overwriting a pull |
| `c372072` | 16 Sep | Report each series as it lands rather than all at the end |
| `cbc4992` | 16 Sep | Record the first pull, and what the data turned out to contain |
| `dcbf3d9` | 16 Sep | Locate the load-forecast gaps, which narrows the decision |
| `cd811ec` | 16 Sep | Record the reproducibility checkpoint passing |
| `92ee29b` | 17 Sep | Recover the values the chunked request silently drops |
| `8aece32` | 17 Sep | Record what the seven years of data actually contain |
| `9148a66` | 17 Sep | Note the blind spot in the gap check |
| `7552599` | 17 Sep | Check the ends of a series, not only the middle |
| `68b6f03` | 17 Sep | Record that the dropped days are recoverable, and defer the choice |
| `d4dbb2b` | 17 Sep | Report what seven years of prices actually did |
| `d612f98` | 17 Sep | Close stage 0 |
| `486db52` | 18 Sep | Record where the value goes as storage capacity grows |
| `76c9c5c` | 18 Sep | Report what the data shows, not what it suggests |
| `8b4f583` | 18 Sep | Make checkability the tiebreaker when a choice is open |
| `48d2cce` | 18 Sep | Make plain language the default for explaining, not only for writing |
| `e83a5c3` | 18 Sep | Draw the per-year fit, and count what negative prices actually are |
| `20f2dfa` | 18 Sep | Count the days a battery should have stayed idle |
| `165ff65` | 18 Sep | Record what reading the figures changed |

---

### Open items

1. **SMARD filter IDs beyond `4169` remain unverified.** Prices are confirmed against
   ENTSO-E to the cent; every other filter is still an undocumented magic number and must
   not be used for a forecast series until validated the same way.
2. **Document-count cap unknown.** ENTSO-E's own articles disagree — one says 100 matching
   documents, the other 200. Needs pinning down before request chunking is built.
3. **Coverage counted — 16 September** (HANDOVER open question 1). Price, wind/solar and
   actual load are near-complete: 0, 0 and 3 missing hours across seven years after the
   backfill. **The load forecast is missing 890 hours**, but 840 fall in 2018 and they
   arrive as whole days — roughly 37 delivery days from the market's opening quarter.
   Dropped for now; see item 9, which is the decision to come back to.
9. **CLOSED 29 September — the 37 dropped load-forecast days.** *(opened 17 September)*

   **Resolved by measurement rather than by fetching anything.** The trigger was a measured
   rMAE, and with one available the question became answerable directly: does early training
   data affect the score at all? Same model, different start dates, scored on 2023:

   | Train from | Rows | linear | gbm |
   |---|---|---|---|
   | 2018 | 36,335 | 0.532 | **0.488** |
   | 2019 | 35,016 | 0.535 | **0.488** |
   | 2020 | 26,256 | 0.574 | 0.490 |
   | 2021 | 17,472 | 0.750 | 0.507 |
   | 2022 | 8,712 | 0.977 | 0.615 |

   Dropping **all** of 2018 — 1,319 hours — moves the tree not at all and the linear fit by
   0.003. The 37 missing days would add roughly 888 hours to a year contributing 3.6 % of
   training and nothing measurable to the result. **A second source is not justified.**
   `src/sources/energy_charts.py` is not written, and the validated recipe stays in
   `docs/data-quality.md` in case a later stage changes the arithmetic.

   Worth noting what the same table says about something else: more data helps steeply, and
   **two years alone (2021–22) is clearly worse than five.** Those are the crisis years, so it
   is the worst possible pair for a calm 2023. It confirms the 21 September finding on the
   target metric rather than on a slope, and it says "just use recent data" is wrong here. It
   does *not* settle the rolling window, whose benefit comes from the window moving forward
   into the year being forecast — which a fixed window ending in December 2022 cannot show.

   The original entry follows, unchanged.

   ---

   **REVISIT AFTER STAGE 1 — the 37 dropped load-forecast days.** *(opened 17 September)*

   The days are missing from ENTSO-E but **available from Energy-Charts**, and that source
   has been validated rather than merely noticed:

   - `de` + `lu` reproduces ENTSO-E's DE-LU load forecast to **0.025 MW** mean error, worst
     deviation 0.1 MW, over two separate control weeks. It is the same data item.
   - The gap-day values pass the Contract 1 provenance test: compared against what actually
     happened they score 0.974 correlation, 781 MW error and **zero exact matches**. A
     reconstruction from actuals would match at every point. This does not.

   So the choice is genuine, and it is deliberately not being made yet. Dropping costs about
   2.5 % of training days from the least representative quarter of the record; adding a
   second source costs `src/sources/energy_charts.py`, its caching and its tests, and
   CLAUDE.md warns specifically against adding sources without a requirement.

   **Trigger for revisiting:** stage 1 errors concentrated in early data, or a training set
   that proves too short. **Decide with a measured rMAE rather than in advance.**

   The full evidence and the exact API recipe are in `docs/data-quality.md`, so acting on
   this later is an hour's work and not a fresh investigation. Recorded at this length on
   purpose: dropping data while knowing exactly how to get it back is a decision, and
   dropping it without knowing is an oversight. This is meant to stay the former.
4. **Revision behaviour** (HANDOVER open question 2): whether ENTSO-E overwrites published
   day-ahead values. The comparison in `src/data.py` now answers it by construction — a
   second pull reports `unchanged`, `extended` or `revised` per series. One data point so
   far is not a revision rate; that accumulates in `data/raw/manifest.csv`.
5. **Platform stability** — resolved as of 14 September: sub-second responses, no retries.
   Keep generous timeouts and SMARD as a fallback anyway; the outage cost half a day once.
6. **CLOSED 2 October — the 23/25-hour delivery day.** *(opened 17 September)*

   **Decided, not yet built:** every delivery day becomes 24 slots, once, at the point where
   `src/data.py` hands data out. The missing spring hour is the mean of its two neighbours, and the
   doubled autumn hour is the mean of its two values. This is the field's convention (Weron;
   Lago et al. 2021). The UTC cache stays as pulled. Only stage 4's settlement puts forecasts
   back onto real hours. Alternatives and reasoning are under [2 October](#d20261002).

   **5 October:** built as `to_slots()` in `src/data.py`. It is applied in `features.py` after the
   loader rather than at the point `data.py` hands data out, so that test fixtures and the leak
   test pass through it. Labels are naive Berlin wall clock, the field's form. See
   [5 October](#d20261005).

   The original entry follows, unchanged.

   ---

   **The 23/25-hour delivery day** contradicts CLAUDE.md's "24 values per run". Storing in
   UTC keeps joins safe but does not settle it. Needs an explicit rule at stage 2, when the
   model layout is chosen.
7. **`expected_resolution` is declared but still unchecked.** `src/data.py` now *measures*
   what arrives and records it in the manifest, but nothing compares that against the
   catalog's claim. The measurement is the harder half; the comparison is a few lines, and
   worth adding the next time the catalog gains an entry.
8. **`QUARTER_HOUR_GOLIVE` turned out to be unnecessary**, which is worth noticing.
   Resampling rather than reshaping meant the switch needed no date at all — a series that
   changes resolution halfway through comes out hourly without being told when. The
   constant stays as a named hazard, like `DE_AT_LU_EIC`, but it is documentation now
   rather than a promise. `GATE_CLOSURE_LOCAL`, `INTERIM` and `PROCESSED` are still
   waiting for `features.py`.
11. **Two feature families left out of v1, both stage 2 experiments.** *(moved here
    30 September from `HANDOVER.md`, written 8 September, which held the only record of them)*

    **Weather.** Deliberately absent, and not for lack of availability. The ENTSO-E
    day-ahead wind and solar *generation* forecast already carries the weather forecast —
    converted onto the real installed fleet, by the people who own the fleet — and it is
    what the market actually saw before gate closure. Raw weather would be a worse version
    of a signal already in the frame. If it is ever added, the open-meteo Previous Runs API
    is the correct endpoint; the Historical Forecast API is a danger zone, because it
    stitches the first hours of successive model runs and so approximates what happened
    rather than what was forecast.

    **Fuel and carbon prices.** Also absent. The price lags already in the frame carry the
    fuel signal indirectly: a gas price move shows up in yesterday's clearing price,
    because gas usually sets the margin. Whether real TTF and EUA series beat that proxy is
    a measurable question and an hour's work.

    **Trigger:** stage 2, after recalibration and the per-hour layout have been measured.
    Both are additive feature experiments, so they belong after the structural levers rather
    than tangled up with them.

10. **REVISIT AFTER STAGE 1 — one forecast hour lost on every autumn clock-change day.**
    *(opened 28 September)*

    Found by asking where the incomplete feature rows actually sit, rather than assuming
    they were all warm-up. Of 939 dropped rows, 936 are in training. The other three are one
    row per year, and they are not scattered:

    | Dropped row (UTC) | Local | Split |
    |---|---|---|
    | 2023-10-28 22:00 | 2023-10-29 00:00 CEST | valid |
    | 2024-10-26 22:00 | 2024-10-27 00:00 CEST | test |
    | 2025-10-25 22:00 | 2025-10-26 00:00 CEST | test |

    Every one is local midnight on the autumn clock-change day. The raw file jumps from
    21:45 straight to 23:00 — the whole hour, quarter-hours included. The day-ahead price
    has all 25 hours; only the forecast series are short.

    **It is not a timezone bug on our side.** The 25-hour index is correct and the repeated
    02:00 is present twice. Data arrives tz-aware from the client, so nothing here localizes
    or resolves ambiguity. The hour is absent from the publication.

    The pattern matches the trap CLAUDE.md already names: under `curveType A03` an absent
    position means *"same as the row above"*, not *"no data"*. There is no A03 handling
    anywhere in `src/`, so a carried-forward value is being read as unknown and the row
    dropped. **Unverified** — the API is still down and the Third Law forbids overwriting the
    cache to check.

    **Deliberately not fixed now.** Three rows in 62,636 cannot move an rMAE, and the fix
    touches Contract 5, whose dependents are everything; re-deriving the frame mid-stage buys
    nothing. **Trigger for revisiting:** the first rMAE exists, or the API returns and the
    curve type can be confirmed. It recurs annually, so it will keep.

    Related to item 6, which asks what the *rule* for a 23/25-hour day should be. This is the
    narrower question of one hour going missing inside it.

    **5 October — checked: the grid does not dissolve it.** The rows sit at local midnight, not at
    02:00, so they stay empty on the grid as they should. Still blocked on the API.

12. **The wind/solar forecast may legally appear after gate closure.** *(opened 8 October)*
    Regulation 543/2013, Art. 14(1)(d), sets its deadline at **18:00 Brussels time on D−1**, six
    hours after the auction closes. The catalog's claim "D-1, before gate closure" rests on
    practice, not on the rule, and the data cannot settle it: ENTSO-E stores the hour a value
    describes, not when it was published. The real German publication time is unverified.

    **Decided: stated as a limit, not fixed.** Every model so far uses the series the same
    way, so comparisons between them stay fair; the *level* of every score is what is in
    question. The working assumption is that a forecast of this kind is at hand by 12:00, if
    not from ENTSO-E then from a vendor or the TSOs directly. **Trigger for revisiting:** the
    actual publication time is found, or stage 5 runs live and has to fetch it before noon.

<a id="d20260918"></a>
### 18 September 2026 — where the money actually is

**Residual load, measured across our own seven years.** Wind and solar rose from 34 % of
demand to 43 %. What that did to residual load — demand minus wind minus solar, the thing
dispatchable plant must cover:

| | 2019 | 2025 | |
|---|---|---|---|
| Mean | 36.4 GW | 30.6 GW | **−16 %** |
| Minimum | −5.0 GW | −11.7 GW | more than doubled |
| **95th percentile** | 54.9 GW | **53.9 GW** | **−2 %** |
| Hours below zero | 8 | 188 | ×23 |

**Nine points of renewable share bought one gigawatt off the peak.** Solar does not help at
six in the evening in December, and neither does wind in a windless week. So renewables
*widen* the distribution rather than shifting it down: the floor falls away, the ceiling
stays. That is the structural reason daily spreads quadrupled, and it is still running.

A second observation from the same data: in 2025 the price was negative for **576 hours**
while residual load was negative for only **188**. Prices go below zero roughly three times
more often than supply genuinely exceeds demand — the rest is inflexibility, which is the
mechanism rather than the arithmetic.

And a warning for stage 1: mean residual load was ~36 GW across the training years and ~30 GW
across the test years. **The input distribution has moved, not only the price relationship.**
That is a second regime shift, slower than the 2021–22 one, running through the whole record.

---

**Market analysis — what happens to this opportunity as competitors enter.** Asked whether
battery arbitrage cannibalises itself. It does, and the current figures are sharper than
expected.

| German grid-scale BESS | |
|---|---|
| End 2025 | 2.4 GW (+842 MW, strongest year to that point) |
| First half of 2026 alone | **+888 MW** — more than all of 2025 |
| Expected end 2026 | **5.7 GW** |

German TSOs procure roughly 2 GW of aFRR. About 580 MW of battery capacity is pre-qualified
today; if 35 % of the expected end-2026 fleet qualifies, **batteries alone fill the entire
procurement.** In July 2026, aFRR-up capacity prices fell **35 % in a single month** to about
€10/MW/h, and German BESS revenues fell to €205k/MW/year.

**This reversed the working assumption.** The expectation was that arbitrage would be
compressed and ancillary services would be the escape. The opposite is happening: ancillary
services are saturating first and pushing value *onto* the wholesale markets. Projections
have 2-hour revenues roughly halving to ~€125k/MW by 2030, with **wholesale arbitrage at
95 % of the total.**

So compression does not make this project less relevant. It makes forecast quality the whole
competitive surface: when arbitrage is nearly all the revenue and the spread is thin, the
marginal euro comes from ranking hours better than the next participant.

For scale, the largest adjacent pool is congestion: German grid congestion management cost
**€3.07 billion in 2025**, up from €187 million a decade ago. But Germany is one price zone
by design, so that is reached through regulated redispatch and TSO procurement, not trading.

**The gap worth aiming at.** The industry reports revenue per MW. That figure falls when the
market compresses *and* when a forecast is poor, and it cannot distinguish them. Capture rate
can, because its denominator is perfect foresight on the same asset under the same
conventions. Three things follow, and they are close to unpublished:

1. **Separating market conditions from forecast skill.** As revenue per MW halves, every
   operator needs to know which half was theirs.
2. **When a better forecast stops being worth anything.** rMAE against capture rate answers
   it, and it is the question that sets a forecasting budget.
3. **Probabilistic forecasts driving the decision to act at all.** With a compressed spread
   the real question is whether a day is worth cycling for — a decision under uncertainty,
   where a point forecast is the wrong instrument.

**This moves stage 3 from a technical exercise to the commercially load-bearing stage.**
Quantile forecasts are not a refinement of stage 1; they are what the third point needs.

#### Reading the three figures, which changed three things

The figures had been produced at the end of 17 September and never discussed. Reading them
properly cost an hour and was worth more than that, because two claims sitting under them did
not survive and a third number was never computed at all.

**The residual-load figure asserted its own finding.** It showed seven years in seven colours
and the caption said they were several relationships rather than one. A reader had to take
that on trust — a colour gradient over 62,684 half-transparent points is not evidence of
anything. Fitting one least-squares line per year makes the claim checkable, and the line that
appears is a better result than the correlation table underneath it:

| Years | Slope (EUR/MWh per GW) | Correlation |
|---|---|---|
| 2018–2020 | 1.1 – 1.3 | 0.83 – 0.91 |
| 2021–2022 | 3.5 – 7.1 | 0.58 – 0.62 |
| 2023–2025 | 3.0 – 3.1 | 0.78 – 0.88 |

The correlation was the wrong number to lead with. Within the recent years the fit is *good* —
0.88, 0.78, 0.87 — so the relationship is not unstable now. What moved is the **slope**, which
roughly tripled and stayed tripled. One GW of residual load is worth three times what it was
in 2019, which is the same sentence as: a forecast error of one GW now costs three times as
much. *(Corrected 22 September — that second sentence is wrong. Bids are placed against the
published forecast, so a forecast that turns out wrong is settled in balancing, not in this
auction. What a steeper slope punishes is a model carrying a relationship learned from years
that no longer apply: fitted on 2019–20 and asked about an ordinary 40 GW day in 2024–25 it
answers 39 EUR/MWh where the answer is 114.)* That is a more useful thing to know before building a model than "the correlation is
0.44 pooled".

The instability is confined to 2021–22, and those two years sit inside the training period
while the test years fit well and share a slope. That is the exact shape stage 2 has to handle.

**A claim under the figure was wrong.** The README said *"where residual load turns negative,
so does the price"*. Counting it: of 2,053 negative-price hours, **424 (21 %)** had negative
residual load. The median negative-price hour still needed **+5.1 GW** from something other
than wind and solar. So prices go below zero long before the country runs out of demand, and
the tidy explanation — renewables made more than was needed — covers a fifth of the cases.

Naming what does the rest is beyond this dataset; it holds no plant-level costs. Counting the
hours is not beyond it, and the count is enough to retire the simple story. The figure title
carried the same overreach — *"What thermal plants must cover, against what it cost"* — and is
now the finding instead: *"The same residual load cleared at very different prices"*.

This is the third time a mechanism has been asserted that this data cannot support, after the
gas-price framing on 18 September. A leftover copy of that one was still in the README, found
while fixing this. The pattern is specific enough to name: **the error arrives as a causal
connective**, in a *because* or a *so does* bolted onto a number that was measured correctly.
The number is checked; the clause after it is not.

**The spread columns are not one story twice.** 2025 has more negative hours than 2022 (576
against 69) and a *smaller* spread (124 against 187). So what produces the spread changed —
in 2022 the expensive hours were extreme, in 2025 the cheap hours are. For a battery these are
not equivalent: it recovers 81 % of what it stores but 100 % of what it is paid to absorb, so
spread made of negative prices is worth more per euro than spread made of high ones.

#### Stage 3 rescoped: which hours, not whether to act

Earlier today stage 3 was justified partly by *"with a compressed spread the real question is
whether a day is worth cycling for"*. Checking it against the battery parameters already in
`config.py` — 81 % round trip, 8 EUR/MWh wear — the decision has almost stopped existing:

| | Days a battery with perfect foresight should have stayed idle |
|---|---|
| 2019 | 26 |
| 2020 | 12 |
| 2023–2025 | **1, across three years** |

A day where doing nothing was right used to happen monthly. Now it happens once every three
years. **So "whether to act" is not a live question, and stage 3 must not be built around it.**

What remains is harder, not easier: *which* hours, and *how many* cycles. Two cycles a day
earn more than one only if the second spread clears the wear cost, and that is a judgement
made under uncertainty about a spread that has not happened yet. A point forecast commits to
one answer; a distribution can say how likely the second cycle is to be worth its degradation.
That is a real use for quantiles, and unlike the discarded one it survives the linearity
argument from earlier today — because the cycle count enters through the wear cost, which is
where the objective stops being a straight line.

The column is now in `just explore`, so the number that rescoped a stage regenerates with
everything else rather than sitting in a log.

#### Closing the day: the plan had no address

Asked where the project plan lives, the honest answer was *"in a chat transcript"*. It exists
as a private page and nothing in the repository pointed at it. Six stages, a schedule and the
reasoning behind both, reachable only by scrolling.

That is the same failure as an unreproducible number, one level up. A link now sits at the top
of this file. Whether the plan should instead live in the repository as a file is a real
question and is deliberately not answered today — it would be the seventh document, and
`CLAUDE.md` is explicit that a new file gets asked about rather than added.

The commit table was also three days stale, ending at 15 September while twenty-five commits
had landed since. Refreshed from `git log`. Worth noting as a pattern rather than a chore:
**the parts of a document nobody reads are the parts that rot**, and both of today's
housekeeping items were in that category.

---

<a id="d20260921"></a>
### 21 September 2026 — the contract stops being a comment

#### Recap interview: eight questions, two wrong answers, one repo correction

The market questions went well. Congestion came up unprompted as a reason conventional
plants keep running through a negative price — the copper-plate-versus-reality framing,
which is a system-operations answer rather than a market-theory one and better than the
question deserved. The two-regime point went past what was asked, into what a battery
should *do* about it.

Two answers were wrong and both are worth keeping.

**`revised` was read as a fetch failure.** It is the opposite: a failure raises an
exception, and `revised` means ENTSO-E returned a *different value* for a timestamp already
cached. That is published history moving underneath a number, which is why the displaced
copy is archived rather than overwritten.

**The naive benchmark was justified as a business case.** It is a denominator. An error of
15 EUR/MWh is neither good nor bad until divided by what zero effort achieves. Building it
first also removes a temptation — choose the benchmark after seeing your own score and
there is quiet pressure to choose a weak one.

**And one answer corrected the repository.** Asked why 2025's spread is smaller than 2022's,
the answer said both the highs and lows are less extreme now. Checking it: the lows are
*more* extreme (deepest hour −19 in 2022, −250 in 2025), and relative to the price level the
spread nearly doubled — 0.79 of the mean in 2022 against 1.39 in 2025.

That prompted re-checking a claim written on 18 September: *"a battery keeps 81 % of what it
stores but 100 % of what it is paid to take."* The conclusion was right and the mechanism was
wrong. To deliver 1 MWh a battery must buy 1 ÷ 0.81 = 1.235 MWh, so the charging price is
always **multiplied** by 1.235 — which hurts above zero and helps below it. Three days with
an identical spread of 100 EUR/MWh earn 68.5, 92.0 and 103.7 depending only on where the
spread sits relative to zero. Corrected in the README and the prices page.

#### The stage plan got an address

Asked on Friday where the plan lives, the honest answer was "a chat transcript". Four options
were weighed; the deciding factor was that **two copies drift**, which this project had just
demonstrated twice in a week — a commit table three days stale, and a wrong sentence surviving
in four places after being "fixed".

So the README gained a six-row table carrying *status only*, and the reasoning stayed in one
place. A markdown copy of the full plan was rejected for exactly the reason it looked
attractive: it would have to be kept in step with something else.

#### The training window, decided by measurement rather than argument

The Friday framing was sloppy — "full record or 2023 onward" is not a choice, because 2023 is
the validation set. Contract 2 locks training to Oct 2018 – Dec 2022. The real question was
whether to use all of that window or a recent slice.

| Window | Hours | Mean | SD | Slope |
|---|---|---|---|---|
| Train, full 2018–22 | 36,383 | 98.2 | 113.8 | 3.19 |
| Train, recent slice 2021–22 | 17,472 | 166.1 | 133.2 | 4.81 |
| Validation 2023 | 8,759 | 95.2 | 47.6 | 3.09 |
| **Test 2024–25** | 17,542 | **83.9** | **52.7** | **3.07** |

The usual instinct — prefer recent data for a drifting series — is **backwards here**, because
training stops in December 2022 and the recent end of that window *is* the crisis. The full
window's pooled slope lands closest to test, though by accident of aggregation rather than
representativeness.

Decision: full window for stage 1. A subset chosen now would be chosen without a measured
rMAE, which is the mistake open item 9 exists to avoid. The signal to watch is the SD gap,
114 against 53: errors concentrated in high-price hours would say the training years are
doing harm, and rolling recalibration is the stage 2 answer.

#### `src/features.py` — where Contract 1 starts costing something

18 columns, one row per delivery hour. 63,575 rows, 62,636 usable after dropping incomplete
ones. Train 36,335 · validate 8,759 · test 17,542.

**Two guards, because one was not enough.** `SOURCES` names the three permitted series and is
checked against the catalog at import. That guards the *declaration* — but reaching past the
list is a one-word edit inside any function, and the declaration would still read correctly.
So `data_load()` refuses any key outside `SOURCES` at the point of use.

**The load-bearing test rebuilds one delivery day from a world truncated at gate closure and
requires every feature value to be identical.** Careful naming cannot satisfy it.

**Writing that test exposed a real design fault.** `build()` inner-joined on the price, so a
day with no cleared auction produced no rows at all. Harmless for history, and fatal for the
one moment the project is about: at 12:00 on D-1 tomorrow has forecasts and no price, and
tomorrow is the row a schedule must be built from. The target is now joined on last and may
be absent. The backtest path and the eventual production path are the same function, which is
a classic way for two things to disagree, removed before it could.

A second fault surfaced with it: `shift(24)` moves 24 *rows*, not 24 hours, so a single
missing hour would shorten every lag past it — and the result still looks like a price.
`_hourly_span()` now builds a gapless index first, making the assumption true rather than
hoping.

**Nine injected bugs, nine caught.** One was caught for the wrong reason: swapping
`load_forecast` for `actual_load` failed only because the test fixture lacks that key. A door
that stops you because the handle is broken. That is what prompted the second guard.

#### Explaining the mechanism, which took longer than building it

Most of the afternoon went on one question: how does withholding actually work, mechanically?
The expectation was a moving time window that cuts off at gate closure and is redefined at
each step.

There is no such window. `grep` for a date comparison in `features.py` returns nothing but
comments. The boundary is **structural, not temporal**: every price column is defined as a
fixed step backwards from *its own row*, and the step is chosen so that no row can reach
forward. That works only because the publication schedule is regular — which is also why
CLAUDE.md rules out ENTSO-E outage data, where it is not.

The related confusion, and a good one: is giving the target to `fit()` not itself leakage? No
— that is supervised learning. The separating question is whether predicting a *new* row
requires that row's answer. What the instinct correctly points at is feature construction: a
lag that is too short leaks the target through a column that looks respectable, which is
precisely what `MIN_PRICE_LAG_HOURS` defends.


---

<a id="d20260922"></a>
### 22 September 2026 — an answer that rewrote six documents

#### The recap corrected the project, not the answerer

Five questions, and the second one landed somewhere unplanned. Asked what a wrong wind
forecast costs, the answer was that it costs nothing in this market: the auction closed before
anyone knew what the wind did, so the error is settled in balancing and redispatch, not in a
price that was already fixed.

That is correct, and it invalidated a sentence written on 18 September and repeated since:

> *"a forecast error of one GW now costs three times as much"*

**The day-ahead price responds to the published forecast, not to the outcome.** So the slope
is not an amplifier of input error. It is an amplifier of *transfer* error — it punishes a
model carrying a relationship learned from years that no longer apply:

| Fitted on | Asked about an ordinary 40 GW day |
|---|---|
| 2019–20 | says **39 €/MWh** |
| 2024–25 | answer is **114 €/MWh** |

Seventy-four euros before any noise at all. That is a Contract 2 problem, not a data-quality
one, and no amount of better input touches it.

The claim was live in **six places**: README, the EDA page, `architecture.md`, the plan
artifact, the work log and `learnings.md`. Corrected in the four that present as current;
the two dated records keep the original with a pointer forward, because seeing understanding
change is what they are for.

**Sixth instance, same shape, and worth naming again.** Every one of these has been a correct
number with a wrong clause attached — a *because*, a *so*, a *which is why*. The error class
that keeps recurring is the one with no automated guard, and all six were caught by someone
reading.

#### And it settled something larger

The availability rule reads as a restriction: *use the published forecast, never the
measurement*. Which invites treating the forecast as an honest second best.

It is not. **Bids were placed against the published forecast, so that is what set the price.**
The measurement taken afterwards never touched the auction. A model given the actual would be
given something that played no part in forming the number it is predicting.

Here the honest choice and the accurate choice are the same choice. That will not always be
true, and it is worth noticing when it is. Now stated in `features.py` where someone reading
the code will meet it.

#### The EDA page, retitled around its own result

*"Seven Years of DE-LU Prices"* was a category label — it said what the page contained, and it
was written before the page contained a finding. It is now **"Eight Years, Three Markets"**,
which is the result: the eight fitted lines sort into flat-and-tight (2018–20), steep-and-
badly-fitting (2021–22), and steep-and-tight again (2023–25).

Also: the third hero figure swapped from the −500 floor to the slope, the figure-1 caption
dropped a gas attribution, and open question 3 now carries the 74 €/MWh number instead of a
promise to measure it.

#### Three things removed

| Removed | Why |
|---|---|
| `notebooks/` and its `.gitignore` rules | Empty for two weeks. Exploration turned out to run through `just explore` and be presented as a page. |
| `data/interim/` | Reserved on day one, never written to. |
| `data/processed/` | Same — and labelled "feature frames ready for a model", which describes work this project does not do. |

The rule that came out of it: **cache what is slow, limited or impossible to fetch again;
rebuild everything else.** Raw data qualifies on all three counts. The feature table rebuilds
in under a second and would only introduce a copy that can fall out of step with the code.

Open item 8's trigger has now fired and is closed: `INTERIM` and `PROCESSED` were "waiting for
`features.py`", and it did not need them.

#### A stale comment, and a check that was not built

`GATE_CLOSURE_LOCAL` carried a justification written on day one: the constant was a time object
*"because the lag arithmetic in features.py will have to compare against it"*. It never does —
the deadline is kept by shifting rows, not by consulting a clock. A prediction about code that
did not exist yet, wearing a comment's authority, and never revisited.

Deriving `MIN_PRICE_LAG_HOURS` from it was considered and **declined**. The arithmetic needs
the latest delivery hour, the publication lag and a rounding rule — three fudge factors, and
it would need its own test to prove the derivation right. **When a check is harder to be
confident about than the thing it checks, it adds surface rather than safety.** A one-line
pointer went in instead, so searching for the constant finds both ends.

#### What the map was getting wrong

`architecture.md` predated `features.py`. It showed that file writing a cache it never writes,
omitted `explore.py` entirely, and sent a first-time reader to a verification script rather
than to the file the whole backtest depends on being right.

Rewritten around the boundary that actually matters: **above `features.py` everything is
transport, below it everything is a decision.** Plus a section on the three treatments, because
describing the lag as though it governed every column invited exactly the misreading it got.


---

<a id="d20260923"></a>
### 23 September 2026 — aligning on the modelling approach, then building half of it

#### Two decisions taken before any code

**Six algorithms, or two?** The instinct was a bake-off — random forest, boosting, linear,
a neural net — to see what wins. Costed honestly it came to nine or ten hours against three,
and most of the extra was not the models:

- untuned defaults compare *libraries*, not algorithms, so each needs a hyperparameter search
- searching on validation makes the validation score optimistic, which needs a nested split
- two of the six need feature scaling, which introduces the fit-on-train-only trap that
  `CLAUDE.md` names as a danger zone — a new leakage surface the other four do not have
- and "is A really better than B" is a significance test, which the plan already places at
  stage 2

**Decided: naive, linear, gradient boosting.** The bake-off moves to stage 2, where tuning
and significance testing are the stage's actual subject and the stage-1 runs become the
control group rather than being thrown away.

The deciding argument was not cost. **The problem we know we have is three markets inside the
training data, worth 74 EUR/MWh of transfer error, and no algorithm choice touches it.**
Comparing six models on a mis-specified problem measures which one tolerates
mis-specification best.

**MLflow now, or later?** Chosen, then reconsidered on request, and the reassessment reversed
it. Experiment tracking solves *"I ran something and cannot remember what"* — and this
repository already solves that: every number regenerates from a clean clone in seconds, the
work log carries the reasoning, and git carries the code. **You cannot lose a run here, not
because runs are recorded but because they are cheap to recreate.**

And the setup cost does not compound. Installing it is the same 45 minutes whenever it
happens, unlike tests, where early adoption changes everything written afterwards.

**Trigger recorded so the deferral is a decision rather than a gap: adopt tracking when a run
costs more to reproduce than to record.** Stage 2's search hits that on all three counts —
dozens of trials, hours of compute, per-trial parameters that cannot be recovered cheaply.
Stage 1 hits none.

Worth noting the portfolio argument runs the same way. Tracking wired up for three runs reads
as tooling adopted because it is expected. Adopted at stage 2 for a sixty-trial search, with
the deferral written down, reads as judgement — and `CLAUDE.md` is explicit about which is
worth more.

#### `src/evaluate.py` — built by hand, and the first version was wrong

Scaffolded rather than delivered: every block explained, the benchmark written out as the
worked example, `mae` and `rmae` left with their reasoning and no body, tests written first.

Both were implemented correctly against the notes and passed all nine tests. **And `rmae` was
still wrong**, because the notes were incomplete.

```
mae(model, actual)      -> trimmed to hours the model reaches
mae(benchmark, actual)  -> trimmed to hours the benchmark reaches
```

Two independent trims. The naive rule has a value for the opening week where a fitted model
has none, so the benchmark collects a free hour and **the ratio moves without either forecast
changing** — 0.67 where the answer is 0.50, a third of the score from one hour in four.

Fixed by widening `aligned` to take any number of series and trimming them as a set. `rmae`
and `score` both go through it, so the hour count a row reports is the hour count its own
numbers came from — otherwise `n` audits a different set than the score beside it, which is
worse than no audit.

**Four injected bugs, two caught, and the two survivors meant different things.** One was a
genuinely missing test: breaking `score` so it trimmed only two of three went unnoticed,
because the existing test used three series with identical coverage and could not
discriminate. The other was equivalent — an outer join followed by dropping blanks leaves
exactly the rows an inner join would, so the setting is redundant. Noted in place rather than
changed.

#### Two questions that improved the repository

**"Are we sure forecasts are ever actually missing?"** On the scored rows, no — measured, and
the blank-dropping never fires. The earlier example was accurate but drawn from a path the
project does not take, which made a precaution look like a fix. The comment now says which
guard is measured and which is insurance.

The check did turn up something new: **the two estimators do not agree on reach.** A
gradient-boosted tree predicts through missing features; a linear fit refuses. So "score each
model on whatever it can reach" would give them different exams, and only one would say so.
That converts the open scoring decision from a judgement call into a measured one.

**"Is sixteen failing tests what an outside user sees?"** Yes, and that was a real fault.
Test-first is a sound local workflow; a red default branch is a claim about the project's
state, and it was a false one. **The terminal is read before the README**, so a footnote
never arrives in time.

The tests now expect one specific failure — the function being absent — and nothing else, so
a wrong implementation still fails loudly and a correct one reports an unexpected pass as the
signal to remove the marker. Verified by implementing one function correctly, then breaking
it, and checking each outcome.

#### And the first instruction was a prerequisite

The setup began `brew install just`: macOS-only, for a tool needed before the repository
could do anything, in a project whose only real prerequisite is Python. It was also circular —
`just setup` builds the environment, but `just` had to exist first.

Plain commands are now the documented path, verified on a genuinely fresh clone rather than
assumed. `just` stays as optional shorthand with a platform-independent install. The justfile
is deliberately **not** duplicated in the README, because two copies of the same commands is
the drift this project has already been bitten by twice this month.


---

<a id="d20260928"></a>
### 28 September 2026 — the first number, and a fixture that could not fail

#### Recap — one answer right, one half right, one wrong

**Q1, negative prices and rMAE — half.** The absolute value was correctly identified as the
reason a score cannot come out negative. But that is not what breaks the percentage error.
It breaks because prices pass *through* zero: at exactly zero the division has no answer, and
at 0.50 EUR/MWh a ten-euro miss becomes 2,000 %, drowning the year. rMAE never puts a price
underneath the line at all.

**Q2 — needed rephrasing, then right.** Restated as four hours of arithmetic it was answered
correctly: the free hour the benchmark got right is not an hour the model got wrong, because
the model was never in the room.

**Q3, the two surviving mutants — wrong.** The proposed test was to run the suite and see
whether the mutant passes. Both had already passed; that is what surviving means. The
separating question is whether the change alters behaviour at all. One did and no test
noticed, so a test was missing. The other could not, because `dropna` on the next line makes
the two versions identical for every possible input — nothing can catch it.

**Q4, red tests on a clean clone — right,** including the reason that matters: the terminal is
read before the README.

#### A scoping question that found a defect

The question was whether the missing forecast rows could be avoided by starting the record in
January rather than October. Answer: mostly they already are, and starting later would discard
1,319 good training rows to avoid 888 that cost nothing.

But checking *where* the gaps sit rather than *how many* there are turned up something the
count could never have shown. Of 939 dropped rows, 936 are in training. The other three are
one per year, all at local midnight on the autumn clock-change day, two of them in test data.
The raw file jumps from 21:45 to 23:00 — the whole hour, quarter-hours included — while the
price series has all 25 hours. Not a timezone bug here; the hour is absent from the
publication, and matches the `curveType A03` carry-forward trap `CLAUDE.md` already names.
**Logged as open item 10 rather than fixed:** three rows in 62,636 cannot move a score, and
the fix touches Contract 5.

The distribution said something the count could not. That is the whole finding.

#### `models.py` — a test that caught the bug for the wrong reason

All four functions were written correctly first time. Two `frame.copy()` calls were removed:
nothing in either function mutates the frame, so they defended against something that cannot
happen while copying 36,335 rows to do it.

Then the leak was reintroduced on purpose — the answer column let into both `fit` and
`predict`. The headline test failed, but with `ValueError: Input X contains NaN`. **It caught
the bug by crashing, not by comparing.** The test blanks the target with NaN, which a linear
fit refuses outright, so the forecast the assertion exists to compare was never produced.

A sibling test now blanks the target with a finite wrong value instead. Nothing can refuse it,
so the comparison actually runs. Both stay: NaN is the honest picture of a day not yet
cleared, and the finite value is the one that exercises the logic.

#### Three decisions before `train.py` was written

1. **Fit once on 2018–2022, never refit.** The stricter test — the model sees no validation
   row — and it keeps the stage's question attributable. A win belongs to the model rather
   than to the refitting. Walking the fit forward is stage 2, measured against this.
2. **Validation only; the test years unreachable from the script.** `cfg.split` returns three
   frames and this one binds the third to `_`. Contract 2 made checkable in one character
   instead of promised in a docstring.
3. **Results appended to `results/scores.csv`, stamped with the commit.** MLflow reassessed
   again and still deferred: the trigger was *adopt tracking when a run costs more to
   reproduce than to record*, and a run here takes seconds. What was actually wanted — results
   comparable over time — is five lines. The commit stamp is the part that earns its place:
   the Third Law asks that a number be reproducible from a clean clone, and a number beside a
   commit says which clone.

A blanket `*.csv` rule was silently swallowing the file. Negated, with the reason written next
to it.

#### The first rMAE

```
| Model  | Split | Hours | MAE   | rMAE  |
|--------|-------|-------|-------|-------|
| naive  | valid | 8,759 | 33.64 | 1.000 |
| linear | valid | 8,759 | 17.89 | 0.532 |
| gbm    | valid | 8,759 | 16.43 | 0.488 |
```

Modelling beats not-modelling. Both free checks passed: the benchmark reads exactly 1.000, and
all three sit on identical hour counts.

One display bug fixed on the way: the run printed the validation range as `2022-12-31 to
2023-12-31`, which is correct in UTC and wrong-looking to everyone. Delivery days are
market-local, and now it prints that way.

#### The mutant that exposed a rigged fixture

Scoring each model against **itself** rather than the benchmark makes every rMAE exactly
1.000 and the table meaningless. **All 13 tests passed.** Nothing checked what sat in the
denominator.

The missing test — the fitted models must beat the naive rule — then failed on the *correct*
code, which meant the fixture was wrong. It was, in two ways at once, both from the same
cause. Its price rose by 0.002 every hour, so:

- last week's price was **always exactly 0.336 too low**, making the benchmark near-perfect
  and unbeatable by construction
- every validation price sat above anything in training, and a tree can only output values it
  has already seen, so it scored **rMAE 15.04** — fifteen times worse than doing nothing

Rebuilt on waves of 24 hours, 13 days and ~29 days, none of which line up with a week. The
benchmark now has something to miss and the tree is never asked to extrapolate.

**A test fixture can be wrong in a way that hides the bug the test exists to find.** Only the
mutation exposed it; a green suite never would have.

#### Leakage, calibrated rather than asserted

The target was copied into the features under another name, scored, and removed:

| | linear | gbm |
|---|---|---|
| honest | 0.532 | **0.488** |
| leaked | 0.000 | 0.023 |

Twenty times away from leaked territory, and 0.4–0.6 is the ordinary band for this problem.

#### What the errors are made of

| Price quartile | naive | linear | gbm |
|---|---|---|---|
| lowest | 46.56 | 22.73 | **17.98** |
| low | 25.24 | 15.38 | **11.49** |
| high | 26.40 | **14.01** | 14.52 |
| highest | 36.37 | **19.45** | 21.72 |

**The tree wins at cheap hours and loses at expensive ones** — the same extrapolation weakness
that destroyed the fixture, showing up on real data in a milder form.

Two more things worth carrying forward. The naive rule is still the closest of the three on
**23.6 %** of hours, so it is not a straw man. And the gbm is closer than the linear fit on
only **53.4 %** of hours — close enough to a coin flip that *"the tree is better"* is not yet
a claim that can be made. That is what the significance test in stage 2 is for.

Error by hour of day spans **7.79** between the quietest night hours and the 19:00 peak, which
is the argument for fitting each delivery hour separately. Error by month runs from 13.0 in
June to 23.7 in January — the months hardest to forecast are the ones most like the crisis the
training data ends in.

> **Corrected 29 September.** The last sentence does not survive checking and should be read
> as withdrawn. January's raw error is highest because January *prices* swing hardest — the
> naive rule misses by 61.33 there against 21.38 in June. Measured as a ratio the ranking
> inverts: January **0.387** is among the model's best months and May **0.721** its worst.
> Monthly error tracks monthly price spread at **0.675**. This was a raw number read without
> normalising for how much there was to get wrong. The rolling-window argument stands on the
> 74 EUR/MWh transfer error and the field's two-year default, not on this.

---

<a id="d20260929"></a>
### 29 September 2026 — a number that could not carry the claim resting on it

#### Recap — and a correction that went the other way

**Q1, the surviving mutant — described, not explained.** The answer said what the mutation
did, correctly. The question was why none of four tests could notice. They were all checking
the table's *shape* — hour counts agreeing, three models present, rows labelled correctly —
and **nothing was checking the contents.** The subtle part: `test_the_benchmark_scores_exactly_one`
looks like it guards the denominator and cannot, because the benchmark is passed as both
numerator and denominator explicitly. That row reads 1.000 whether the code is right or not.

**Q2, the rigged fixture — both breakages right, second half unanswered,** and the true answer
is sharper than the question implied. The new assertion is `rmae < 1.0` for both models. On the
broken fixture the linear fit scored 0.000 and **passed**; only the tree's 15.04 tripped it. The
near-perfect benchmark never surfaced as a failure at all — an assertion that a model beats the
benchmark cannot detect a benchmark that is impossible to beat, so long as something beats it
anyway. It was found by asking why the naive MAE was exactly 0.336.

**Q3, LASSO — one blade of the scissors.** Fewer rows per model is right: 36,335 to ~1,514. But
that alone is comfortable at 89 rows per input. The missing half is that the per-hour layout
*invites many more inputs* — yesterday's same hour, the neighbouring hours, last week's, the
daily peak — so rows divide while columns multiply. At LEAR's ~200 inputs that is ~7.5 rows
each, which is where ordinary least squares collapses and LASSO becomes necessary.

**Q4, the rolling window — right reasoning, and my evidence was wrong.**

#### The correction

I had pointed at error by month: January 23.70 against June 12.99, read as *the hardest months
are the ones most like the crisis*. Checking it took one line.

| | model | benchmark | ratio |
|---|---|---|---|
| January | 23.70 | 61.33 | **0.387** |
| June | 12.99 | 21.38 | **0.608** |
| May | 14.78 | 20.49 | **0.721** |

**The ranking inverts.** January is among the model's best work and May its worst. January's raw
error is large because January prices swing hardest — there was more to get wrong. Monthly error
tracks monthly price spread at **0.675**.

Withdrawn in the 28 September entry with a dated note, and removed from the forward plan. The
rolling-window lever is unaffected; it rests on the measured 74 EUR/MWh transfer error and on the
field's two-year default, not on this.

**Second time in a week for the same shape of mistake.** The first was 939 dropped rows, where
the count said one thing and the distribution another. A number can be true and still unable to
carry the claim resting on it.

#### Sources, finally attached to the claims they support

LEAR, the two-year calibration window and Diebold-Mariano were named in the README's ground
rules with nothing a reader could check. A references section now lists each with **the claim it
supports**, split into method and data. Verified rather than recalled: Lago, Marcjasz, De Schutter
& Weron (2021), Applied Energy 293, doi:10.1016/j.apenergy.2021.116983, and the accompanying
`epftoolbox`; Diebold & Mariano (1995) plus the author's own twenty-years-later retrospective;
and the recent result that the test **loses power as errors become more dependent**, so a
non-significant answer means *cannot tell* rather than *the same*.

The "0.4–0.6 is the normal band" claim I had offered twice was left out entirely rather than
propped up with a vague citation.

#### Open item 9 — closed without fetching anything

The trigger was a measured rMAE, and with one available a better question was available too:
**does the data those days belong to matter at all?**

| Train from | Rows | linear | gbm |
|---|---|---|---|
| 2018 | 36,335 | 0.532 | **0.488** |
| 2019 | 35,016 | 0.535 | **0.488** |
| 2021 | 17,472 | 0.750 | 0.507 |
| 2022 | 8,712 | 0.977 | 0.615 |

Dropping **all** of 2018 moves the tree by nothing. The 37 missing days would add ~888 hours to
a year contributing 3.6 % of training and no measurable accuracy. `energy_charts.py` was not
written; the validated recipe stays in `docs/data-quality.md`.

The same table says something else worth carrying: more data helps steeply, and **two years alone
is clearly worse than five.** Those are the crisis years, the worst possible pair for a calm 2023
— which confirms the 21 September finding on the target metric rather than on a slope. It does
not settle the rolling window, whose benefit comes from the window *moving forward* into the year
being forecast, which a fixed window ending in December 2022 cannot show.

#### Open item 10 — still blocked

The ENTSO-E API returned **HTTP 000 after twenty seconds**. The `curveType A03` hypothesis stays
unverified, so the three clock-change rows stay as they are. Fixing them later would change the
held-back set by 2 rows in 17,542 — 0.01 %, below anything that could move a number, but it
belongs beside the result so the change is visible rather than discovered.

#### `final_score.py` — built, broken on purpose, and not run

Two decisions first. The name: `close_stage` said *when* to run it rather than *what it does*,
and anything containing "test" would collide with `just test` — a collision that had already
caused real confusion earlier in the day. **`just final-score`.** And what the models learn from:
**everything through 2023**, because validation has already chosen between them and every 2023
price was public before any 2024 delivery hour.

The line deciding that is the highest-stakes one in the repository, so it was mutated both ways:

| Mutation | Caught by |
|---|---|
| drop validation from the fit | `test_the_fit_includes_the_validation_year` |
| let the held-back years into the fit | `test_the_fit_stops_before_the_held_back_years` |

Each failed the test named for the failure it causes. The self-benchmark hole that survived a
mutation in `test_train.py` was closed here in advance rather than rediscovered.

**152 tests pass. The command has not been run** — that read is deliberate, and it is being taken
tomorrow rather than at the end of a long session.

---

<a id="d20260930"></a>
### 30 September 2026 — the ranking reversed

#### Recap — one inverted, one explained, one partial, one right

**Q1, closing open item 9 — inverted.** The answer described asking whether the data could be
fetched first, and only then whether it could be dropped. That is the natural order and it is
the trap. **Availability was never in question** — the Energy-Charts recipe had been validated
on 17 September. The question that closed the item was whether the data mattered, and it did
not. Asked the other way round, `energy_charts.py` would exist permanently for a measured
benefit of zero.

**Q2, the test that cannot fire — explained rather than marked,** on request. The benchmark row
is built as `E.score("naive", SPLIT, benchmark, benchmark, actual)`: the same object twice, so
the row is a number divided by itself and reads 1.000 whether the code is right or wrong.
Demonstrated live by scoring every model against itself — the table became a column of ones and
that test still passed.

**Q3, two years worse than five — partial.** The general point about long windows averaging
across regimes would have predicted the opposite of what was measured; five years beat two. The
narrower answer is that the test was a *fixed* window ending December 2022, so "two years" meant
the crisis years exactly. A rolling window moves, and by mid-2023 would hold 2023 itself.

**Q4 — right,** with the sharpening that what is forbidden is adjusting *in response to what was
seen*, and that the limit is once per stage rather than once ever.

#### A push that changed the script

The plan was to score one recipe on the held-back years, fitted through 2023. The objection —
that this mixes up what validation is for — was right in substance, and my first answer to it
overcorrected into dropping 2023 from the fit entirely, on an argument that did not hold: stage
1's "never refit" rule existed to keep the *validation* score honest, and the held-back years
are 2024-25.

**Settled properly: both recipes, one reading.** Contract 2 limits how often the held-back years
are looked at, not how many models are scored inside one look. Fitting to the end of 2022 keeps
a row directly comparable to the validation score; fitting to the end of 2023 gives the model
that would actually run.

That decision is the only reason the finding below was visible.

#### Two tests found unable to fire

Mutation before running anything, since the read cannot be repeated.

**The test named for the leak did not catch the leak.** It built its own `pd.concat([train,
valid])` and checked *that* — so when the held-back years were let into the fit on purpose, it
passed. The leak was caught incidentally, by a label reading `2018-2025`. It now stands in front
of `M.fit` and records every frame that arrives; the same mutation now fails the test named for
it.

**A second test claimed to verify a fresh estimator per fit.** Sharing them was tried: every test
passed, because each row is scored before the next fit replaces the estimator. Both the test name
and the comment above the code now say what is actually true.

Same shape as the benchmark-scores-one check, twice in one file. **A test that reconstructs its
own version of the thing under test is testing its own reconstruction.**

#### The number

```
| Model            | Split | Hours  | MAE   | rMAE  |
|------------------|-------|--------|-------|-------|
| naive            | test  | 17,542 | 32.81 | 1.000 |
| linear 2018-2022 | test  | 17,542 | 18.85 | 0.575 |
| gbm 2018-2022    | test  | 17,542 | 20.58 | 0.627 |
| linear 2018-2023 | test  | 17,542 | 18.46 | 0.563 |
| gbm 2018-2023    | test  | 17,542 | 17.44 | 0.532 |
```

Benchmark exactly 1.000, all five hour counts identical, recorded under commit `4c7ace0`.
**Modelling beats not-modelling: 17.44 against 32.81.**

#### And the result that matters more

| Same recipe | validation | held-back |
|---|---|---|
| linear | 0.532 | **0.575** |
| gbm | **0.488** | **0.627** |

**The ranking reversed.** The tree won on 2023 and loses on 2024-25 with the identical recipe.
The tree also degraded three times as hard — 0.139 against 0.043.

The warning had been sitting there since 28 September and was not acted on: the tree was closer
on only **53.4 %** of hours, barely better than a coin toss. An average can differ because one
model is steadily better or because a few hours differ a lot, and a summary table cannot tell
those apart.

Had the validation number been reported and the stage closed, a false belief would have gone
into stage 2. **This is the apparatus working, and it only works once.**

One coincidence, named so nobody reads meaning into it: the headline 0.532 happens to equal the
validation linear score exactly. Unrelated.

The extra year is worth more to the tree than to the line — 0.095 against 0.012 — which fits the
recalibration finding below. Recency is what the tree wants.

#### Recalibration, measured

A feasibility probe, written to answer whether stage 1's single-fit choice constrains stage 2.
It does not: walk-forward refitting took about ten lines using only what already exists, with
**no changes to `src/`**. `M.fit` and `M.forecast` are stateless, so the single-fit decision
lives in a script rather than in the library.

| Recipe (validation) | linear | gbm |
|---|---|---|
| one fit, 2018-2022 | 0.532 | 0.488 |
| refit monthly, expanding | 0.525 | **0.440** |
| refit monthly, rolling 730d | 0.709 | 0.442 |
| refit monthly, rolling 365d | 0.711 | 0.458 |

**Refitting helps; forgetting does not.** The expanding window wins, and the rolling two-year
window — the field's default — is a wash for the tree and much worse for the line. The lever is
*refit more often*, not *forget the crisis*, which reframes what had been assumed since
28 September. Caveats: monthly rather than daily, one validation year, no significance test.

#### The plan, reordered on evidence

Researched on request rather than settled from memory. The field's families: LEAR and DNN as
reference benchmarks, gradient boosting as the workhorse, random forests competitive, deep
sequence models mixed. **We are already in the strongest family** — though the model in use is
`HistGradientBoostingRegressor`, sklearn's histogram-based implementation, not LightGBM.

Stage 2 led with "model craft". It now leads with **recalibration**, because that produced a
larger measured gain than any algorithm choice, and because the one algorithm comparison made so
far did not survive contact with the held-back years.

**CatBoost and Random Forest parked until stage 4**, with the reason recorded: both are reported
to trade well despite worse error scores. **Capture rate may not rank models the way rMAE does**
— a battery needs the *ordering* of hours, not the level — so ranking more algorithms on rMAE
before stage 4 says whether the two agree would be careful measurement against the wrong target.

`CLAUDE.md`'s stage table updated to match and now points at the README as canonical.

#### The split rationale, three weeks late

Written into `src/config.py` where someone looking at the split will find it. The dates were set
on day one and the reasoning existed only in someone's head until a question on 28 September
found that nobody had asked.

Recorded with the weakness rather than only the justification: training ends inside the gas
crisis, validation is the recovery, the held-back years are calmer still, so each block is unlike
the one before it. Honest about the market, and it makes validation an unusually *different*
exam — which is exactly what the reversal above turned out to demonstrate.

---

<a id="d20261002"></a>
### 2 October 2026 — a convention chosen from the literature

The first hour went on housekeeping, each piece committed on its own: `HANDOVER.md` was dissolved
into the files that stay current, the plan page was replaced (the old one is kept as a dated
snapshot), and the score record moved under `reports/`. A short session followed.

#### Recap — short form, two reversed

There wasn't time for the four questions, so five one-liners instead. Two came back the wrong way
round, which is the useful part:

- **Which training window won when refitting monthly?** Answered "the one that drops old years".
  It was the one that **keeps every year**: 0.440 against 0.442 for the tree, and 0.525 against
  0.709 for the line.
- **Which model won on 2024–25 when trained up to the end of 2022?** Answered "the tree". It was
  **the line: 0.575 against 0.627.** That is the reversal, and the main finding of stage 1.

Also sharpened: an rMAE of 1.0 means *as good as copying last week*, in general. Comparing a model
with itself is one way to get exactly 1.0, and that was the bug, not what the number means. The
four full questions move to Monday.

#### Open item 6 — every day becomes 24 slots

Stage 2 fits one model per delivery hour, so a day with no 02:00, or two of them, needs a rule
before anything is built. Five options were weighed:

| Option | What it does | Verdict |
|---|---|---|
| A. Real hours | per-hour models take whatever rows carry their clock label | **rejected:** works for today's models, but LEAR wants "yesterday's 24 prices" as one block, and lags stay one clock hour off for a week after each change |
| **B. 24 slots** | mean of neighbours for the missing hour, mean of the pair for the doubled one | **chosen** |
| B inside, real hours for scoring | fit on the grid, map back before scoring | **rejected:** two conventions to keep in step, to keep 4 hours in 17,544 exact. The field does not do it |
| C. UTC hours | one model per UTC hour | **rejected:** one model would cover 07:00 in winter and 08:00 in summer |
| D. Drop the days | skip clock-change days | **rejected:** the battery still trades them, and the evaluation would have a silent hole |

**What decided it was the literature, looked up rather than recalled.** The convention goes back
to Weron, and the standard open benchmark (Lago, Marcjasz, De Schutter and Weron 2021, with its
`epftoolbox` code) builds its datasets this way, German market included. Scoring happens on the
24-slot data too. My first proposal, the middle row, was extra care the field does not take. I had
also overstated what stage 4 must "undo": it is a few lines that drop one slot or repeat one.

**One side effect fixed by construction.** Lags step back a fixed number of rows. On real UTC
hours, `price_lag_168h` points one clock hour off for the week after each clock change. That is
about 14 days a year, and the naive benchmark is that same column. On a 24-slot grid, 168 rows
back is always the same clock hour. This was worked out from the code, not measured.

**What it costs, in Contract 5 terms:**
1. Contract 5 (time and resolution) is affected. Owner: `src/data.py`.
2. Its dependents are everything: `features.py`'s lags and daily summaries, the split boundaries in
   `config.py` (currently UTC timestamps), the models, the scoring.
3. Not updated today. This entry and the CLAUDE.md wording record the decision. The build is
   Monday's first job.
4. **Previously produced results:** stage 1's held-back 0.532 stays as recorded, under the
   real-hour convention. It is not re-scored now, because that would be a second look at
   2024–25. Stage 1's recipe gets re-scored **inside stage 2's single final run**, alongside
   stage 2's models, which is the "five models, one look" lesson. Validation numbers get
   re-scored freely once the grid exists. Expected to move very little (2 hours in 8,760), but
   that is not measured yet.

Sources: [Lago et al. 2021](https://www.sciencedirect.com/science/article/pii/S0306261921004529) ·
[epftoolbox](https://github.com/jeslago/epftoolbox) ·
[Ziel & Weron, LASSO](https://arxiv.org/pdf/1509.01966)

---

<a id="d20261005"></a>
### 5 October 2026 — the grid built, and a convention checked rather than reasoned

#### Recap — three partial, one forgotten, one reversed again

- **What predicted the reversal?** Answered in general: results on one year need not carry over
  to the next. True, and true of everything, so it predicts nothing. The specific warning was a
  number: the tree was closer on only **53.4 % of hours**, barely better than a coin toss.
- **What does "once" limit?** Half right. It limits look, adjust, look again, not how many
  models are scored in one look. The recipe fitted to the end of 2022 was the row comparable to
  the validation score, and the only reason the reversal was visible.
- **The leak test that stayed green.** Not remembered. It built its own copy of the training
  data and checked that. *A test that builds its own copy of the thing it checks is testing its
  copy.*
- **Why recalibration leads stage 2.** Drifted towards "choose the right training window", for
  the second session running. The measurement says the opposite: keep every year, refit more
  often. Asked again tomorrow.
- **Why stage 4 needs real hours.** Right for spring (the invented 02:00 is dropped), missed
  autumn: there are two real 02:00s, each traded and each paid at its own price.

#### MLflow — the deferral had answered a different question

The 23 September deferral asked *could a run be lost?* It could not, because every run
regenerates in seconds. Today's question was *can runs be compared side by side?* The deferral
never weighed that, and stage 2 is where it starts to matter. There will be several refitting
variants, and the significance test needs every hour's forecast, which `reports/scores.csv`
does not keep.

**Decided:** MLflow comes in after the grid is wired and before recalibration.
`reports/scores.csv` stays the record. It is in git, while `mlruns/` is local and ignored, so only
the CSV satisfies the Third Law. MLflow is where runs are compared and where per-hour forecasts
are kept. The 2023 baseline is scored into the CSV as soon as the grid is wired, then re-run
(seeded, so identical) as MLflow's first run. The held-back years are never re-run to fill it.

For stage 4: one run can log capture rate beside rMAE, which is exactly the comparison that
decides whether error ranks models the way money does. There are two things MLflow cannot
enforce. Every run must record its horizon convention (Contract 4), or incomparable runs sit in
one table. And scenarios are explored on 2023 and run on 2024–25 once.

The README's *Parked on purpose* table still says deferred. It changes when MLflow lands.

#### Stage 2 — what to expect, written down before measuring

| Step | Expected | Basis |
|---|---|---|
| Refit monthly, every year kept | tree 0.488 → 0.440 | **measured** |
| Refit daily instead | small extra gain, if any | guess: monthly already removes most of the staleness |
| Diebold-Mariano | none, by design | it tells real gains from luck |
| LEAR | unknown | the plain line already beat the tree on 2024–25 |
| One model per hour | more for the line than the tree | reasoning: a tree can already split on hour |
| Public holidays | large on ~10 days, small on the year | arithmetic |

Tuning the tree's settings is not in the plan. It needs its own held-out slice to stay honest,
and is worth it only if the tree and LEAR end up close.

#### The grid's labels — looked up in the field's code

My first recommendation was a two-part label, date plus slot number, chosen to keep the guard
that refuses timestamps without a timezone. The pushback asked what the field actually does.
`epftoolbox` reads every dataset with `pd.to_datetime(data.index)`: no timezone, 24 rows a day.
LEAR builds lags as `- pd.Timedelta(hours=24)` and daily blocks as `reshape(-1, 24)`, both of
which only work on such an index. **So: naive timestamps, Berlin wall clock.**

A follow-up asked whether a timezone is implied somewhere else. It is, in one sentence of the
paper (§3.1), checked verbatim: *"All available time series are saved using the local time, and
the daylight savings are treated by either arithmetically averaging two values from the extra
hour or interpolating the neighboring values for the missing observation."* Averaging and
interpolating only make sense on a clock that changes, and UTC never does.

Second time in a week for the same lesson: check the convention before designing around it.

#### Piece 1 — `to_slots()` (`f679b21`, citation in `673d835`)

Built in `src/data.py` and not yet called. Tested on 2024's real clock-change dates. Four
mutations (no spring fill, fill every gap, keep the first autumn 02:00, UTC instead of Berlin)
each failed the test named for them. On the real cache every full day has 24 rows, and
31 March 2024 02:00 reads 65.84, the mean of 66.71 and 64.98. `numpy` is now in
`requirements.txt`; four test files had already been importing it unlisted.

**Open item 10 is not dissolved by the grid.** Its three rows sit at local midnight, not at
02:00, so they stay empty. Checked rather than assumed, as the last entry asked.

#### Piece 2 — three jobs, and a split by date (in progress)

The explanation that landed, after several that did not, was three jobs rather than two clocks:

| Job | Needs | Why |
|---|---|---|
| Storing | world clock (UTC), every real hour | on 27 Oct 2024 Berlin's 02:00 occurs twice (82.23, 80.43); only UTC names them apart |
| Models | Berlin clock, 24 hours a day | prices follow Berlin life; every day the same length |
| Battery | the real hours | it is paid for what happened, both 02:00s |

Decisions taken:

- **The translation happens in `features.py`, after the loader, not inside it.** Three test
  files replace the loader with world-clock fixtures. Translating afterwards sends those
  fixtures through the same path as real data. It also means the leak test cuts the future off
  the *original* before translating, which is the order reality has. A `load_slots()` was
  written and withdrawn for this reason.
- **`split()` sorts by Berlin delivery date.** Grid labels are compared directly, and world-clock
  labels are read on the Berlin clock first. This replaces `_first/_last_delivery_hour` and the
  four `*_UTC` constants, and their tests go with them.
- **Found while rewriting the tests:** the three split tests (no overlap, no gap, every row
  once) cannot see *where* the cut falls. Moving it to UTC midnight left all three green. The
  constant tests being removed were what pinned the position. They are replaced by position
  checks on what `split()` returns, for both clocks. Both mutations were caught.
- **The leak test gains 1 April 2024**, the first day to read the invented 02:00 as "yesterday".
  To fill that hour, the grid reads a *later* hour, which is exactly what this test exists to
  catch.
- **2023 is re-scored as soon as the wiring is done**, because the chain must run end to end.

**State at close.** `src/config.py`, `tests/test_config.py` and a docstring in `src/data.py` are
**modified and uncommitted**. `test_config.py` passes 10/10, but the full suite is red:
`test_train.py`, `test_final_score.py` and `test_data.py` still reference the removed `*_UTC`
constants. `main` is green at `673d835`.

---

<a id="d20261006"></a>
### 6 October 2026

#### Recap — two partial, three wrong, refitting missed a third time

- **Three jobs, three clocks.** Battery right (25 real hours). Put the models on UTC, with the
  averaging there. The models run on Berlin's clock: a UTC day has 24 hours but starts at a
  different Berlin hour in summer and winter, so the morning peak would move twice a year. On
  27 October 2024 the stored 82.23 and 80.43 become one model hour of 81.33.
- **The three split tests.** Answered that they checked "the wrong time format". They check
  that the pieces fit (no overlap, no gap, every row once) and look at no time at all. Moving
  the first hour of 2023 into training broke nothing they looked at.
- **Translate after loading.** "Keep the data original" holds either way, since the loader never
  writes back. The reasons are that the tests swap the loader for world-clock fakes, and that
  cutting before translating is the order reality has. The danger was framed as a neighbour
  going missing. It is the reverse: a future neighbour already averaged in before the cut.
- **MLflow.** Both questions misremembered as timing and cost. Deferred on *could a run be
  lost?*, adopted on *can runs be compared side by side?* `scores.csv` stays the record because
  it is in git, not because it is easier to read.
- **Refitting.** Answered "every year wins for the tree, the recent window for the line, try
  both". Every year wins for both: tree 0.440 against 0.442, line 0.525 against 0.709. Third
  session running. The pull is the field's default and the "crisis distorts" story, both of
  which lose to this project's own measurement.

#### Piece 2 — the grid wired in (`406b9b0`, `7f10d59`)

**The split went first, on its own** (`406b9b0`). Eight test references to the removed `*_UTC`
constants were rewritten as boundary hours spelled out in full rather than read back from
`split()`, so they cannot agree with a mistake there. Planting yesterday's mutation (cut at UTC
midnight) turned eight tests red. The cut falls on the same rows as before, so no number moved.

**Then the features** (`7f10d59`). `data.to_slots()` is called where `features.py` loads each
series, not inside `data_load()`, because the tests replace `data_load()` and would otherwise skip
the grid. Lags now mean the same Berlin hour on the day before, including across a clock change,
and a test pins that on 1 April. The leak test runs for 20 March and 1 April 2024. A spring fill
reaching 25 rows ahead (into day D) failed 1 April and passed 20 March, which is the intended
result. CLAUDE.md names the grid as the one exception to "no naive timestamps".

**Found while moving the tests:** `BLANK_TRAIN not in train.index` would have passed whatever
happened. A UTC timestamp is never `in` a naive index (checked: `False` for an hour that is
there). The check now uses the grid label and also requires the hour before to be present.

#### 2023 on the grid — a prediction that missed, and why

| | rMAE before | rMAE on the grid |
|---|---|---|
| linear | 0.532 | 0.532 |
| gbm | 0.488 | **0.483** |

Predicted beforehand: a change in the third decimal. Right for the line, wrong for the tree.
The old and new code were run side by side to find out where the 0.005 came from:

- **4 % of training rows changed, not "two days a year".** The 168-hour lag carries a clock
  change through the following week, so each of the nine changes in 2018–22 touches about eight
  days, 1,448 rows across 70 days. My estimate forgot the longest lag.
- **On the 8,040 validation hours away from any clock change**, the actual prices and the
  benchmark are identical, the line's forecasts differ by 0.02 EUR/MWh on average, and the
  tree's differ by **4.8 EUR/MWh**, in every hour. Its rMAE on just those hours moves
  0.499 → 0.494.

So the tree's gain is not the grid helping. It is the tree landing differently after 4 % of its
training rows changed. **A tree score can move about 0.005 from a small change in its data.**
That is a calibration for stage 2: tree variants closer than this are not distinguishable by
rMAE alone, which is one more reason Diebold-Mariano comes before any second model. It also
fits the measured tie between keeping every year and keeping two (0.440 against 0.442).

**Comparability.** Earlier 2023 rows (`90e57fb`) are on the old convention, and the new ones are
on the grid. Stage 2 compares only against grid rows. The held-back years were not re-run. The
stage 1 headline 0.532 stands as recorded, on the old convention.


#### Stage 2 reordered: the significance test before recalibration

The 0.005 above changes what the first stage 2 comparison can show. Monthly against daily
refitting is expected to differ by little, and a tree can move that much from 4 % changed rows.
So the order is **MLflow → Diebold-Mariano → recalibration**, not recalibration first. MLflow
stays first because the test needs every hour's forecast, which is what MLflow keeps. The
alternative of building the test on in-memory forecasts and adding MLflow later was declined.

---

#### MLflow begun

Decided: its calls live in a new `src/tracking.py`. A `track()` beside `record()` in `train.py`
was recommended instead, on the precedent of `final_score.py` borrowing `record()` and on there
being one caller. Overruled in favour of a module from the start.

Checked rather than assumed: MLflow 3.16.1 now stores runs in a SQLite file, `mlflow.db`, in
whatever folder it starts from, and older guides mention only `mlruns/`. Both paths are now
fixed from the project root in `config.py`, and `mlflow.db` is ignored. A dry run showed no
pinned package would change. MLflow brings about 60 packages of its own.

**Step 2 done** (`01eeda2`): `run()` hands back the hourly forecasts beside the scores. A new
test rescores each column of that table and requires the exact rMAE of the score rows. Adding
0.01 to the kept forecast after scoring failed it.

**State at close.** `requirements.txt`, `.gitignore` and `src/config.py` hold step 1 (the pin,
the ignore rule, the two paths), **uncommitted on purpose**: the pin goes in with the first
import, which is `src/tracking.py`. `main` is green at `01eeda2`, 163 tests.

---

<a id="d20261007"></a>
### 7 October 2026

**Recap (questions 1–2):** 1 half right: the lesson "keep every year" was right, but which model won was wrong for the fourth time (every year wins for both). 2 the plan change was right, but "we don't know where the 0.005 came from" was wrong: it was measured side by side.

#### MLflow finished (`29023c8`)

`src/tracking.py` writes one run per scored forecast, the benchmark included, and reads a run
back. Two choices were walked through first. **An explicit client per call** rather than the
global `set_tracking_uri`, so a test pointed at a temporary folder cannot leave later code
writing there. **Each run keeps actual, benchmark and its own forecast**, the three columns its
rMAE comes from, rather than its own column only, so one run proves its own score without a join.
The convention is written by `tracking.py` from a constant, not passed in, so no run can be
stored without it.

Asked why SQLite rather than MLflow's "native" folder format, and checked rather than answered
from memory: 3.16.1 reports `sqlite:///…/mlflow.db` as its default, and asked for the folder
store it **raises an error** ("maintenance mode … migrate to a database backend"). The folder
`mlruns/` still holds the files; the database holds the index.

**Tests** (`tests/test_tracking.py`, 4) log once into a temporary folder and read back. Removing
the convention from the stored params failed one; storing only the model's own column failed two.
Suite 167 green.

**Baseline**, `just train` at `29023c8`: naive 1.000, linear **0.532**, gbm **0.483**, identical to
`7f10d59` to the last digit. Recomputed in a fresh process from the forecasts **read back out of
MLflow**, found by their commit param: 0.531806 and 0.482824, matching the stored metrics, 8,759
naive grid hours each. The README's `mlflow ui --backend-store-uri sqlite:///mlflow.db` was started
and served all three runs.

Leakage check: no feature changed, nothing fitted, and the actual prices MLflow stores beside the
forecasts are read by nothing on the decision path.

Not done: a run logged from a working tree with uncommitted changes is stamped with the last
commit, the same as `scores.csv` has always been. Not observed to matter; noted, not guarded.

#### Diebold-Mariano (`1d90457`)

`E.dm(first, second, actual, lags=7)` returns a one-sided p-value that `second` is more accurate.
The field's reference was read before anything was proposed: epftoolbox's `DM`, multivariate
version, norm 1. It collapses each day to one number (the first's average miss minus the
second's) and tests those days with a plain spread. Days rather than hours because the hourly
gaps echo strongly (0.79 one hour apart in 2023): all 24 are forecast at once.

**One departure, chosen by the measurement.** The daily gaps between line and tree in 2023 echo
too: 0.25 one day apart, 0.11 at two, gone by four. epftoolbox assumes none, which makes it too
confident. Options were the field's version exactly, with the echo as a stated limit, or the
field's version plus a one-week correction (*Newey-West*, fading weights). **The second was
chosen.** On 2023 the correction widens the spread ×1.31: a plain p of 0.02 becomes 0.058. That is
the difference between "real" and "cannot tell" for exactly the close calls stage 2 will make.
`lags=0` reproduces epftoolbox.

No dependency added: the normal tail is `math.erfc`, so scipy stays out of `requirements.txt`.

**Tests** (4): with `lags=0`, it matches epftoolbox's code transcribed line for line, with the normal
curve from `statistics` rather than `erfc`; a three-day case worked out on paper (p at statistic
6); direction; and streaky weeks giving a weaker verdict than scattered days. Five planted
mutations each turned at least one red: hours instead of days, echo counted once, no fading weight,
direction flipped, correction never run. The "more cautious" test first failed on its own fixture.
Uncentred weekly shifts made the second forecast worse on average, so p sat near 1, and the
correction pulled it *down* toward 0.5. Cautious means *toward cannot tell*, from either side.
Suite 171 green.

Leakage check: evaluation only. No feature, nothing fitted, and settlement is untouched.
Nothing calls `dm` yet, so no reported number moved.

Also today: `c773fa7` fixed the stale Contract 5 comment (joined on the grid, not in UTC).
`d991a08` moved the README's MLflow UI command to port 5001: on macOS, AirPlay holds 5000, and
`localhost:5000` answered 403 while `127.0.0.1:5000` reached MLflow.

#### MLflow moved to `reports/mlflow/` (`76f15f8`)

The database and run files sat in the project root, beside things people read and edit. They are
machine output, so they now sit beside `scores.csv`. Not named `mlflow/` at the root, which would
share a name with the package on the import path.

**Asked for: hide the full path, username included. Not possible inside MLflow, and checked.**
MLflow stores every run's file location as a full machine path. A plain relative path, `./…` and
`file:…` were each turned into one, and its built-in Default experiment does the same on its own.
Keeping the forecasts outside MLflow's storage would leave the experiment's own location string
behind, so it would not achieve it either. What protects the path is where it lives: the whole
folder is ignored by git (`reports/mlflow/`, with the reason beside the rule), and the UI answers
only on this machine. Checked: no tracked file and no commit in the history contains the home path.

The move orphaned the three runs from `29023c8`, because their stored links pointed at the old
folder. They were deleted and regenerated: `just train` at `76f15f8` gave 0.532 and 0.483 again,
and the same figures were recomputed from the forecasts read back from the new location. The README's
UI command was updated and served all three runs. `scores.csv` gains three identical rows. That
is a third reproduction, not a new result. The same orphaning would follow a rename of the project folder.

#### Recalibration built and measured (`bb7501a`)

Explained first in plain terms, and two confusions cleared that are worth keeping. **Hourly is the
size of a row, monthly/daily is how often the model is retrained.** And **walking forward does not
break the split**: each period is forecast before it joins the training rows, so every score is
still earned on unseen hours. Validation becomes *never seen before it is forecast*, not *never
seen*. Test years stay locked, and all choices are made on 2023.

**Timing measured instead of run.** One tree fit on 36,335 rows took 0.49 s and one line fit under
0.01 s. That made daily retraining an estimated 3–4 minutes, and the timing step was dropped from the
plan. Actual daily run: **233 s**.

**`M.walk_forward(make, history, scored, every)`.** For each period of 2023 it fits a fresh model on
every hour strictly before the period starts, then forecasts it. `every` is a pandas period: `"Y"`
once, `"M"` monthly, `"D"` daily. "Once" is the same loop with one period, so the stage 1 recipe runs
through the new path. The schedule is a flag (`just train daily`) rather than all three per run,
so one run is one recipe in `scores.csv` and MLflow, and `just train` alone is unchanged.

**Tests** (4, with a spy model that records the hours it was shown): never learns from the period it
forecasts, but learns everything up to one hour before it, from the very first hour. Also one fit per
period, every hour forecast exactly once, and "Y" equal to the single fit. Four planted bugs each
failed two tests: learning the first forecast hour, learning the whole period, learning from
everything, and keeping only the last 14 days. Suite 175 green.

Leakage check: for day D the model learns up to D−1 23:00, and those prices were published around 13:00 on
D−2. Nothing is fitted outside those rows. Settlement is untouched.

| 2023, walk-forward, every year kept | line | tree |
|---|---|---|
| once | 0.532 | 0.483 |
| monthly | 0.525 | 0.437 |
| daily | **0.523** | **0.430** |

| Diebold-Mariano, read from MLflow | line p | tree p |
|---|---|---|
| once → monthly | 0.0001 | < 0.0001 |
| monthly → daily | 0.0012 | **0.11** (0.08 without the echo correction) |
| once → daily | 0.0001 | < 0.0001 |

**The size of a gain and its reality are different things.** The line's 0.002 from monthly to daily
is real. The tree's 0.007 is not distinguishable from noise. The line moves smoothly and steadily, so
a small lead repeats day after day. The tree's daily gaps wobble more, which is the instability seen
on 6 October. Monthly on the grid (0.437) sits close to the pre-grid 0.440.

Once fitted, "once" reproduced 0.532 and 0.483 exactly through the new loop.

#### LEAR introduced, not built

LEAR was introduced in plain terms, after reading epftoolbox's `_lear.py` rather than recalling it.
Confirmed there: 24 Lasso models, one per delivery hour. The inputs are all 24 prices of D−1, D−2,
D−3 and D−7 (96), each exogenous series for D, D−1 and D−7 (72 each), and 7 weekday dummies. The
asinh-median transformation is fitted on the training window. Alpha comes from `LassoLarsIC(criterion='aic')`,
then a plain `Lasso` is refitted with it. Daily recalibration on a 1,092-day window. **Not confirmed in
the code:** the paper's ensemble over several calibration windows. Check it in Lago et al. 2021
before relying on it. No new dependency is needed, because sklearn has both estimators.

Also today: the walkthrough covered `walk_forward` and its use in `train.py`, including why `make`
is passed without brackets. `history` in `main()` was renamed `recorded` (`6eecab1`). The tests'
walkthrough was skipped by choice.

**State at close.** `main` is green at `6eecab1`, 175 tests, working tree clean. MLflow holds
the once, monthly and daily runs of `bb7501a` in `reports/mlflow/`.

#### Both plan pages brought up to date, the plan re-dated

Asked at close whether the two pages were current. They were not. The old page (18 September)
is archived on purpose, but **said so nowhere on the page**, so a reader saw "Now in stage 0".
It now opens with a banner naming it a snapshot and linking the current plan, and nothing else on it
changed. The current page was a week behind. It now shows stage 2 under way, the grid, MLflow,
the significance test and walk-forward retraining built, the walk-forward results with their DM
verdicts, and 175 tests. The README was updated first, because it is canonical (`6fe2672`).

**Dates re-estimated, not dropped,** from what the stages took: seven, six and so far four working
days at about three and a half a week. Stage 2 runs about a week long, because the grid, MLflow and the
significance test went in front of recalibration. Stage 2 ends around the week of 19 October and stage 5
around the week of 16 November.

**The ENTSO-E API answers again** (HTTP 401 without a token, 7 October). That reopens open item 10
(the autumn clock-change hour), which can now be checked with a fresh request. Not done today.

<a id="d20261008"></a>
### 8 October 2026

**Recap (questions 1, 2, 4):** 1 half right: every year wins for both, but the big drop was put on the tree, not the line (0.709), for the fifth time. 2 half right: days because the 24 hours miss together, but the echo correction (×1.31, p 0.02 → 0.058) was missing. 4 not remembered: the line's 0.002 is real (p 0.0012), the tree's 0.007 is not (p 0.11).

**LEAR, one fit timed.** Real data, epftoolbox's recipe (`LassoLarsIC` then `Lasso`), one core: one delivery hour 0.15–0.26 s, a day of 24 fits 3–6 s, so a daily refit through 2023 runs **about 20 min** with 247 columns (load + wind/solar summed) and **about 37 min** with 391 (four separate series). Window length barely matters; width does.

**Open item 12 opened:** the wind/solar forecast's legal deadline is 18:00 on D−1, after gate closure. Stated as a limit, not fixed.

---

### Next — Thursday 8 October 2026

**Start at LEAR. Nothing is uncommitted.** Open item 10 is unblocked (the API answers again), and is a short check whenever it fits.

#### Recap questions

1. *(Fifth time.)* Refitting monthly: keeping every year or only the last two, which won for
   each model, and by how much?
2. Why does the significance test count days rather than hours, and what does the echo
   correction change? Give the 2023 numbers.
3. Refitting daily through 2023 trains on validation rows. Why does that not break the split,
   and what has to stay locked?
4. Monthly → daily moved the line by 0.002 and the tree by 0.007. Which gain is real, and why
   can the smaller one be the real one?
5. Why does `train.py` pass `M.linear` to `walk_forward` and not `M.linear()`?

#### Then, in order

1. **LEAR**, one decision at a time:
   - **Time one fit first:** a daily run is about 17,500 small fits.
   - **Training window:** the field's 1,092 days against every year, measured, since every year
     won for both of our models.
   - **The table's shape:** one row per day with the 24 hours side by side. This brings in the
     per-hour layout. It is the largest piece, so walk it through before writing.
   - Judged against the daily line and tree with Diebold-Mariano.
2. **German public holidays**, which are not in the feature frame.
