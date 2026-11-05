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

## Source-only deployment accepted

At **2026-11-05T23:31:42.133291+08:00**, source/runtime hashes, CPU proof and private storage all passed. Deployed source revision **0eff7bbd981895b073e6fb0f95ca0a617bbf1572**; scope **c3b5f2dd12163d90379c1f7d0831f289cad06f943468d1e90471fa5f45feff1f**; registration SHA256 **0a2fb7d143f8b6d6502e726fa323cee065b1a9cdac2da377384befa2257abd87**. Stage has1512 registered base/overlay files. `reports/cara_sparse_refresh_probe_r1_20261105/deployment.json` is the final receipt.

Linux production CPU R2 exited0 with OOMKilled=false, Torch2.7.1+cu128, CUDA_initialized=false and no GPU device requests. It imported the real production entry and completed the10 sampler checks plus real pinned tiny28-block S1/gate/S2 paths. The first CPU attempt exited1 after the sampling fixtures because ops eagerly imported a Mac-only SSH module; that import is now deferred to actual local RPC calls. Original failure is retained in linux_cpu_r1.json and the stopped CPU container ending-cpu-failed-r1; source correction and R2 are in source_prepare_r2.json/cpu_launch_r2.json/linux_cpu.json. These are CPU verification attempts, not GPU probe executions.

Private16GiB loop57 output mount and48MiB journal are ready;4GiB output low-water is unchanged. GPU-authorization/intent/launch/dispatch, central-reservation, guardian, supervisor and billing files are all absent. The documented status command was executed successfully and reports production_CPU_passed=true, storage_prepared=true, GPU_launch_exists=false. Both GPUs had no compute processes at the final observation; confirm10's original container was no longer running. That observation is not launch permission in this ZERO-GPU preparation: use the documented command later for a fresh admission, retaining50GiB and all existing gates.

The central ledger SHA256 was identical before/after preparation: **427919c992f43a40f50174705e12467a56e1eed06ab458b6d39ccdb1c31216c6**; used231.1691439833172GPUh, reserved20.6GPUh, events103, probe job absent. No reservation/settlement or GPU process was started by this task. No routine or automatic launch is installed.
