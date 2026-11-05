# Sparse refresh probe R1 — source-only deployment; future single launch

Current preparation is ZERO GPU: no launch, ledger reservation, or routine. Design is fixed at b/c x O1/O3/N1/N3, S1 local raw/sync, same-age synthetic A anchor, and dual gate P/D<=0.5 AND amplitude kappa<0.45. Hard1.05GPUh; quote center0.962497396, range[0.875376657333,1.006057765333].

From the CARA-cache repository root, the **later launch command** is:

```sh
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/ops.py launch --route relay --gpu-uuid GPU-de9a5370-cd87-0f1c-a48e-288888777dd3
```

It performs a fresh read-only GPU/confirm10/host-memory precheck, prefers that UUID if admissible and otherwise selects another idle UUID excluding active/claiming confirm10. MemAvailable must be>=50GiB, selected GPU idle/no compute process/<=1024MiB/Default/<90C; then the existing fresh source/assets/CPU/storage/owner-lock admission runs. Disk low-water4GiB and all existing guardian gates are unchanged. Only after admission does it reserve1.05GPUh in the shared ledger and dispatch exactly once. The authorization records the user's approved design/limit. An existing intent/launch is recovered by status/capture, never replayed.

The **read-only status command** is:

```sh
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/ops.py status --route relay
```

Remote project R=/data20t/gaokuangda/worldcache_workspace; stage S=$R/.sync/cara-budget-calibration-GPU-sparse-refresh-probe-r1-20261105; output O=$R/outputs/cara-sparse-refresh-probe-r1-20261105. Private16GiB output and48MiB journal belong only to this probe. Source deployment/CPU/storage receipts are under reports/cara_sparse_refresh_probe_r1_20261105/. No confirm10 file/container/stage is edited.

The single session runs S1 once:28 parent steps,20 local29 evaluations, next30 raw/sync/no-P comparisons, no video. It writes O/s1.json. Gate failure writes S1_GATE_STOP with8 NOT_REACHED S2 rows, exits0 and releases normally; no S2. Gate pass runs8 b/c videos in the existing full-request routes and writes O/collection.json. Halfway means S1 complete plus4/8 S2. No extra checkpoints, automatic retries, heartbeat, scheduler or cron. Actual start/ETA/deadlines and reservation seq do not exist until the future command succeeds. Guardian hard limit3780s and stop-new-work/release margin600s remain unchanged.

One future terminal `capture`, then exactly one `settle` use the same lifecycle. Example capture (read-only):

```sh
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/ops.py capture --route relay --receipt /tmp/cara_sparse_terminal.json
```

The settlement input is the existing lifecycle envelope `{capture: <terminal capture>, launch_sha256: <original launch SHA>}`; pass it to `ops.py settle --input <file> --route relay --receipt <new receipt>`. Settle actual wall cost even on S1 gate stop; preserve old16.5. Only a complete8-video S2 collection is eligible for the postrelease CPU LPIPS scorer. It reuses Native/R18C unchanged. No settlement is performed by this source-only preparation.

Local checks:

```sh
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/cpu_check.py
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/runtime_cpu.py
PYTHONPATH=src:tests .venv/bin/python -m unittest test_cara_f19_speed190_sampling_r1
```

## Fresh admission observation — not launched

Read-only relay precheck at **2026-11-05T22:36:00.092395+08:00**: confirm10 launch `fe91fe0468944be18b8c0950c33e092b` targets `GPU-cebf7119-cf03-23b9-e192-cd196332b704`; nvidia-smi shows its active runner1353553 on that UUID. The other GPU `GPU-de9a5370-cd87-0f1c-a48e-288888777dd3` is idle (no compute process,346MiB,0% utilization,Default,41C).

**Host-memory admission fails:** MemAvailable=30367076KiB (**28.960300GiB**) <50GiB. Source receipt: `reports/cara_sparse_refresh_probe_r1_20261105/precheck.json`. The50GiB gate is unchanged. Quote center0.962497396/range[0.875376657333,1.006057765333] does fit hard1.05; this is a resource refusal, not a quote refusal.

No ledger read/reservation/settlement, remote source stage, CPU container, storage provisioning, GPU mode change, or dispatch was performed for this probe. No launch_id, start/ETA/deadlines, ledger sequence or active status command exists. This was the earlier admission refusal before the source-only deployment. No polling loop, routine or automatic retry is installed. A later launch requires a passing production CPU proof and a fresh live resource check, while preserving confirm10 priority.
