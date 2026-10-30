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
| [8 Oct 2026](#d20261008) | Recap: two half right, one forgotten; the refitting numbers swapped for the fifth time. **One LEAR fit timed:** a daily run over 2023 is 20–37 min. **Open item 12:** the wind/solar forecast's legal deadline is after gate closure, stated as a limit. **Open item 10 answered:** the autumn hour is missing from the publication itself. LEAR's day table walked through; the price rule written in whole days. Nothing built. |
| [10 Oct 2026](#d20261010) | Recap: two right, two half right, one not known (the autumn hour); the refitting question finally right. **LEAR's table decided, decisions 2–4:** built in `features.py` and scored on shared hours; the field's two forecast series; the autumn midnight hour filled for every model. The fill walked through as code, not written. Nothing built. |
| [13 Oct 2026](#d20261013) | Recap: AIC re-explained with 20 random columns, which it keeps at tiny weights, correcting 12 October. **LEAR built and measured** (pieces 3 and 4): **0.429, a tie with the daily tree** (DM p 0.50), better at night, worse through solar hours. Checked for hindsight on real data. **Cross-checked against epftoolbox's own LEAR:** one rounded constant was the only difference; fixed, now equal to 1e-10. Convergence warnings silenced, as epftoolbox does. |

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

    **8 October — checked against a fresh request; the A03 guess was wrong.** The raw XML for
    26–27 October 2024 (read only, cache untouched) splits each series into one `Period` per day.
    The 26th ends at 22:00 UTC and the 27th starts at **23:00 UTC**, which is midnight in winter time,
    so the first hour of the clock-change day falls between the two and is in neither. This holds
    for load, onshore wind and solar. Offshore wind comes as one continuous `Period` and has the hour.
    A03 compression is real but harmless: solar at night sends 48 of 96 positions, and entsoe-py
    fills them, which is why the cache has no solar gaps. So the 28 September conclusion stands
    (absent from the publication), and the mechanism is the publisher's day boundary, not ours.
    Checked for 2024 only. **It now matters more:** on LEAR's one-row-per-day table, one missing
    hour empties a whole day, and through the D−1 and D−7 inputs, two more (29 and 30 October and
    5 November 2023). Fill or drop is decision 4 of LEAR's table.

    **10 October — decided: fill**, with the mean of its neighbours, for every model (see 10 October).
    The hole exists in 2023, 2024 and 2025 only; 2019–22 publish the hour.

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

**LEAR's table walked through, not built.** One row per delivery day: the 24 prices of D as targets, and as inputs
all 24 hours of the prices of D−1, D−2, D−3 and D−7, the forecasts for D, D−1 and D−7, and the weekday. Shown on
15 March 2023 against today's one-row-per-hour layout. Same numbers, laid out differently: the 18:00 model can
now see every hour of earlier days, not only 18:00. Four decisions follow from it. **Decision 1 taken: the price
rule is written in whole days** (inputs move back at least one day), with its own check beside
`MIN_PRICE_LAG_HOURS` and the leak test run on the day table too. For delivery hour 00:00, D−1 at 23:00 is one
hour earlier but was published around 13:00 on D−2. CLAUDE.md's rule is *prices of days ≤ D−1*, and the 24
hours was the hourly table's way of enforcing it. The existing `price_d1_last` already uses this form. Rejected:
keeping 24 hours per hour-model, which is stricter than the boundary, gives the 24 models different inputs and
is no longer the field's LEAR.

**Open item 10 checked** (above): the hour is absent from the publication because the operators start the
clock-change day at midnight winter time. The A03 guess was wrong.

<a id="d20261010"></a>
### 10 October 2026

**Recap (all five):** 1 right at last: the line lurches, the tree ties; numbers dropped from this question by request. 2 half right: what a daily run is and ~20 min, but not that the backtest repeats a 3–6 s morning 365 times. 3 right. 4 half right: comparisons fair, but not why every score's level is in question. 5 not known: the publishers' day blocks start at midnight winter time, and one row per day turns one hour into three days.

**LEAR's table, decision 2 taken: built in `features.py`, scored on shared hours.** The day table is a new function
beside `build()`, so one file still answers "was this public by 12:00 on D−1?" and the leak test runs on it directly.
Rejected: building it inside the model, as epftoolbox's LEAR does, which would guard the rule in two files. LEAR's
day × 24 forecasts are unfolded back to hour labels (date of the row + hour of the column; nothing computed), and
all three models are scored on the hours every one covers, `train.py`'s existing rule. Shown on 14–15 March 2023:
48 real prices folded and unfolded came back identical. Works only because every day has 24 slots. Leaning for
decision 4: fill the hour. With it, LEAR covers 8,760 hours, the shared set stays 8,759, and no recorded score moves.

**Decision 3 taken: the field's two forecast series**, load and wind plus solar summed (247 inputs, ~20 min a daily
run). Shown on 15 March 2023: load flat across 07:00, 13:00 and 19:00, price 160 → 91 → 199, and the sum alone carries
the swing (21.8, 40.0, 16.5 GW). Rejected for now: our four separate series (391 inputs, ~37 min). Splitting is a
second change on top of the method, so it is left as a later measured variant rather than mixed into the first LEAR.

**Decision 4 taken: the autumn midnight hour is filled, for every model**, with the mean of its two neighbours (the
grid's spring rule; 29 Oct 2023: load 40,116, wind plus solar 24,411). Both neighbours are forecasts published on D−1,
so nothing leaks. Found while checking: the hole exists only in 2023–25, not in the 2019–22 training years, so three
rows change in the whole history. Filled in `features.py` where the forecasts load, not in LEAR's table alone, so one
table holds one answer per hour. Cost: line and tree gain an hour (8,760 in 2023) and their daily scores are re-run
once as new rows; the old 8,759-hour rows are a different exam. Rejected: LEAR-only filling, which leaves two tables
disagreeing and is dropped again by shared-hours scoring. Separately, 2022 has two whole blank days (22 Feb, 24 Mar),
skipped by every model as now.

---

**State at close.** `main` at `dcb5143`, no code changed today, working tree clean. The plan page was not
refreshed: no step was built or measured, and the decisions sit inside the existing LEAR step.

---

<a id="d20261012"></a>
### 12 October 2026

**Recap (all five):** 1 wrong for the second time: spring's never-happening hour was given, not autumn's forecast hour that falls between two publishing blocks; the three days roughly right. 2 half right: two dimensions yes, but not that unfolding only gives the cell its label back, and the 18:00 model was put back to seeing 18:00 only. 3 half right: speed, but not *one change at a time*. 4 mostly right, except old rows are kept as a different exam, not thrown away. 5 not remembered and judged minor; retired from the recap.

#### Piece 1 — the autumn midnight filled (`efd0a3b`)

`fill_autumn_midnight` in `features.py`, called on load and wind/solar right after `data.to_slots`, as
walked through on 10 October. Three tests on a grid frame of 26–28 October 2024, each checked by planting
its bug, each bug failing exactly its own test: a fill from the hour before only; the general rule (any
blank hour); overwriting a published value. Suite 178 green.

**On real data it fills 8 cells, not 9.** Load 2023 and 2024 (29 Oct 2023: 40,116 as predicted), onshore
wind and solar in all three years. The **2025 load forecast has its autumn midnight** (42,213, published),
so it was left alone, which is the case the third test guards. Offshore untouched in every year.

Leakage check: the fill averages the 23:00 forecast for D−1 and the 01:00 forecast for D, both published
before gate closure; nothing fitted; settlement untouched. The leak test passes unchanged.

**`just train daily` once, a new exam** (213 s). Same recipe as `bb7501a`, one more hour:

| 2023, daily walk-forward | hours | line | tree |
|---|---|---|---|
| `bb7501a` (old exam) | 8,759 | 0.5233 | 0.4299 |
| `efd0a3b` (new exam) | **8,760** | **0.5233** | **0.4294** |

Nothing moved that matters, as predicted. The old rows stay in `scores.csv`, told apart by the `n` column.
**All three re-run on the new exam, by decision**, so the README matches what the commands produce (`f0d17ba`):
once 0.532 / 0.483, monthly 0.525 / **0.440** (was 0.437), daily 0.523 / 0.429, line / tree. Once is identical,
because no training row before 2023 changed. Diebold-Mariano re-read from MLflow: every step is real, and the
tree's monthly → daily **flips from 0.11 to 0.028**. Daily did not improve; monthly got worse. January–October are
identical to the hour; every November and December forecast moved (MAE +0.64, +0.59), because those two refits
gained one training row, 29 Oct 00:00. Guessed cause, the tree's 10 % early-stopping hold-back being redrawn,
**checked and mostly wrong**: with it off, the one row still moves November by 2.64 €/MWh on average. The tree is
that sensitive to its data, as on 6 October; why exactly was not chased. The README states the verdict as fragile.
Plan page refreshed to 12 October: 8,760 hours, the fragile verdict, 178 tests, the autumn-hour note closed.

**Third Law gap noticed, not fixed:** the README's p-values are read from MLflow by hand, not by a documented command.

---

#### Piece 2 — the day table (`2e0272f`)

Walked through first on 15 March 2023 (a Wednesday), then shown as four real rows, 13–16 March: each row one
delivery day, columns named *what, which day, which hour* (`price_d1_h18`). Monday's `price_d0` reappears as
Tuesday's `price_d1`, one row down. 271 columns: 24 answers, 96 price clues, 144 forecast clues (load and wind
plus solar summed, for D, D−1, D−7), 7 weekday columns. 2,649 days; all 365 of 2023 complete, thanks to piece 1.

`fold`, `unfold`, `day_table`, `day_answer_columns`, `day_feature_columns` in `features.py`, plus
`MIN_PRICE_LAG_DAYS = 1` with its own assert beside `MIN_PRICE_LAG_HOURS`. Nothing calls it yet.

**A claim of mine corrected twice, by a question.** I proposed a `reindex(days)` "so a missing day can't turn
`shift(1)` into the day before last", and a test planted by removing it. Asked whether the test would catch
that, I ran it: it would not, because `to_slots` already returns every day, blank ones as 24 blank hours. So the
line was dropped from the plan. Writing the code then showed **a reindex is needed after all, for another
reason**: at gate closure prices stop at D−1 and forecasts reach D, so without stretching the price table onto
one shared run of days, day D has no row to receive yesterday into and its clues come out blank. The leak test
catches that.

**Tests** (4, suite 182 green), each bug planted:

| Planted bug | Caught by |
|---|---|
| unfold puts values at the wrong time | round trip |
| "today's" forecast is really tomorrow's | leak test, both days |
| price not stretched to day D | leak test, both days |
| blank hours dropped before folding | **nothing**: the stretch puts the day back |
| that and no stretch | leak test and missing-day test |

So the missing-day test guards the outcome ("tomorrow's yesterday is blank"), which two lines each provide; it
cannot be shown failing by removing one. Kept by decision. The round trip first failed for a real reason: the
fixture starts and ends on part days, and folding pads them with blank cells, so the test now says only blanks
were added.

Leakage check: prices from whole earlier days only (assert and leak test); forecasts for D, D−1, D−7, public
at gate closure; nothing fitted; settlement untouched.

#### Calibration windows read: the first LEAR is single, 1,092 days

Read before the walkthrough, as the 7 October note asked. **epftoolbox's `_lear.py`:** one window, default
`364 * 3` = 1,092 days, no averaging over windows anywhere. **Lago et al. 2021, §4.2:** LEAR recalibrated daily
on four windows, 8 weeks, 12 weeks, 3 and 4 years. **§4.4:** their plain average is offered "as open-access
benchmarks of ensembles methods", i.e. the yardstick for methods that average, not for single models.
**Not read:** the paper's tables comparing the average with single windows; the HTML stops before them and
the PDF could not be parsed here without a new tool. A later paper on DE 2022–May 2023 (arXiv 2311.02610)
used 56/84/364/728 days because its data starts in 2019; the longest did best (rMAE 0.40 against 0.42–0.44),
on a different period and setup, so only the direction carries over.

**Decision: a single LEAR on 1,092 days first.** Line and tree are single models, so the fair opponent is a
single LEAR; averaging four would add a second change and about four times the run (~80 min). Every year
against 1,092 days stays the measured second run. Rejected for now: the four-window average (a later variant,
not built), and every year first (departs from the field's LEAR on the first run).

---

#### LEAR walked through, not built: three ideas on the 18:00 model of 15 March 2023

Shown with a scratch fit on the 1,092 days before 15 March, outside the repository. The recipe was read in
epftoolbox first: `InvariantScaler` is the median, statsmodels' `mad` (divided by 0.6745) and `arcsinh`, on prices
and on every column except the 7 weekday dummies; then `LassoLarsIC(criterion='aic', max_iter=2500)` for alpha
and `Lasso(max_iter=2500, alpha=...)` refitted. statsmodels is not needed: median and MAD are two numpy lines.

1. **Lasso, a line that pays for every clue it uses.** Of 247 clues it kept 128, every kind somewhere, six of
   seven weekdays. Forecast 167.3 against 182.3 actual, one day so it means nothing. Warned against reading
   single weights: the largest were load at 11:00 and the price two days ago at 09:00, because neighbouring
   hours move together and one stands in for a group. Landed first time.
2. **Same scale, then squash.** Load is in tens of thousands of MW, price in hundreds of euros, and the cost is
   per unit of weight, so scaling makes it fair. Median 105.5 and spread 100.1 against mean 160.7 and std 144.0;
   29 August 2022 at 837.7 goes from 7.31 spreads to 2.69 after asinh. Asked whether this is "scaling as feature
   engineering": steps 0–1 are scaling (the robust kind), asinh is a transformation that changes the shape, and
   both are preprocessing rather than feature engineering, which adds information. Our line and tree never
   needed it: the tree splits on order, the plain line just rescales its weights. The cost is what makes it matter.
3. **AIC chooses the cost.** 391 steps on the path from 0 clues to 246; lowest AIC at 124 clues. **Did not land
   the first time**, explained with "fit term", "fixed charge" and a trade-off. **Re-explained** as each clue
   paying a 2-point fee to join: the first clue saved about 16,600 points, while the last 122 clues cost 244
   and saved only 152, most likely luck. Whether that version landed is not yet known; the session closed on it.

The path keeps 124 clues and the refitted `Lasso` 128 at the same alpha. The paper does not say why epftoolbox
refits, and no reason was guessed.

---

**State at close.** `main` at `fcd5948`, suite 182 green, working tree clean. The day table is built; LEAR is
explained, not written. README and plan page refreshed at close (day table built, one window, 182 tests).

---

<a id="d20261013"></a>
### 13 October 2026

**Recap (all five):** 1 half right for the third time: spring right, but load *does* lose 00:00 on 27 Oct 2024 (only offshore and the price keep it), and the why (day blocks start at midnight winter time) not remembered. 2 wrong: the Nov–Dec change was checked to be the new 29 Oct hour, not volatility; verdict fragile, p 0.11 → 0.028. 3 half right: Monday's price, but set in Sunday's auction; the stretch's purpose (no Tuesday row to receive Monday) missed. 4 half right: Lasso cuts clues, not values; the charge is per unit of weight. 5 named, not explained; re-explained with 20 random columns, which **corrected my 12 October claim**: AIC kept 17–20 of 20 random columns at 03:00, 08:00 and 18:00 over five seeds, with weights ~0.004 against ~0.09 for real clues (BIC 0–13). AIC picks for forecast quality, not for true clues. Recipe unchanged; BIC a possible later variant.

---

#### Piece 3 — LEAR in `models.py` (`3081fec`)

Walked through first, in a scratch copy, then written. epftoolbox's source read today rather than recalled:
the ruler is per column (`np.median(axis=0)`, statsmodels `mad` = MAD / 0.6745), for clues and for the 24
answers alike, then asinh; the last 7 columns (weekdays) unscaled; the window is `iloc[-1092 * 24:]` on a
gapless frame. `robust_ruler`, `LEAR` (fit / predict, 24 models in a dict) and `lear_walk_forward`, beside
`walk_forward` rather than inside it, because that one reads hourly rows and has no window.

**Decision 5b taken: the window counts complete days**, as epftoolbox's `iloc` counts rows: every fit sees
1,092 days and the blank days of 2022 push the start back 6 days. Rejected: calendar days (1,086 usable).

**Tests** (4, five cases), each bug planted in a scratch copy:

| Planted bug | Caught by |
|---|---|
| window includes day D | window spy, deleting the future |
| no window / window one day too long | window spy only (no future used, so not a leak) |
| window from the end of the table | window spy, deleting the future |
| no unsquash / 00:00's ruler for every hour / hour labels one off | wiring (rMAE 0.144 against a 0.5 limit) |
| mean and std instead of median and MAD | ruler |
| ruler measured on every complete day | deleting the future |
| weekdays squashed / forecast day read with its own ruler | **crash**, "Input X contains NaN": spread 0. Loud, so no test |
| my first whole-table-ruler plant | **nothing**: it computed a ruler and never used it. Faulty plant, replaced |

#### Piece 4 — `train.py` (`c177c07`)

**Decision taken: LEAR joins `just train daily` only**, because daily refitting is its recipe (run 1,280 s).
Rejected: its own switch. Scoring moved after all fitting, with `forecasts.dropna()` as the shared-hours rule;
trimming before fitting would remove hours from later refits too. `day_rows()` drops the test years from the
day table with `cfg.split`, as `data()` does; `lear_days` keeps the days whose 247 clues are present. Three
tests with a stand-in LEAR, each planted: own-hours scoring and asking for blank-clue days fail the
same-hours test; trimming before fitting fails *adding LEAR changes no other forecast* (monthly); the whole
table fails *never handed a test-year day*. Suite 190 green.

Leakage check: no feature changed; LEAR sees `day_feature_columns` only, its ruler and models fitted on the
window strictly before D; the day table split by `cfg.split`; settlement untouched.

#### LEAR on 2023: a tie with the tree, checked before believed

| 2023, daily walk-forward (`c177c07`) | hours | MAE | rMAE |
|---|---|---|---|
| naive | 8,760 | 33.65 | 1.000 |
| line | 8,760 | 17.61 | 0.523 |
| tree | 8,760 | 14.45 | 0.429 |
| **LEAR** | 8,760 | **14.44** | **0.429** |

Line and tree identical to `efd0a3b`, as the new test says they must be. Diebold-Mariano (read from MLflow
by hand, the Third Law gap of 12 October): LEAR against tree p 0.496 / 0.504, cannot tell; LEAR better than
the line, p 4.5e-08.

**Hindsight, four checks, none fired.** (1) Four real days (2 Jan, 15 Mar, 29 Oct, 24 Dec) rebuilt from the
cache cut at gate closure: forecasts identical to the bit, every window 1,092 days ending D−1. (2) Not
suspiciously good: closer than the tree on 49.6 % of hours. (3) Uneven, as a leak would not be: LEAR wins at
night (00:00 8.2 against 11.6 €/MWh), loses through the solar hours (14:00 19.5 against 17.1); worst misses
2 July 13–15:00 and 11 September 19–20:00, the days hindsight would fix. (4) Slightly worse than published, not
better. Like for like: arXiv 2311.02610 uses *our* benchmark (the price 7 days earlier) and gets LEAR 0.40
(728 days) and 0.43 (all data) on DE 2022–May 2023; ours is 0.429 on 2023. Lago et al. 2021 use the field's
naive (yesterday Tue–Fri, last week Sat–Mon, checked in epftoolbox's `_rmae.py`) and get LEAR-1092 0.431 on
DE 2016–17; ours under that rule is 0.505. *Corrected the same day:* first written as 0.505 against 0.40,
which mixed the two benchmark rules.

**3,186 of 8,760 refits stop before converging** at epftoolbox's `max_iter=2500` (gap up to 122× the
tolerance). Eight days rerun at 100,000 steps: forecasts move 0.09 €/MWh on average, 1.69 at most; MAE on
those days 31.26 → 31.23. Kept as the field's recipe; the warnings flood the run's output (1.4 MB).
One day rerun at 2,500 reproduces the recorded forecast exactly.

README and plan page refreshed (LEAR done, 190 tests, about four working days left in stage 2).

---

**State at close.** `main` after this entry's commit, suite 190 green.

---

#### Questions after the result: the literature, capture rate, and which model orders hours

**Published scores, like for like** (corrects the hindsight note above): arXiv 2311.02610 divides by the 7-day
price, as we do: LEAR 0.40–0.43, DNN 0.36, adaptive scaling 0.34–0.36 (DE 2022–May 2023). Lago et al. 2021
divide by the field's mixed rule: LEAR-1092 0.431, LEAR ensemble 0.395, DNN ensemble 0.374 (DE 2016–17).
**No public capture-rate benchmark** exists in epftoolbox's sense; German BESS studies each pick their own
battery and years (search summaries only, papers not read). XGBoost not tried: the tree is the same family.

**Which orders the hours better** (a rough stand-in, not a backtest: no efficiency, no state of charge):

| 2023 | rank agreement within a day | spread kept, 2 cheapest vs 2 dearest by forecast |
|---|---|---|
| naive | 0.752 | 78.5 % |
| line | 0.896 | 92.4 % |
| tree | 0.911 | 92.8 % |
| LEAR | 0.891 | 92.5 % |
| tree + LEAR averaged | 0.918 | 94.6 % |

Decided with the user: no tuning chase; move towards stages 3 and 4.

#### LEAR against epftoolbox's own code (one-off, outside the repo)

Decided: a one-off rather than a committed script, because `requirements.txt` cannot install epftoolbox
without TensorFlow (~500 MB) and it is AGPL. Commands, so it can be repeated:

```bash
pip install --target <scratch>/epf --no-deps \
  "git+https://github.com/jeslago/epftoolbox@47d6e0629f65ebd19d3c12cb5689dbad0c2ea078" statsmodels patsy
```

```python
# load _lear.py by file path, skipping models/__init__ (which imports TensorFlow)
spec = importlib.util.spec_from_file_location("epf_lear", f"{EPF}/epftoolbox/models/_lear.py")
table = T.day_rows(); clues, answers = F.day_feature_columns(table), F.day_answer_columns(table)
for day in pd.date_range("2023-01-09", "2023-12-31", freq="38D"):       # all seven weekdays
    known = table.dropna()[lambda t: t.index < day].iloc[-1092:]
    ours = M.LEAR().fit(known[clues], known[answers]).predict(table.loc[[day], clues])
    epf_model.recalibrate(known[clues].to_numpy().copy(), known[answers].to_numpy().copy())
    # their predict, line for line, except models[h].predict(X)[0]: NumPy 2.4 refuses array-into-scalar
```

Same inputs to both, so this tests the machinery (ruler, AIC, refit, 24 models, back to €/MWh), not the
inputs and not the information boundary. **First result: up to 0.0012 €/MWh apart**, different clues kept
on 2 of 11 days. Cause found and checked: statsmodels' `mad` divides by `Gaussian.ppf(3/4)` =
0.6744897501960817, ours by 0.6745. **With the exact constant: 1e-10 €/MWh apart**, same clues on all ten
days (`4cfc6b4`). Not bit-identical because the two do their sums in a different order. A new test pins
the constant; planting 0.6745 fails it. My first test days were all Mondays (35-day steps); changed to 38.

Asked whether so close a match is suspicious: no. LEAR has no random step (LARS path, cyclic coordinate
descent), and the check had already failed once on a 0.0015 % difference, so it can fail.

**Re-run on the fixed code** (`039ab70`, rows stamped `4cfc6b4`): LEAR 0.42928 (was 0.42928), MAE 14.4447
(14.4446); forecasts moved 0.0006 €/MWh on average, 1.28 at most. Line and tree identical.

#### Convergence warnings silenced, as epftoolbox does (`4fc97fd`)

epftoolbox wraps `recalibrate` in `@ignore_warnings(category=ConvergenceWarning)`. Decided: the same, with
stdlib `warnings` scoped to `LEAR.fit` and that one category, and the reasoning in the code comment and
the README for outside readers. Rejected: printing a count per run (guards an unseen failure) and raising
`max_iter` (departs from the recipe just matched). No test: the synthetic data never triggers the warning,
so a test could not fail. Checked on 28 Feb 2023: 12 warnings in 24 fits without the line, 0 with it, same
forecast. Suite 191 green.

**State at close.** `main` at `4fc97fd` before this entry, suite 191 green. README and plan page updated
(cross-check, silencing, 191 tests); the score is the same.

---

<a id="d20261014"></a>
### 14 October 2026

**Recap (all five):** 1 half right: AIC's trade-off named, but the random columns bring no information and survive only because their weights are tiny. 2 half right: night against solar hours correct, but the test was described as grading a model rather than asking whether the gap between two is bigger than luck. 3 wrong: validation days become training days later, so trimming first would change the line's and tree's refits. 4 one half right (window ending D−1, no leak signature given), one a unit test rather than a hindsight check. 5 half right: no random step named; what the check cannot catch (shared inputs, the information boundary) missed. LEAR re-summarised in six steps.

---

#### LEAR's window: every year against 1,092 days (`e8792c6`)

Walked through on real data first. "Every year" starts at 20 October 2018, the first complete day:
on 1 January 2023 that is 1,462 days against 1,092 (the extra days are October 2018 to December
2019), on 31 December 1,826 against 1,092. All the extra days are pre-crisis, and the ruler is
measured over them too. The evidence pointed both ways beforehand: the tree did better expanding,
arXiv 2311.02610's LEAR did worse on all data (0.43 against 0.40 at 728 days).

**Decision taken: a flag and a separate run**, `just train daily all`, scored as `lear_all` so
`scores.csv` never mixes the two windows; `--lear all` outside the daily run is refused rather than
ignored. Rejected: both LEARs in every daily run (~55 min every time, even after one window loses).
`window=None` in `lear_walk_forward` means no cut; the rule `index < day` is unchanged.

**Tests** (4 new), each bug planted in turn:

| Planted bug | Caught by |
|---|---|
| `<=` instead of `<` when `None` | spy (*every day before*), deleting the future (both days) |
| `None` branch skips the date filter | same three |
| `None` falls back to 1,092 | **nothing**: the fixture has 159 days, so a 1,092 cut keeps them all. On real data it would show as `lear_all` equal to `lear`; it did not |
| window read but not passed to LEAR | *every-year LEAR gets no window and its own name* |
| every-year row named `lear` | same |
| `main` never passes the window to `run` | **nothing**: the row would print as `lear`. It printed `lear_all` |

Suite 195 green. Leakage check: no feature changed; ruler and models still fitted only on days
strictly before D; split and settlement untouched.

| 2023, daily walk-forward (`e8792c6`) | hours | MAE | rMAE |
|---|---|---|---|
| line | 8,760 | 17.61 | 0.523 |
| tree | 8,760 | 14.45 | 0.429 |
| LEAR, 1,092 days (`4cfc6b4`) | 8,760 | 14.44 | 0.429 |
| **LEAR, every year** | 8,760 | **15.89** | **0.472** |

Run 1,534 s, under the 30–35 min estimated. Line and tree identical to `4cfc6b4` to the last digit.
Diebold-Mariano (read from MLflow by hand, the last time before a command exists): 1,092 better than
every year, p 7.5e-05; tree better than every year, p 0.010. Every year is closer on 44.7 % of hours.

**Where:** worse in every hour, most through the solar hours (13:00 +3.3, 14:00 +3.2 €/MWh), least at
19:00 (+0.2). Worse in ten of twelve months, most in January (+4.6); better in September (−0.4) and
December (−3.0). **My walkthrough framing was wrong:** I said the extra days grow through the year,
which suggests a growing gap; the gap is largest in January, when the fewest are added. Not
explained. A possible reason for the whole result, *not checked*: one set of line weights must fit
calm and crisis years together, where the tree can split them apart.

**Decision: LEAR keeps 1,092 days.**

#### One model per delivery hour: dropped, a limit stated instead

Asked rather than assumed, because LEAR already is one. The user's question first: can models this
different be compared at all? Answered as two questions. **Ranking** is fair already: every model
sits the same exam (same hours, prices, benchmark, information boundary), whatever its method.
**Attribution** is not: LEAR differs from the line in three ways at once (24 models, Lasso on the
ruler, the day table's inputs), so which earns its gain is unknown.

**Decision: dropped.** LEAR is the per-hour line; the tree splits on the hour already, and a tree per
hour is tuning, which 13 October ruled out. The attribution gap goes into the README as a stated
limit. Rejected: one in-between model (24 plain lines on LEAR's inputs) to attribute the gain, and
parking the item until stage 4. CLAUDE.md's stage table follows the README.

Plan page refreshed (window measured, per-hour dropped, 195 tests, about three working days left).

---

#### `just significance`: the README's p-values from one command (`9506116`, `335b542`)

The Third Law gap of 12 October: every p-value in the README had been read from MLflow by hand.
**Shape agreed before building:** a fixed list of the README's seven comparisons in
`scripts/significance.py`, each side named by its params (model, refit, LEAR window) rather than a
run id, which differs per clone; resolved to the newest matching run by `tracking.latest`; both rMAEs
and p in both directions computed on the hours the two runs share; each run's commit printed, so a
p-value that moved because its run moved is visible. Prints only; `scores.csv` stays the record. A
missing run names the `just train` call that makes it. Rejected: `just dm <a> <b>` for any pair (the
README's numbers would again depend on typing the right pairs), and a CSV record beside the print.
**Clean-clone limit:** MLflow is not in git, so the command needs the four `just train` runs first.

**Removed before committing:** a filter on the run's grid convention. All 33 runs in the store state
the 24-slot grid, so it guarded a case never observed.

**Tests** (5), each planted: newest replaced by oldest, and only the first param matched, both caught
by *latest finds the newest matching run*; p directions swapped; the first side scored on its own
hours (the fixture's second run is a day shorter, and that day is far off); the second side read from
the first run; the trim skipped. All caught. Suite 200 green.

**Output on today's store** reproduces every p in the README and work log: line once → monthly
0.00013, monthly → daily 0.0012; tree once → monthly 3e-11, monthly → daily 0.028; tree → LEAR 0.50
both ways; line → LEAR 4.5e-08; every year → 1,092 days 7.5e-05. Leakage check: evaluation only,
reads stored forecasts, fits nothing, settlement untouched.

Plan page refreshed (p-value command built, 200 tests, about two working days left).

---

#### German public holidays (`d1f6252`, `e70e7c2`)

**Decisions with the user:** nationwide holidays only (the nine; regional ones left out), from a
package rather than a hand list (`holidays==0.106`, `holidays.Germany()` with no state = nationwide),
as a separate yes/no column (`is_holiday` hourly, `holiday` in the day table) rather than reading a
holiday as Sunday, which would have changed the meaning of existing columns. **Keep rule fixed before
the result:** kept unless it makes a model significantly worse. Rejected: keep only if significant
(about 216 affected hours; one year was unlikely to prove a real gain).

**Walkthrough on 2023 first.** The tree already matched its weekday error on holidays (14.3 against
14.5 €/MWh); LEAR (21.4 against 14.3) and the line (29.0 against 17.2) did not. Checked why: the load
forecast on holidays averages 44.0 GW, Sunday 44.9, Mon–Fri 56.1, so the holiday is already in the
data. **My explanation that the weekday column misleads LEAR and the line was wrong:** given the flag,
both gave it almost no weight (line −0.5 €/MWh against +7.9 for the weekend; LEAR non-zero in 17–20 of
24 hours, mean ±0.03 on the squashed scale), and their holiday misses did not shrink (LEAR 21.4 → 21.5,
line 29.0 → 29.6; tree 14.3 → 13.6). What they get wrong on holidays is not known; a guess, not checked:
the price clues from earlier days do not look like a holiday.

**Leakage check:** (1) every holiday fixed by law years ahead; nine a year 2018–2025, no one-off
additions in the window (the 2017 Reformation Day precedes the data). (2) Nothing fitted on it; LEAR
leaves it unscaled. (3) Settlement untouched.

**Tests** (2 new; the clue count 247 → 248), each planted: holiday read on UTC days, regional holidays
(Brandenburg, which adds Easter Sunday), flag on the day before, and the day table forgetting the
flag, all caught. **LEAR scaling the flag:** no test; on real data it crashes at the first fit with
"Input X contains NaN" (median and spread both 0), loud, as the weekday case on 13 October.

**Runs** (all four at `d1f6252`; my shell loop first passed "daily all" as one word, zsh does not split
`$r`, and the grep pipe hid the failure; rerun on its own):

| 2023, without → with holidays | once | monthly | daily |
|---|---|---|---|
| line | 0.532 → 0.532 | 0.525 → 0.525 | 0.523 → 0.523 |
| tree | 0.483 → 0.484 | 0.440 → 0.443 | 0.429 → 0.428 |
| LEAR | | | 0.429 → 0.429 |

No change significant in either direction (`just significance`, both sides pinned to their commits;
closest the monthly tree, p 0.097 for worse). **Kept.** Knock-ons: tree monthly → daily now p 0.0015
(was 0.028; monthly got worse again), tree → LEAR p 0.53 / 0.47, every year → 1,092 days 0.471 against
0.429, p 9.2e-05. Every 2023 number from here on includes the flag; earlier rows are a different
feature set. Suite 203 green. README and plan page refreshed (holidays measured, 203 tests, about one
working day left in stage 2).

#### Stage 2's one reading of the held-back years (`f5d5f5b`, `69e1998`)

Explained first: `final_score.py` still scored stage 1's two recipes (line and tree fitted once, on
2018–2022 and on 2018–2023, then frozen for two years), with no LEAR and no daily refitting, so it
would have tested stage 1's recipe again. **Decided with the user:** walk line, tree and LEAR forward
day by day through 2024–25 as through 2023, with line and tree fitted once on 2018–2023 beside them
for contrast; p-values through MLflow. Rejected: daily only (no same-reading contrast), and adding
the every-year LEAR (~+50 min for a verdict already clear).

**The old safety test had to go:** "no fit ever sees a held-back row" is false by design once the
daily refits learn from earlier held-back days. Replaced by spying every fit and the forecast after
it: each fit ends before the first hour it forecasts; the frozen fits start at the first training
hour and end at 23:00 on 31 Dec 2023; the last daily refits end the hour before the last held-back
day. Six plants, all caught: refits never adding held-back days, daily rows fitted once on
everything, frozen fit on 2018–2022 only, frozen fit including the held-back years, scoring before
the shared-hours trim (the stand-in LEAR now skips a day so this can fail), LEAR handed validation
days. **`just significance`** now pins every 2023 claim to `split=valid` (planted: unpinned, caught)
and adds five held-back comparisons. Suite 204 green. Leakage check: no feature changed; every fit
ends before its hours; settlement untouched.

**The reading** (`just final-score` at `69e1998`, 2,356 s, 17,544 hours: two more than stage 1's,
the autumn midnights):

| rMAE | 2023 | 2024–25 | 2024 | 2025 |
|---|---|---|---|---|
| line daily | 0.523 | 0.541 | 0.557 | 0.525 |
| tree daily | 0.428 | 0.457 | 0.458 | 0.457 |
| **LEAR daily** | 0.429 | **0.405** | 0.433 | 0.377 |
| tree fitted once 2018–2023 | | 0.530 | 0.519 | 0.542 |
| line fitted once 2018–2023 | | 0.563 | | |

p (`just significance`): tree → LEAR 7.5e-06; line → tree 1.9e-12; line → LEAR 8.5e-28; frozen →
daily 4.5e-20 (tree), 1.3e-14 (line). **The ranking held**, unlike stage 1, and the 2023 tie broke
for LEAR: better in every hour (most at night, 00:00 6.3 against 10.0, and in the evening peak),
closer on 55.1 % of hours; the tree better on the 1,033 negative-price hours (17.3 against 19.5).
Why LEAR's lead grows into 2025 is not known; guess, not checked: its 1,092 days leave the crisis
behind while the tree learns from every year. Not suspiciously good: inside arXiv 2311.02610's
0.40–0.43 with the same benchmark. Not done: rebuilding held-back days cut at gate closure.
The frozen tree reads 0.530 against stage 1's 0.532 (grid, autumn hours, holidays since).

**Stage 2 closed.** README (status, stage table, *Where stage 2 landed*, dates moved a week earlier),
CLAUDE.md's stage table and the plan page refreshed (stage 2 closed, held-back 0.405, stage 3 next).

**State at close.** `main` after this entry's commit, suite 204 green. README and plan page refreshed.

---

<a id="d20261015"></a>
### 15 October 2026

#### Is retraining on the held-back years sound, and is 0.405 too good? Checked

Asked by the user, sceptical of both. **Retraining during the test period is the field's own
protocol**, not a shortcut: epftoolbox's `evaluate_lear_in_test_dataset` ("evaluates a LEAR model in
a test dataset using daily recalibration") loops over every test day, joins the training data with
the test data up to that day, blanks that day's prices, and recalibrates (read in `_lear.py` today).
It is sound on two conditions, both held here: a refit sees only days before the one it forecasts
(tested, planted), and no choice is made after seeing the test years (every stage 2 choice was made on
2023). **Weaker than a first look:** this was the second reading of 2024–25, and stage 1's reading
(tree reversed by the line) was known while stage 2 was planned.

**0.405 is not near the best in the field. Our benchmark is the easier one.** We divide by the price
one week earlier; the field divides by yesterday's price Tue–Fri and last week's Sat–Mon. On the
same held-back forecasts, the field's naive misses less (MAE 27.38 against 32.81), so every rMAE
rises: LEAR 0.405 → **0.485**, tree 0.457 → 0.548, line 0.541 → 0.648. For comparison, under the
field's rule, Lago et al. 2021 report LEAR 0.431 and the best ensemble 0.374 on DE 2016–17 (other
years, so only roughly comparable). So our LEAR is a LEAR-level result, slightly behind the published
one, not a top one. Like for like with our rule, arXiv 2311.02610 has LEAR 0.40–0.43 and its best
models 0.34–0.36 on DE 2022–May 2023. **The README states rMAE against the weekly naive only; it should
say this.**

**Still open, already recorded:** item 12 (8 Oct), the wind/solar forecast's legal deadline is 18:00
on D−1, after gate closure; the level of every score rests on it being at hand by noon in practice.
Not done: rebuilding held-back days from data cut at gate closure.

---

#### Decided: the field's benchmark becomes the denominator, the weekly one stays beside it

**Decision with the user (15 Oct):** from the build onwards, every rMAE divides by the field's rule
(yesterday's price Tuesday to Friday, last week's Saturday to Monday, as epftoolbox's `_rmae.py`).
The weekly rule is kept beside it for continuity. Rejected: keeping the weekly rule as headline
with the field's as a second column (the headline would stay the easy bar), and switching
completely (stages 0–2's record could no longer be read against the new numbers).

**The user's condition:** the revision must be impossible to miss. The README says, where the
numbers are, that the field's comparison was introduced at the close of stage 2, that every number
before that date was divided by last week's price, and that from then on everything is compared
against the field's rule.

**Transparency, before building.** Affected: how every score is computed (`evaluate.py`,
`models.naive_forecast` and its comment, `train.py`, `final_score.py`, `significance.py` labels,
`scores.csv`). The README's headlines all change, stage 1's 0.532 included. Previously produced
numbers stay valid as what they were, last-week ratios, and are not rewritten. Rankings and p-values
do not move: every model shares the denominator, and Diebold-Mariano does not use it. Held-back
forecasts get re-scored, not refitted, so no choice is made from them; that is said where they are
reported.

README (*Where stage 2 landed*) and plan page note the revision as decided, not built; no new number
is quoted until a documented command regenerates it.

---

**Recap (all five, second session):** 1 wrong: the script was allowed to read the held-back years (once per stage); it measured stage 1's frozen recipe, not daily refitting. 2 half right: a refit sees only days before the one it forecasts, but the second rule (nothing chosen after seeing the test years) was missed. 3 half right: tree better on negative-price hours correct, but daily refitting cannot explain the change, since both were refitted daily in both years. 4 not understood: explained (newest matching run would silently become the 2024–25 run). 5 right: the load forecast already drops to Sunday's level on holidays.

---

#### The field's benchmark built, every README run repeated (`93d3290`, `9b2ed8d`, `c7b4739`)

**Design agreed before building.** The field's rule is `models.field_naive`, beside `naive_forecast`:
`price_lag_24h` Tue–Fri, `price_lag_168h` Sat–Mon, weekday read off the grid's Berlin labels (checked
against epftoolbox's `naive_forecast` today: Mon, Sat, Sun weekly; Tue–Fri daily). One departure:
epftoolbox builds its naive from inside the test series, so its denominator skips the first week; ours
reaches back before the split, so both sides score identical hours. **`scores.csv`: `rmae` keeps its
meaning (last week's), `rmae_field` added as the headline** — the header line rewritten once, old rows
blank there, no recorded value touched. Rejected: renaming to `rmae_week` with a new `rmae` (the word
would mean different things in old and new clones). **Re-run rather than re-score:** no new script,
and the weekly ratio reproducing to the last digit proves nothing else moved. Rejected: a re-score
script over MLflow (a new file, and rows stamped with the scoring commit, not the forecasting one).
**Correction to 15 Oct's "re-scored, not refitted":** the held-back years were refitted a third time;
the models are deterministic, the forecasts identical, and no choice was made from them.

**First, a guard** (`93d3290`): pandas appends without reading the header, so a row with a new
column was written into the record and only the read-back failed (shown on a copy of the real
file). `record` now refuses before writing. Plants: no guard, check after the write; both caught.

**Then the benchmark** (`9b2ed8d`). `score` takes the field's benchmark as a required keyword and
trims all four series together; the table leads with it; MLflow keeps `naive_field` and logs
`rmae_field`; both benchmarks are scored rows, each reading 1.000 on its own ratio. `just
significance` divides by the field's when the first run stored it, else last week's, and prints
which: the holiday claims are pinned to runs from before the revision. Leakage check: no feature
changed; lag 24 already meets the minimum; benchmark only, nothing fitted; settlement untouched.

| Planted bug | Caught by |
|---|---|
| Monday from yesterday; Saturday from yesterday; rule swapped | *field benchmark takes yesterday Tue–Fri…* |
| field's benchmark outside the shared trim | *an hour missing from the field benchmark…* |
| field ratio divided by last week's | three tests (score, trim, MLflow reproduces) |
| table prints last week's first | *table renders one line per row* |
| MLflow drops the field column | two tracking tests |
| `train.run` / `final_score.run` fill the column with last week's | **nothing at first**: it still reads 1.000 on itself and the models still beat it. Two tests added that read the value off the prices by date; both caught |
| significance always last week's; never falls back; mislabels | three significance tests |
| `final_score.main` logs the field run with the frozen batch | **nothing**: `main` is untested. Checked on the real run: `refit=daily` |

My first plant loop passed four test files as one word under zsh (the 14 Oct trap again) and ran
nothing; rerun with the words split. Suite 210 green.

**The runs** (`c7b4739`, all at `9b2ed8d`; validation 1 s, 13 s, 1,569 s, 1,608 s; held back 2,233 s).
Every last-week ratio identical to `d1f6252` / `69e1998` to the last digit, 13 rows. The field's
benchmark misses by 28.62 €/MWh in 2023 (last week's 33.65) and 27.38 in 2024–25 (32.81).

| rMAE, field's (last week's) | 2023 | 2024–25 |
|---|---|---|
| line once / monthly / daily | 0.625 / 0.618 / 0.615 | |
| tree once / monthly / daily | 0.569 / 0.521 / 0.503 | |
| LEAR 1,092 days / every year | 0.504 / 0.554 | |
| line daily | 0.615 (0.523) | 0.648 (0.541) |
| tree daily | 0.503 (0.428) | 0.548 (0.457) |
| **LEAR daily** | 0.504 (0.429) | **0.485** (0.405) |
| tree / line fitted once on 2018–2023 | | 0.636 (0.530) / 0.675 (0.563) |

`just significance` reproduces every p-value logged before. README (revision note under the stage
table, both ratios, stage 1 marked as last week's), CLAUDE.md's stage table and the plan page
(version 14) refreshed. README's stale "108 passed, 16 xfailed" replaced by 210 (`387c0f3`).

---

#### Stage 3 agreed: QRA on LEAR, because stage 4 now bids with limit prices

**Walked through on 11 September 2023** (a validation day, so nothing is chosen from the test years):
a rough 80 % band from LEAR's own misses over the 91 days before held 77.9 % of hours April–December;
at 19:00 it ran 157–210 and 524 came in, yet the schedule was right (cheapest 13:00, dearest 19:00,
both forecast). **The point raised:** a risk-neutral fixed schedule depends only on the average
forecast, so a range changes nothing it does. **The user's pushback, correct:** an operator wants to
understand risk. So my claim was too broad — a range matters when risk is reported or acted on (CVaR),
and when bids are price-dependent.

**Read first.** Lipiecki, Uniejewski & Weron 2024 (arXiv 2404.02270): QRA, conformal prediction and
IDR postprocessing LEAR on DE and ES, windows 28–182 days, 99 percentiles, CRPS; QRA alone
competitive with a distributional DNN, the average of all three best. Nitka & Weron 2023 (arXiv
2308.15443): DE 2019–20, battery 2 MWh at 90 % each way (ours), median picks the hours, limit prices
at quantiles; the CRPS-best combination earned *less*. Hirsch & Ziel 2026 (arXiv 2604.19580): DE
2019–23; quantile trading rules can be gamed by biased forecasts and ignore links between hours; a
better score does not guarantee a better decision. **Not verified:** how an unfilled order is closed
(a search summary says the next day at market; not found in the paper text read).

**Decisions with the user.** Stage 3: QRA on LEAR's daily forecasts, conformal beside it, pinball
loss and coverage on 2023. Rejected: quantiles fitted directly from the features. Stage 4: price-
dependent bids from the quantiles, fixed schedule kept beside them (one shared ceiling; shows in euros
whether the range paid). Rejected: a stochastic program over price paths (scope), a fixed schedule
only (the user wants the auction as it works). Recorded as direction now, details later; the unfilled-
order rule and its settlement (Contracts 3 and 4) open until stage 4 starts. README and plan page say so.

---

#### How the field handles an unfilled order: read, not yet decided

Asked by the user ahead of stage 4. Read in the papers' own text today. **Three conventions:**
(1) **half full, rebalanced next day** — Nitka & Weron 2023 (arXiv 2308.15443) start the 2 MWh
battery at 1 MWh and trade 1 MWh a day, so either side can fail; "If B=0 at the beginning of a day,
an unlimited bid to buy 1 MWh is placed", and likewise at B=2. Hirsch & Ziel's Table 1 lists the same
"balance non-accepted by unlimited bids on d+1" for Uniejewski (2025) and others. (2) **balance in
another market at day end** — Maciejowska et al. 2024, per Hirsch & Ziel. (3) **coupled execution**
— Hirsch & Ziel 2026 assume both orders fill or neither, citing EPEX SPOT's *loop blocks* (two
blocks executed or rejected together, offered for storage on EPEX day-ahead markets since 2019).
Hirsch & Ziel: the first two "introduce additional risk and make the (predicted) distribution of
battery returns intractable". **Not checked:** how a loop block's price limit is evaluated in the
auction, which decides whether quantile limits map onto it. Decision stays at stage 4's start.

---

#### Stage 3's design agreed, nothing built

Measured first: one quantile fit on 182 days takes 2.3 ms (scikit-learn 1.9.1 `QuantileRegressor`,
HiGHS, no new dependency), so 99 percentiles × 24 hours × 365 days is about 33 min; LEAR's stored
forecasts start on 1 January 2023. Explained on one hour (19:00): QRA fits lines through the cloud
of (LEAR's forecast, real price) over the window, with 90 % of the dots below the p90 line; the lines
need not be parallel, so the band can widen on expensive days, which conformal's fixed width cannot.

**Decisions with the user:**
- **History:** walk LEAR day by day through the last 182 days of 2022 first, so QRA learns only from
  forecasts LEAR really made and all 365 days of 2023 are scored. Rejected: score July–December only.
- **Inputs: LEAR alone.** The user asked whether the percentiles would also serve the tree and line,
  and whether hourly and daily models can be combined. Answered: QRA makes one range per hour, built
  from whichever forecasts are its inputs, and all three sit on the same 24-slot grid. Rejected for
  now: LEAR, tree and line combined (little disagreement to combine; attribution).
- **Window: 182 days**, shorter ones compared on 2023 only if the first result suggests it matters.
  Rejected: the field's average of four windows from the start (~4× the fits).
- **Code:** a new `scripts/quantiles.py` behind `just quantiles`, running LEAR itself; QRA in
  `src/models.py`, pinball loss in `src/evaluate.py`. Rejected: reading LEAR from MLflow (a clean
  clone would need `just train daily` first; inputs from another commit).

**Defaults stated, not objected to:** one fit per delivery hour; each fit on days strictly before
the one it forecasts; 99 percentiles; crossing lines sorted back into order and counted; conformal
over the same window; scored on 2023 by average pinball loss and coverage of the 50, 80 and 90 %
bands.

---

**State at close (15 Oct, second session).** `main` after this entry's commit, suite 210 green.
README, CLAUDE.md's stage table and the plan page (version 14) refreshed for the field's benchmark
and the stage 3/4 decisions. Pinball loss walked through four times in plain words at the user's
request (what it scores, the flipper-shaped penalty, its link to false positives and negatives, how
minimising it places the line); all in `docs/learnings.md`.

---

<a id="d20261016"></a>
### 16 October 2026

**Recap (all five):** 1 mostly right: the average is enough, but the reason is that revenue is a straight sum, and price-limited bids (stage 4's reason) were missed beside risk aversion. 2 half right: the last-digit match was the proof, but not that a re-score needed a new script and stamped the wrong commit. 3 not remembered: only a test reading the price off the dates could see a column that agrees with itself. 4 two of three: the first is a half-full battery rebalanced next day by an unlimited bid, not oversizing. 5 answered with a question: the penalty does change, +0.1 per dot below, −0.9 per dot above, and stops falling at 1 in 10 above.

#### Stage 3 built: pinball, QRA, conformal, `just quantiles` (`5b5024f`, `d70cb35`, `abc7187`, `3f838b4`)

**Decided with the user before building.** Conformal is the paper's symmetric form: the band's
width comes from the *size* of LEAR's past misses, centred on LEAR (Lipiecki et al. 2024: "only
possible under the assumption of symmetrically distributed errors"). Rejected: percentiles of the
signed misses (can lean one way; not the field's conformal). Shown on 11 Sep 2023, 19:00 (window
13 Mar–10 Sep): 80 % band 158.7–206.9 symmetric, 160.4–208.0 signed, LEAR too low 54 % of days;
the price came in at 524, outside both. **Scores in both places**: MLflow keeps each method's run
with all 99 percentiles per hour; `reports/quantile_scores.csv` (in git, a second named exception in
`.gitignore`) keeps the headline numbers, stamped, through `train.record`. Rejected: MLflow only (a
clean clone would see no history; `reports/mlflow/` is local, holding machine paths).

**Checked in the paper first:** QRA has an intercept and one fit per hour; the paper feeds it the
average of four LEARs (56, 84, 1,092, 1,456 days), here one (1,092), a stated departure. Crossing
is not discussed in the paper, so sorting and counting is ours. Not checked: whether its conformal
uses the (n + 1)/n rounding; ours is the plain percentile.

**Built in four pieces, each planted before it was claimed.**

| Piece | Planted bug | Caught by |
|---|---|---|
| pinball, coverage | V flipped; miss sign flipped; sum for mean; blanks kept; band's low edge ignored; p20–p80 for 80 % | hand-worked pinball (3 tests), median = half MAE, 1,000-price line search, coverage by band, trim test |
| QRA | window includes D; never trimmed; one day too long | *a range learns only from the window before each day* |
| | read at yesterday's forecast; hours backwards; percentile mirrored | fan-out and label tests |
| | **scikit-learn's default `alpha=1`** | **nothing at first**: the test data's spread made the penalty negligible. Measured on real 2023 data: p90 at 19:00 moves 48.5 → 60.3. Test added (dots on an exact line); caught |
| conformal | signed misses; p90 at the 90 % size; both edges above; centred on the price | hand-worked band, coverage test |
| | shared walk: includes D, untrimmed, yesterday's forecast | the window test, now run on both methods |
| script | walk a day late; reaches 2024; incomplete days walked; prices on wrong hour; QRA scored unsorted; kept table untrimmed; window not recorded; percentiles back as text; run without convention | `test_quantiles.py`, `test_tracking.py` |
| | **conformal row scores QRA's lines** | **nothing at first**: each row reproduced from its own table, so a swapped pair agreed with itself (the 15 Oct lesson again). Test added from outside the row: conformal's band is symmetric around LEAR, QRA's is not; caught |

**A bug no test could see, found on real data before the run.** A one-day check with LEAR's
stored 2023 forecasts crashed: prices span 1,918 days, LEAR's forecasts 547, and the walk applied
one table's "days before D" to the other. Every test had handed in two series of equal length. Dots
now come only from days LEAR forecast; a test with a longer price span, planted back, caught it.
The same check: the day table's prices equal the hourly 2023 prices exactly (8,760 hours), the
walk covers 547 days (3 Jul 2022–31 Dec 2023, none incomplete), one day of 99 percentiles for both
methods takes 6.0 s, and QRA's lines crossed on 23 of that day's 24 hours.

Leakage check, answered for each piece: no feature changed; QRA and conformal read LEAR's forecast
for D and prices of days before D only (planted: window including D, caught for both); LEAR's
late-2022 forecasts learn from days before each, training days all; the test years are dropped at
`day_rows()`; settlement untouched. Suite 234 green.

---

#### Stage 3's first result: QRA beats conformal, both bands lag the market (`53ed091`, `88673bd`)

`just quantiles` at `3f838b4`: LEAR 1,645 s, ranges 2,303 s. **The check held:** LEAR's 2023 rMAE
read 0.504 (last week's 0.429) on 8,760 hours, as `scores.csv` holds for `just train daily`, so QRA
learned from the LEAR the README reports.

| 2023, window 182 | Pinball | 50 % band | 80 % band | 90 % band | Hours crossed |
|---|---|---|---|---|---|
| **QRA** | **5.381** | 0.557 | 0.832 | 0.912 | 5,477 of 8,760 |
| conformal | 5.546 | 0.584 | 0.851 | 0.927 | 0 |

`just significance`: conformal → QRA, **p = 0.0011** (reverse 1), so QRA's 3 % lower pinball is
not luck. Both bands hold *more* than their share across the year, which is not what a leak looks
like (a leak gives narrow bands that still hold).

**The year's coverage is two opposite errors.** By month, the 80 % band held 83–92 % (QRA) and
93–97 % (conformal) January–June, but 70–83 % and 70–80 % July–December; October 0.695 / 0.700.
Conformal's band was 124 EUR wide in January and 42 in October, while LEAR's own miss went from
21 EUR in January to 11 in June and back to 16 in September–October. The 182-day window remembers
the market half a year late: crisis-era late 2022 widens early 2023, the calm spring narrows the
autumn. QRA shrinks better in the first half; in the second both are too narrow alike.

**Decided with the user: compare 28, 56 and 91 days on 2023**, the validation year, so choosing
from it is legitimate. Built: `just quantiles 28 56 91` shares one LEAR walk; windows over 182 are
refused, because the walk starts 182 days before 2023 and a longer one would be quietly short in
early 2023 (planted: guard removed, off by one, default lost, first window only; all caught;
`main`'s loop untested, as `train.main` is). Rejected: three runs as they stand (~3¼ h, the window
edited between runs). One real day: 3.6–4.3 s per day per window. **Caution stated before the run:**
one year's two halves; a short window helps if swings come every few months, and may chase noise.

---

#### What "QRA's lines crossed" means, measured during the run

Asked by the user. On 1 Dec 2023, **747 of 2,352 neighbouring pairs** of QRA's lines were out of
order; half by under 0.38 EUR (lines 1 percentile apart swap on noise), but up to **58 EUR at 14:00**,
38 at 15:00, 24 at 13:00. There LEAR forecast 215–224 while every dot in the June–November window
lay below 170–187: the lines were read beyond their data, where different slopes drift apart. So
*hours that crossed* (the recorded column) cannot tell harmless swaps from extrapolation, and the
raw crossings are not stored (MLflow keeps the sorted lines).

**How often is LEAR's forecast outside its window?** Measured on July–December 2023, where the window
lies inside 2023 (stored LEAR forecasts, 4,392 hours, nothing fitted): **2.9 % of hours** (above
1.1 %, below 1.7 %), by 11 EUR median, 59 at most. Spread evenly over the hours (1–5 %), rising at
the season's turn: October 4.0 %, December 6.2 %. Six of 183 days had six or more such hours; most
was 24 December (14). January–June not measured: their windows reach late 2022, not stored. Read:
not enough alone to say 182 days is too long; worth scoring pinball separately on these hours.

---

#### Diebold-Mariano on pinball, for `just significance` (built during the run, committed after)

**Decided with the user.** The daily loss is pinball over all 99 lines, the headline score, so the
test judges the reported number. Rejected for now: parts of the range tested separately (several
p-values, and which lines matter is stage 4's question). Shown on 1 Dec 2023 why it was asked:
QRA 6.90 against conformal 6.97 overall, but conformal better at the edges (p10 alone 4.09 against
6.23, p90 3.96 against 5.52) and QRA in the middle (8.21 against 9.71): a total can hide offsetting
parts. **Runs from `just significance`**, reading the stored percentiles; no refit. Rejected: inside
`just quantiles` (another run for one p-value). Not checked: whether Lipiecki et al. test this way.

`E.dm`'s daily step moved into `_dm_days`, shared; the existing DM tests, including epftoolbox's,
passed unchanged. Anchor for the new one: on a single p50 line pinball is half the miss, so
`dm_pinball` must equal `dm`; it does at lags 0 and 7.

| Planted bug | Caught by |
|---|---|
| gap signed the wrong way | p50 = `dm` (both lags), *says which range is better* |
| hours one range lacks kept | *drops an hour one range lacks from both* |
| pinball summed over lines | hand-worked pinball, trim test |
| hours, not days, as evidence | epftoolbox reference, echo by hand |
| echo correction dropped | p50 = `dm` at lags 7 |
| significance: each run on its own hours; p swapped; second side reads the first run | range comparison tests |
| significance: prices read from LEAR's column | **nothing at first**: the fixture set LEAR equal to the price. Given its own miss; caught |

Suite 241 green.

---

#### How a loop block's price limit is evaluated: read

**The exchange checks the pair, not each order.** EPEX's FRA algorithm description (Release 1.0,
Feb 2022, hosted by NESO): loop blocks are "a 2-block linked family where the two block orders are
parent of each other"; "If accepted, the surplus of the loop family must be non-negative" and "the
two block orders have the same acceptance ratio". Euphemia's public description (18 Dec 2025, §5.4.1)
does not name loop blocks; its linked-family rule is the same ("the surplus of a family is
non-negative"; an out-of-the-money parent "can be accepted in case its accepted child blocks provide
sufficient surplus"). Hirsch & Ziel 2026, footnote 1: loop bids "are conditional on the total
cashflow of the linked bids", "contrary to individual directional limit prices".

**What it means for stage 4.** With equal volumes, the pair fills when the realised sell-minus-buy
spread is at least the spread between the two limits; only the limits' difference matters. So a loop
cannot say "buy below p10 *and* sell above p90"; quantiles would set one spread threshold per pair.
**Not verified:** the FRA document is EPEX's UK frequency auction, not SDAC; loop blocks' availability
in DE-LU after the 15-minute switch (EPEX's own pages refused automated fetches); with 90 %
efficiency the two volumes differ, so the condition is volume-weighted (my arithmetic, not quoted).

#### The windows compared: a shorter memory mattered more than the method (`148893b`, `ef602df`)

`just quantiles 28 56 91` at `f8566fb`: LEAR 1,662 s (the check read 0.504 again), ranges 1,284 /
1,424 / 1,624 s.

| 2023 | QRA pinball | conformal pinball | QRA 50 / 80 / 90 % | conformal 50 / 80 / 90 % | QRA hours crossed |
|---|---|---|---|---|---|
| 182 days | 5.381 | 5.546 | 0.557 / 0.832 / 0.912 | 0.584 / 0.851 / 0.927 | 5,477 |
| **91 days** | **5.300** | 5.397 | 0.537 / 0.814 / 0.897 | 0.533 / 0.817 / 0.907 | 5,925 |
| 56 days | 5.304 | 5.388 | 0.521 / 0.800 / 0.887 | 0.522 / 0.804 / 0.898 | 6,200 |
| 28 days | 5.394 | 5.395 | 0.473 / 0.757 / 0.857 | 0.514 / 0.787 / 0.877 | 6,039 |

`just significance` (comparisons added, `ef602df`): QRA 182 → 91 **p = 0.033**; 56 → 91 p = 0.47
(tie); conformal 182 → 91 **p = 3.2e-05**; at 91 days conformal → QRA **p = 0.078**. Ad hoc, not in
the command: QRA 182 → 56 p = 0.145, 28 → 91 p = 0.112; conformal → QRA at 56 days p = 0.18, at 28
p = 0.50. **Read:** a shorter window helps QRA a little and conformal a lot, and QRA's clear lead at
182 days was mostly its better handling of a stale window. One year, so a reading, not a finding.
**The lag shrinks, not gone:** QRA's 80 % band at 91 days held 0.917 in February, 0.675 in August,
0.707 in October. **Flattered slightly:** best of four windows on one year. 28 days under-covers
everywhere (0.757 for 80 %). Nothing implausible: gains of 1.5 % in pinball, coverage near nominal.

---

**Plan refreshed:** README (*Where this is going*: stage 3 built and measured on 2023, *Where
stage 3 stands*, loop-block note, *Roughly when*), CLAUDE.md's stage table, the plan page (version
15), `docs/architecture.md`. Stage 3 stays open: window choice and the held-back reading remain.

**State at close (16 Oct).** `main` after this entry's commit, suite 246 green. Learnings for today
(the two conformal bands, crossing lines, a total hiding offsetting parts, a window remembering the
market late, the loop block's pair test) in `docs/learnings.md`.

---

<a id="d20261019"></a>
### 19 October 2026

**Recap (all five):** 1 half right: non-parallel lines named, but the lead shrank with the window, so it was about coping with a stale window. 2 half right: the situation is known, LEAR's forecast beyond every dot in the window at the season's turn. 3 not remembered: the outside fact (conformal symmetric around LEAR) caught it; the principle matters, not the test. 4 mostly right: only the limits' gap counts, but 50 is a gap not a price, and negative prices are fine. 5 half right: the window lags, not just holds noise; selection on 2023 not answered.

#### Window chosen: the average of four, as the field does

**Shown on real 2023 data first** (stored runs, nothing refitted). 56 and 91 days are a coin toss
day by day (91 better on 185 days, 56 on 180) and within ~0.2 pinball every month from April; they
part only in late winter, each way once: February 56 better (5.18 against 5.74), March 91 better
(5.39 against 5.65; 80 % band held 0.905 against 0.804, 64 € wide against 47 €). With 56 days
about half a dot lies below the p1 line, with 91 about one. **Then the field's recipe**
(Lipiecki et al.: average the ranges of several windows, percentile by percentile), from the four
stored runs: QRA **5.195**, 50 / 80 / 90 % held 0.539 / 0.821 / 0.911; against 91 days
**p = 0.0001** (reverse 1.0), better in 10 of 12 months. Conformal gains nothing (5.398). Why it
works: each window is wrong at different moments (56 in March, 91 in February, 182 all spring).

**Decided with the user: the average of 28, 56, 91 and 182 days**, for QRA and conformal alike.
Rejected: 91 days (ties 56, loses to the average), 56 days. **Stated limits:** a fifth candidate
looked at on 2023, so slightly flattered; less so than a tuned one, because it is the published
recipe and its lead holds month by month. Not checked: that the paper uses exactly these lengths.

**What it costs to run, asked by the user.** The hours are a backtest's, not a live day's. A live
run forecasts one day: one LEAR fit (~3 s: 1,662 s over 547 days) and one day's ranges per window
(3.6–4.3 s at 28–91 days, ~6 s at 182, both methods, 99 percentiles, measured 16 Oct), so
**~20–25 s on this laptop** against ~8 s for one window. The held-back reading replays 912 days,
hence ~4.5 h (derived, not timed). A faster machine shortens the replay only; the four windows are
independent and could run on separate cores, not built. Derived from the pieces, not timed as one
live run.

#### Stage 3's held-back reading designed and built

**Decided with the user.** `just final-score ranges`: one file stays the only door to the
held-back years, and a separate argument keeps stage 2's forecasts unread. Rejected: a new
`final_ranges.py` (two doors). Only the two averages are recorded; rejected: each window too
(choosing the window again on the test years). 2023's average goes into the record by re-running
`just quantiles 28 56 91 182`, which now also scores the average of the windows it runs; it must
read 5.195 again. Rejected: printing it from stored runs (no row in the record).

**Defaults stated:** each window's lines sorted, then averaged (matches 5.195; an average of
ordered lines is ordered); an averaged hour counts as crossed if any window crossed there. LEAR
walks from 3 July 2023; its 2024–25 MAE must read 13.283 on 17,544 hours, stage 2's `lear daily`.

| Piece | Planted bug | Caught by |
|---|---|---|
| `M.average`, `untangle` | divided by n−1; a range dropped; columns unchecked; no check; crossed by `all` | hand-worked average, refusal tests, untangle test |
| `quantiles.runs` | crossed by `all`; each window scores the first; no average; label lost; one window left out; count of hours, not crossed | average by hand from the windows' tables, crossed counted from raw lines refitted outside |
| | **average only from three windows up** | **nothing at first**: every test used one or three. Two-window test added; caught |
| `final_score` ranges | walk a day short; walk stops at 2023; 2023 scored; one window averaged; labelled valid; label from the constant; prices a day early; a window dropped; LEAR walks held-back days only | walk, label, average-from-outside and *never learns from itself or later* tests (scoring 2023 crashes on an empty first window rather than failing an assertion) |
| `significance` | held-back miss names `just quantiles`; held-back comparison reads 2023 runs (either side) | two tests added |

**Two lessons from the planting itself.** (1) A plant restored within the same second, at the
same length, kept running from Python's bytecode cache: `any`→`all` went on executing after the
file was restored, and a new test "failed" on correct code. Planting now runs with
`PYTHONDONTWRITEBYTECODE=1` and the pycache cleared, and every plant was repeated. (2) A
`git checkout` to undo a plant restored the committed file and discarded uncommitted work; it was
recovered from the copy taken before planting. Plants are restored only from their copy.

Leakage check: no feature changed; each range at D reads LEAR's forecast for D and prices of days
before D (planted: prices a day early, caught); windows and average chosen on 2023; the held-back
ranges learn from held-back days only once past, as stage 2's daily refits; settlement untouched.
`main`'s new argument untested, as `main` is elsewhere. Suite 260 green.

#### The 2023 re-run crashed at its last line; the held-back run stopped before it could (`5411efd`, `b4b9700`)

`just quantiles 28 56 91 182` at `886afeb`: LEAR's check read 0.504 again, every window reproduced
16 October's scores to the last digit, and **the average read 5.195** (conformal 5.398), recorded.
Then MLflow refused the average's run: `log_range` logged every row field as a metric, and the
window `"28+56+91+182"` is text. Every tracking test had a numeric window. The held-back run would
have hit the same line at ~20:00, after writing its rows but before keeping its hourly tables, so
its p-value could only have come from a second reading. **Stopped at 17:55 with the user's
agreement**, 28 and 56 days done and nothing scored: `final_score` prints only timings until the
end, and no held-back row was recorded. Fixed (window a param only), with a test that failed on
the old code; and a test that runs `just final-score ranges` to its last line on the fixture,
record and MLflow in a temporary folder (planted: the crash, logging skipped; both caught). **The
16 October lesson again, from the other side:** the end of a long run is what no test reaches.
Both runs restarted at 18:03 at `b4b9700`. A half-written MLflow run for the 2023 average is left
in the local store; `latest` reads the newer one.

#### Hours where LEAR lies outside its window: hard hours, not QRA's failure (item 3)

From stored 2023 runs, July–December (every window inside stored LEAR forecasts), nothing refitted:

| | Outside | QRA in / out | Conformal in / out | LEAR's miss in / out |
|---|---|---|---|---|
| 28 days | 11.0 % | 4.81 / 9.79 | 4.98 / 9.23 | 13.4 / 23.6 € |
| 56 days | 6.5 % | 4.79 / 10.66 | 5.03 / 11.09 | 13.6 / 28.0 € |
| 91 days | 4.7 % | 4.81 / 12.14 | 5.08 / 12.32 | 13.8 / 30.8 € |
| 182 days | 2.9 % | 4.94 / 13.91 | 5.15 / 14.34 | 14.0 / 35.1 € |

Both methods score 2–3 times worse there, and conformal, which cannot extrapolate, as badly as
QRA; LEAR's own miss is twice as large. So these hours are the market doing something new, not
QRA's lines running past their data; only at 28 days (fewest dots) is QRA worse than conformal
there. **Recommended, not yet agreed with the user: *hours crossed* stays as it is, no size measure.**

#### Stage 3's one reading of the held-back years: QRA's lead holds (`b4b9700`)

`just final-score ranges` at `b4b9700`, 18:03–22:33: LEAR walked 913 days in 2,288 s and **the
check held** (MAE 13.283, rMAE 0.485, last week's 0.405, on 17,544 hours: stage 2's `lear daily`);
windows 2,747 / 3,100 / 3,396 / 4,625 s. "2 held-back rows recorded. This is the first reading."
The 2023 re-run at the same commit reproduced every window to the last digit and the average at 5.195.

| 2024–25, average of four windows | Pinball | 50 % band | 80 % band | 90 % band | Hours crossed |
|---|---|---|---|---|---|
| **QRA** | **4.655** | 0.494 | 0.789 | 0.883 | 15,611 of 17,544 (any window) |
| conformal | 4.983 | 0.511 | 0.805 | 0.899 | 0 |

`just significance`: held back, conformal → QRA **p = 1.2e-06** (reverse 1). On 2023: 91 days →
average p = 0.00013; average, conformal → QRA p = 0.0019, so averaging restores QRA's lead that a
single 91-day window had lost (p 0.078). **The ranking chosen on 2023 held.**

**Where the lead sits.** January–March 2024 carries most of it: QRA 3.86 / 3.23 / 2.88 against
conformal 5.26 / 4.96 / 4.91. Prices fell from ~100 € late 2023 to 61–77 €; LEAR was not biased
(mean miss −0.6 to +2.0, typical miss 13.6–15 €, as later). QRA's 80 % band was 28–36 € wide and
held 0.84–0.86; conformal kept the dearer window's 45 € and held 0.79–0.81. Read (not decomposed):
QRA's lines narrow the band on cheaper hours, conformal keeps the window's width. After March the
two are close month by month. By year: QRA 4.805 / 4.505, conformal 5.337 / 4.627.

**Stated limits.** QRA's bands are slightly narrow on these years (80 % held 0.789, 90 % 0.883);
conformal's sit on nominal. The lag remains: QRA's 80 % band held 0.71–0.76 April–June 2024, and
both fell to ~0.70–0.75 in November–December 2024, the most expensive months (LEAR's miss 19–22 €).
Pinball scales with the price level, so 4.655 is not comparable with 2023's 5.195. **Still error,
not money**: whether the range earns anything is stage 4's question. Nothing implausible: coverage
near nominal, not narrow bands that still hold.

---

**Plan refreshed:** README (status line, stage table, *Where stage 3 landed*, *Roughly when*,
structure), CLAUDE.md's stage table, `docs/architecture.md`, the plan page (version 16). **Stage 3
closed.**

**State at close (19 Oct).** `main` after this entry's commit, suite 262 green. Learnings for today
(averaging windows, backtest against live cost, the untested end of a run, the bytecode cache, why
QRA narrowed in early 2024, pinball and the price level) in `docs/learnings.md`.

---

<a id="d20261020"></a>
### 20 October 2026

#### Item 3 closed: no size measure for crossing lines

Agreed with the user after a plain-language walk-through of crossing lines, hard hours, calibration
against sharpness and why the best score may not earn the most. *Hours crossed* stays as it is;
nothing built. Reason, from 19 October: on hours where LEAR lies outside its window, conformal,
which cannot cross, scores as badly as QRA, so the crossings mark hard hours rather than cause the
loss. Shown on held-back data during the walk-through (stored runs, read only): 80 % band width
median 34.3 € QRA against 40.8 € conformal (mean 37.3 / 39.6); QRA's pinball lower on every line
checked, p5 to p95 (p10 2.90 / 2.98, p50 6.21 / 6.64, p90 3.47 / 3.81).

#### Stage 4 previewed in plain language; a rough timing sketch on 2023

Asked by the user: how bids with limits work, why a trade can fail, why the best score may not
earn the most, and whether a forecast of averages can time a battery. **Sketch, not a result**
(stored `lear daily` 2023 run, one buy hour before one sell hour per day, 0.81 round trip, no
capacity, carry-over, wear or limits): the best 10 % of days held 23 % of the year's perfect-
knowledge value (20 %: 39 %); LEAR named the exact cheapest hour on 39 % of days, the dearest on
53 %, and captured ~90 % (98 % on the best 10 % of days, 88 % on the rest). Read: ordinary days
carry most of the money, and the shape of a day matters more than its level. Not to be quoted.
**Design ideas for stage 4, not decided:** split the capture rate by ordinary against extreme days
(and by hour, which needs a rule, since profit comes from pairs of hours); the naive rule's capture
rate beside the model's. Practice claims not checked this session: decision-focused learning, and
operators correcting day-ahead positions intraday. Plain-language notes in `docs/learnings.md`.

---

### 20 October 2026, second session

**Recap (all five):** 1 half right: the two ways windows fail, not that they fail on different days
and cancel. 2 off: no one-off training, each day refits; the backtest replays 913 days. 3 not
remembered: the last step stored a text label as a number; the whole-command test catches it. 4
mostly right: pays 58 €; missing that a high limit also fills on dear hours, and the line sets the
fill rate. 5 half right: non-parallel lines right, but prices fell rather than spiked; pinball and
the price level not answered.

#### The unfilled-order rule decided: loop blocks

**Shown on real 2023 data first** (stored QRA average run, nothing refitted; an illustrative rule,
not a proposal: buy 1 MWh in LEAR's cheapest hour with its limit on the p80 line, sell in the
dearest with its limit on p20, losses and hour order ignored). With two separate limits, both went
through on 223 days, only the buy on 71, only the sell on 59, neither on 12; the buy went through
on 80.5 % of days, as a p80 line should. As a pair, the same limits went through on 90 % of days.
Two days walked through: 4 January (bought at 8.70 €, sell missed at 86.20 € against a 108.60 € limit;
the pair fills, +77.50 €) and 14 January (bought at 41.20 €, the 18:00 price fell to 13.70 €; the
pair fills neither side, no loss). Under the half-full rule the forced sale the next day fetched
178 € on 5 January and 27 € on 15 January.

**Decided with the user: loop blocks** (Hirsch & Ziel 2026). The battery never ends a day
half-traded, so every run keeps the 48/24 convention (Contract 4) and settlement checks one
condition per pair (Contract 3). Rejected: (a) half full, rebalanced next day by an unlimited order
(Nitka & Weron 2023, most papers): half the battery, a different ceiling, and our years and model
differ from theirs, so comparability buys little; (c) fixed schedule only: postpones the question.
The user asked twice before deciding: how the loop works, and how a battery can act on a real gap
it cannot know. Answered: it hands in a condition before 12:00 (the limits' gap, from the
forecast), the exchange checks it against the real gap after clearing; the decision step reads only
forecasts, settlement only actuals. **Not yet checked:** loop blocks in DE-LU after the 15-minute
switch; one package spanning several charging hours; how the range sets one minimum gain per pair;
with 90 % efficiency the volumes differ and the check is volume-weighted (my arithmetic).

**Plan refreshed:** README (*Where this is going*, *Roughly when*), CLAUDE.md, the plan page
(version 17: stage 4 under way, a *Stage 4, in order* list).

#### The perfect-foresight ceiling designed and built (`1bac4c3`, `8046d66`, `f1e7837`, `6952451`)

**Explained first, then decided with the user:** scipy's `milp` (HiGHS; already installed through
scikit-learn, now pinned as a direct import), rejected PuLP and highspy (new installs for no gain
at 192 variables a window); planning and settlement on **real hours**, the model's slots to be put
back onto real hours just before planning (rejected: planning on the 24-slot grid, whose spring and
autumn slots would need energy rules, not only price rules); `just backtest ceiling` through a new
`scripts/backtest.py` (rejected: functions only until the fixed schedule exists).

**Why a MILP, from the data.** Without an on/off switch per hour, a plan at a very negative price
charges and discharges at once and is paid for burning energy as losses; it pays below about −34 €,
and 2023 had 27 such hours (lowest −500). On 2–3 July 2023 the plain LP did it in 6 hours and
claimed 50 € too much; the switch, in none. **Defaults stated, not asked:** the first day starts
empty; the last day of a period plans alone, so 2023 never reads 1 January 2024 (Contract 2); the
planner takes prices as an argument and cannot tell real from forecast (Contract 3). Checked
before guarding: no hour missing in any split, so the hour-after-hour balance needs no gap check.

| Piece | Planted bug | Caught by |
|---|---|---|
| `plan` | losses dropped; switch made continuous; switch removed; wear removed; capacity unbounded; start ignored; power doubled | hand-worked cheap-then-dear, negative-price, wear and capacity tests |
| | **power doubled in the bounds only** | **survived**: the switch constraints already cap power at P, so the bound is redundant; planted on P itself, caught |
| `walk` | one-day horizon; window's end level carried; UTC days; both days kept; start ignored | midnight hold, carry-over, re-plan with day 3 in view, energy balance across midnights, 23-hour March day |
| | UTC days | caught only by the direct `delivery_days` check: the 48-hour window makes the schedule barely sensitive to where midnight falls |
| `settle`, `ceiling` | price an hour late; wear added; bought and sold swapped; unpriced hours dropped; ceiling plans on shifted prices; **ceiling plans without wear** | hand-worked settlement, refusal, one-window property; the last **survived** until a 50 → 66 € case was added |
| `scripts/backtest.py` | every year handed over; held-back years; 2023 plus 1 January 2024 | the command run to its last line on a stand-in cache spanning both year ends |

**My expectations were wrong twice, not the code.** At a base price of 150 buying to sell at 200
still pays (5.52 €), and at 300 on day 3 so does buying at 180; both tests were corrected with the
arithmetic beside them. And the "nothing beats the ceiling" test first ran over two days, which are
two windows, where it is not a theorem; it now runs on one.

**The ceiling on 2023, at `6952451`: 51,024 €**, 365 days, 8,760 hours, 3.2 s; median day 122 €,
best 1,108, worst −242; about 523 full cycles. Reproduces the scratch sketch shown before the code
(same formulation, so a reproduction, not an independent check). **The 12 losing days all end
full**: they buy for tomorrow (5 February: 2.22 MWh bought, nothing sold, next day 371 €). So a
capture rate split by day must follow the charge, not the calendar.

**Stated limit found while designing:** the ceiling is the best plan within each two-day window, not
over the year. A forecast-made plan can by luck carry charge into a third day and beat it, so a
capture rate slightly above 100 % is possible without a leak. CLAUDE.md's "always a bug" stays
until the fixed schedule measures how often and by how much.

Leakage check, each piece in writing during the session: no feature touched; no statistic fitted
(battery figures are constants); settlement is the only place real prices meet a schedule, and the
planner never sees where its prices came from. The ceiling plans on actuals by definition, as the
denominator, never a decision. Suite 277 green.

**Plan refreshed:** README (*Where this is going*, *Roughly when*, structure), the plan page
(version 18).

### 21 October 2026

**Recap (all five):** 1 half right: no simultaneous flow, but not that the plan is paid for burning
energy as losses; 2 mostly right; 3 half right: the losing days end full (buy for tomorrow), not
empty, and the split-follows-the-charge point not answered; 4 verdict and timing right, but stated
as two separate limits rather than the pair's gap against the limits' gap; 5 not remembered.

#### The plan's second day decided: one delivery day at a time

**The question:** at 12:00 D−1 LEAR forecasts D only, and the TSO forecasts for D+1 come out on D,
so whatever fills a two-day plan's second day is a choice. **Shown on 2023 first** (scratch, stored
`lear` run `9b2ed8d`, nothing refitted): ceiling 51,024 € two-day, 50,542 € one-day, so seeing
tomorrow is worth 482 € even on real prices. LEAR one-day 45,950 €; D copied 42,502 €; real prices
of the same weekday last week 40,627 €; **LEAR's own D+1 forecast, made a day later (a leak),
45,047 €**; leftover charge valued at 0.5–1.0 × LEAR's day mean, 45,871 → 44,220 €, falling with
the value. Walked through 23 February: the copy's 199 € morning peak bought 2 MWh at 131–151 € for
a real peak of 155 €; −253 € over two days against +1 €. Mechanism: day two only serves overnight
trades, capped at ~480 €, each a bet on a gap the size of LEAR's error. A Friday-into-Saturday
cause was tested and not supported (losses spread over the week).

**The user asked for more before deciding**: why the copy loses, what research does and promises,
good and bad ways to build it. Research, read in part: Hirsch & Ziel 2026 (German day-ahead, one day,
empty at its end); Uniejewski 2025 (half full at day end); Prat et al., *How long is long enough?*
(perfect prices: the needed horizon grows with hours-to-fill; their 10-hour storage loses 16 % at
24 h, 0.1 % at 48 h; uncertainty beyond day one left open). A Spanish 4-hour study reportedly 87 %
at 24 h, 89 % at 168 h with a real week-ahead forecast: page refused, **not verified**. **Bad way
found in our own code:** `walk(lear)` on the two-day walk silently plans D on D+1's later forecast,
and earns less, so no alarm fires. **Decided with the user: one-day plan for every run**, charge
carried. Rejected: D copied; a 36–60 h model (no TSO inputs for D+1, a second model). Stated limit:
overnight trades given up, ≤ 482 € (0.9 %).

#### Built (`a8ddc5f`, `cc573e1`, `f8b91e1`, `dcf16a1`, `a4245e8`)

Contract 4 changed with its dependents in one commit: the walk plans each day alone; the horizon
constants left `config.py`; CLAUDE.md, README and justfile reworded; tests that encoded the
two-day view replaced. **Ceiling rerun: 50,542 €** (541 cycles, no losing day). `data.from_slots`
puts slot forecasts on real hours (spring slot dropped, autumn slot on both). `backtest.fixed`
plans on one series and settles at another; the ceiling is `fixed(actual, actual)`. `just backtest
fixed` reads the stored run, ignores its slot-averaged `actual` column, and prints LEAR and naive.

| Piece | Planted bug | Caught by |
|---|---|---|
| walk | two-day window back (the `walk(lear)` leak) | **planned without seeing tomorrow**, carry-over test |
| | level reset to start / to empty | carry-over + energy balance / **only** the new carry-over test |
| | UTC days | 5 tests |
| `from_slots` | UTC clock; no blank check | clock-change tests; refusal test |
| | no tz check | **caught only by pandas' own TypeError**, not by the check |
| `fixed`, ceiling | settled at the forecast; planned on the actual; ceiling on a flat price | hand-worked −98.38 € test; settlement and ceiling tests |
| `just backtest fixed` | settle at forecast; settle at the stored slot `actual`; naive read as LEAR; no-run guard off | the command test (stand-in run with a deliberately wrong `actual`); the missing-run test |
| | held-back years handed over | **not by the new test** (a constant 5,000 € day earns nothing); the ceiling command test |

Leakage check in writing: the plan for D reads LEAR's D forecast and D−1's end level only, never D+1
(tested); nothing fitted; settlement reads the price cache on real hours, never the forecast or
the stored slot `actual`. Suite 281 green.

#### The first capture rate, at `a4245e8`: LEAR 90.9 %, naive 79.1 %

45,950 € and 39,978 € against 50,542 €, `just backtest fixed`, 9 s. LEAR never beat the ceiling on
a day; the naive rule on 4 (113 €), each one starting with different charge than the ceiling and
repaid by the day before (7–8 January: bought 2 MWh at a forecast of −1 €, real 38–88 €, −202 €,
then +4.60 €). 25 December: the naive plan started **empty** and still won by 0.40 €, because the
ceiling started full when the market paid buyers up to 13 €. **CLAUDE.md reworded with the user**
(day vs period): a period above 100 % is a bug until shown otherwise; a day can be honest.

**Plan refreshed (two milestones, one refresh):** README (*Where this is going*, *Roughly when*,
structure), CLAUDE.md, the plan page (version 19).

#### Loop blocks after the 15-minute switch: half confirmed

EPEX's *Trading at EPEX SPOT*, February 2026: "Loop blocks: families of two blocks which are executed
or rejected together. They allow to bundle buy and sell blocks to model storage", for its day-ahead
auctions incl. Germany (types not listed per country); 60, 30 and 15-minute products all offered.
EUPHEMIA public description, 18 December 2025, §5.4: a block can span non-consecutive periods with
a different volume in each and one acceptance ratio; a block's resolution may be coarser than the
hub's, so hourly blocks remain. **So one loop can carry several hours**: a buy block over every
charging hour, a sell block over every discharging hour. **Not confirmed:** the loop's acceptance
rule. EUPHEMIA 2025 never names loop blocks; linked families accept an out-of-the-money parent if
the family's surplus is non-negative, but a loop has no parent. If each block must clear its own
limit, our 20 October rule (the pair's gap against the limits' gap) is wrong, 4 January would not
fill, and the recap answer 4 correction was too strong. Also unread: whether a loop's minimum
acceptance ratio may be below 1 (EPEX sFTP spec, code C88, per a search snippet).

#### Several trades a day, and the fill assumption (end of session)

**Asked by the user:** can the battery trade several times a day, and why only one buy and one
sell? **Answered from the schedules:** it already does. Buy-then-sell rounds per day on 2023: ceiling
0/1/2/3+ on 3/162/198/2 days, LEAR's fixed schedule 3/150/209/3. 14 June (LEAR): buy 02–04 at ~87 €,
sell 07–08 at 128–136, buy 12–14 at 74–78, sell 19–20 at 142–152; two valleys (night, solar midday)
and two peaks. "One buy, one sell" came only from the 20 October illustrations and from the
papers' bidding rule (Uniejewski & Weron's cheapest and dearest hour, kept simple so each side has
one limit; Hirsch & Ziel allow one or two cycles). With loop blocks a day goes out either as one
loop (each block covering both rounds' hours, one condition) or one loop per round (each judged
alone; each round starts and ends empty, so a failed round never leaves the battery over- or
under-filled), if several loops a day are allowed.

**Asked next: what kind of problem are the two open exchange rules?** A *fill assumption*: settlement
imitates the auction, so the backtest must guess someone else's rules. What usually goes wrong: the
generous reading is taken and flatters every result (our pair rule fills 90 % of days on the 20
October illustrative rule, the strict per-block reading 61 %); rules taken from a paraphrase (ours
from Hirsch & Ziel, not EPEX); rules changing over the backtest's years (EUPHEMIA 2025 dropped the
loop wording; the 15-minute switch sits in the held-back years); silent failure, like leakage; a
bid design learning to exploit the generous rule; small rules left out (paradoxically rejected
blocks, volume tick 0.1 MW, block caps). **Proposed, not decided:** primary sources first; until
found, report bids under both rules; if one must lead, the strict one. **The user asked that the
several-trades question be settled soon rather than late**: it is now step 1 of *Next*, time-boxed.

**README and plan page corrected** (`e429a38`, plan page version 20): two of the "not yet checked"
items closed, the acceptance rule and loops per day named as binding, a step added before the bids.

### 22 October 2026

**Recap (all five):** 1 half right: the losing bet named, not why the gain is capped (only overnight
trades); 2 not remembered (a leak that lowers the score sets off no alarm); 3 right, the ceiling's
"from its own starting charge" missing; 4 right; 5 half right: two loops and its assumption, not the
direction (too many loops assumed flatters the capture rate).

#### Step 1: the exchange's rules, from EPEX's own documents (about 45 minutes)

EUPHEMIA's public descriptions (2019, 2020, 2025) never name loop blocks; EPEX's site answers
automated downloads with 403 or a maintenance page. Read instead: EPEX's press release of 13 Dec 2018
(Wayback copy), its *FRA algorithm – Public description* (11.02.2022) and *CTS++ Trader User Guide*
(v12, 19.04.2022), both for the GB frequency auction, hosted by NESO.
**(a) Pair or each block:** FRA §1.4.4, "it is a 2-block linked family where the two block orders are
parent of each other" and "If accepted, the surplus of the loop family must be non-negative".
EUPHEMIA 2020 §5.4.1 rule 3 lets an out-of-the-money parent through on its children's surplus, so
mutual parents give the pair rule: an inference, not stated for the German day-ahead. **Found on
the way:** the exchange checks surplus in euros (margin over the limit × volume), not price gaps;
with 2.22 MWh bought and 1.8 sold, the 20 October gap rule is not the exchange's even as a pair
rule. **(b) Several loops a day:** EPEX's *Block parameters* sheet (13/12/2023) caps loop families
per portfolio and market area; only search summaries were read, giving 3 or 8: **unknown**. The
user was asked to download it. **(c) Fill ratio below 1:** CTS++ "For C88, 0 < MAR < 1", FRA
"MAR in [0;1]", both GB; the press release confirms loop and curtailable blocks on the German
day-ahead from 12 Dec 2018 but not curtailable loops: **unknown**, all or nothing applies.

#### Step 2: the second round, priced (scratch, nothing committed)

The planner with a phase switch that may flip once, buy to sell, reproduces nothing new by itself;
the free walk reproduced 50,542 / 45,950 / 39,978 € and 21 October's round counts exactly.
Held to one round: ceiling 44,277 € (−6,265), LEAR 40,160 € (−5,790), naive 33,717 € (−6,261).
LEAR's share stays put (90.7 % of the one-round ceiling against 90.9 %). The second round is the
midday solar dip: 2,207 € in September–October, 221 € in January, November and December together,
where it is worth nothing on 74 of 92 days; LEAR's second round lost on 46 days (−773 €). Walked
through 14 June (both rounds, the morning one worth 31.40 € after wear, LEAR found it too) and
23 November (real evening 74–78 €, LEAR forecast 99–101 €: bought midday, −32.50 €).

#### Decided with the user, one question each

1. **One loop per round, the day cut where the battery is empty again.** The user asked first for
   bad and good ways. Bad: cutting by the clock; separate loops for rounds that share energy (17 of
   LEAR's days; a failed first round would leave the second selling energy never bought, flattering
   the result); carrying planned instead of real charge; re-planning within the day; checking one
   hour's price or price gaps; imitating the whole auction. Good: the empty-again cut merges sharing
   rounds by itself and makes every mix of fills physically possible; one loop settlement serves
   every cutting; both rules from two surpluses; wide-open limits must reproduce the fixed schedule
   to the cent. LEAR's days cut into at most 3 pieces, inside either cap reading. Option 3 (one
   round) needs a second planner, so it is the most code, not the least.
2. **Every day ends empty** (Contract 4). Measured: ceiling +14.50 €, LEAR +42 €, naive +215 € on
   2023, because a battery that fills on a paid evening meets the next paid morning with no room
   (24/25 December, +7 € over the two days). The user asked for a plain-language explanation of the
   three options before deciding. Rejected: the evening buy sent alone (planning and settling
   alternate day by day, for 3 days a year); planned but not sent (next day planned from charge not
   there). Stated limit: negative evenings before paying mornings are given up.
3. **The strict fill rule leads, the pair rule beside it**, both as surplus in euros. On
   illustrative limits (QRA's 75th percentile to buy, 25th to sell, volume-weighted): strict fills
   307 of 561 rounds for 30,192 €, pair 504 for 44,083 €, a 14,000 € gap. 11 September: strict
   drops a 673 € round whose buy missed by 3.70 €/MWh; 31 January: pair fills a −67 € round because
   those limits put the buy limit above the sell limit. Found: if the limits themselves describe a
   profitable round (1.8 × sell limit − 2.22 × buy limit − 14.40 € ≥ 0), no filled round can lose,
   under either rule; arithmetic, not yet tested.

Transparency stated before code for Contract 4 and Contract 3.

#### Built (`35259c9`, `f3a0d2f`)

One bound in `plan`: the last hour's level is empty. **Ceiling 50,557 €; LEAR 45,992 € (91.0 %),
naive 40,193 € (79.5 %), no day above the ceiling for either.** Three tests rewritten: the −200 €
switch test now starts empty; the carry-over test became "every day ends empty even when holding on
would pay" (hand-worked +3.02 €); the ceiling test now holds on every day, a hand-worked 24/25
December case (−15.98 €, 0 €).

| Planted bug | Caught by |
|---|---|
| no end-empty bound | switch test, ends-empty test, ceiling-every-day test |
| | **the first version of the ceiling test, on random prices, missed it** (both plans ended full alike); random prices caught it on 3–5 seeds of 10, so it was replaced by the hand case |
| each day restarts at `start_mwh` | energy balance across midnight |
| ceiling settled from a full start | settlement, wear and command tests |

Leakage check: the plan for D reads D's forecast only and now starts from a fixed empty battery, so
its one link to D−1 is gone; nothing fitted; settlement unchanged, real prices only. 281 green.
README, CLAUDE.md (battery, stage 4, Contract 4, the above-100 % danger zone) and justfile reworded.

**Plan refreshed (three milestones, one refresh):** README (*Where this is going*, *Roughly when*),
the plan page (version 21).

### 23 October 2026

#### Loop settlement built (`38882e0`), limits still an input

`rounds(schedule)` numbers each hour's round, cut where the battery is empty again (−1 for an empty
hour with no trade); `bid(schedule, actual, limits, rule)` judges each round's two blocks by surplus
in euros, strict or pair, drops failed rounds and pays the rest through `settle`. Limits come in as
one row per round, so how the range sets them stays open. A round without limits is refused: NaN
compares as "no" under both rules, and the round would vanish quietly. **On 2023, LEAR's schedule
cuts into 561 rounds, at most 3 a day; with open limits both rules return the fixed schedule's
45,991.96 € to the cent.** Tests on hand-written schedules (the planner left 0.2 MWh between rounds
on the first test prices, a tie too fragile to test on).

| Planted bug | Caught by |
|---|---|
| cut also where selling turns to buying | the cutting test (shared-energy case) |
| strict as pair; pair as strict | strict-and-pair test |
| buy block at its plain average or dearest hour | strict-and-pair test |
| sell block at its plain average or cheapest hour | strict-and-pair test, **only after its sell limit was set to 113**: at first it was wide open, so the sell side's weighting was untested |
| failed rounds kept | strict-and-pair test |
| no missing-limit guard | refusal test |
| sell surplus sign flipped | strict-and-pair test, open-limits test |

Leakage check: `bid` reads the schedule and limits (decision side) and real prices only to fill and
pay; nothing returns to a plan; nothing fitted. Where limits come from is checked when built. 285
green. Not a plan milestone: no number measured.

### 26 October 2026

**Recap (all five):** 1 half right: the cut packages the plan, and sharing rounds sent apart flatter
the result (direction missing); 2 right instinct, wrong cause (the ceiling can't misjudge prices, it
can't see tomorrow); 3 not answered (strict drops, pair fills); 4 half right: the solar dip, not why
LEAR lost (error as big as the gap); 5 half: a test sees a bug only if its inputs make it matter.
EPEX *Block parameters* sheet not on disk (docs/, Downloads, Desktop, Documents): cap still unknown.

#### Step 1: the limits, read and measured before deciding

**The field.** Read through arXiv's HTML pages (the PDFs would not convert here; formulas came
through a summariser, so the reading of q is inferred). Nitka & Weron 2023: a buy limit at the
(1−q)-quantile, a sell limit at the q-quantile, q = (1−α)/2 read from a garbled "q=1−α2" (only that
reading fits their 80 % interval example), α from 0.5 to 0.9; their best model earned most at α 0.5,
that is p75/p25; one hour per order. Hirsch & Ziel 2026: the same family as their benchmark (buy at
the (1−α)-quantile, sell at the α-quantile, one hour each); its expected profit can be raised by a
too-wide forecast, and it ignores how hours move together; their own method picks hours by a risk
measure over simulated joint days (Gaussian copula), the stochastic program rejected 15 October.
**Neither has a rule for a block over several hours.**

**One limit for a block.** The exchange compares a block's limit with its real prices averaged by
volume, so the limit is QRA's percentiles averaged by volume. On LEAR's 561 rounds of 2023 (stored
range `78b90af8`, built on the identical LEAR forecast, max difference 0.0): at p75 77.0 % of buy
blocks pass against 76.7 % of single buy hours; p90 91.3 % against 90.8 %. LEAR's hour-to-hour error
correlation is 0.84, so the average barely narrows. Blocks: 503 rounds buy over 3 hours, 521 sell
over 2.

**Which percentiles, and the guard (scratch, before deciding).** The field's p75/p25 band promises
a loss on 208 of 561 rounds (margin 1.8 × sell − 2.22 × buy − 14.40 € below zero). A sweep with that
band (strict / pair): p50 19.4 / 62.0 %, p75 59.7 / 87.2 %, p90 78.0 / 90.7 %, p99 89.7 / 91.0 %;
dropping rounds that fail the guard: p75 49.8 / 75.5 %. **Found:** the two surpluses add up to real
earnings minus the margin, so the pair rule fills a round exactly when it earned at least the
margin; and loosening limits to a margin of exactly 0 only adds rounds that earn ≥ 0, under either
rule. Moved to break-even: strict 81.0 % (p75), 80.3 % (p90), 79.8 % (LEAR's own averages, no range);
pair 92.2 % for every one. The fixed schedule's 42 losing rounds lost 608 €: the most any limits on
its hours can add.

**Decided with the user, one question each** (the second rephrased in plain words on request):
1. **One limit per block: the range averaged by volume.** Rejected: QRA refitted on block averages
   (a new walk per round shape, for a 0.3-point gap); one representative hour (not what the exchange
   checks).
2. **Limits at break-even, starting from p75/p25.** Rejected: the band as published (filled rounds
   can lose; 31 January −67 €); dropping rounds that fail the guard (208 skipped, most of them good);
   picking the best band on 2023. p90 was shown on 2023 before the choice and did slightly worse.

#### Step 2: built (`27b25c0`)

`backtest.limits(schedule, buy_at, sell_at)`: per round, both sides averaged by volume, then moved
by the same EUR/MWh to a margin of 0; refuses a traded hour with no range price. `just backtest
bids` reads the stored LEAR run and QRA range, refuses a range built on another LEAR forecast, and
counts filled rounds that lost money (the guard's alarm).

**Bids on 2023: strict 40,956 € (81.0 %), 366 of 561 rounds; pair 46,600 € (92.2 %), 519 rounds;
0 lost money under either.** Ceiling 50,557 €, fixed LEAR 45,992 € (91.0 %), unchanged.

| Planted bug | Caught by |
|---|---|
| limits not moved | hand case, margin-zero test, guard test |
| moved the wrong way | hand case, margin-zero test, guard test |
| wear left out of the margin | hand case, margin-zero test (**not** the guard test: only losses smaller than the wear slip through) |
| plain average instead of by volume | hand case |
| the whole move on the buy side | hand case (margin is still 0) |
| move shared over MWh bought only | hand case, margin-zero test (limits too safe, so the guard test passes) |
| no missing-price check | refusal test |
| no same-forecast check | command refusal test |
| bids planned on the naive forecast | perfect-forecast command test |
| bids paid at a forecast | perfect-forecast command test |
| losing rounds never counted | **survived at first**; caught after adding the backwards-forecast alarm test |
| 2024 read too | ceiling command test (the bids test's flat 5,000 € day never trades) |
| **band swapped (buy p25, sell p75)** | **survives**: moving to break-even undoes any band set a constant distance either side of the forecast, so stand-in data cannot see it; only the band's uneven shape reaches the limits |

**Leakage check.** (1) The limits read the plan for D (LEAR's forecast for D) and QRA's p75/p25 for
D, fitted on days strictly before D (`x.index < day`); D−1's prices were public at ~12:45 on D−2.
(2) Nothing fitted here; the band is the paper's. (3) Real prices only in `bid`, to fill and pay;
the command's check compares two forecasts. 292 green.

**Stated limits:** one year; the backtest fills every loop whose limits were beaten, while EUPHEMIA
may reject a block in the money (not checked for loops); the 11-point gap between the rules rests on
a rule not confirmed for Germany.

**Plan refreshed (milestone: the bids' first capture rate):** README (*Where this is going*, *Roughly
when*), the plan page (version 22).

#### Step 3: LEAR's lead in euros, tested (`d7d5ddd`)

Explained before code: the project's Diebold-Mariano test (`_dm_days`, 7-day allowance for runs of
good and bad days) on each delivery day's earnings gap, rather than a sign test that ignores how
much a day was won by. `evaluate.dm_earnings(first, second)` takes daily totals by Berlin day;
`just backtest fixed` prints it. **LEAR earned more than the naive rule on 261 of 365 days, 15.89 €
a day on average, one-sided p 1.4 × 10⁻¹⁷ (2.7 × 10⁻¹⁹ with no allowance); ahead in every month**
(162 € in June to 916 € in October).

| Planted bug | Caught by |
|---|---|
| gap sign flipped | hand case (p 0.00067), direction test, fixed command test |
| days not lined up | the only-shared-days test |
| allowance for runs switched off | **survived**; caught after adding a runs test |
| command: arguments swapped | fixed command test |
| command: days cut at UTC midnight | fixed command test |

**The runs test was wrong at first:** runs of 5 good and 5 bad days make days 5–7 apart move in
opposite directions, which *shrinks* the allowance (p 5.5 × 10⁻⁹ against 3.9 × 10⁻⁶ without it).
Runs of 21 days, longer than the 7-day window, make it grow. The planted bug was re-run after the
fix, because its first "catch" was the broken test failing on its own. 296 green.

Leakage check: reads only settled earnings of two finished runs; nothing fitted; no decision path.

**Plan refreshed (milestone: the open significance question closed):** README, plan page (version 23).

**Asked mid-session, answered in plain words:** what "the first loop can fail" means (two loops
cut at noon on a day whose evening sells night energy: the night loop fails, the evening loop still
fills, and the backtest is paid for energy never bought); how 22 October's idea (the guard, both
rules) leads to today's finding; and, rephrased again on request, what "strict leads" means and
what the guard checks (11 September and 31 January walked through).

#### Step 4: the stored models ranked by money (`2f2f348`)

Asked to continue; order changed first: a model choice must come before the held-back reading
(Contract 2), so the CatBoost / Random Forest question went ahead of it. Its cheap first step:
plan on the three stored 2023 forecasts (one `just train daily` batch, `9b2ed8d`). **LEAR 91.0 %,
tree 90.7 %, straight line 91.6 %**, the line clearly worst by error (rMAE 0.615 against 0.504).

**The user stopped the recommendation twice, rightly.** First: think calmly about why the line won,
whether the reasons hold, and what could improve. Second, before deciding: why the line does not win
in other papers, and whether the data is enough. What came out:

- **No win.** Line over LEAR p 0.18 (ahead on 184 days, behind on 158; first stated as 207, ties
  counted as wins); its 10 best and 10 worst days cancel (+517 / −514 €), months split 7 to 5.
- **Data not enough to rank the three.** The smallest gap one year detects (80 %, one-sided 5 %):
  1.4–1.7 points between models; observed 0.2–0.8. The line's +0.83 €/day would need about 7 years.
  Enough for LEAR against naive (11.5 against 3.4) and for the average against LEAR (3.0 against 1.2).
- **Level against shape, tested by intervening.** Shifting LEAR by −20 to +20 € moves earnings by
  ≤ 0.4 points (cycles 584 to 527: losses of 19 % make a high forecast cautious, so the level is
  cheap, not free; the first explanation said free). Hindsight diagnostics only: the true daily level
  adds nothing to any model; the true shape takes each to 99.5–99.8 %. The line's extra error is
  mostly level (13.86 against 10.16 €). The average shape error does not explain the order (the tree
  has the best, 9.98, and earns least), and the order is noise, so no metric was fitted to it.
- **The field.** Spread THieF (arXiv 2609.23223, DE and ES 2021–25): accuracy and profit rankings
  differ, value lies in "the relative evolution of prices within the day"; foundation models for
  arbitrage (arXiv 2609.00089): "lower statistical errors do not necessarily imply higher cumulative
  profits". Neither tests its profit gaps. The straight line loses on accuracy there as here; nobody
  claims it trades best. Not seen: whether ARX beat the plain neural net in Spread THieF.
- **The average of the three, hour by hour: 47,485 €, 93.9 %**, ahead of LEAR on 207 days, behind on
  105, p 1.9 × 10⁻⁹; shape errors correlate 0.71–0.78. Plans expected more than they earned: LEAR by
  906 €, the line 2,227, the tree 3,723 (an optimiser picks hours where the forecast erred low).

**Decided with the user:** (1) the average is a candidate, in `just backtest fixed` beside the three
and the naive rule; the held-back reading scores, fixed now: LEAR, the average, the tree and the line
as fixed schedules, the bids on LEAR under both rules, the ceiling. (2) No new algorithms in stage 4:
a new member's gain to the average would likely sit below the 1.2 points one year detects. CatBoost
and Random Forest closed; a neural net (the field's LEAR partner) after stage 5.

Built: `forecasts()` reads the three runs of one batch and their mean; each lead tested day by day.

| Planted bug | Caught by |
|---|---|
| average of LEAR and the tree only | fixed command test (LEAR and tree miss one way, the line twice as far the other, so only the true mean is exact) |
| median instead of mean | same |
| sum divided by 2 | same |
| the tree read from LEAR's column | same |
| runs read without the batch filter | same |
| lead's p reversed | same |
| ahead and behind swapped | **survived**: the assertion searched the rest of the output, where the tree's line satisfied it; caught once narrowed to the average's own line |

Leakage check: the average is the mean of three forecasts each made at 12:00 on D−1; nothing fitted;
settlement unchanged. Found on 2023 and tried once, so the held-back years are its test. 296 green.

**Plan refreshed (decision changing scope):** README (*Where this is going*, *Parked on purpose*,
*Roughly when*), CLAUDE.md (parked models), the plan page (version 24).

**Asked at the close, answered in plain words:** what fixing the held-back list before looking
means: why each item is on it, what 2024–25 can show (the average's lead, a sunnier market, the loop
cap) and what it cannot (a ranking of the three single models), and that the result stands as read.

### 27 October 2026

**Recap (all five):** 1 answered another question: spikes explain why the plan misses 100 %, not the
92.2 % roof (limits can only refuse rounds in the plan; dropping its 42 losing rounds is the most);
2 right, missing why strict refuses good rounds (each block judged alone); 3 half right: shape named,
not "level", nor why it is not free (losses bought at the market price); 4 half, cut off: averaging
cancels only the error the models do not share; 5 first part right, the bigger battery wrong (gaps
and daily swings scale alike), why read 2024–25 and what to fix first missing. Corrected in writing:
strict gives up about 5,600 € of gains, first said 5,000. EPEX *Block parameters* sheet not on disk
(docs/, Downloads, Desktop): cap still unknown.

#### Step 1: checked before any code (decision side only, no 2024–25 price read)

Stored held-back runs, all at `9b2ed8d`: LEAR `393b88b1`, tree `56ff405b`, line `9a3f131c`, naive
`5c06e862`; each 17,544 slots, no gaps; LEAR's run's naive column equals the naive run. QRA range
`d248116a` (`b4b9700`): every slot, p75/p25 complete, **its LEAR differs from the plan's by 0.0**.
LEAR's plan on 2024–25 cuts into 1,103 rounds, **at most 3 a day** (0: 4 days, 1: 355, 2: 368, 3: 4),
inside either cap reading. No battery number on 2024–25 had been computed before.

#### Decided with the user, one question each

1. **`just final-score battery`**, beside stage 2's and 3's readings; `just backtest` keeps no path
   to the held-back years. Rejected: `just backtest test` (gives the 2023 command that path).
2. **A stamped record, `reports/capture_scores.csv`**, through `train.record`, with the first-reading
   note. Rejected: print only (a second reading would leave no trace in git).

What gets printed was not a choice: the list of 26 October and nothing else (no year or month split).

#### Built (`21a87ba`)

`scripts/backtest.py`: `actual_prices`, `forecasts`, `ranges`, `capture`, `bids` take the split
(held-back runs are named `lear daily` etc.); printing moved into `show_fixed`, `show_bids`.
`final_score.read_battery` runs them on `test` and records 8 rows. **2023 reproduced to the euro**
(91.0 / 90.7 / 91.6 / 93.9 / 79.5 %, p 1.4e-17, bids 81.0 / 92.2 %). Two tests on a stand-in cache
with 5,000 € on 31 Dec 2023 and 1 Jan 2026, runs found only by their held-back names. 298 green.

| Planted bug | Caught by |
|---|---|
| prices read from 2023 | battery reading test |
| forecasts or range ignore the split | battery reading test |
| held-back run read by its 2023 name | battery reading test |
| capture or bids not handed the split | battery reading test |
| rows labelled valid | battery reading test |
| share of fixed LEAR, not the ceiling | battery reading test |
| bid rows carry fixed LEAR's euros | battery reading test |
| days counted at UTC midnight | battery reading test |
| missing-run message names 2023's command | names-the-run test |

Leakage check: (1) the plan for D reads the stored forecast for D (daily refits on days before D);
QRA's range for D learns from days strictly before D; limits read the plan and the range only. (2)
Nothing fitted: equal weights, the paper's band, break-even from decision-side numbers. (3) Real
prices only to settle; the stored `actual` column unused; the one forecast-to-forecast comparison
is the same-LEAR check.

#### The reading, once (run at `21a87ba`, 43 s; recorded `85540a0`)

"8 held-back rows recorded. This is the first reading." 731 days.

| Share of the ceiling | 2023 | 2024–25 |
|---|---|---|
| Ceiling | 50,557 € | 134,077 € |
| **Bids, strict** (803 / 1,103 rounds, 0 lost) | 81.0 % | **90.1 %** |
| Bids, pair (998 / 1,103, 0 lost) | 92.2 % | 94.0 % |
| LEAR, fixed | 91.0 % | 93.0 % |
| Average, fixed | 93.9 % | 94.4 % |
| Line, fixed | 91.6 % | 92.8 % |
| Tree, fixed | 90.7 % | 92.2 % |
| Naive, fixed | 79.5 % | 84.9 % |

Day by day: LEAR over naive 501 / 211 days, +14.78 €/day, p 1.3e-26; **average over LEAR 372 / 224,
+2.67 €/day, p 0.00013**; tree −1.41 €/day, p 0.94; line −0.29 €/day, p 0.63.

**The alarm, explained, nothing changed.** Line and average each "beat the ceiling on 1 day, by 0
EUR": 8 Apr 2024 by 1.3 cents, 5 Feb 2024 by 0.7 cents, same volume traded. HiGHS stops within its
default relative gap (1e-4); re-solved with gap 0, the ceiling equals the line and sits 0.4 cents
above the average. Stated limit: the ceiling may sit up to ~0.01 % low (≤ ~13 € over two years).

**Found on the way:** `.gitignore`'s blanket `*.csv` swallowed the record; unignored like the two
other score files, in the record's commit.

#### Stage 4 closed (`ae41d0e`)

Headline **capture rate 90.1 %** (bids on LEAR, strict; 94.0 % pair). README (status, stage table,
*Where stage 4 landed* with what stage 5 starts from, *Roughly when*, structure), CLAUDE.md (stage
table; the third early-warning sign now has its instrument).

**Plan refreshed (milestones: the held-back reading, stage 4 closed):** README, the plan page (version 25).

**Asked after the close, answered in plain words:** what the results mean in practice (per year: ceiling
~67,000 €, fixed LEAR ~62,300, strict bids ~60,400, naive ~56,900; the forecasting work is worth ~5,400 €
a year over the naive rule, the average ~1,000 more), whether they are reasonable, where the approach is
simpler than reality (one market, hours not quarter-hours since 1 Oct 2025, price-taker, guessed exchange
rules, simplified costs), whether it can forecast tomorrow (**no**, checked: the pull stops at
`PULL_END` = 31 Dec 2025 and re-fetches everything; `complete_rows` drops tomorrow's priceless row; no
single-day command), and a look back on the project. Then strict against no limits, on 2024–25 from
the recorded totals: strict stopped losing rounds worth 1,376 € (pair − fixed) and winning rounds worth
5,197 € (pair − strict), net −3,821 €; so under the strict rule sending the plan without limits pays more.

**Decided with the user, one question each:** (1) three additions, in order: published German battery
revenues against our euros; a one-page summary at the top of the README; in stage 5, a Streamlit page.
Rejected: summary first (rewritten if the check finds something), stage 5 first. (2) The page shows past
results first (a day's forecast, range, real price, plan, earnings; the capture rates), tomorrow's
forecast once the daily run exists, from a small committed data file (MLflow is not in git). Rejected:
tomorrow only (nothing to show yet), past results only.

**Plan refreshed (decision changing scope and dates):** README (*Where this is going*, stage table,
*Roughly when*), CLAUDE.md (stage table), the plan page (version 26).

### 30 October 2026 (begun 28 October)

**Recap (all five):** 2 right (the cent; missing how it was shown: re-solved at gap 0); 1 half right
(insurance, yes; missing that strict judges each block alone, and that the first check is euros and
rounds refused per year: 195 of 561 and ~5,600 € on 2023, 300 of 1,103 and ~2,600 € a year on
2024–25, while the ceiling grew ~50,600 → ~67,000 € a year); 3 half right (final exam, yes; "wrong
metrics" no: no path from daily work, and a second reading leaves rows in git); 4 wrong (not regimes:
the average's lead is clear on two separate periods, the line's never was, p 0.18 and 0.63); 5 not
understood, explained (the plan is decision-side, the score is not). Written to `docs/learnings.md`.

#### Step 1: our euros against published German battery revenues

Searched, then each source's method read before its number. Ours: day-ahead alone, hourly, 81 %
round trip, 8 €/MWh wear charged (`backtest.settle`), before fees; ceiling ~67,000 € a year.

| Source | Markets | Battery | Foresight | Costs | Period | Figure |
|---|---|---|---|---|---|---|
| PortfolioEnergy, "RTC-Tools (day-ahead only)" | day-ahead | 2 h, rest not stated | not stated | not stated | 2025 | 89 k€/MW/yr |
| Aurora (solarserver, pv magazine, Feb 2025) | DA, ID, FCR, aFRR | 1 MW / 2 MWh | not stated | not stated | 2024 | 180,000 € |
| Enervis index (ess-news) | ID, FCR, aFRR | 1 MW / 2 MWh, 87.5 % RT, 1.5 cyc/day | imperfect | not stated | 2024 | ~144 k€/MW/yr (2025 fc 134 k) |
| enspired / ISEA | all five | 1.22 cyc/day avg | not stated | not stated | Apr–Dec 2024 | ~100–220 k€/MW/yr annualised |
| Modo | DA, IDA, FCR, aFRR, ×0.80 | 88 % RT, 1.5 cyc/day | auctions perfect | no grid fees | from May 2026 | not our years |
| Pexapark | DA "arbitrage opportunity" | 2 h | — | — | Jul–Aug 2024 | 274 €/MWh, undefined |

Left out: hobby GitHub repos (their figures changed between two reads: 75.6 / 80.5 / 83.9 k);
the 50Hertz study (10 MB PDF, no reader installed); a search summary turning "1 MW earned 180,000 €"
into "90,000 per MW". Shares of a stack ("29 % energy trading", Phelas's "~10 %", Modo's 2026 DA slice)
not usable: untraced, illustrative, or outside our years.

**Comparable, and what it says.** (1) All-market figures are 2–3× our ceiling, most of it reserve: the
finding, and a limit now in the README. (2) A day-ahead *share* of a stacked battery understates
day-ahead alone (reserve holds part of the battery back), so the user's suggestion to read shares off
the studies was checked and set aside for that reason. (3) One day-ahead-only figure, above our ceiling,
every known difference pointing that way: a direction. (4) No published figure plans on a forecast.

**ISEA, checked twice.** The user read it as FCR, aFRR and continuous intraday only: right for its
headline "Cross-Market" ("For now we include FCR, aFRR and intraday continous trading"), but its
monthly chart also scores DA alone (ENTSO-E, DE-LU, hourly, 90.25 % RT, 1 or 2 cycles, day closed,
deliberately simple). Its settings pull both ways, so it is a candidate only if our ceiling is re-run
on them over the overlapping months (from late 2024). Its chart data could not be fetched: calling the
page's data feed directly was refused as circumventing the site, and not retried.

**Decided with the user:** record as a direction (README *Where stage 4 landed*, *Honest framing*,
*Roughly when*). Rejected: splitting the ceiling by year now (a new reading of 2024–25, too little
to reconcile against); building the ISEA check (new code, a second look at 2024–25 prices).

**Plan refreshed (milestone: the revenue check):** README, the plan page (version 27).

---

### Next — next session

**Stage 5 starts.** Main after this entry's commit, 298 green. Stage 4 closed on the held-back years
(`just final-score battery`, read once at `21a87ba`): strict bids on LEAR **90.1 %**, pair 94.0 %;
fixed LEAR 93.0 %, average 94.4 % (p 0.00013 over LEAR), naive 84.9 %; ceiling 134,077 €.

#### Recap questions

1. Sending LEAR's plan without limits kept 93.0 % on 2024–25, the strict bids 90.1 %. On 2023 the gap
   was 10 points, now 2.9. What does the strict rule do that costs money, and what would you check
   first to learn why it cost less on these years?
2. The line and the average "beat the ceiling" on one day each. Why was that not a leak, and how was
   it shown rather than assumed?
3. Why does the held-back reading live in `final_score.py` rather than `just backtest`, and what does
   the stamped record protect against?
4. The average's lead held on 2024–25; the line's 2023 lead over LEAR turned into a deficit. Why is
   the first a finding and the second not a reversal?
5. Before the reading, LEAR's plan on 2024–25 was cut into rounds to count loops per day. Why was
   that safe to do before looking, when settling it was not?

#### Then, in order

1. **Our euros against published German battery revenues.** Find figures for day-ahead arbitrage
   alone, for 2024 and 2025, per MW of a 2-hour battery, and read each source's method before
   comparing (all markets or day-ahead only, before or after fees, which battery). Our ceiling ~67,000 €
   a year, fixed LEAR ~62,300, strict bids ~60,400 for 1 MW / 2 MWh. A gap is a finding to explain,
   not a reason to change anything already read.
2. **A one-page summary at the top of the README**, for a reader deciding whether to hire: the question,
   the headline, what held and what did not, the limits, and how to reproduce, before the detail.
3. **Stage 5's first decision: what a scheduled run sends each morning.** LEAR's plan (one daily refit,
   a range built for it) or the average (more money on both readings; three daily refits, no range of
   its own). Under the strict rule, sending without limits earned more on both readings: say so when
   explaining. One question.
4. **Stage 5 planned before building**: the daily run (a "tomorrow" command, an incremental pull, a
   row without a price), drift monitoring, and the Streamlit page, past results first. Streamlit is a
   new dependency, so `requirements.txt` in the same commit. Say what "reproducibility" measures.
5. Noted, not tasks: the EPEX *Block parameters* sheet (cap not binding: ≤ 3 loops a day on both
   readings); EUPHEMIA may reject a block in the money; the ceiling solved to HiGHS's default 0.01 %
   gap; QRA narrow in November–December 2024; why every share rose on 2024–25 (not tested); the
   market trades quarter-hours since 1 October 2025, the models hours.
