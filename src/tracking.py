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
    db.parent.mkdir(parents=True, exist_ok=True)         # SQLite makes the file, not its folder
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
# Each run's file holds the actual price, both benchmarks and its own forecast — the
# columns its two rMAEs are computed from — so one run can prove its own scores
# without opening another.

def log(rows: list[dict], forecasts: pd.DataFrame, params: dict,
        *, db: Path = cfg.MLFLOW_DB, store: Path = cfg.MLRUNS) -> dict[str, str]:
    """Store one run per score row. Returns model name → run id."""
    client = _client(db)
    experiment = _experiment(client, store)
    ids = {}
    for row in rows:
        model = row["model"]
        kept = forecasts[list(dict.fromkeys(["actual", "naive", "naive_field", model]))]   # each once
        metrics = {key: row[key] for key in ("mae", "rmae", "rmae_field", "n")}
        ids[model] = _write(client, experiment, model, {**params, "split": row["split"]},
                            metrics, kept)
    return ids


def _write(client: MlflowClient, experiment: str, model: str, params: dict,
           metrics: dict, kept: pd.DataFrame) -> str:
    run = client.create_run(experiment, run_name=model).info.run_id
    for key, value in {**params, "model": model, "convention": CONVENTION}.items():
        client.log_param(run, key, value)
    for key, value in metrics.items():
        client.log_metric(run, key, value)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / FORECASTS
        kept.to_parquet(path)
        client.log_artifact(run, str(path))                  # copied into `store`
    client.set_terminated(run)
    return run


# ── Writing a range ───────────────────────────────────────────────────────────
# Stage 3's runs keep a range rather than one forecast: the actual price, LEAR's
# point forecast and all 99 percentiles per hour, so a later test or figure reads
# them back instead of refitting for an hour.  Parquet wants text column names,
# so percentile 90 is stored as "90", and `read_range` turns it back into 90.

def log_range(row: dict, kept: pd.DataFrame, params: dict,
              *, db: Path = cfg.MLFLOW_DB, store: Path = cfg.MLRUNS) -> str:
    """Store one range run: its scores as metrics, its hourly table as the file."""
    client = _client(db)
    metrics = {k: v for k, v in row.items()
               if k not in ("method", "split", "window")}   # the window is a param: "28+56+91+182" is text
    return _write(client, _experiment(client, store), row["method"],
                  {**params, "split": row["split"]}, metrics,
                  kept.rename(columns=str))                  # 90 -> "90" for parquet


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


def read_range(run: str, *, db: Path = cfg.MLFLOW_DB) -> tuple[dict, pd.DataFrame]:
    """A range run's params and hourly table, percentile columns back as whole numbers."""
    params, kept = read(run, db=db)
    return params, kept.rename(columns=lambda c: int(c) if c.isdigit() else c)


# ── Finding a run by what it states ───────────────────────────────────────────
# Run ids differ from one clone to the next, so a command that regenerates the
# README's p-values names runs by their params instead: the newest run whose
# params match.  Every run so far is on the 24-slot grid, so no filter for it.  Newest, because a rerun at a later commit is meant to
# replace the earlier reading; the caller prints the commit, so a replacement is
# visible rather than silent.

def latest(*, db: Path = cfg.MLFLOW_DB, **params: str) -> str | None:
    """The newest run whose params all match, or None."""
    client = _client(db)
    found = client.get_experiment_by_name(EXPERIMENT)
    if found is None:
        return None                                      # nothing has ever been logged here
    where = " and ".join(f"params.{k} = '{v}'" for k, v in params.items())
    runs = client.search_runs([found.experiment_id], where, max_results=1,
                              order_by=["attributes.start_time DESC"])
    return runs[0].info.run_id if runs else None
