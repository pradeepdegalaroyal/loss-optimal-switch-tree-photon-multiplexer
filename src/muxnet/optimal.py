"""Exact dynamic program for the best switch tree under per-switch loss.

Let V(n, k) be the largest expected probability of delivering exactly one
photon from a subtree of n sources whose output still has to cross k further
switches. With left-priority switching,

    V(1, k) = x * h1(eta0 * t^k)
    V(n, k) = max_a  V(a, k+1) + (1-x)^a * V(n-a, k+1)

because the right subtree is consulted only when none of the a left sources
heralded. The recursion is exact for any tree shape, so one table gives the
optimum for every n <= N at once in O(N^3) time.
"""

from __future__ import annotations

from typing import Literal

import numpy as np

from .source import leaf_one
from .tree import Tree

Rule = Literal["free", "balanced", "chain"]


def _candidates(n: int, rule: Rule) -> np.ndarray:
    if rule == "free":
        return np.arange(1, n)
    if rule == "balanced":
        return np.unique([(n + 1) // 2, n // 2])
    if rule == "chain":
        return np.unique([1, n - 1])
    raise ValueError(f"unknown rule {rule!r}")


def solve_dp(
    n_max: int, x: float, t: float, eta0: float = 1.0, rule: Rule = "free"
) -> tuple[np.ndarray, np.ndarray]:
    """Fill the dynamic-programming tables.

    Args:
        n_max: largest number of sources considered.
        x: per-source thermal brightness.
        t: power transmission of one switch.
        eta0: transmission outside the network.
        rule: ``"free"`` (any shape), ``"balanced"`` or ``"chain"`` (the left
            subtree size is restricted to what that topology allows, but the
            priority order is still optimised).

    Returns:
        ``(V, split)`` with shape ``(n_max + 1, n_max + 1)``; ``V[n, 0]`` is
        the optimal probability of exactly one output photon for n sources.
    """
    K = n_max + 1
    ks = np.arange(K)
    V = np.zeros((n_max + 1, K))
    split = np.zeros((n_max + 1, K), dtype=int)
    V[1] = x * leaf_one(eta0 * t**ks, x)
    w = (1.0 - x) ** np.arange(n_max + 1)
    for n in range(2, n_max + 1):
        a = _candidates(n, rule)
        cand = V[a, 1:] + w[a][:, None] * V[n - a, 1:]
        idx = cand.argmax(axis=0)
        V[n, : K - 1] = cand[idx, np.arange(K - 1)]
        split[n, : K - 1] = a[idx]
        V[n, K - 1], split[n, K - 1] = V[n, K - 2], split[n, K - 2]
    return V, split


def best_tree(split: np.ndarray, n: int, k: int = 0) -> Tree:
    """Rebuild the optimal tree for ``n`` sources from the ``split`` table."""
    if n == 1:
        return 1
    a = int(split[n, k])
    return (best_tree(split, a, k + 1), best_tree(split, n - a, k + 1))
