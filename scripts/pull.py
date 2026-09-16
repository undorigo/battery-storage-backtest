"""Download every series in the catalog and cache it.

Run:  just pull

Fetches the whole history each time, compares against what is already on disk, and
moves the old copy aside if any published value has been rewritten.  Running it
twice in a row should report `unchanged` for every series — that is the Third Law
check, and it is the cheapest evidence that the pull is reproducible.

The work happens in src/data.py.  This file reads the result and prints it.
"""

from __future__ import annotations

import sys

from src import data

# Marks the line a reader should stop at.  A revision is not an error — ENTSO-E is
# entitled to correct its own history — but it means numbers already published may
# no longer regenerate, so it must not scroll past unnoticed.
FLAG = {"revised": "  <-- CHECK", "created": "", "unchanged": "", "extended": ""}


def main() -> int:
    print("Pulling the full history for every series in the catalog.")
    print("Roughly twenty minutes, most of it in actual generation.\n")

    # Each line is written in two halves: the series name when its fetch starts,
    # the verdict when it lands.  A carriage return would look neater live and
    # illegible in a log, and a scheduled run only ever produces the log.
    def starting(key: str) -> None:
        print(f"  {key:<22}", end="", flush=True)

    def finished(r) -> None:
        print(f"{r.outcome:<11}{r.detail}{FLAG[r.outcome]}", flush=True)

    try:
        results = data.pull(on_start=starting, on_done=finished)
    except RuntimeError as exc:                     # no token: cannot start, not a failure
        print(exc)
        return 2
    except Exception as exc:                        # network, platform outage, bad response
        print(f"\nPull failed: {exc}")
        return 1

    revised = [r for r in results if r.needs_attention]
    print()

    if revised:
        print(f"{len(revised)} series had published values rewritten by ENTSO-E.")
        for r in revised:
            print(f"  previous copy kept at {r.archived.relative_to(data.cfg.ROOT)}")
        print("\nAny result built on the earlier data may no longer reproduce.")
        return 1

    print(f"Cache is current. Record appended to {data.manifest_path().relative_to(data.cfg.ROOT)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
