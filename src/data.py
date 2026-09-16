"""Getting data in, keeping it, and putting it on one clock.

The public `load()` API every other module calls, and the pull that fills the cache
behind it.  Applies Integration Contract 5: `config.py` holds the constants — one
storage timezone, one resolution — and this file is where they are enforced, once,
on the way in.

Nothing outside `src/sources/` knows which platform the bytes came from.  Swapping
ENTSO-E for another source is a change to the catalog and to this file, and to
nothing else.

**The pull never overwrites.**  ENTSO-E revises published history, so a pull months
after the last one can quietly rewrite the years a published result was built on,
and nothing errors.  Every save therefore compares against what is already on disk
and moves the old copy aside if any existing value changed.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src import config as cfg
from src.sources import entsoe as cat

# ── Where things live ─────────────────────────────────────────────────────────
# One file per catalog item, named by its key, so a directory listing reads as the
# catalog.  Superseded copies go to archive/ stamped with the pull that replaced
# them, and are never deleted — a published number may rest on one.
#
# The paths are derived at call time from a `root` argument rather than fixed at
# import, so a test can point the whole mechanism at a temporary directory without
# patching module globals.

MANIFEST_COLUMNS = (
    "pulled_at,series,outcome,rows,added,changed,first,last,resolution,sha256\n"
)


def _root(root: Path | None) -> Path:
    return cfg.RAW if root is None else root


def path_for(key: str, root: Path | None = None) -> Path:
    """Where one series is cached.  Resolved through the catalog, so a typo raises."""
    return _root(root) / f"{cat.get(key).key}.parquet"


def archive_dir(root: Path | None = None) -> Path:
    return _root(root) / "archive"


def manifest_path(root: Path | None = None) -> Path:
    return _root(root) / "manifest.csv"


# ── The window ────────────────────────────────────────────────────────────────
# Every pull asks for the whole history rather than the missing tail.  That is what
# makes a revision visible at all: a pull that fetched only new days could never
# notice that 2023 had been rewritten underneath it.  The cost is about 35 requests
# against a published limit of 400 per minute.

PULL_START = pd.Timestamp(cfg.HISTORY_START, tz=cfg.TZ_MARKET)
PULL_END = pd.Timestamp(cfg.TEST_END, tz=cfg.TZ_MARKET) + pd.DateOffset(days=1)


# ── Talking to ENTSO-E ────────────────────────────────────────────────────────
# Deliberately two functions.  `client` needs a token and a network; `fetch` needs
# neither until it is handed one.  Both the pull and the verification script use
# these, so there is exactly one definition of how this project calls ENTSO-E.  Two
# would be free to drift apart, and the catalog exists precisely to stop that.

def client(timeout: int = 90):
    """Build an authenticated client, or say plainly what is missing."""
    load_dotenv(cfg.ROOT / ".env")                  # explicit path: the cwd may be anything
    token = os.getenv("ENTSOE_API_KEY")
    if not token:
        raise RuntimeError(
            "ENTSOE_API_KEY missing — copy .env.example to .env and fill it in"
        )

    from entsoe import EntsoePandasClient          # imported here, so this module imports offline

    return EntsoePandasClient(api_key=token, timeout=timeout)


def fetch(
    client,
    key: str,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Ask ENTSO-E for one catalog item, by the method the catalog names.

    The method is looked up rather than written here.  If this file named it
    directly, the catalog could say one thing while the pipeline did another, and
    both would look correct on their own.
    """
    item = cat.get(key)
    out = getattr(client, item.query)(
        cfg.BIDDING_ZONE,
        start=PULL_START if start is None else start,
        end=PULL_END if end is None else end,
    )
    return out.to_frame(item.key) if isinstance(out, pd.Series) else out


# ── Contract 5: one clock, one shape ──────────────────────────────────────────
# entsoe-py returns timestamps in the market's local time.  Converting to UTC at
# this single point is what makes everything downstream safe: in UTC every day has
# 24 hours, no timestamp occurs twice, and "a day earlier" is always the same
# arithmetic.  Do it per-script instead and two series disagree by an hour twice a
# year, silently.
#
# Column names are flattened here too.  Actual generation arrives with two-level
# columns, because a technology can both generate and consume — pumped storage
# does each in different hours — and parquet will not store a column index like
# that.  Joining the levels keeps both facts and gives one naming convention.

def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Join two-level column names with ' | ', leaving single-level names alone."""
    if not isinstance(df.columns, pd.MultiIndex):
        return df
    out = df.copy()
    out.columns = [" | ".join(str(p) for p in col) for col in df.columns]
    return out


def normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Put a fetched frame on the project's clock, without changing any value."""
    if df.index.tz is None:                         # a naive index cannot be placed in time
        raise ValueError(
            "Source returned a naive index; cannot place it in time (Contract 5)."
        )
    return flatten_columns(df.tz_convert(cfg.TZ_STORAGE).sort_index())


def to_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """Average a UTC-indexed frame up to the project's hourly convention.

    The mean, not the sum, for both prices and power.  A megawatt figure averaged
    over an hour is the energy delivered in it; and the revenue from four
    quarter-hour products at 1 MW is the mean price times 1 MWh, not their sum.

    Resampling rather than reshaping is what makes the October 2025 switch to
    quarter-hourly products a non-event: a series that changes resolution halfway
    through still comes out hourly throughout.
    """
    if df.index.tz is None:
        raise ValueError("Index must be tz-aware before resampling (Contract 5).")
    return df.resample(cfg.RESOLUTION).mean()


def detected_resolution(df: pd.DataFrame) -> str:
    """The commonest gap between timestamps — what actually arrived, not what was promised."""
    if len(df) < 2:
        return "?"
    step = df.index.to_series().diff().mode()
    return f"{int(step.iloc[0].total_seconds() // 60)}min" if len(step) else "?"


# ── Reading ───────────────────────────────────────────────────────────────────

def load_raw(key: str, root: Path | None = None) -> pd.DataFrame:
    """The cached series exactly as pulled: UTC index, the resolution it arrived in."""
    p = path_for(key, root)
    if not p.exists():
        raise FileNotFoundError(f"{key!r} has not been pulled yet. Run: just pull")
    return pd.read_parquet(p)


def load(key: str, root: Path | None = None) -> pd.DataFrame:
    """The cached series on the project's hourly convention."""
    return to_hourly(load_raw(key, root))


# ── Writing: four outcomes, and only one of them is dangerous ─────────────────
# Appending is not overwriting.  A pull that reaches further forward in time adds
# rows and rewrites nothing, and archiving that would fill the disk with copies for
# no reason at all.
#
# What must never pass unnoticed is an existing value changing.  That is ENTSO-E
# revising history underneath a number already published, and it is the one case
# where the old copy has to survive — otherwise the Third Law claim that any
# reported number can be regenerated quietly stops being true.

@dataclass(frozen=True)
class SaveResult:
    """What happened to one series during one pull."""

    key: str
    outcome: str                  # created | unchanged | extended | revised
    rows: int
    added: int = 0
    changed: int = 0
    archived: Path | None = None
    detail: str = ""

    @property
    def needs_attention(self) -> bool:
        return self.outcome == "revised"


def checksum(df: pd.DataFrame) -> str:
    """A fingerprint of the data, not of the file.

    Hashing the parquet bytes would change whenever the library changed its footer,
    so two identical pulls could look different.  This hashes the values and the
    index, which is the thing we actually care about staying the same.
    """
    ordered = df.sort_index(axis=1)
    digest = hashlib.sha256(
        pd.util.hash_pandas_object(ordered, index=True).values.tobytes()
    )
    digest.update("|".join(str(c) for c in ordered.columns).encode())
    return digest.hexdigest()[:16]


def _diff(old: pd.DataFrame, new: pd.DataFrame) -> tuple[int, int, list[int]]:
    """Rows added, existing rows whose values changed, and the years they fall in."""
    added = len(new.index.difference(old.index))
    lost = new.index.symmetric_difference(old.index).difference(new.index)

    if set(old.columns) != set(new.columns):        # a column appearing or vanishing counts
        return added, len(old), sorted({t.year for t in old.index})

    overlap = old.index.intersection(new.index)
    o = old.loc[overlap].sort_index(axis=1)
    n = new.loc[overlap].sort_index(axis=1)
    differs = ~((o == n) | (o.isna() & n.isna()))   # missing in both is not a change
    rows = differs.any(axis=1)

    changed = int(rows.sum()) + len(lost)           # a vanished row is a change too
    years = sorted({t.year for t in overlap[rows]} | {t.year for t in lost})
    return added, changed, years


def save(df: pd.DataFrame, key: str, root: Path | None = None) -> SaveResult:
    """Cache one series, never silently replacing what a result may rest on."""
    base = _root(root)
    base.mkdir(parents=True, exist_ok=True)
    p = path_for(key, root)

    if not p.exists():
        df.to_parquet(p)
        return SaveResult(key, "created", len(df), added=len(df), detail=f"{len(df):,} rows")

    old = pd.read_parquet(p)
    added, changed, years = _diff(old, df)

    if not changed:
        if not added:
            return SaveResult(key, "unchanged", len(df), detail=f"{len(df):,} rows")
        df.to_parquet(p)
        return SaveResult(key, "extended", len(df), added=added, detail=f"+{added:,} rows")

    # A value that was published has been rewritten.  Keep the old copy under the
    # moment it was displaced, so the results built on it stay reproducible.
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    archive_dir(root).mkdir(parents=True, exist_ok=True)
    moved = archive_dir(root) / f"{key}__{stamp}.parquet"
    p.rename(moved)
    df.to_parquet(p)

    where = ", ".join(str(y) for y in years) if years else "unknown period"
    return SaveResult(
        key, "revised", len(df), added=added, changed=changed, archived=moved,
        detail=f"{changed:,} rows changed in {where}",
    )


# ── The manifest ──────────────────────────────────────────────────────────────
# One line per series per pull, appended and never rewritten.  This is the record
# the Third Law asks for: what was fetched, when, how much of it, and a fingerprint
# to compare against.  At roughly twenty pulls over the project's life it stays
# short enough to read directly.

def append_manifest(result: SaveResult, df: pd.DataFrame, root: Path | None = None) -> None:
    """Record one save.  Creates the file with a header on first use."""
    path = manifest_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(MANIFEST_COLUMNS)

    row = [
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        result.key,
        result.outcome,
        str(result.rows),
        str(result.added),
        str(result.changed),
        str(df.index.min()) if len(df) else "",
        str(df.index.max()) if len(df) else "",
        detected_resolution(df),
        checksum(df),
    ]
    with path.open("a") as fh:
        fh.write(",".join(row) + "\n")


# ── The pull ──────────────────────────────────────────────────────────────────
# Orchestration only: fetch, normalise, save, record.  The printing lives in
# scripts/pull.py, so this stays callable from a notebook or a test without
# producing output nobody asked for.

def pull(
    keys: list[str] | None = None,
    root: Path | None = None,
    on_start=None,
    on_done=None,
) -> list[SaveResult]:
    """Fetch every catalog item and cache it.  One result per series, in order.

    Two callbacks rather than a return value alone, because a full pull takes about
    twenty minutes and a caller that can only report at the end leaves the operator
    watching a blank screen.  Printing still belongs to the caller.
    """
    keys = list(cat.CATALOG) if keys is None else keys
    api = client()                                  # fails here if the token is missing
    results = []

    for key in keys:
        if on_start:
            on_start(key)
        frame = normalise(fetch(api, key))
        result = save(frame, key, root)
        append_manifest(result, frame, root)
        results.append(result)
        if on_done:
            on_done(result)

    return results
