"""Photon-number statistics of a heralded pair source with a threshold detector.

A source emits n pairs with thermal statistics P(n) = (1 - x) x^n, where
``x`` in (0, 1) is the per-source brightness. A click of the herald detector
means n >= 1 (it cannot count photons), so the heralded mode holds n >= 1
photons with P(n | click) = (1 - x) x^(n-1). The heralded mode then crosses a
lossy path of total power transmission ``T``; each photon survives independently.
"""

from __future__ import annotations

import numpy as np

ArrayLike = float | np.ndarray


def leaf_one(T: ArrayLike, x: float) -> ArrayLike:
    """P(exactly one photon leaves | click) for path transmission ``T``.

    Closed form of sum_n (1-x) x^(n-1) n T (1-T)^(n-1).
    """
    return (1.0 - x) * T / (1.0 - x * (1.0 - T)) ** 2


def leaf_ge1(T: ArrayLike, x: float) -> ArrayLike:
    """P(at least one photon leaves | click) for path transmission ``T``."""
    u = 1.0 - T
    return 1.0 - (1.0 - x) * u / (1.0 - x * u)


def db_to_transmission(loss_db: ArrayLike) -> ArrayLike:
    """Convert a loss in dB to a power transmission."""
    return 10.0 ** (-np.asarray(loss_db, dtype=float) / 10.0)
