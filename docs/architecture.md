# How this project is put together

A map, for someone opening the repository for the first time.

Read this before reading any code. It says what each file is for and how they connect,
so that opening a file is a decision rather than a guess.

**This is not the rulebook.** [CLAUDE.md](../CLAUDE.md) holds the laws and the five
integration contracts — the things you must not break. This file holds the shape.

---

## The one-sentence version

Ask ENTSO-E for German electricity data, predict tomorrow's prices, use the prediction to
decide when a battery should charge and discharge, then check how much money that decision
would really have made.

---

## The shape

```
   COMMANDS                 THE LIBRARY                       ON DISK
   (scripts/)                 (src/)

                    ENTSO-E Transparency Platform
                                │
   just verify ─────▶  sources/entsoe.py        the catalog: what may we ask
                                │               for, and what may a model see?
   just pull ───────▶      data.py      ─────▶  data/raw/*.parquet
                                │               (fetch · repair · cache · never overwrite)
   just explore ────▶    (reads data) ───────▶  reports/figures/
                                │
   ═══════════════════ features.py ════════════════════  ◀── THE GATE
                                │                             Contract 1 lives here
   just train ──────▶     models.py
                                │
   just backtest ───▶    backtest.py
                                │
                        evaluate.py    ───────▶  reports/

   config.py  ──  every box above reads its settings from here
```

`src/` is the machine. `scripts/` are the buttons on the front.

**The double line is the most important boundary in the project.** Above it, everything is
transport — getting bytes from ENTSO-E onto disk without damaging them. Below it, everything
is a decision. `features.py` is where the question changes from *"did we fetch this
correctly?"* to *"were we allowed to know this?"*

---

## One question per file

Each file answers exactly one question. If you can't say which, it is doing too much.

| | File | Its one question | Status |
|---|---|---|---|
| **Settings** | `src/config.py` | What are the fixed facts of this project? | built |
| **Library** | `src/sources/entsoe.py` | What may we ask for, and what may the model see? | built |
| | `src/data.py` | How do we get it, keep it, and make it consistent? | built |
| | `src/features.py` | What does the model get to look at? | **built** |
| | `src/models.py` | What will tomorrow's prices be? | next |
| | `src/backtest.py` | What should the battery do, and what did that earn? | planned |
| | `src/evaluate.py` | How good was it? | planned |
| **Buttons** | `scripts/pull.py` | Go and get the data. | built |
| | `scripts/verify_forecast_series.py` | Are these series really forecasts? | built |
| | `scripts/explore.py` | What does the record actually contain? | built |

Seven of ten exist. Everything marked *planned* is a name and an intention, nothing more.

---

## The one arrow that never reverses

```
   scripts/  ──imports──▶  src/
   scripts/  ◀──never───   src/
```

| | What it is | How to tell |
|---|---|---|
| `src/` | The library. Definitions. | Nothing in it runs by itself. |
| `scripts/` | The entry points. | You run these. `just` runs these. |

If something in `src/` ever needs to import from `scripts/`, it is in the wrong folder.

This is also why `scripts/` has no `__init__.py`. That file marks a folder as a library,
and `scripts/` is the opposite of a library.

**Scripts should stay thin.** Read the settings, call the library, print the result, return
a number. A script that grows is usually holding logic that belongs in `src/`.

---

## The catalog, and why it is a file

`src/sources/entsoe.py` is a list of five entries. It holds no market data at all — not one
price, not one megawatt. Think of it as a box of index cards, one per kind of data we can
ask for:

```
    name          load_forecast
    ask for it    query_load_forecast
    comes in      megawatts, every 15 minutes
    published     the morning before delivery
    ──────────────────────────────────────────
    may the model see it?     YES
    why                       published before the deadline
```

Those last two lines are the reason it exists as a file rather than a comment.

**"May the model see it?" is the rule the whole project stands on.** Written as a sentence
in a document, only a person can check it. Written as a field on a record, two different
things can read it:

| Reader | What it does |
|---|---|
| A script, while running | "the catalog says use `query_load_forecast`" — so it does |
| A test, offline | "does every entry point somewhere different?" — fails if not |

The rule stops being something to remember and becomes something to check. That is worth a
file.

---

## Getting data and splitting data are different jobs

They feel like one step. They are not.

| | Does what | Lives in |
|---|---|---|
| **Download** | Get raw data. Save it. Never edit it. | `src/data.py` |
| **Split** | Cut a loaded table into train / validate / test | `src/config.py` |

**You download once. You can re-split as often as you like.** The files on disk hold one
long undivided series; the split happens in memory, every time something needs it.

If splitting meant downloading, every experiment would cost an API call — and the rule that
a saved pull is never quietly overwritten would be impossible to keep.

---

## Where data lives

```
data/raw/         what ENTSO-E sent, on a UTC index, at the resolution it arrived in
  archive/        copies displaced by a revision.  Never deleted.
  manifest.csv    one line per series per pull
data/interim/     empty, and nothing reads it
data/processed/   empty, and nothing reads it
```

**The last two are scaffolding that never found a use.** They were created on day one for a
feature table that would be written to disk. `features.py` builds its 63,575 rows in under a
second, so caching them would add a staleness problem in exchange for nothing. Recorded here
rather than quietly left, because an empty directory implies a workflow that does not exist.

None of it is committed. It is rebuilt by a command. Any number reported in the README has
to be reproducible from a clean copy of the repository — that is the Third Law, and it is
what keeps the results honest.

**The raw files keep their original resolution.** Converting to hourly happens in
`load()`, every time, rather than being baked into the file. That way a normalisation bug
is fixed by editing code, not by pulling again — and pulling again months later would get
whatever ENTSO-E believes today, not what it said when the result was published.

## A pull never overwrites

ENTSO-E revises published history. A pull months after the last one can quietly rewrite the
years a published result was built on, and nothing errors. So every save compares against
what is already on disk, and there are four outcomes:

| Outcome | What happened | Archived? |
|---|---|---|
| `created` | nothing was there before | — |
| `unchanged` | byte-for-byte the same data | no |
| `extended` | new rows on the end, nothing rewritten | **no** |
| `revised` | **an existing value changed** | **yes** |

The third row is the one that makes this practical. Appending is not overwriting, so
reaching further forward in time does not fill the disk with copies. Only a genuine
rewrite displaces anything.

And the second row is the Third Law check: **run `just pull` twice and every series should
say `unchanged`.** That is what "reproducible" means, made observable.

## A pull also repairs what the client library drops

`entsoe-py` splits any request longer than a year into blocks, then removes each block's
first timestamp, expecting it to duplicate the previous block's last one. The API returns
half-open windows, so it does not — and a real value is deleted. Seven hours vanished from
the price series that way before anyone counted them.

So after fetching, every series is checked against its **own spacing** and anything missing
is re-fetched in a narrow window. The check works from the data rather than from the
library's block arithmetic, so it is not tied to the one defect that prompted it.

A re-fetch that recovers nothing is useful too. It separates *we failed to fetch this* from
*this was never published* — which is exactly the distinction a coverage count needs, and
the reason the load-forecast gaps can be called genuine rather than assumed to be.

What the history actually contains is recorded in [data-quality.md](data-quality.md).

---

## The gate: how `features.py` keeps the future out

This is the file the whole backtest rests on, so it is worth understanding before anything
downstream of it.

It turns three cached series into **one table, one row per delivery hour, 18 columns**. One
column is the answer. The other seventeen are things the market knew before it had to decide.

### Three treatments, decided by when a series is published

A series is not simply allowed or forbidden. What matters is *when it became public relative
to the deadline for the hour being predicted*, and that yields three different treatments:

| Series | Published | Treatment |
|---|---|---|
| `load_forecast`, `wind_solar_forecast` | **before** the deadline, morning of D−1 | used **as-is**, at its own timestamp |
| `day_ahead_price` | **after** it, ~12:45 on D−1 | **lagged ≥ 24 h** — and is the target |
| `actual_load`, `actual_generation` | long after delivery | **never used** |

So of the seventeen feature columns, **nine are shifted** (four lags, five daily summaries),
five are forecasts used at their own timestamp, and three are calendar values read off the
index.

**A blanket "shift everything by 24 hours" would satisfy the contract completely and gut the
model.** It cannot tell "this was unknowable" apart from "this was published yesterday
morning", so it would replace tomorrow's expected demand with yesterday's — discarding the
most informative column in the table to guard against a risk that column does not carry.

That is what the catalog earns its file for. It records *when*, not merely *whether*, which is
the richer fact and the one three treatments can be derived from.

### There is no clock in it

The natural guess is that the lag works by hiding data at the right moment — pick a time, cut
everything after it, step forward, repeat. Search the file for a date comparison and you find
nothing but comments.

**The boundary is built into the shape of the price columns, not applied at a moment.**

```python
out["price_lag_24h"] = full.shift(24)
```

*Every row takes the value from 24 rows above.* One instruction, obeyed by all 63,575 rows at
once. Row 3 and row 50,000 obey it identically, and no row can reach forward.

Like a newspaper: every edition prints yesterday's closing prices, and you do not need to know
today's date for that to be true.

**Why 24 and not 12.** Prices for a day are published just after midday the day before, so at
the moment of the decision all of yesterday is public and none of today is. A 12-hour lag is
harmless for the 08:00 delivery hour and reaches into the answer for the 23:00 one. One rule
covers all 24 hours, so the worst hour sets it.

**This only works because publication is punctual.** Same timetable every day, forever, so a
fixed offset of 24 rows *is* a statement about time. For a series that gets revised after
publication the trick fails — which is why `CLAUDE.md` rules out outage data.

### Two guards, because one covered only half

| | Guards | Fails when |
|---|---|---|
| `SOURCES` + catalog check | the **declaration** | a forbidden series is added to the permitted list |
| `data_load()` refusing | the **use** | any function reaches past the list without saying so |

The second exists because the first was not enough: reaching past `SOURCES` is a one-word edit
inside any function, and the list at the top would still read perfectly.

### The test that cannot be satisfied by naming

`test_deleting_the_future_changes_nothing` rebuilds one delivery day from a world truncated at
the deadline and requires every feature value to be identical. Careful naming does not help;
if a column reaches forward, a number moves.

Writing it exposed a real fault. `build()` used to require the price to exist before producing
a row — harmless across all 63,575 historical rows, and fatal for the only row that matters in
production, because at midday on D−1 tomorrow has forecasts and no price. The target is now
joined on last and may be absent.

**So the backtest and the eventual live run use the same function.** Two code paths for one
job is a standard way for a backtest to measure something the live system never does.

### What is in the table

| Group | Columns | Shifted? | Why it is allowed |
|---|---|---|---|
| Target | `price` | — | the answer; never a feature |
| Price memory | `price_lag_24h · 48h · 72h · 168h` | **yes** | far enough back to be public |
| Yesterday | `price_d1_min · max · mean · last · spread` | **yes**, by a day | a day that had fully cleared |
| Forecasts | `load_forecast · wind_onshore · wind_offshore · solar · residual_load` | no | published the previous morning |
| Calendar | `hour · dayofweek · is_weekend` | no | read off the index itself |

The forecast columns need no lag, and they are not a second-best substitute for measured
output. **Bids were placed against the published forecast, so that is what set the price.**
The measurement taken afterwards never touched the auction. Here the rule and the better
modelling choice happen to agree.

---

## Two guards, doing different jobs

| | `tests/` | `scripts/verify_forecast_series.py` |
|---|---|---|
| Asks | Did we **write down** the right request? | Is the data **actually** a forecast? |
| Needs network | no | yes |
| Cost | under a second | about 20 seconds, 4 API calls |
| Run it | every time | when something changes |

One is a spelling check. The other is a taste test.

You need both. The spelling check alone will pass happily while the catalog points at
entirely the wrong data — we proved that by breaking it on purpose, and the whole suite
shrugged.

Run verify when a new entry is added to the catalog, a request parameter changes, the
`entsoe-py` library is upgraded, or ENTSO-E changes something. Otherwise leave it alone.

---

## The supporting cast

| File | Job |
|---|---|
| `justfile` | The menu. Every command in one place. Run `just` to see it. |
| `conftest.py` | Tells pytest where the repository root is, so `from src import config` works |
| `tests/` | Checks that the contracts still hold. No network needed. |
| `docs/worklog.md` | What was done, dated |
| `docs/learnings.md` | What was understood, dated. Local only, not committed. |

---

## How to read the repository in ten minutes

Open these four, in this order. Each one only needs the ones above it.

1. **`justfile`** — what can I run?
2. **`src/config.py`** — what is fixed and not up for debate?
3. **`src/sources/entsoe.py`** — what data exists, and what is allowed?
4. **`src/features.py`** — where that permission stops being a declaration. The file the
   rest of the project depends on being right.
5. **`tests/test_features.py`** — specifically `test_deleting_the_future_changes_nothing`,
   which is the shortest statement of what this project is trying to be careful about.

Then read [CLAUDE.md](../CLAUDE.md) for the rules that govern changing any of it.
