# ─────────────────────────────────────────────────────────────────────────────
# Project commands, in one place.
#
# The Third Law requires a result to be reproducible from a clean clone by
# running a documented command.  This file is that documentation, and it is
# executable, so the two cannot drift apart.  It also moves three pieces of
# knowledge out of anyone's head: which interpreter to use, that scripts run as
# modules rather than file paths, and that the repository root is the only
# working directory that resolves imports.
#
# Run `make` with no argument for the list.
# ─────────────────────────────────────────────────────────────────────────────

# The one place the interpreter is named.  Change it here and every target
# follows — a different venv, a newer Python, or `python` inside a container.
PY := .venv/bin/python

# Targets are names, not files, so tell make not to look for a file called
# "test".  Without this a file of that name would make the target a no-op.
.PHONY: help setup test verify clean

# The default target, because a bare `make` should explain itself rather than
# guess.  The sed line prints every target that carries a `## ` comment, so the
# menu is generated from the file instead of maintained beside it.
help:
	@echo "Battery Storage Backtest — available commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'
	@echo ""

setup: ## create the venv and install pinned dependencies
	python3 -m venv .venv
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --quiet -r requirements.txt
	@echo "Environment ready. Run 'make test' to check it."

test: ## run the offline contract tests (no network, no token)
	$(PY) -m pytest tests/ -q

verify: ## check the forecast series really are forecasts (needs network + token)
	$(PY) -m scripts.verify_forecast_series

clean: ## remove caches and compiled files, leaving data and the venv alone
	find . -path ./.venv -prune -o -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	@echo "Caches cleared."
