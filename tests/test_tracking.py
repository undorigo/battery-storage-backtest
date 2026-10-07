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
                              "linear": actual + 3 * np.cos(n), "gbm": actual - 2 * np.sin(n)})
    rows = [E.score(name, "valid", forecasts[name], forecasts["naive"], actual)
            for name in ("naive", "linear", "gbm")]

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
    """The reason each run keeps three columns: its rMAE, recomputed from MLflow alone."""
    rows, _, back = stored
    for row in rows:
        _, kept = back[row["model"]]
        again = E.rmae(kept[row["model"]], kept["naive"], kept["actual"])
        assert again == row["rmae"]


def test_the_stored_hours_are_the_scored_hours(stored):
    """Parquet must hand the naive grid labels back unchanged: no zone added, none moved."""
    _, forecasts, back = stored
    for model, (_, kept) in back.items():
        assert kept.index.equals(forecasts.index), f"{model} run's hours moved"
        assert list(kept.columns) == list(dict.fromkeys(["actual", "naive", model]))
