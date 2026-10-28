"""The individual studies run by ``experiments/run_all.py``.

Each function returns plain pandas / dict objects so that plotting and result
writing stay separate from the physics.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .montecarlo import simulate_tree
from .optimal import best_tree, solve_dp
from .search import hill_climb
from .source import db_to_transmission
from .tree import balanced_tree, chain_tree, evaluate_tree, leaf_depths, render

RULES = ("free", "balanced", "chain")


@dataclass(frozen=True)
class Config:
    """Size of the experiment grid (``quick`` is a smoke run)."""

    n_max: int
    loss_db: tuple[float, ...]
    x_grid: tuple[float, ...]
    seeds: int
    mc_shots: int
    hc_budget: int
    hc_sizes: tuple[int, ...]
    runtime_sizes: tuple[int, ...]
    n_design: int
    mismatch_db: tuple[float, ...]
    sigma_db: tuple[float, ...]
    draws: int
    heat_n: tuple[int, ...]
    ref_loss_db: float = 0.3
    x_baseline: float = 0.1


def make_config(quick: bool) -> Config:
    """Full or quick configuration."""
    if quick:
        return Config(
            n_max=32,
            loss_db=tuple(np.geomspace(0.03, 1.0, 5)),
            x_grid=tuple(np.geomspace(0.02, 0.6, 7)),
            seeds=2,
            mc_shots=20000,
            hc_budget=300,
            hc_sizes=(8, 16),
            runtime_sizes=(8, 16, 32, 64),
            n_design=16,
            mismatch_db=(0.1, 0.3, 1.0),
            sigma_db=(0.0, 0.1, 0.3),
            draws=10,
            heat_n=(2, 4, 8, 16, 32),
        )
    return Config(
        n_max=128,
        loss_db=tuple(np.geomspace(0.01, 1.0, 13)),
        x_grid=tuple(np.geomspace(0.01, 0.7, 18)),
        seeds=5,
        mc_shots=200000,
        hc_budget=3000,
        hc_sizes=(8, 16, 32, 64),
        runtime_sizes=(16, 32, 64, 128, 256),
        n_design=32,
        mismatch_db=tuple(np.geomspace(0.03, 1.0, 7)),
        sigma_db=(0.0, 0.05, 0.1, 0.2, 0.3),
        draws=100,
        heat_n=(2, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128),
    )


def _t(loss_db: float) -> float:
    return float(db_to_transmission(loss_db))


def topology_sweep(cfg: Config) -> tuple[pd.DataFrame, np.ndarray]:
    """Optimal one-photon probability for every topology, loss, brightness and size.

    Returns a long table of the best brightness per (rule, loss, n) and the raw
    array ``P[rule, loss, x, n]``.
    """
    P = np.zeros((len(RULES), len(cfg.loss_db), len(cfg.x_grid), cfg.n_max + 1))
    for r, rule in enumerate(RULES):
        for i, ldb in enumerate(cfg.loss_db):
            for j, x in enumerate(cfg.x_grid):
                V, _ = solve_dp(cfg.n_max, x, _t(ldb), 1.0, rule)  # type: ignore[arg-type]
                P[r, i, j] = V[:, 0]
    rows = []
    for r, rule in enumerate(RULES):
        for i, ldb in enumerate(cfg.loss_db):
            for n in range(1, cfg.n_max + 1):
                j = int(P[r, i, :, n].argmax())
                rows.append(
                    dict(rule=rule, loss_db=ldb, n=n, x_best=cfg.x_grid[j], p_one=P[r, i, j, n])
                )
    return pd.DataFrame(rows), P


def loss_scaling(df: pd.DataFrame, cfg: Config) -> tuple[pd.DataFrame, dict]:
    """Best infidelity 1 - P1 over size and brightness vs switch loss, with power-law fits."""
    rows = []
    for rule in RULES:
        for ldb in cfg.loss_db:
            sub = df[(df.rule == rule) & (np.isclose(df.loss_db, ldb))]
            top = sub.p_one.max()
            n_eff = int(sub[sub.p_one >= 0.999 * top].n.min())
            best = sub[sub.n == n_eff].iloc[0]
            rows.append(
                dict(rule=rule, loss_db=ldb, p_one=top, infidelity=1 - top, n_eff=n_eff,
                     x_best=best.x_best)
            )
    single = df[df.n == 1].groupby("loss_db").p_one.max().iloc[0]
    out = pd.DataFrame(rows)
    out.attrs["single_source_p_one"] = float(single)
    fits = {}
    for rule in RULES:
        sub = out[out.rule == rule]
        ok = sub[sub.n_eff < cfg.n_max]
        use = ok if len(ok) >= 4 else sub
        slope, icpt = np.polyfit(np.log10(use.loss_db), np.log10(use.infidelity), 1)
        fits[rule] = dict(slope=float(slope), intercept=float(icpt), n_points=int(len(use)),
                          loss_range_db=[float(use.loss_db.min()), float(use.loss_db.max())])
    return out, fits


def gain_map(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Relative gain of the free-shape optimum over the balanced tree at fixed size n."""
    rows = []
    for n in cfg.heat_n:
        for ldb in cfg.loss_db:
            sel = df[(df.n == n) & np.isclose(df.loss_db, ldb)]
            free = sel[sel.rule == "free"].p_one.iloc[0]
            bal = sel[sel.rule == "balanced"].p_one.iloc[0]
            chain = sel[sel.rule == "chain"].p_one.iloc[0]
            rows.append(dict(n=n, loss_db=ldb, p_free=free, p_balanced=bal, p_chain=chain,
                             gain_vs_balanced=free / bal - 1.0, gain_vs_chain=free / chain - 1.0))
    return pd.DataFrame(rows)


def _design(n: int, ldb: float, cfg: Config, rule: str) -> tuple[float, object, float]:
    """Best brightness and tree for ``n`` sources at ``ldb`` dB per switch."""
    best = (-1.0, 0.0, None)
    for x in cfg.x_grid:
        V, sp = solve_dp(n, x, _t(ldb), 1.0, rule)  # type: ignore[arg-type]
        if V[n, 0] > best[0]:
            best = (float(V[n, 0]), float(x), best_tree(sp, n))
    return best[1], best[2], best[0]


def mismatch_map(cfg: Config) -> pd.DataFrame:
    """Design at one loss, operate at another: relative deficit vs the matched optimum."""
    n = cfg.n_design
    designs = {rule: {d: _design(n, d, cfg, rule) for d in cfg.mismatch_db}
               for rule in ("free", "balanced")}
    rows = []
    for true in cfg.mismatch_db:
        ref = designs["free"][true][2]
        ref_bal = designs["balanced"][true][2]
        for d in cfg.mismatch_db:
            row = dict(design_db=d, true_db=true, p_matched_free=ref, p_matched_balanced=ref_bal)
            for rule in ("free", "balanced"):
                x, tree, _ = designs[rule][d]
                row[f"p_{rule}"] = evaluate_tree(tree, x, _t(true))[0]
            row["deficit_free"] = 1.0 - row["p_free"] / ref
            row["deficit_balanced"] = 1.0 - row["p_balanced"] / ref_bal
            rows.append(row)
    return pd.DataFrame(rows)


def variation_study(cfg: Config) -> pd.DataFrame:
    """Per-switch loss spread (fabrication variation) with designs made for the mean loss."""
    n, ldb = cfg.n_design, cfg.ref_loss_db
    designs = {rule: _design(n, ldb, cfg, rule) for rule in ("free", "balanced")}
    rows = []
    for sigma in cfg.sigma_db:
        for seed in range(cfg.seeds):
            rng = np.random.default_rng(1000 + seed)
            acc = {"free": [], "balanced": []}
            for _ in range(cfg.draws):
                loss = np.clip(rng.normal(ldb, sigma, size=n - 1), 0.0, None)
                t = db_to_transmission(loss)
                for rule in acc:
                    x, tree, _ = designs[rule]
                    acc[rule].append(evaluate_tree(tree, x, t)[0])
            rows.append(dict(sigma_db=sigma, seed=seed, p_free=np.mean(acc["free"]),
                             p_balanced=np.mean(acc["balanced"])))
    return pd.DataFrame(rows)


def search_baseline(df_sweep: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Hill-climbing shape search versus the exact program at the reference loss."""
    ldb = min(cfg.loss_db, key=lambda v: abs(v - cfg.ref_loss_db))
    rows = []
    for n in cfg.hc_sizes:
        x, _, exact = _design(n, ldb, cfg, "free")
        t = _t(ldb)
        t0 = time.perf_counter()
        solve_dp(n, x, t, 1.0, "free")
        dp_time = time.perf_counter() - t0
        for seed in range(cfg.seeds):
            rng = np.random.default_rng(seed)
            t0 = time.perf_counter()
            _, val = hill_climb(n, x, t, 1.0, cfg.hc_budget, rng)
            rows.append(dict(n=n, seed=seed, loss_db=ldb, x=x, exact=exact, hill_climb=val,
                             relative_gap=1.0 - val / exact, hc_seconds=time.perf_counter() - t0,
                             dp_seconds=dp_time))
    return pd.DataFrame(rows)


def mc_validation(cfg: Config) -> pd.DataFrame:
    """Closed-form probabilities versus event-level Monte Carlo."""
    ldb, x = cfg.ref_loss_db, cfg.x_baseline
    n = min(16, cfg.n_design)
    trees = {
        "free": _design(n, ldb, cfg, "free")[1],
        "balanced": balanced_tree(n),
        "chain": chain_tree(n),
    }
    rows = []
    for name, tree in trees.items():
        exact_one, exact_ge1 = evaluate_tree(tree, x, _t(ldb))
        sims = []
        for seed in range(cfg.seeds):
            rng = np.random.default_rng(seed)
            sims.append(simulate_tree(tree, x, _t(ldb), 1.0, cfg.mc_shots, rng))
        s1 = np.array([s[0] for s in sims])
        sg = np.array([s[1] for s in sims])
        rows.append(dict(topology=name, n=n, loss_db=ldb, x=x, exact_p_one=exact_one,
                         mc_p_one_mean=s1.mean(), mc_p_one_std=s1.std(ddof=1),
                         exact_p_ge1=exact_ge1, mc_p_ge1_mean=sg.mean(), mc_p_ge1_std=sg.std(ddof=1),
                         z_p_one=(s1.mean() - exact_one) / (s1.std(ddof=1) / np.sqrt(len(s1)) + 1e-12)))
    return pd.DataFrame(rows)


def dp_runtime(cfg: Config) -> tuple[pd.DataFrame, dict]:
    """Wall-clock time of the exact program versus the number of sources."""
    rows = []
    t = _t(cfg.ref_loss_db)
    for n in cfg.runtime_sizes:
        times = []
        solve_dp(n, cfg.x_baseline, t, 1.0, "free")  # warm-up
        for _ in range(7):
            t0 = time.perf_counter()
            solve_dp(n, cfg.x_baseline, t, 1.0, "free")
            times.append(time.perf_counter() - t0)
        rows.append(dict(n_max=n, seconds=float(np.min(times))))
    out = pd.DataFrame(rows)
    slope, icpt = np.polyfit(np.log10(out.n_max), np.log10(out.seconds), 1)
    return out, dict(slope=float(slope), intercept=float(icpt))


def waterfall(cfg: Config) -> pd.DataFrame:
    """Stepwise contribution of each design component at the reference loss."""
    n, ldb, x0 = cfg.n_design, cfg.ref_loss_db, cfg.x_baseline
    t = _t(ldb)
    steps = [("single source", evaluate_tree(1, x0, t)[0])]
    steps.append(("+ cascade of sources", evaluate_tree(chain_tree(n), x0, t)[0]))
    steps.append(("balanced tree instead", evaluate_tree(balanced_tree(n), x0, t)[0]))
    V, sp = solve_dp(n, x0, t, 1.0, "free")
    steps.append(("+ optimal unbalanced shape", float(V[n, 0])))
    x_star, tree, p_star = _design(n, ldb, cfg, "free")
    steps.append(("+ re-tuned brightness", p_star))
    rows, prev = [], 0.0
    for name, val in steps:
        rows.append(dict(step=name, p_one=val, delta=val - prev))
        prev = val
    out = pd.DataFrame(rows)
    p_one, p_ge1 = evaluate_tree(tree, x_star, t)
    depths = leaf_depths(tree)
    out.attrs.update(x_star=x_star, p_one=p_one, p_ge1=p_ge1, purity=p_one / p_ge1,
                     min_depth=int(min(depths)), max_depth=int(max(depths)), tree=render(tree))
    return out
