"""Binary switch trees: construction, evaluation and bookkeeping.

A tree is either the integer ``1`` (one heralded source, a leaf) or a pair
``(left, right)`` (a 2x2 optical switch that forwards a photon from ``left`` if
that subtree holds a heralded photon and otherwise from ``right``). Every
switch has power transmission ``t``; a leaf at depth d therefore sees t^d.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Union

import numpy as np

from .source import leaf_ge1, leaf_one

Tree = Union[int, tuple]


def n_leaves(tree: Tree) -> int:
    """Number of sources in ``tree``."""
    return 1 if isinstance(tree, int) else n_leaves(tree[0]) + n_leaves(tree[1])


def n_switches(tree: Tree) -> int:
    """Number of 2x2 switches in ``tree`` (always leaves - 1)."""
    return n_leaves(tree) - 1


def balanced_tree(n: int) -> Tree:
    """Most balanced tree on ``n`` leaves (subtree sizes differ by at most one)."""
    if n == 1:
        return 1
    a = (n + 1) // 2
    return (balanced_tree(a), balanced_tree(n - a))


def chain_tree(n: int) -> Tree:
    """Cascade in which every switch merges one source with the rest of the chain."""
    if n == 1:
        return 1
    return (1, chain_tree(n - 1))


def leaf_depths(tree: Tree, depth: int = 0) -> list[int]:
    """Depth (number of switches crossed) of every leaf, in left-to-right order."""
    if isinstance(tree, int):
        return [depth]
    return leaf_depths(tree[0], depth + 1) + leaf_depths(tree[1], depth + 1)


def internal_paths(tree: Tree, path: tuple[int, ...] = ()) -> Iterator[tuple[int, ...]]:
    """Paths (0 = left, 1 = right) to every internal node."""
    if isinstance(tree, int):
        return
    yield path
    yield from internal_paths(tree[0], path + (0,))
    yield from internal_paths(tree[1], path + (1,))


def get_subtree(tree: Tree, path: Sequence[int]) -> Tree:
    """Return the subtree at ``path``."""
    for step in path:
        tree = tree[step]  # type: ignore[index]
    return tree


def replace_subtree(tree: Tree, path: Sequence[int], new: Tree) -> Tree:
    """Return a copy of ``tree`` with the subtree at ``path`` replaced by ``new``."""
    if not path:
        return new
    assert not isinstance(tree, int)
    if path[0] == 0:
        return (replace_subtree(tree[0], path[1:], new), tree[1])
    return (tree[0], replace_subtree(tree[1], path[1:], new))


def evaluate_tree(
    tree: Tree, x: float, t: float | np.ndarray, eta0: float = 1.0
) -> tuple[float, float]:
    """Exact output statistics of ``tree``.

    Args:
        tree: switch tree.
        x: per-source thermal brightness.
        t: power transmission of every switch (scalar) or one value per
            internal node in pre-order (array of length ``n_leaves - 1``).
        eta0: transmission outside the switch network (collection, coupling).

    Returns:
        ``(p_one, p_ge1)``: probability that exactly one photon, respectively at
        least one photon, leaves the network.
    """
    t_arr = np.broadcast_to(np.asarray(t, dtype=float), (max(n_leaves(tree) - 1, 1),))
    counter = [0]

    def rec(node: Tree, t_up: float) -> tuple[float, float, float]:
        if isinstance(node, int):
            T = eta0 * t_up
            return x, x * float(leaf_one(T, x)), x * float(leaf_ge1(T, x))
        tn = float(t_arr[counter[0]])
        counter[0] += 1
        q_l, one_l, ge_l = rec(node[0], t_up * tn)
        q_r, one_r, ge_r = rec(node[1], t_up * tn)
        miss_l = 1.0 - q_l
        return 1.0 - miss_l * (1.0 - q_r), one_l + miss_l * one_r, ge_l + miss_l * ge_r

    _, p_one, p_ge1 = rec(tree, 1.0)
    return p_one, p_ge1


def render(tree: Tree) -> str:
    """Compact string such as ``((1,1),1)`` for logging."""
    if isinstance(tree, int):
        return "1"
    return f"({render(tree[0])},{render(tree[1])})"
