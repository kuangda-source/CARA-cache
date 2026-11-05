# Sparse refresh probe R1 — blocked before launch

Read PREREGISTRATION.md and quote.json. Full requested scope center1.208701193, range[1.076816127,1.274643725], hard1.0GPUh. Even S2 with zero S1 exceeds the limit at center/upper. **Do not prepare, admit, reserve, or dispatch this manifest.** No launch_id, GPU binding, first request, times, ETA, reservation sequence, active status command, or settlement exists.

Local reproducible preparation:

```sh
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/prepare.py
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/cpu_check.py
PYTHONPATH=src:tests .venv/bin/python -m unittest test_cara_f19_speed190_sampling_r1
```

Implemented: SpeedOwner/SpeedReadout extension points with historical F19 defaults; opt-in SparseOwner sync/raw age<=6 and birth receipts; LayerReuse P14/P20; loaded-request routing for sparse_policy; fixed masks/inputs/reused R18C rows and Native references; future released-CPU score/analyze entry in postprocess.py. No baseline generation, rescoring, or source/window synchronization beyond the registered residual-cache write.

Because the quote gate refuses the job, no S1 GPU collector or ops launch stage is created. The S1 collection/gate procedure is frozen in PREREGISTRATION.md and manifest.json, not claimed runnable. A future admissible task must finish that affected-path integration and Linux production CPU acceptance before any dispatch. It cannot directly launch this blocked manifest. No change to the1.0 hard limit or12-video scope has been requested or assumed.

Lifecycle reference only: plans/cara_next_stage_20261104/sensitivity/ops.py {launch,status,capture,settle}, --route relay. Its historical default UUID must never substitute for the actual idle UUID. Preserve50GiB/90C/4GiB gates,600s release margin, mainline confirm10 priority, old16.5 reserve, and one reservation/one terminal actual settlement. No central-ledger command was run in this task. Saved AVSLC seq102 is historical evidence, not a fresh ledger or capacity check.

If an admissible run is later registered, use exactly one card session and in-job S1 cost gate before the12 S2 requests. Halfway expects6/12 S2 videos after S1, subject to actual timing; terminal handles gate-fail partial scope honestly. Check scheduling is external. No routine, cron, automation, or monitor is created. Reports would go to reports/cara_sparse_refresh_probe_r1_20261105/; there are no GPU result files now.
