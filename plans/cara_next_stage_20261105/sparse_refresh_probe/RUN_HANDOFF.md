# Sparse refresh probe R1 — confirmed b/c scope, hard1.05

Read PREREGISTRATION.md and quote.json. User approval recorded there: remove the raw S2 arm, keep b/c on O1/O3/N1/N3, hard1.05GPUh, and run only if the exact quote and an idle card pass. S1 still compares sync/raw locally. **Center and upper now fit1.05. Complete the collector/production CPU entry before fresh admission and launch.** No routines.

Local reproducible preparation:

```sh
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/prepare.py
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/cpu_check.py
PYTHONPATH=src:tests .venv/bin/python -m unittest test_cara_f19_speed190_sampling_r1
```

**Confirmed:** sparse sync now writes the same-age uncond residual and synthetic A anchor, with DD-only probe/residual differences. It does not train uncond regression on synthetic P observations; the next real D restores its real-DD predecessor. Original F19 defaults and shared request/runner/ops code are untouched. Ten full36 CPU paths include actual A30/A33 anchor-read controls; P14/P20 fixtures remain.

The confirmed callable `wcomr.cara_sparse_refresh_probe_r1.s1_gate` admits S2 only at median P/D<=0.5 AND amplitude kappa<0.45. Manifest records its entry and formula; postprocessing recomputes it from raw measurements. Read PREREGISTRATION.md for same-state no-P C control and frozen-drift requirements. CPU fixtures check both thresholds. The GPU collector/ops stage is still unprepared; no deployed-job acceptance is claimed.

Selected quote: S2=8 videos,1568.173296s; one S1 prefix makes9 parent/video requests total. S1=540s plus600s load+600s release, P upper bound0.5D. Center**0.962497396GPUh**, range**[0.875376657333,1.006057765333]GPUh**. Decimal range seconds[3151.3559664,3621.8079552], upper is below3780 by**158.1920448s**. All existing allowances remain unchanged. Alternative quote file and CLI options are removed. No raw endpoint LPIPS contrast/closure criterion remains; postprocessing only reports b/c, with raw limited to S1.

Only a passing quote may proceed to collector/ops integration and affected-path Linux CPU acceptance, then live read-only confirm10 UUID/capacity checks and selection of the other idle UUID. Guardian50GiB/90C/4GiB, mainline priority, old16.5, launch-only1.05 reservation and one terminal settlement remain unchanged. No GPU UUID, launch_id, ledger seq or actual times exist until fresh admission and one dispatch succeed. Future halfway target would be4/8 S2 videos after S1, scheduled externally. Reports would go to reports/cara_sparse_refresh_probe_r1_20261105/; no GPU result or routine is created.
