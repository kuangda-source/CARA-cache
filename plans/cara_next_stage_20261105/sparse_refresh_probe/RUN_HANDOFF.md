# Sparse refresh probe R1 — zero-GPU provisional amendment

Read PREREGISTRATION.md, quote.json and quote_options.json. Current instruction: **no GPU jobs, ledger reservation, or routines**. Keep b/b0/c x4 and hard1.0; scope/limit awaits the user. Full scope center1.206218031, range[1.074784449,1.271934821]GPUh. No remote preparation, admission, launch, or settlement exists for this probe.

Local reproducible preparation:

```sh
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/prepare.py
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/cpu_check.py
PYTHONPATH=src:tests .venv/bin/python -m unittest test_cara_f19_speed190_sampling_r1
# Quote-only: prints an option and leaves canonical manifest/quote unchanged.
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/prepare.py --quote-option drop_b0 --hard-gpuh 1.0
```

**Provisional:** sparse sync now writes the same-age uncond residual and synthetic A anchor, with DD-only probe/residual differences. It does not train uncond regression on synthetic P observations; the next real D restores its real-DD predecessor. Original F19 defaults and shared request/runner/ops code are untouched. Ten full36 CPU paths include actual A30/A33 anchor-read controls; P14/P20 fixtures remain.

The provisional callable `wcomr.cara_sparse_refresh_probe_r1.s1_gate` admits S2 only at median P/D<=0.5 AND amplitude kappa<0.45. Manifest records its entry and formula; postprocessing recomputes it from raw measurements. Read PREREGISTRATION.md for same-state no-P C control and frozen-drift requirements. CPU fixtures check both thresholds. The GPU collector/ops stage is still unprepared; no deployed-job acceptance is claimed.

Quote-only alternatives: drop b0 center0.962497396/range[0.875376657,1.006057765]; drop one unspecified input center1.025496856/range[0.926921670,1.074784449]. All options retain S1=0.15 plus600s load+600s release, use P=0.5D, and exceed1.0 at the upper bound. Full scope fits1.3 on quote alone. No alternative, dropped input, or raised limit is selected. Quote-only flags also accept full_3_arms/drop_one_input and a comparison --hard-gpuh without changing canonical files.

Any future separately authorized run still needs affected-path Linux production CPU acceptance and collector/ops integration, fresh idle-UUID/exclusivity admission,50GiB/90C/4GiB gates and mainline priority. Preserve old16.5 and unique reservation/settlement; bind the eventual scope/limit rather than inferring it from these options. Halfway/final scheduling remains external. Reports would go to reports/cara_sparse_refresh_probe_r1_20261105/; no GPU result or routine is created by this amendment.
