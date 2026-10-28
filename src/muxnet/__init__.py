"""muxnet: loss-aware design of photon-source multiplexing switch networks."""

from .optimal import best_tree, solve_dp
from .source import leaf_ge1, leaf_one
from .tree import balanced_tree, chain_tree, evaluate_tree, leaf_depths, n_leaves

__all__ = [
    "balanced_tree",
    "best_tree",
    "chain_tree",
    "evaluate_tree",
    "leaf_depths",
    "leaf_ge1",
    "leaf_one",
    "n_leaves",
    "solve_dp",
]
__version__ = "0.1.0"
