# Sparse refresh probe R1 — S1 gate-stop completed and settled

The original session completed S1, failed both frozen gate conditions and exited0 without S2. Its unique terminal capture and actual settlement are complete (seq106,0.10446689446870651GPUh). Do not repeat launch, deploy, CPU, provision, reservation, capture or settlement. See reports/cara_sparse_refresh_probe_r1_20261105/report.md and analysis.json for accepted facts. No routine was created. Design is fixed at b/c x O1/O3/N1/N3, S1 local raw/sync, same-age synthetic A anchor, and dual gate P/D<=0.5 AND amplitude kappa<0.45. Hard1.05GPUh; quote center0.962497396, range[0.875376657333,1.006057765333].

From the CARA-cache repository root, the **original launch command (already executed; do not replay)** was:

```sh
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/ops.py launch --route relay --gpu-uuid GPU-de9a5370-cd87-0f1c-a48e-288888777dd3
```

It performs a fresh read-only GPU/confirm10/host-memory precheck, prefers that UUID if admissible and otherwise selects another idle UUID excluding active/claiming confirm10. MemAvailable must be>=50GiB, selected GPU idle/no compute process/<=1024MiB/Default/<90C; then the existing fresh source/assets/CPU/storage/owner-lock admission runs. Disk low-water4GiB and all existing guardian gates are unchanged. Only after admission does it reserve1.05GPUh in the shared ledger and dispatch exactly once. The authorization records the user's approved design/limit. An existing intent/launch is recovered by status/capture, never replayed.

The **read-only status command** is:

```sh
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/ops.py status --route relay
```

Remote project R=/data20t/gaokuangda/worldcache_workspace; stage S=$R/.sync/cara-budget-calibration-GPU-sparse-refresh-probe-r1-20261105; output O=$R/outputs/cara-sparse-refresh-probe-r1-20261105. Private16GiB output and48MiB journal belong only to this probe. Source deployment/CPU/storage receipts are under reports/cara_sparse_refresh_probe_r1_20261105/. No confirm10 file/container/stage is edited.

The single session runs S1 once:28 parent steps,20 local29 evaluations, next30 raw/sync/no-P comparisons, no video. It writes O/s1.json. Gate failure writes S1_GATE_STOP with8 NOT_REACHED S2 rows, exits0 and releases normally; no S2. Gate pass runs8 b/c videos in the existing full-request routes and writes O/collection.json. Halfway means S1 complete plus4/8 S2. No extra checkpoints, automatic retries, heartbeat, scheduler or cron. Original actual-start timings and reservation sequence are recorded below. Guardian hard limit3780s and stop-new-work/release margin600s remain unchanged.

The original terminal `capture` and exactly one `settle` completed using the same lifecycle. The following capture command is historical and must not be repeated:

```sh
.venv/bin/python plans/cara_next_stage_20261105/sparse_refresh_probe/ops.py capture --route relay --receipt reports/cara_sparse_refresh_probe_r1_20261105/terminal_capture.json
```

The completed settlement used the lifecycle envelope `{capture: <terminal capture>, launch_sha256: <original launch SHA>}` with `ops.py settle --input <file> --route relay --receipt <new receipt>`. It settled actual wall cost on S1 gate stop and preserved old16.5. Only a complete8-video S2 collection is eligible for the postrelease CPU LPIPS scorer. It reuses Native/R18C unchanged. The original settlement is now saved as reports/cara_sparse_refresh_probe_r1_20261105/settlement.json and mirrored to S/central-settlement.json; never settle again. The canonical settlement input was {capture: terminal_capture.json content, launch_sha256: ddcbcf72262217d2cb30af33e902156e79368378c76472bc226d3f2599598956}. LPIPS was skipped because S2 completed0/8.

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


## Original GPU launch — 2026-11-06 Asia/Shanghai

Direct user approval: 「P 探针硬限放到 1.05 GPUh，设计不动，空闲卡上跑」. Run `cara-sparse-refresh-probe-r1-20261105`, launch `4fbe2d7463614c2e9fc40cca8ab34bf1`, GPU `GPU-de9a5370-cd87-0f1c-a48e-288888777dd3`; source remains `0eff7bbd981895b073e6fb0f95ca0a617bbf1572`. `reports/cara_sparse_refresh_probe_r1_20261105/launch.json` preserves the original fresh admission, central transaction and one dispatch. `startup.json` binds the original GPU context/handles and schedule.

Fresh read-only precheck found confirm10 running=false/claiming=false and no compute processes on either GPU. Final admission MemAvailable **53.612747 GiB**, selected GPU Default/idle/350 MiB/41C, private output free **16,713,109,504 bytes**; production CPU/source/assets/runtime/storage and both owner locks passed. Gates50GiB/90C/4GiB are unchanged. Central ledger **seq105**, exact **1.05 GPUh** reserve; total reserved17.55 including old16.5. All previous jobs were unchanged by this transaction. No confirm10 settlement or file/container/stage mutation was performed.

| Timing (Asia/Shanghai, 2026-11-06) | Original session |
|---|---|
| Guardian actual start | 01:30:58.276 |
| Whole-session ETA center | 02:28:43.267 |
| Quote ETA range | 02:23:29.632–02:31:20.084 |
| Stop new work / release begins (start+3180s) | 02:23:58.276 |
| Hard wall deadline (start+3780s) | 02:33:58.276 |

Original guardian1441006, container CLI1441035, supervisor1441097, runner1441139 (PID/start-ticks in startup.json). Sole-runner CUDA context was granted at01:31:08.322. The first S1 O1 prefix request began at01:32:51; prompt guardrail passed at01:33:12 and the first denoising step was observed by01:33:51. At that startup observation, S1 completion and the scientific gate were pending; the terminal acceptance below supersedes that observation. Halfway is **S1 done +4/8 S2** (5/9 parent/video requests), conditional on the frozen S1 gate passing. S1 gate stop is a terminal outcome and skips S2. The above ETA includes quoted load/release allowances and is not a measured completion guarantee. No monitoring routine, retry or extra GPU submission is installed.


## Terminal acceptance — 2026-11-06

Original run/launch/GPU identities are unchanged. S1_COMPLETE; S1_GATE_STOP; S2 all8 NOT_REACHED. P/D=0.5013310384683857 fails<=0.5; amplitude kappa=0.6362258732588199 fails<0.45. Overall NO_GO_S1_GATE; b/c endpoint Go criteria are unevaluated. P_k locally closed by k20 MSE/C=1.496923838069763>0.5. No LPIPS or endpoint claim.

Original guardian wall376.08082008734345s (01:30:58.276–01:37:14.357 Asia/Shanghai); container exited0, no OOM, all original processes ended, GPU released/Default restored/locks free. One capture and one settle accepted. Ledger seq105 reservation1.05GPUh -> seq106 SETTLED actual0.10446689446870651GPUh. Cumulative used232.6049995725559GPUh; remaining reserved16.5GPUh, old responsibility untouched. Other ledger jobs were unchanged. Remote S/central-settlement.json holds the exact unique receipt so status reports settlement rather than pending. No source redeployment or new GPU process occurred. Do not resume, re-reserve, score S2, or settle this original again. Evidence and the S1-only decision are in reports/cara_sparse_refresh_probe_r1_20261105/report.md, analysis.json, terminal_capture.json and settlement.json.
