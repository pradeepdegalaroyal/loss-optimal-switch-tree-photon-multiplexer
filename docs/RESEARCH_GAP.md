# Research gap: how lossy switches should shape a photon-source multiplexer

## State of the art (from the supplied literature)

Integrated photonics is moving from components to systems. Wang et al. (2020, digital object identifier (DOI) 10.1038/s41566-019-0532-1) review programmable integrated devices approaching 1,000 components with on-chip multiphoton-state generation, and Zhong et al. (2020, DOI 10.1126/science.abe8770) show that a 100-mode, ultralow-loss interferometer is the enabling element of photonic computational advantage. At the component level, Wang et al. (2018, DOI 10.1038/s41586-018-0551-y) report thin-film lithium niobate (LN) modulators with a complementary metal-oxide-semiconductor (CMOS) compatible drive and on-chip loss below 0.5 dB, and name feed-forward photonic quantum computation as a target use. Zhu et al. (2021, DOI 10.1364/AOP.411024) survey the LN platform and list its open challenges. Nevzorov et al. (2027, DOI 10.1016/j.mssp.2026.111196) compare five phase-change alloys as non-volatile switching cells in silicon-nitride waveguides by settling time and transmission contrast. Preskill (2018, DOI 10.22331/q-2018-08-06-79) and Kjaergaard et al. (2020, DOI 10.1146/annurev-conmatphys-031119-050605) frame the broader constraint: noise limits how deep a circuit can be before error correction takes over.

## Related work table

| Paper | Year | Role | What it does | What it does NOT cover |
|---|---|---|---|---|
| Wang et al., integrated photonic quantum technologies (10.1038/s41566-019-0532-1) | 2020 | review | Surveys integrated photonic quantum devices up to about 1,000 components | No rule for sizing or shaping a switch network under a per-switch loss |
| Zhong et al., quantum computational advantage using photons (10.1126/science.abe8770) | 2020 | landmark | Gaussian boson sampling with 50 squeezed states in a 100-mode low-loss interferometer | Loss enters as a fidelity concern, not as a design variable of a source-multiplexing network |
| Wang et al., LN modulators at CMOS voltages (10.1038/s41586-018-0551-y) | 2018 | landmark | Gives an on-chip loss figure (below 0.5 dB) for a fast switch element | Does not say how many such elements a network can afford |
| Zhu et al., photonics on thin-film LN (10.1364/AOP.411024) | 2021 | review | Maps the LN device toolbox and open challenges | No system-level loss budget |
| Preskill, Noisy Intermediate-Scale Quantum (NISQ) era (10.22331/q-2018-08-06-79) | 2018 | landmark | Argues gate noise limits circuit size | Silent on photonic loss budgets |
| Cerezo et al., variational quantum algorithms (10.1038/s42254-021-00348-9) | 2021 | landmark | Trainability and efficiency limits of variational methods | Not photonic; no hardware-loss model |
| Kjaergaard et al., superconducting qubits (10.1146/annurev-conmatphys-031119-050605) | 2020 | review | State of play for a competing modality | No photonic network analysis |
| Nevzorov et al., GeTe-Sb2Te3 switching cells (10.1016/j.mssp.2026.111196) | 2027 | adjacent | Measures settling time and contrast of non-volatile photonic cells | Does not connect cell properties to network design |
| Pachuau et al., Flexible Representation of Quantum Images (FRQI) and Novel Enhanced Quantum Representation (NEQR) circuits (10.1007/978-3-032-28478-5_36) | 2027 | adjacent | Exposes a resource trade-off (measurements versus circuit depth) | Different problem; shows only that such trade-offs must be quantified |
| Abdiwi et al., topological-spintronic qubits (10.1007/978-3-032-39708-9_30) | 2027 | recent | Reports coherence and fidelity gains for a hybrid device | Not photonic; no architecture-level model |
| Wang et al., band-folded quasi-bound states (10.1016/j.optcom.2026.133845) | 2027 | recent | Resonant grating for sensing | Component physics only |

## The gap

The recent and landmark papers supply per-component numbers (loss in dB, settling time, contrast) and system scale (tens of modes, about a thousand components), and the reviews list material and integration challenges. None of them turns a per-switch loss into an architecture decision. A concrete instance is the heralded-source multiplexer: N probabilistic photon sources feed a tree of 2x2 switches, and every photon pays the loss of every switch on its path. A deeper network raises the chance that some source heralded, yet taxes every photon. Common designs (a balanced tree, a cascade) are fixed in advance and are not derived from the loss figure. Sources with thermal pair statistics add a second cost: brighter sources herald more often but also emit multiple photons, which hurts when the goal is exactly one photon.

## Hypotheses and success metric

Setting: thermal heralded sources with a threshold detector, perfect switching logic, per-switch loss between 0.01 and 1 dB (the upper range brackets the 0.5 dB figure of Wang et al., 2018). Metric: the probability P1 that exactly one photon leaves the network. The regime and thresholds below were set after a short pilot run in which the exact solver was checked against direct evaluation; the experiments then ran with these thresholds fixed.

- **H1 (shape).** At 0.3 dB per switch and N = 32 sources, the loss-optimal unbalanced tree improves P1 over the best balanced tree by at least 3 percent (relative), with brightness tuned separately for each topology. Falsified if the gain is below 3 percent.
- **H2 (scaling).** The best achievable infidelity 1 - P1, optimised over N and brightness, grows sublinearly with per-switch loss, with a fitted log-log slope below 1.
- **H3 (baseline).** A generic stochastic shape search with 3,000 evaluations falls at least 1 percent short of the exact optimum at N = 64. Falsified if it matches the exact optimum within 1 percent.
- **H4 (robustness).** A design made for the wrong loss value still beats a matched balanced design in most design/operation pairs.

## Novelty

An exact dynamic program returns the loss-optimal, generally unbalanced, priority-ordered switch-tree shape for thermal heralded-source multiplexing, and this study uses it to measure how the best achievable single-photon probability scales with per-switch loss and how fragile a design is to a wrong loss assumption.

## Scale and honesty note

Everything is an exact or Monte Carlo (MC) calculation on a single laptop central processing unit (CPU); no hardware data is used and no quantum advantage is claimed. The balanced-tree and cascade topologies are common design conventions, not taken from a paper in the supplied literature, and are therefore not cited.
