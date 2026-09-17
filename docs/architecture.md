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
   COMMANDS                      THE LIBRARY                    ON DISK
   (scripts/)                      (src/)

                          ENTSO-E Transparency Platform
                                     │
                            sources/entsoe.py          what may we ask for?
                                     │
   just pull ──────────────▶     data.py    ──────────▶  data/raw/*.parquet
   just verify ────────────▶     data.py               (fetches, compares,
                                     │                   throws away)
                            features.py     ──────────▶  data/processed/
                                     │
   just train ─────────────▶    models.py
                                     │
   just backtest ──────────▶   backtest.py
                                     │
                            evaluate.py     ──────────▶  reports/

   config.py  ──  every box above reads its settings from here
```

`src/` is the machine. `scripts/` are the buttons on the front.

---

## One question per file

Each file answers exactly one question. If you can't say which, it is doing too much.

| | File | Its one question | Status |
|---|---|---|---|
| **Settings** | `src/config.py` | What are the fixed facts of this project? | built |
| **Library** | `src/sources/entsoe.py` | What may we ask for, and what may the model see? | built |
| | `src/data.py` | How do we get it, keep it, and make it consistent? | built |
| | `src/features.py` | What does the model get to look at? | next |
| | `src/models.py` | What will tomorrow's prices be? | planned |
| | `src/backtest.py` | What should the battery do, and what did that earn? | planned |
| | `src/evaluate.py` | How good was it? | planned |
| **Buttons** | `scripts/pull.py` | Go and get the data. | built |
| | `scripts/verify_forecast_series.py` | Are these series really forecasts? | built |

Five of nine exist. Everything marked *planned* is a name and an intention, nothing more.

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
data/interim/     part-way work
data/processed/   the feature table the model trains on
```

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

## Two guards, doing different jobs

| | `tests/` | `scripts/verify_forecast_series.py` |
|---|---|---|
| Asks | Did we **write down** the right request? | Is the data **actually** a forecast? |
| Needs network | no | yes |
| Cost | under a second | about 20 seconds, 4 API calls |
| Run it | every time | when something changes |

One is a spelling check. The other is a taste test.

You need both. The spelling check alone will pass happily while the catalog points at
entirely the wrong data — we proved that by breaking it on purpose, and all 40 tests
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
4. **`scripts/verify_forecast_series.py`** — one worked example that uses 2 and 3 together.

Then read [CLAUDE.md](../CLAUDE.md) for the rules that govern changing any of it.
