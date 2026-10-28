# Method

## System model

- **Source.** Each of N sources emits n photon pairs with thermal statistics P(n) = (1 - x) x^n, where x is the brightness. A threshold herald detector clicks when n >= 1, so a heralded source holds n >= 1 photons with probability (1 - x) x^(n-1).
- **Switch tree.** A tree of N - 1 two-by-two switches. Each switch forwards its left input if that subtree holds a heralded source and its right input otherwise (left priority). Every switch has power transmission t = 10^(-loss/10); a source at depth d sees t^d. Loss outside the network is set to zero.
- **Output.** Each photon of the selected source survives independently with probability T = t^d. The target is the probability P1 that exactly one photon leaves. Closed form for one source: P(exactly one | click) = (1 - x) T / (1 - x (1 - T))^2.
- **Recursion.** Let V(n, k) be the best expected P1 of a subtree with n sources whose output must still cross k switches. Then V(1, k) = x h(t^k) and V(n, k) = max over a of [V(a, k+1) + (1 - x)^a V(n - a, k+1)], where h is the closed form above. This is a dynamic program (DP) with O(N^3) arithmetic that gives the optimum for every n <= N at once, over all tree shapes and priority orders. Restricting the split sizes a gives the balanced tree (a near n/2) and the cascade (a = 1 or n - 1) with their priorities optimised, so the baselines are strong.

## Methods compared

| Role | Method |
|---|---|
| Proposed | Exact dynamic program over all shapes (`rule="free"`) |
| Standard architecture baseline | Balanced binary tree and cascade, priorities optimised (`rule="balanced"`, `rule="chain"`) |
| Classical optimisation baseline | Hill climbing over shapes (swap priorities, redraw a subtree), 3,000 objective evaluations, random start |
| No multiplexing | Single source, brightness tuned |

## Metrics

P1 (exactly one photon), infidelity 1 - P1, purity P1 divided by the probability of at least one photon, relative gain over the balanced tree, deficit against the matched optimum, solver wall-clock time.

## Experiments

1. **Validation.** Closed forms against event-level MC (200,000 shots, 5 seeds) for N = 16 at 0.3 dB.
2. **Loss scaling.** 13 per-switch losses (0.01 to 1 dB, log-spaced), 18 brightness values, N up to 128. For each topology, infidelity at the best N and brightness, and a log-log power-law fit.
3. **Shape gain map.** Relative gain of the free optimum over the balanced tree on an N by loss grid.
4. **Ablation (waterfall).** At 0.3 dB and N = 32: single source, add a cascade, switch to a balanced tree, switch to the optimal shape, re-tune brightness.
5. **Noise and robustness sweeps.** (a) Design for one loss value, operate at another (7 by 7 grid). (b) Switch-to-switch loss spread: per-switch loss drawn from a clipped Gaussian around 0.3 dB with standard deviation 0 to 0.3 dB, 100 draws per seed, 5 seeds.
6. **Baseline search.** Hill climbing against the exact program for N = 8, 16, 32, 64, 5 seeds.
7. **Cost.** Solver time against N.

## Seeds and limits

Seeds 0 to 4 (MC and hill climbing), 1000 to 1004 (loss spread). Exact calculations are deterministic. Reference loss 0.3 dB for the waterfall and the spread study; grid points closest to it (0.316 dB) for the baseline search. Total compute well under 5 minutes on a laptop CPU.

## Out of scope

Herald-detector inefficiency and dark counts, source-to-source brightness spread, switch crosstalk, delay-line loss and timing are not modelled; per-switch loss can be read as including a delay-line share.
