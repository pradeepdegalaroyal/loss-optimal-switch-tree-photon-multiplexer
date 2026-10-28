"""Figures (earth-tone palette, 200 dpi)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

BROWN, TEAL, OCHRE, SAND, INK, CLAY = "#6b4226", "#1f6f6b", "#cc8f1d", "#e8d9bd", "#2f2a26", "#b5532f"
EARTH = LinearSegmentedColormap.from_list("earth", [SAND, OCHRE, CLAY, BROWN])
EARTH_DIV = LinearSegmentedColormap.from_list("earthdiv", [TEAL, "#f4ecd8", CLAY])
DPI = 200


def _style(ax: plt.Axes) -> None:
    ax.set_facecolor("#fbf7ee")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(alpha=0.3, color=BROWN, lw=0.5)


def _save(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=DPI, facecolor="white")
    plt.close(fig)


def fig_scaling(scal: pd.DataFrame, fits: dict, runtime: pd.DataFrame, rt_fit: dict,
                single_p1: float, path: Path) -> None:
    """Log-log: infidelity versus switch loss (left), solver runtime versus size (right)."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    ax = axes[0]
    _style(ax)
    style = {"free": (TEAL, "o", "optimal shape"), "balanced": (OCHRE, "s", "balanced tree"),
             "chain": (BROWN, "^", "cascade")}
    for k, (rule, (col, mk, lab)) in enumerate(style.items()):
        sub = scal[scal.rule == rule]
        ax.loglog(sub.loss_db, sub.infidelity, mk + "-", color=col, label=lab, ms=5)
        f = fits[rule]
        xs = np.array(f["loss_range_db"])
        ys = 10 ** (f["intercept"] + f["slope"] * np.log10(xs))
        ax.loglog(xs, ys * 0.8, "--", color=col, lw=1)
        ax.text(0.03, 0.9 - 0.07 * k, f"{lab}: fitted slope {f['slope']:.2f}", color=col,
                fontsize=9, transform=ax.transAxes)
    ax.axhline(1 - single_p1, color=INK, ls=":", lw=1)
    ax.text(scal.loss_db.max(), (1 - single_p1) * 0.95, "single source, no switches",
            color=INK, fontsize=8, va="top", ha="right")
    ax.set_xlabel("loss per switch (dB)")
    ax.set_ylabel("best infidelity 1 - P(exactly one photon)")
    ax.set_title("Infidelity versus switch loss")
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax = axes[1]
    _style(ax)
    ax.loglog(runtime.n_max, runtime.seconds, "o-", color=TEAL)
    xs = runtime.n_max.to_numpy()
    ax.loglog(xs, 10 ** (rt_fit["intercept"] + rt_fit["slope"] * np.log10(xs)) * 0.7, "--", color=BROWN, lw=1)
    ax.annotate(f"fitted slope {rt_fit['slope']:.2f}", (xs[0], runtime.seconds.iloc[0]), color=BROWN,
                xytext=(10, 40), textcoords="offset points")
    ax.set_xticks(xs, [str(v) for v in xs])
    ax.minorticks_off()
    ax.set_xlabel("number of sources N")
    ax.set_ylabel("exact solver time (s)")
    ax.set_title("Cost of the exact shape optimisation")
    _save(fig, path)


def _annotated_heatmap(ax: plt.Axes, mat: np.ndarray, xt: list[str], yt: list[str], cmap, fmt: str,
                       label: str, fig: plt.Figure, vmin=None, vmax=None) -> None:
    mat = np.where(np.abs(mat) < 0.05, 0.0, mat)
    im = ax.imshow(mat, aspect="auto", origin="lower", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(xt)), xt, rotation=45)
    ax.set_yticks(range(len(yt)), yt)
    lo, hi = np.nanmin(mat) if vmin is None else vmin, np.nanmax(mat) if vmax is None else vmax
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            dark = (mat[i, j] - lo) / (hi - lo + 1e-12) > 0.6
            ax.text(j, i, format(mat[i, j], fmt), ha="center", va="center", fontsize=7,
                    color="white" if dark else INK)
    fig.colorbar(im, ax=ax, label=label)


def fig_gain(gain: pd.DataFrame, path: Path) -> None:
    """Heatmap of the percentage gain of the optimal shape over the balanced tree."""
    piv = gain.pivot(index="n", columns="loss_db", values="gain_vs_balanced") * 100
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    _annotated_heatmap(ax, piv.to_numpy(), [f"{c:.2g}" for c in piv.columns],
                       [str(i) for i in piv.index], EARTH, ".1f",
                       "gain in P(exactly one photon) (%)", fig)
    ax.set_xlabel("loss per switch (dB)")
    ax.set_ylabel("number of sources N (brightness tuned per topology)")
    ax.set_title("Optimal shape versus balanced tree")
    _save(fig, path)


def fig_mismatch(mm: pd.DataFrame, path: Path) -> None:
    """Heatmaps: relative deficit when the design loss differs from the true loss."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    vmax = float(max(mm.deficit_free.max(), mm.deficit_balanced.max()) * 100)
    for ax, col, title in zip(axes, ("deficit_free", "deficit_balanced"),
                              ("optimal-shape design", "balanced-tree design")):
        piv = mm.pivot(index="true_db", columns="design_db", values=col) * 100
        _annotated_heatmap(ax, piv.to_numpy(), [f"{c:.2g}" for c in piv.columns],
                           [f"{c:.2g}" for c in piv.index], EARTH, ".1f",
                           "deficit vs matched optimum (%)", fig, vmin=0.0, vmax=vmax)
        ax.set_xlabel("loss per switch assumed at design (dB)")
        ax.set_title(title)
    axes[0].set_ylabel("loss per switch in operation (dB)")
    _save(fig, path)


def fig_waterfall(wf: pd.DataFrame, path: Path) -> None:
    """Waterfall of the stepwise contribution of each design component."""
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    _style(ax)
    base = 0.0
    labels = list(wf.step) + ["optimised design"]
    for i, r in wf.iterrows():
        bottom = 0.0 if i == 0 else base
        col = TEAL if r.delta >= 0 else CLAY
        if i == 0:
            col = BROWN
        ax.bar(i, r.delta if i else r.p_one, bottom=bottom if i else 0.0, color=col, width=0.6)
        ax.text(i, max(bottom, bottom + r.delta) + 0.012, f"{r.delta:+.3f}" if i else f"{r.p_one:.3f}",
                ha="center", fontsize=9)
        base = r.p_one
    ax.bar(len(wf), wf.p_one.iloc[-1], color=OCHRE, width=0.6)
    ax.text(len(wf), wf.p_one.iloc[-1] + 0.012, f"{wf.p_one.iloc[-1]:.3f}", ha="center", fontsize=9)
    ax.set_xticks(range(len(labels)), labels, rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("P(exactly one photon at the output)")
    ax.set_title("Contribution of each design step (loss per switch fixed)")
    _save(fig, path)


def fig_variation(var: pd.DataFrame, path: Path) -> None:
    """Mean and standard deviation over seeds versus switch-to-switch loss spread."""
    g = var.groupby("sigma_db").agg(["mean", "std"])
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    _style(ax)
    for col, c, lab, mk in (("p_free", TEAL, "optimal shape", "o"), ("p_balanced", OCHRE, "balanced tree", "s")):
        ax.errorbar(g.index, g[col]["mean"], yerr=g[col]["std"], color=c, marker=mk, capsize=3, label=lab)
    ax.set_xlabel("spread of loss per switch, standard deviation (dB)")
    ax.set_ylabel("P(exactly one photon)")
    ax.set_title("Robustness to switch-to-switch loss spread")
    ax.legend(frameon=False)
    _save(fig, path)
