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

# Check the forecast series really are forecasts. Needs network and a token.
verify:
    {{py}} -m scripts.verify_forecast_series

# Clear caches and compiled files. Leaves data and the venv alone.
clean:
    -find . -path ./.venv -prune -o -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
    rm -rf .pytest_cache
    @echo "Caches cleared."
