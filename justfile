# ─────────────────────────────────────────────────────────────────────────────
# Project commands, in one place.
#
# The Third Law requires a result to be reproducible from a clean clone by
# running a documented command.  This file is that documentation, and it runs,
# so the two cannot drift apart.  It also moves three pieces of knowledge out of
# anyone's head: which interpreter to use, that scripts run as modules rather
# than file paths, and that imports only resolve from the repository root.
#
# `just` rather than make, for two reasons that matter here.  It searches parent
# directories for this file and runs every recipe from the directory containing
# it, so a command works from anywhere in the project — make requires you to be
# in the root.  And `just --list` is built in, where make needs a grep-and-awk
# incantation to produce the same menu.
#
# Install:  brew install just
#           or  curl -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin
#
# From stage 5 this becomes a line in the Dockerfile, per the Dependency Check
# protocol: a new CLI call means the binary is declared where the image is built.
# ─────────────────────────────────────────────────────────────────────────────

# The one place the interpreter is named.  Change it here and every recipe
# follows — a different venv, a newer Python, or `python` inside a container.
py := ".venv/bin/python"

# A bare `just` should explain itself rather than guess at what you meant.  The
# first recipe is the one that runs with no argument, and the leading underscore
# keeps it out of the menu it prints.
_default:
    @just --list --list-heading $'Battery Storage Backtest — available commands\n' --list-prefix '  '

# Create the venv and install the pinned dependencies.
setup:
    python3 -m venv .venv
    {{py}} -m pip install --quiet --upgrade pip
    {{py}} -m pip install --quiet -r requirements.txt
    @echo "Environment ready. Run 'just test' to check it."

# Run the offline contract tests. No network, no token.
test:
    {{py}} -m pytest tests/ -q

# Download every series in the catalog. Needs network and a token.
# Safe to re-run: never overwrites a pull, and reports anything ENTSO-E revised.
pull:
    {{py}} -m scripts.pull

# Check the forecast series really are forecasts. Needs network and a token.
verify:
    {{py}} -m scripts.verify_forecast_series

# Headline numbers and the README figures. Offline: reads the cache `just pull` filled.
explore:
    {{py}} -m scripts.explore

# Scores on the validation year. Offline. Appends to reports/scores.csv and MLflow.
# Cannot reach the test years — Contract 2 evaluates those once, when the stage ends.
# `just train` refits once (stage 1); `just train monthly` or `just train daily` walk forward.
# `daily` also runs LEAR, refitted every day: about 25 minutes rather than 4.
# `just train daily all` gives LEAR every day before instead of the last 1,092.
train refit="once" lear="1092":
    {{py}} -m scripts.train --refit {{refit}} --lear {{lear}}

# Walks LEAR from July 2022 first, so every 2023 range learns from real forecasts.
# Appends to reports/quantile_scores.csv and MLflow. About 1 to 1.5 hours.
# `just quantiles 28 56 91` shares one LEAR walk: ~27 min, then ~40 min per window.
# Stage 3: QRA and conformal ranges around LEAR, scored on 2023. Offline.
quantiles *windows:
    {{py}} -m scripts.quantiles {{windows}}

# Stage 4: the battery planned on 2023's real prices, the most it could have earned. Offline.
# Plans one day at a time, each day ending empty. A few seconds.
# `just backtest fixed` plans on LEAR's stored 2023 forecasts (needs `just train daily`)
# and the naive rule's, settles both at real prices: the capture rate.
# `just backtest bids` sends that LEAR plan as one loop per round, limits from QRA's
# stored range moved to break-even (needs `just quantiles 28 56 91 182` too).
backtest what="ceiling":
    {{py}} -m scripts.backtest {{what}}

# Every p-value the README states, from the runs `just train` left in MLflow. Offline.
# Needs `just train once`, `monthly`, `daily`, `daily all` and `just quantiles` first; names any missing.
significance:
    {{py}} -m scripts.significance

# The number a stage ends on, from the years held back. Offline.
#
# Run this once per stage, and mean it. Reading the held-back years and then changing
# something in response is what turns them into a second validation set — the final
# number stops being honest and nothing about it looks wrong. Every row it writes
# carries the commit that produced it, so a second reading is visible in the record.
# `just final-score` is stage 2's forecasts; `just final-score ranges` is stage 3's
# ranges (about 4.5 hours: LEAR from July 2023, then four windows over two years).
# `just final-score battery` is stage 4's: the battery planned on what those two stored,
# to reports/capture_scores.csv (needs both first; under a minute).
final-score what="points":
    {{py}} -m scripts.final_score {{what}}

# The web page's data: every hour of 2023-25 with its forecasts, range, plans and
# earnings, rebuilt from the stored runs into reports/page.parquet. Offline, about a minute.
# Needs the runs `just backtest bids` and `just final-score battery` read.
page-data:
    {{py}} -m scripts.page_data

# Clear caches and compiled files. Leaves data and the venv alone.
clean:
    -find . -path ./.venv -prune -o -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
    rm -rf .pytest_cache
    @echo "Caches cleared."
