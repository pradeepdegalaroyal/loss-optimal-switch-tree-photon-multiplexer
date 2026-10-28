import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muxnet.montecarlo import simulate_tree  # noqa: E402
from muxnet.optimal import best_tree, solve_dp  # noqa: E402
from muxnet.search import hill_climb  # noqa: E402
from muxnet.source import db_to_transmission, leaf_ge1, leaf_one  # noqa: E402
from muxnet.tree import balanced_tree, chain_tree, evaluate_tree, leaf_depths, n_leaves  # noqa: E402


def test_leaf_formulas_limits():
    assert np.isclose(leaf_one(1.0, 0.3), 0.7)  # lossless: only the one-pair events are single
    assert np.isclose(leaf_ge1(1.0, 0.3), 1.0)
    assert np.isclose(leaf_one(0.0, 0.3), 0.0)


def test_single_source_closed_form():
    x = 0.2
    assert np.isclose(evaluate_tree(1, x, 0.5)[0], x * (1 - x))


def test_tree_shapes():
    assert n_leaves(balanced_tree(13)) == 13
    assert max(leaf_depths(balanced_tree(16))) == 4
    assert max(leaf_depths(chain_tree(16))) == 15


def test_dp_matches_direct_evaluation():
    t = float(db_to_transmission(0.3))
    for rule in ("free", "balanced", "chain"):
        V, split = solve_dp(20, 0.1, t, 1.0, rule)  # type: ignore[arg-type]
        for n in (5, 12, 20):
            tree = best_tree(split, n)
            assert n_leaves(tree) == n
            assert np.isclose(evaluate_tree(tree, 0.1, t)[0], V[n, 0])


def test_free_dominates_restricted_rules():
    t = float(db_to_transmission(0.5))
    Vf, _ = solve_dp(40, 0.1, t, 1.0, "free")
    Vb, _ = solve_dp(40, 0.1, t, 1.0, "balanced")
    Vc, _ = solve_dp(40, 0.1, t, 1.0, "chain")
    assert np.all(Vf[1:, 0] >= Vb[1:, 0] - 1e-12)
    assert np.all(Vf[1:, 0] >= Vc[1:, 0] - 1e-12)


def test_dp_beats_brute_force_small():
    # exhaustive over all ordered shapes for n = 6
    from functools import lru_cache

    t = float(db_to_transmission(1.0))

    @lru_cache(maxsize=None)
    def shapes(n):
        if n == 1:
            return [1]
        return [(a, b) for k in range(1, n) for a in shapes(k) for b in shapes(n - k)]

    best = max(evaluate_tree(s, 0.2, t)[0] for s in shapes(6))
    V, _ = solve_dp(6, 0.2, t, 1.0, "free")
    assert np.isclose(best, V[6, 0])


def test_monte_carlo_agrees():
    t = float(db_to_transmission(0.3))
    tree = balanced_tree(8)
    exact = evaluate_tree(tree, 0.1, t)
    sim = simulate_tree(tree, 0.1, t, 1.0, 200000, np.random.default_rng(0))
    assert abs(sim[0] - exact[0]) < 0.006
    assert abs(sim[1] - exact[1]) < 0.006


def test_hill_climb_never_beats_exact():
    t = float(db_to_transmission(0.3))
    V, _ = solve_dp(10, 0.1, t, 1.0, "free")
    _, val = hill_climb(10, 0.1, t, 1.0, 200, np.random.default_rng(1))
    assert val <= V[10, 0] + 1e-12
