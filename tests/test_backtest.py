"""The battery's plan and its settlement, checked against cases worked out by hand.

The battery is the project's own: 1 MW, 2 MWh, 90 % each way, 8 EUR per MWh sold.
Every expected number below follows from those four figures on paper.
"""

from __future__ import annotations

import numpy as np
import pytest

from src import backtest as BT


# ── One plan ──────────────────────────────────────────────────────────────────

def test_cheap_then_dear_charges_then_sells_what_survives_the_losses():
    # Buy 1 MWh at 10, 0.9 is stored, 0.81 reaches the grid at 100.
    got = BT.plan(np.array([10.0, 100.0]), start_mwh=0.0)
    assert got.charge == pytest.approx([1.0, 0.0], abs=1e-6)
    assert got.level == pytest.approx([0.9, 0.0], abs=1e-6)
    assert got.discharge == pytest.approx([0.0, 0.81], abs=1e-6)


def test_never_charges_and_discharges_in_the_same_hour():
    # Full battery, price -200.  Buying 1 and selling 0.81 at once keeps the level
    # at 2 MWh and nets 0.19 x 200 - 0.81 x 8 = 31.52 EUR for burning energy.
    # A real battery cannot; it can only sit still.
    got = BT.plan(np.array([-200.0]), start_mwh=2.0)
    assert got.charge * got.discharge == pytest.approx([0.0], abs=1e-9)
    assert got.charge == pytest.approx([0.0], abs=1e-6)


def test_wear_stops_a_trade_too_small_to_pay_for_it():
    # Buy at 50, sell 0.81 at 66: 53.46 - 50 = 3.46 EUR before wear, 6.48 of wear.
    got = BT.plan(np.array([50.0, 66.0]), start_mwh=0.0)
    assert got.charge.sum() == pytest.approx(0.0, abs=1e-6)


def test_stored_energy_stays_within_the_battery():
    # Six cheap hours could buy 6 MWh; only 2 fit, so 2 / 0.9 is bought.
    got = BT.plan(np.array([0.0] * 6 + [100.0] * 6), start_mwh=0.0)
    assert got.level.max() == pytest.approx(2.0, abs=1e-6)
    assert got.charge.sum() == pytest.approx(2.0 / 0.9, abs=1e-6)
    assert got.charge.max() <= 1.0 + 1e-9                         # 1 MW, one hour at a time
