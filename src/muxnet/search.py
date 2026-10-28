"""Generic stochastic shape search: the classical baseline for the exact program."""

from __future__ import annotations

import numpy as np

from .tree import (
    Tree,
    evaluate_tree,
    get_subtree,
    internal_paths,
    n_leaves,
    replace_subtree,
)


def random_tree(n: int, rng: np.random.Generator) -> Tree:
    """Tree on ``n`` leaves with uniformly random split sizes."""
    if n == 1:
        return 1
    a = int(rng.integers(1, n))
    return (random_tree(a, rng), random_tree(n - a, rng))


def mutate(tree: Tree, rng: np.random.Generator) -> Tree:
    """Swap the priority of one switch, or re-draw one subtree at random."""
    paths = list(internal_paths(tree))
    path = paths[int(rng.integers(len(paths)))]
    sub = get_subtree(tree, path)
    if rng.random() < 0.5:
        return replace_subtree(tree, path, (sub[1], sub[0]))  # type: ignore[index]
    return replace_subtree(tree, path, random_tree(n_leaves(sub), rng))


def hill_climb(
    n: int, x: float, t: float, eta0: float, budget: int, rng: np.random.Generator
) -> tuple[Tree, float]:
    """Hill climbing from a random tree with ``budget`` objective evaluations."""
    best = random_tree(n, rng)
    best_val = evaluate_tree(best, x, t, eta0)[0]
    for _ in range(budget - 1):
        cand = mutate(best, rng)
        val = evaluate_tree(cand, x, t, eta0)[0]
        if val >= best_val:
            best, best_val = cand, val
    return best, best_val
