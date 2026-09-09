# Work log — Battery Storage Backtest

Running record of what was done, what was decided, and what was found. Newest session
last. Written for a reader who was not present: what changed, and why it changed.
Decisions belong here with their reasoning; `CLAUDE.md` holds the standing rules and
`HANDOVER.md` the decisions settled before any code existed.

---

## Stage 0 — Data · 8–9 September 2026

**Stage goal:** a reproducible data pull with the split locked.
**Checkpoint:** runs twice identically; coverage counted.
**Status:** groundwork and `config.py` complete. Data pull blocked by an ENTSO-E outage;
a verified fallback exists.

---

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
Server-side, unrelated to the token or the local setup. Still failing on retry at 10:44 UTC.

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

#### Housekeeping

Work log moved from `logfiles/` to `docs/`, and `logfiles/` deleted — it was an empty
leftover, and `.gitignore` already covers `logs/` and `*.log` for stage 5 runtime output.
A work log is documentation, not runtime output, so it belongs in version control.

---

### Commits

| SHA | Date | Summary |
|---|---|---|
| `c9ba760` | 08 Sep | Create CLAUDE.md to provide project context & engineering laws *(amended from `dc43e9a`)* |
| `5b5dcda` | 08 Sep | Fix data/ ignore rule so the directory skeleton survives a clone |
| `7beaa76` | 08 Sep | Pin stage 0 dependencies and document the required API token |
| `e7c23c3` | 08 Sep | Add config.py as the single source of truth for split and market |
| `5dec185` | 09 Sep | Set battery cycle degradation cost to 8 EUR per MWh discharged |

---

### Open items

1. **Python version undecided.** Running 3.11.3 — a patch release now past bugfix support,
   and the only version pyenv has installed. 3.13.x is available and every current and
   planned dependency (pandas, pyarrow, scikit-learn, pulp, lightgbm, entsoe-py) ships
   3.13 wheels. Cheapest to switch now, while there is almost no code and no data.
2. **`.vscode/` ignore rule** still blocks committing `settings.json`, so the interpreter
   choice is not reproducible from a clean clone.
3. **Tests not yet written.** Agreed scope: Contracts 1, 2 and 5 only. Needs `pytest` in
   `requirements.txt` in the same commit.
4. **`src/sources/` not yet recorded** in CLAUDE.md's Quick Reference.
5. **SMARD filter-ID mapping unresolved** — blocks using SMARD for anything but prices.
6. **Coverage uncounted** (HANDOVER open question 1): gaps in DE-LU 2018–2025 unknown,
   because no bulk data has been pulled.

### Next

The three data-layer pieces, none of which need the API to be reachable:

1. **Catalog** — the data items as declarative records carrying an `available_at` claim,
   making Contract 1 a field that can be asserted on rather than a comment.
2. **Fetch and cache** — immutable timestamped pulls plus `manifest.jsonl`, which also
   supplies the incremental retrieval an MLOps loop needs, and answers HANDOVER open
   question 2 (does ENTSO-E revise published values?) by letting two pulls be diffed.
3. **Normalisation** — the single Contract 5 choke point: UTC, hourly, the 60→15-minute
   transition, and gap counting.

The `src/sources/` split earns itself here: SMARD works today, the API does not, and the
layer above neither knows nor cares which supplied the bytes.
