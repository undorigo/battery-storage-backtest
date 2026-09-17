"""Contract 5, and the rule that a pull is never silently overwritten.

Every test here is offline.  The network is not the thing worth pinning — the
failures that matter are the quiet ones: a series that shifts by an hour on a
clock-change day, a resolution change that reshapes a frame mid-series, and a
second pull that rewrites the years a published number was built on.

The save tests all write to pytest's tmp_path rather than to data/raw, which is why
every function in src.data takes a `root` argument.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src import config as cfg
from src import data

# ── Fixtures ──────────────────────────────────────────────────────────────────
# Frames built by hand rather than recorded, because what is being tested is the
# handling of shapes — naive, quarter-hourly, mixed — not the parsing of any real
# response.


def frame(start: str, periods: int, freq: str, tz: str = cfg.TZ_MARKET, value: float = 1.0):
    idx = pd.date_range(start, periods=periods, freq=freq, tz=tz)
    return pd.DataFrame({"v": [value] * periods}, index=idx)


# ── Contract 5: one clock ─────────────────────────────────────────────────────


def test_normalise_converts_to_storage_timezone():
    out = data.normalise(frame("2024-06-01", 24, "h"))
    assert str(out.index.tz) == cfg.TZ_STORAGE


def test_normalise_rejects_a_naive_index():
    naive = pd.DataFrame({"v": [1.0]}, index=pd.date_range("2024-06-01", periods=1, freq="h"))
    with pytest.raises(ValueError, match="naive"):
        data.normalise(naive)


def test_normalise_does_not_change_values():
    src = frame("2024-06-01", 24, "h", value=42.0)
    assert data.normalise(src)["v"].tolist() == src["v"].tolist()


def test_normalise_sorts_the_index():
    shuffled = frame("2024-06-01", 24, "h").sample(frac=1, random_state=0)
    assert data.normalise(shuffled).index.is_monotonic_increasing


def test_spring_clock_change_day_has_23_hours_in_market_time():
    """The day the clocks go forward is short, and UTC is what keeps it countable."""
    march = data.normalise(frame("2024-03-31", 23, "h"))
    local = march.index.tz_convert(cfg.TZ_MARKET)
    assert local.normalize().nunique() == 1          # all of it is one local day
    assert len(march) == 23


def test_autumn_clock_change_day_has_25_hours_and_no_duplicates():
    """October repeats 02:00 in local time. In UTC every hour is still distinct."""
    october = data.normalise(frame("2024-10-27", 25, "h"))
    assert len(october) == 25
    assert not october.index.has_duplicates


# ── Contract 5: one resolution ────────────────────────────────────────────────


def test_quarter_hourly_is_averaged_to_hourly():
    quarters = frame("2024-06-01", 8, "15min")
    quarters.iloc[:4, 0] = [10.0, 20.0, 30.0, 40.0]   # first hour averages to 25
    hourly = data.to_hourly(data.normalise(quarters))
    assert len(hourly) == 2
    assert hourly["v"].iloc[0] == 25.0


def test_hourly_input_passes_through_unchanged():
    hourly = data.normalise(frame("2024-06-01", 24, "h", value=7.0))
    assert data.to_hourly(hourly)["v"].tolist() == [7.0] * 24


def test_a_resolution_change_mid_series_still_comes_out_hourly():
    """The October 2025 switch: 24 periods a day before it, 96 after."""
    before = frame("2025-09-30", 24, "h", value=1.0)
    after = frame("2025-10-01", 96, "15min", value=2.0)
    mixed = data.normalise(pd.concat([before, after]))

    hourly = data.to_hourly(mixed)
    assert len(hourly) == 48                          # two days, hourly throughout
    assert hourly["v"].iloc[:24].tolist() == [1.0] * 24
    assert hourly["v"].iloc[24:].tolist() == [2.0] * 24


def test_detected_resolution_reports_what_arrived():
    assert data.detected_resolution(data.normalise(frame("2024-06-01", 8, "15min"))) == "15min"
    assert data.detected_resolution(data.normalise(frame("2024-06-01", 8, "h"))) == "60min"


# ── Column flattening ─────────────────────────────────────────────────────────


def test_two_level_columns_are_joined_not_collapsed():
    """Pumped storage generates and consumes. Both must survive with distinct names."""
    idx = pd.date_range("2024-06-01", periods=2, freq="h", tz=cfg.TZ_MARKET)
    df = pd.DataFrame(
        [[1.0, 2.0], [3.0, 4.0]],
        index=idx,
        columns=pd.MultiIndex.from_tuples(
            [("Hydro Pumped Storage", "Actual Aggregated"),
             ("Hydro Pumped Storage", "Actual Consumption")]
        ),
    )
    out = data.flatten_columns(df)
    assert list(out.columns) == [
        "Hydro Pumped Storage | Actual Aggregated",
        "Hydro Pumped Storage | Actual Consumption",
    ]


# ── The four save outcomes ────────────────────────────────────────────────────
# One of these four is the reason the whole mechanism exists.  Appending is safe;
# rewriting a published value is not.

KEY = "day_ahead_price"


def test_first_save_creates(tmp_path):
    r = data.save(data.normalise(frame("2024-06-01", 24, "h")), KEY, root=tmp_path)
    assert r.outcome == "created"
    assert data.path_for(KEY, tmp_path).exists()


def test_saving_the_same_data_twice_changes_nothing(tmp_path):
    """The Third Law check: run the pull twice, get `unchanged`."""
    df = data.normalise(frame("2024-06-01", 24, "h"))
    data.save(df, KEY, root=tmp_path)
    r = data.save(df, KEY, root=tmp_path)

    assert r.outcome == "unchanged"
    assert not data.archive_dir(tmp_path).exists()    # nothing was displaced


def test_new_rows_extend_rather_than_archive(tmp_path):
    """Reaching further forward in time rewrites nothing, so nothing is archived."""
    data.save(data.normalise(frame("2024-06-01", 24, "h")), KEY, root=tmp_path)
    longer = data.normalise(frame("2024-06-01", 48, "h"))
    r = data.save(longer, KEY, root=tmp_path)

    assert r.outcome == "extended"
    assert r.added == 24
    assert not data.archive_dir(tmp_path).exists()
    assert len(data.load_raw(KEY, tmp_path)) == 48


def test_a_changed_value_is_reported_and_the_old_copy_is_kept(tmp_path):
    """ENTSO-E rewriting history is the one case the old file must survive."""
    original = data.normalise(frame("2024-06-01", 24, "h", value=50.0))
    data.save(original, KEY, root=tmp_path)

    revised = original.copy()
    revised.iloc[5, 0] = 999.0                        # one published hour, rewritten
    r = data.save(revised, KEY, root=tmp_path)

    assert r.outcome == "revised"
    assert r.changed == 1
    assert "2024" in r.detail
    assert r.archived is not None and r.archived.exists()
    assert data.load_raw(KEY, tmp_path).iloc[5, 0] == 999.0        # new data is live
    assert pd.read_parquet(r.archived).iloc[5, 0] == 50.0          # old data survives


def test_a_vanished_row_counts_as_a_revision(tmp_path):
    """Data disappearing is as dangerous as data changing, and just as quiet."""
    data.save(data.normalise(frame("2024-06-01", 24, "h")), KEY, root=tmp_path)
    r = data.save(data.normalise(frame("2024-06-01", 20, "h")), KEY, root=tmp_path)

    assert r.outcome == "revised"
    assert r.archived is not None


def test_a_new_column_counts_as_a_revision(tmp_path):
    """Conservative on purpose: an unnecessary archive costs megabytes, a missed one costs results."""
    df = data.normalise(frame("2024-06-01", 24, "h"))
    data.save(df, KEY, root=tmp_path)

    widened = df.copy()
    widened["extra"] = 1.0
    assert data.save(widened, KEY, root=tmp_path).outcome == "revised"


def test_missing_values_in_both_copies_are_not_a_change(tmp_path):
    """A gap is not a revision. NaN never equals NaN, so this needs saying explicitly."""
    df = data.normalise(frame("2024-06-01", 24, "h"))
    df.iloc[3, 0] = float("nan")
    data.save(df, KEY, root=tmp_path)

    assert data.save(df.copy(), KEY, root=tmp_path).outcome == "unchanged"


# ── Finding what the chunked request dropped ──────────────────────────────────
# entsoe-py splits requests longer than a year and strips each block's first
# timestamp, assuming it duplicates the previous block's last.  ENTSO-E returns
# half-open intervals, so it does not, and a real value is deleted.  Seven hours
# went missing from the price series this way before anyone counted.


def test_a_complete_series_has_no_gaps():
    assert data.gap_windows(data.normalise(frame("2024-06-01", 48, "h"))) == []


def test_one_missing_hour_is_found():
    """The exact shape of the entsoe-py boundary defect."""
    df = data.normalise(frame("2024-06-01", 48, "h"))
    holed = df.drop(df.index[10])

    windows = data.gap_windows(holed)
    assert len(windows) == 1
    a, b = windows[0]
    assert a == df.index[9] and b == df.index[11]     # the hole lies strictly between


def test_several_separate_gaps_are_found_separately():
    df = data.normalise(frame("2024-06-01", 72, "h"))
    holed = df.drop(df.index[[10, 30, 50]])
    assert len(data.gap_windows(holed)) == 3


def test_two_gaps_in_a_row_are_both_reported():
    """A gap must not become the new normal, or the one after it goes unnoticed."""
    df = data.normalise(frame("2024-06-01", 48, "h"))
    holed = df.drop(df.index[[10, 12]])               # one surviving hour between two holes
    assert len(data.gap_windows(holed)) == 2


def test_a_wider_gap_is_one_window_not_many():
    df = data.normalise(frame("2024-06-01", 72, "h"))
    holed = df.drop(df.index[20:26])                  # six consecutive hours
    windows = data.gap_windows(holed)
    assert len(windows) == 1
    assert windows[0][1] - windows[0][0] == pd.Timedelta(hours=7)


def test_a_switch_to_finer_resolution_is_not_a_gap():
    """October 2025: hourly becomes quarter-hourly. Smaller steps, not missing data."""
    mixed = data.normalise(pd.concat([
        frame("2025-09-30", 24, "h"),
        frame("2025-10-01", 96, "15min"),
    ]))
    assert data.gap_windows(mixed) == []


def test_too_short_to_judge_reports_nothing():
    assert data.gap_windows(data.normalise(frame("2024-06-01", 2, "h"))) == []


class _FakeClient:
    """Stands in for entsoe-py. `fetch` resolves the method name through the catalog,
    so the name here is the contract being relied on, not an implementation detail."""

    def __init__(self, frame):
        self._frame = frame

    def query_day_ahead_prices(self, zone, start=None, end=None):
        idx = self._frame.index
        return self._frame.loc[(idx >= start) & (idx <= end)]


def test_backfill_recovers_a_dropped_value():
    full = data.normalise(frame("2024-06-01", 48, "h", value=1.0))
    holed = full.drop(full.index[10])

    out, n = data.backfill(_FakeClient(full), "day_ahead_price", holed)
    assert n == 1
    assert full.index[10] in out.index
    assert len(out) == 48


def test_backfill_never_overwrites_what_is_already_there():
    """A repair that can rewrite history is the thing the archive exists to prevent."""
    full = data.normalise(frame("2024-06-01", 48, "h", value=1.0))
    holed = full.drop(full.index[10])

    disagrees = full.copy()
    disagrees.iloc[20, 0] = 999.0                    # source now claims a different value

    out, n = data.backfill(_FakeClient(disagrees), "day_ahead_price", holed)
    assert n == 1                                    # the hole, and only the hole
    assert out.loc[full.index[20]].iloc[0] == 1.0    # the value we held is untouched


def test_backfill_on_a_complete_series_does_nothing():
    full = data.normalise(frame("2024-06-01", 48, "h"))
    out, n = data.backfill(_FakeClient(full), "day_ahead_price", full)
    assert n == 0
    assert out.equals(full)


# ── Fingerprints and the manifest ─────────────────────────────────────────────


def test_identical_data_has_an_identical_fingerprint():
    a = data.normalise(frame("2024-06-01", 24, "h"))
    assert data.checksum(a) == data.checksum(a.copy())


def test_one_changed_value_changes_the_fingerprint():
    a = data.normalise(frame("2024-06-01", 24, "h", value=50.0))
    b = a.copy()
    b.iloc[5, 0] = 50.01
    assert data.checksum(a) != data.checksum(b)


def test_manifest_gains_one_line_per_save(tmp_path):
    df = data.normalise(frame("2024-06-01", 24, "h"))
    for _ in range(3):
        data.append_manifest(data.save(df, KEY, root=tmp_path), df, root=tmp_path)

    lines = data.manifest_path(tmp_path).read_text().strip().splitlines()
    assert len(lines) == 4                            # one header, three records
    assert lines[0] == data.MANIFEST_COLUMNS.strip()
    assert all(KEY in line for line in lines[1:])


# ── Reading ───────────────────────────────────────────────────────────────────


def test_loading_before_pulling_says_what_to_run(tmp_path):
    with pytest.raises(FileNotFoundError, match="just pull"):
        data.load_raw(KEY, tmp_path)


def test_load_returns_the_hourly_convention(tmp_path):
    data.save(data.normalise(frame("2024-06-01", 96, "15min")), KEY, root=tmp_path)
    assert len(data.load(KEY, tmp_path)) == 24


def test_path_resolves_through_the_catalog(tmp_path):
    """A typo must fail here rather than quietly caching under a new name."""
    with pytest.raises(KeyError):
        data.path_for("day_ahead_prices", tmp_path)   # plural: not a catalog key


# ── The window ────────────────────────────────────────────────────────────────


def test_pull_window_covers_the_whole_project_history():
    assert str(data.PULL_START.date()) == cfg.HISTORY_START
    assert data.PULL_END > cfg.TEST_END_UTC           # exclusive upper bound, past the last hour
