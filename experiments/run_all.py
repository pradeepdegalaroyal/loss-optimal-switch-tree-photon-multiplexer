"""Reproduce every result and figure: ``python experiments/run_all.py`` (add ``--quick`` for a smoke run)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from muxnet import plots, studies  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="small grids, under one minute")
    args = ap.parse_args()
    cfg = studies.make_config(args.quick)
    out = ROOT / ("results_quick" if args.quick else "results")
    figs = ROOT / ("figures_quick" if args.quick else "figures")
    out.mkdir(exist_ok=True)
    figs.mkdir(exist_ok=True)
    t0 = time.perf_counter()
    summary: dict = {"quick": args.quick, "config": {
        "n_max": cfg.n_max, "loss_db": list(cfg.loss_db), "x_grid": list(cfg.x_grid),
        "seeds": cfg.seeds, "n_design": cfg.n_design, "ref_loss_db": cfg.ref_loss_db,
        "x_baseline": cfg.x_baseline}}

    df, _ = studies.topology_sweep(cfg)
    df.to_csv(out / "topology_sweep.csv", index=False)
    scal, fits = studies.loss_scaling(df, cfg)
    scal.to_csv(out / "loss_scaling.csv", index=False)
    summary["single_source_p_one"] = scal.attrs["single_source_p_one"]
    summary["loss_scaling_fits"] = fits
    runtime, rt_fit = studies.dp_runtime(cfg)
    runtime.to_csv(out / "dp_runtime.csv", index=False)
    summary["dp_runtime_fit"] = rt_fit
    plots.fig_scaling(scal, fits, runtime, rt_fit, scal.attrs["single_source_p_one"],
                      figs / "fig1_loss_scaling.png")
    print(f"[{time.perf_counter() - t0:6.1f}s] sweep + scaling done", flush=True)

    gain = studies.gain_map(df, cfg)
    gain.to_csv(out / "gain_vs_balanced.csv", index=False)
    plots.fig_gain(gain, figs / "fig2_shape_gain_heatmap.png")

    mm = studies.mismatch_map(cfg)
    mm.to_csv(out / "loss_mismatch.csv", index=False)
    plots.fig_mismatch(mm, figs / "fig3_loss_mismatch_heatmap.png")
    summary["mismatch"] = {
        "max_deficit_free": float(mm.deficit_free.max()),
        "max_deficit_balanced": float(mm.deficit_balanced.max()),
        "frac_cells_mismatched_free_beats_matched_balanced": float(
            np.mean(mm.p_free >= mm.p_matched_balanced)),
    }
    print(f"[{time.perf_counter() - t0:6.1f}s] gain + mismatch done", flush=True)

    wf = studies.waterfall(cfg)
    wf.to_csv(out / "waterfall.csv", index=False)
    summary["waterfall_design"] = {k: (v if isinstance(v, str) else float(v)) for k, v in wf.attrs.items()}
    plots.fig_waterfall(wf, figs / "fig4_design_waterfall.png")

    var = studies.variation_study(cfg)
    var.to_csv(out / "loss_variation.csv", index=False)
    plots.fig_variation(var, figs / "fig5_loss_variation.png")

    hc = studies.search_baseline(df, cfg)
    hc.to_csv(out / "search_baseline.csv", index=False)
    mc = studies.mc_validation(cfg)
    mc.to_csv(out / "montecarlo_validation.csv", index=False)
    summary["runtime_total_s"] = time.perf_counter() - t0
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"[{time.perf_counter() - t0:6.1f}s] all done -> {out}", flush=True)


if __name__ == "__main__":
    main()
