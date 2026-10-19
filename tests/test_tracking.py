"""What MLflow hands back must be what was scored, and must say which grid it was on.

Everything is written to a temporary folder and read back through `tracking.read`,
never from the objects in memory — the point is to test what was stored.  The run is
logged once for the whole file, because creating an MLflow database takes seconds.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import evaluate as E
from src import tracking as TR


# ── The fixture ───────────────────────────────────────────────────────────────
# Two days on the grid: naive labels, Berlin wall clock, as `train.run` returns
# them.  The numbers only need to differ per hour so a stored column cannot match
# its score by accident.

PARAMS = {"refit": "once", "train_start": "2018-10-01", "train_end": "2022-12-31",
          "commit": "abc1234"}


@pytest.fixture(scope="module")
def stored(tmp_path_factory):
    """Score three forecasts, log them, and read every run back."""
    hours = pd.date_range("2023-03-14 00:00", periods=48, freq="h")
    n = np.arange(48, dtype=float)
    actual = pd.Series(80 + 20 * np.sin(n / 4), index=hours)
    forecasts = pd.DataFrame({"actual": actual, "naive": actual.shift(1).bfill(),
                              "naive_field": actual.shift(2).bfill(),
                              "linear": actual + 3 * np.cos(n), "gbm": actual - 2 * np.sin(n)})
    rows = [E.score(name, "valid", forecasts[name], forecasts["naive"], actual,
                    field=forecasts["naive_field"])
            for name in ("naive", "naive_field", "linear", "gbm")]

    where = tmp_path_factory.mktemp("mlflow")
    ids = TR.log(rows, forecasts, PARAMS, db=where / "mlflow.db", store=where / "mlruns")
    back = {model: TR.read(run, db=where / "mlflow.db") for model, run in ids.items()}
    return rows, forecasts, back


# ── What each run states ──────────────────────────────────────────────────────

def test_every_run_states_its_convention(stored):
    """Without it, a grid score and a UTC score look the same in the run list."""
    _, _, back = stored
    for model, (params, _) in back.items():
        assert params.get("convention") == TR.CONVENTION, f"{model} run has no convention"


def test_every_run_keeps_the_callers_params_and_its_model(stored):
    _, _, back = stored
    for model, (params, _) in back.items():
        assert params["model"] == model
        assert {k: params[k] for k in PARAMS} == PARAMS


# ── What each run kept ────────────────────────────────────────────────────────

def test_a_run_reproduces_its_own_score_from_what_was_stored(stored):
    """The reason each run keeps its columns: both rMAEs, recomputed from MLflow alone."""
    rows, _, back = stored
    for row in rows:
        _, kept = back[row["model"]]
        assert E.rmae(kept[row["model"]], kept["naive"], kept["actual"]) == row["rmae"]
        assert E.rmae(kept[row["model"]], kept["naive_field"], kept["actual"]) == row["rmae_field"]


def test_the_stored_hours_are_the_scored_hours(stored):
    """Parquet must hand the naive grid labels back unchanged: no zone added, none moved."""
    _, forecasts, back = stored
    for model, (_, kept) in back.items():
        assert kept.index.equals(forecasts.index), f"{model} run's hours moved"
        assert list(kept.columns) == list(dict.fromkeys(["actual", "naive", "naive_field", model]))


# ── Finding a run by its params ───────────────────────────────────────────────

def _log_once(where, commit: str) -> dict[str, str]:
    hours = pd.date_range("2023-03-14 00:00", periods=24, freq="h")
    forecasts = pd.DataFrame({"actual": 50.0, "naive": 40.0, "naive_field": 42.0, "gbm": 45.0},
                             index=hours)
    rows = [E.score(m, "valid", forecasts[m], forecasts["naive"], forecasts["actual"],
                    field=forecasts["naive_field"])
            for m in ("naive", "gbm")]
    return TR.log(rows, forecasts, {**PARAMS, "commit": commit},
                  db=where / "mlflow.db", store=where / "mlruns")


def test_latest_finds_the_newest_matching_run(tmp_path):
    first = _log_once(tmp_path, "aaa1111")
    second = _log_once(tmp_path, "bbb2222")
    db = tmp_path / "mlflow.db"
    assert TR.latest(db=db, model="gbm", refit="once") == second["gbm"]
    assert TR.latest(db=db, model="gbm", refit="once", commit="aaa1111") == first["gbm"]
    assert TR.latest(db=db, model="gbm", refit="daily") is None     # no such run


def test_latest_on_an_empty_store_is_none(tmp_path):
    assert TR.latest(db=tmp_path / "mlflow.db", model="gbm") is None


# ── A range run ───────────────────────────────────────────────────────────────

def test_a_range_run_reads_back_with_whole_number_percentiles_and_its_score(tmp_path):
    """Parquet stores percentile 90 as "90"; `read_range` must hand back 90, so the
    stored table scores exactly what the run's metric says."""
    hours = pd.date_range("2023-03-14 00:00", periods=24, freq="h")
    actual = pd.Series(np.linspace(50, 120, 24), index=hours)
    kept = pd.DataFrame({"actual": actual, "lear": actual + 2,
                         10: actual - 15, 50: actual + 1, 90: actual + 20})
    row = {"method": "qra", "split": "valid", "n": 24,
           "pinball": E.pinball(kept[[10, 50, 90]], actual), "crossed": 0, "window": 182}
    run = TR.log_range(row, kept, {"window": 182, "commit": "abc1234"},
                       db=tmp_path / "mlflow.db", store=tmp_path / "mlruns")
    params, back = TR.read_range(run, db=tmp_path / "mlflow.db")
    assert params["model"] == "qra" and params["convention"] == TR.CONVENTION
    assert list(back.columns) == ["actual", "lear", 10, 50, 90]
    assert back.index.equals(hours)
    assert E.pinball(back[[10, 50, 90]], back["actual"]) == row["pinball"]


def test_an_averaged_range_logs_its_window_as_text(tmp_path):
    """An average's window is "28+56+91+182".  MLflow metrics must be numbers, so the
    window is a param only; logging it as a metric crashed the 2023 run on 19 Oct 2026."""
    hours = pd.date_range("2023-03-14 00:00", periods=24, freq="h")
    kept = pd.DataFrame({"actual": 80.0, "lear": 82.0, 10: 70.0, 50: 81.0, 90: 95.0}, index=hours)
    row = {"method": "conformal", "split": "test", "n": 24, "pinball": 1.0, "crossed": 0,
           "window": "28+56+91+182"}
    db = tmp_path / "mlflow.db"
    run = TR.log_range(row, kept, {"window": "28+56+91+182", "commit": "abc1234"},
                       db=db, store=tmp_path / "mlruns")
    assert TR.latest(db=db, model="conformal", window="28+56+91+182", split="test") == run
