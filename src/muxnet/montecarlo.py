"""Event-level Monte Carlo of a switch tree, used to validate the closed forms."""

from __future__ import annotations

import numpy as np

from .tree import Tree, leaf_depths, n_leaves


def simulate_tree(
    tree: Tree, x: float, t: float, eta0: float, shots: int, rng: np.random.Generator
) -> tuple[float, float]:
    """Sample ``shots`` experiments; return (fraction with exactly one photon, fraction with >= 1)."""
    n = n_leaves(tree)
    pairs = rng.geometric(1.0 - x, size=(shots, n)) - 1  # P(k) = (1-x) x^k, k >= 0
    clicked = pairs > 0
    T_leaf = eta0 * t ** np.asarray(leaf_depths(tree), dtype=float)
    pos = [0]

    def rec(node: Tree) -> tuple[np.ndarray, np.ndarray]:
        """Return (subtree has a click, index of selected leaf per shot)."""
        if isinstance(node, int):
            i = pos[0]
            pos[0] += 1
            return clicked[:, i], np.full(shots, i)
        pl, il = rec(node[0])
        pr, ir = rec(node[1])
        return pl | pr, np.where(pl, il, ir)

    has, sel = rec(tree)
    k_in = pairs[np.arange(shots), sel]
    k_out = rng.binomial(k_in, T_leaf[sel])
    k_out = np.where(has, k_out, 0)
    return float(np.mean(k_out == 1)), float(np.mean(k_out >= 1))
