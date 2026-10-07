"""Runs kept side by side — what MLflow is here for, and all it is here for.

`scores.csv` stays the record, because it is in git and reaches a clean clone.  This
module keeps what that file throws away: every hour's forecast behind each score,
which the significance test needs, in a place where runs can be compared.

It writes and reads.  It fits nothing, scores nothing and decides nothing — the
score rows and the hourly table arrive finished from `scripts/train.py`.

**No global MLflow setting is touched.**  Every call builds its own client with the
database spelled out, so a test pointed at a temporary folder cannot leave later
code writing there.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
from mlflow import MlflowClient

from src import config as cfg


# ── What every run states about itself ────────────────────────────────────────
# The convention is written by this module, not passed in by the caller, so no
# run can be stored without it.  Earlier 2023 scores sit on the old UTC convention
# and these do not: a run that cannot say which grid it was scored on cannot be
# compared with anything.

CONVENTION = "24-slot Berlin grid"        # Contract 5: the clock every forecast was scored on
EXPERIMENT = "day-ahead-de-lu"            # one experiment; runs differ by their params
FORECASTS = "forecasts.parquet"           # parquet keeps the naive grid labels exactly


def _client(db: Path) -> MlflowClient:
    return MlflowClient(tracking_uri=f"sqlite:///{db}")


def _experiment(client: MlflowClient, store: Path) -> str:
    """The experiment's id, creating it on first use with its files under `store`."""
    found = client.get_experiment_by_name(EXPERIMENT)
    if found is not None:
        return found.experiment_id
    return client.create_experiment(EXPERIMENT, artifact_location=store.as_uri())


# ── Writing a run ─────────────────────────────────────────────────────────────
# One run per scored forecast, the benchmark included: its run must read exactly
# 1.000, the same free check the score table carries.
#
# Each run's file holds the actual price, the benchmark and its own forecast — the
# three columns its rMAE is computed from — so one run can prove its own score
# without opening another.

def log(rows: list[dict], forecasts: pd.DataFrame, params: dict,
        *, db: Path = cfg.MLFLOW_DB, store: Path = cfg.MLRUNS) -> dict[str, str]:
    """Store one run per score row. Returns model name → run id."""
    client = _client(db)
    experiment = _experiment(client, store)
    ids = {}
    for row in rows:
        model = row["model"]
        run = client.create_run(experiment, run_name=model).info.run_id
        stated = {**params, "model": model, "split": row["split"], "convention": CONVENTION}
        for key, value in stated.items():
            client.log_param(run, key, value)
        for key in ("mae", "rmae", "n"):
            client.log_metric(run, key, row[key])
        kept = forecasts[list(dict.fromkeys(["actual", "naive", model]))]   # naive once, not twice
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / FORECASTS
            kept.to_parquet(path)
            client.log_artifact(run, str(path))              # copied into `store`
        client.set_terminated(run)
        ids[model] = run
    return ids


# ── Reading a run back ────────────────────────────────────────────────────────
# Read from MLflow's own copy rather than handed back from memory, so a check built
# on this sees what was stored, not what was meant to be stored.

def read(run: str, *, db: Path = cfg.MLFLOW_DB) -> tuple[dict, pd.DataFrame]:
    """A run's params and its hourly forecasts, as stored."""
    client = _client(db)
    params = client.get_run(run).data.params
    with tempfile.TemporaryDirectory() as tmp:
        forecasts = pd.read_parquet(client.download_artifacts(run, FORECASTS, tmp))
    return params, forecasts
