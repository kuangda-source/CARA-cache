# Sampler protocol discrepancy — decision needed

F1 smoke r1 produced one Native video, passed input/output guardrails and format checks, then failed the runner's 70-call assertion. No WC arm started. Supervisor exited with code 1 after 418.42 seconds; all work is charged, cumulative GPU budget 0.183703 h / 4 h. No GPU process remains.

## Evidence

- Paper section 4.1 says 35 denoising steps with Euler scheduling: https://arxiv.org/html/2603.22286v1#S4.SS1
- WorldCache's pinned tree lacks model directories. Our separately disclosed completion from NVIDIA a2c298b0a3df3778b973fe65e9e58877b292d8a7 constructs `FlowUniPCMultistepScheduler`, default solver order 2.
- Selected WorldCache experiment enables `use_kerras_sigma_at_inference=True`.
- `fm_solvers_unipc.py` lines 170–179 creates N+1 positive sigma points for this mode. CPU execution of the exact runtime source confirms requested 35 -> actual 36 timesteps; requested 28 -> actual 29. Ordinary non-Karras mode gives 35 for requested 35, but is still UniPC, not Euler.
- Native log shows a complete 36/36 sampling loop. Exact observed block counts were not saved before the original assertion. Do not retrospectively invent them. The runner now persists pending sample/scheduler/count evidence before assertions; this diagnostic-only change does not change the assertion or sampling.
- WorldCache configures its counter horizon as 2*N, so the current 36-step path would reset caching after call 70 and perform two more calls. Simply changing the assertion to 72 would conceal a meaningful scheduler/cache interaction.
- README and paper also use different WC parameter values: local README profile has threshold .06 and saliency weight 1.0; paper section 4.1 lists .08 and .12. This is a public-code technical profile, not a paper-exact reproduction.

## Concrete choices

1. Recommended practical route: finish all four Native/WC pairs under the public-code default UniPC/Karras behavior, explicitly retaining/logging the 70-call WC horizon and 72 actual calls. Treat this as a technical compatibility/local baseline only. Before method or paper claims, add a separately named 35-step Euler comparison with matched parameters and verified implementation.
2. Paper-protocol-first: implement and separately validate a 35-step Euler adapter with explicit sigma schedule in both arms, then start fresh paired outputs. Paper wording does not uniquely specify its sigma grid; do not silently claim exact authors' reproduction. This needs more reconstruction before another run.

User was asked to choose because changing sampler/horizon affects the scientific baseline. No replacement GPU job launched while the answer is pending. Preserve original plans and the eventual F2/W1 goal.

## User decision — 2026-09-30

User chose to complete the current-code technical comparison first. F1 r2 retains UniPC/Karras (35 requested,36 actual,72 CFG calls) and unchanged official WC counter horizon70. Frozen time grid and scheduler hash are in manifests/f1_runtime_protocol.json; both arms are validated against it. Per-call block execution and WC counter snapshots expose the reset rather than hiding it. Fresh four-scene paired outputs are required because r1 has no complete measured receipt.
