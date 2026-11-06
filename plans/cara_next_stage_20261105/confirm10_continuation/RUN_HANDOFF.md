# confirm10 continuation handoff

run_id `cara-generator-v1-confirm10-continuation-r1-20261106`。25 formal、0 warm，硬限 **2.2 GPUh**，中心 **2.0062773472222224 GPUh**，请求和 **5475.0895** 秒。`authority.user_quote` 是启动原话；`execution_authorized=true`、`ledger_reservation_authorized=true`、`sync_launch_authorized=true`；`this_commit_dispatches=false`。`quote.json` 同样是 `execution_authorized=true`、`GPU_dispatch_ready=true`。准备阶段「只做 CPU、不上卡」留在 `preparation_authority`。本 handoff 仍不自己启动、不联网、不碰账本。scope_sha256 `fbe474f85fbd775d3d0514468cde33a76d4749b8672abbb8b45ac6445c77153d`，随这次 authority/preference 重算；25 请求、报价和原 21 份 hash 不变。

`payload()` 把 `authority.user_quote` 和 `gpu_uuid` 写入授权。reserve 仍核对 `execution_authorized`、`billed_limit_GPUh==2.2` 和 `forecast_GPUh==2.0062773472222224`。

## 空闲 A6000

用户允许任意一张空闲 A6000。manifest 核实：`gpu_uuid` 是优先卡 `GPU-cebf7119-cf03-23b9-e192-cd196332b704`。`gpu_preference` 依次是这张和 `GPU-de9a5370-cd87-0f1c-a48e-288888777dd3`。原卡忙时，另一张只要自己的 fresh 门全过就可以用 `--gpu-uuid` 指定。占用中的卡不抢。其他 UUID 等于无卡：不启动、不预留。

ops 只在启动时解析一次 UUID，再把同一个值放进 Linux admit 的 `gpu_uuid`、`launch_host` 的 `selected_gpu(GPU)` 和 `payload` 的 `gpu_uuid`。门限不降低：Default、无 compute pid、显存 ≤1024MiB、utilization 0、`temperature_C<90`、MemAvailable ≥50GiB，以及该 UUID 的 `gpu-locks/<uuid>.lock` 与 `.mode-owner.lock` 空闲。省略 `--gpu-uuid` 时用 `gpu_uuid` 这张优先卡。

reserve/dispatch 前还要过 Linux CPU proof、source hash、asset、storage，以及 `verify-inherited` 核对原 21 份输出。都通过后才按中心 2.0062773472222224、硬限 2.2 唯一预留并 dispatch 一次。不探四卡，不改别人的进程。90°C 自动停、50GiB 和 4GiB 低水位都不降低。容器内存仍是 40g。新的 16GiB 私有输出卷只给本 run；原 confirm10 的 loop 和 collection 只读，不重写。

先在能读到原 21 份文件的现场做只读 hash 核对，通过后才允许预留：

```sh
PY=worldcache_omr/.venv/bin/python
M=worldcache_omr/plans/cara_next_stage_20261105/confirm10_continuation/manifest.json
"$PY" worldcache_omr/plans/cara_next_stage_20261105/confirm10_continuation/postprocess.py verify-inherited --manifest "$M"
```

核对要求 CONFIRM10_001–021 的 latent 与 video 字节和 sha256 与 manifest 一致，且原结算仍是 launch `fe91fe0468944be18b8c0950c33e092b`、actual `1.3313886947699616` GPUh。C05 的 022–026 不在核对通过后的执行矩阵里。hash 不符就停止，不预留。

通过后，执行会话才按 sensitivity ops 使用本 manifest：预检、Linux CPU、新存储、fresh admit、唯一预留 `CONFIRM10_CONTINUATION_WHOLE2_2_RESERVE` 共 2.2 GPUh、一次 dispatch。源必须先提交。不要复用原 4.1 预留，也不要改原 collection/settlement/manifest。k18 和 P 探针都不在本命令序列里。

## 终态后的 status / capture / settle / LPIPS / analyze

半程和终态由执行会话人工查看，不建 heartbeat、cron 或持续监控。收尾只在终态做：

```sh
PY=worldcache_omr/.venv/bin/python
P=worldcache_omr/plans/cara_next_stage_20261104/sensitivity
M=worldcache_omr/plans/cara_next_stage_20261105/confirm10_continuation/manifest.json
"$PY" "$P/ops.py" status --manifest "$M" --route relay --receipt /tmp/cara_confirm10_continuation_status.json
"$PY" "$P/ops.py" capture --manifest "$M" --route relay --receipt /tmp/cara_confirm10_continuation_terminal.json
"$PY" - <<'PY_SETTLE'
import json
from pathlib import Path
c=json.loads(Path('/tmp/cara_confirm10_continuation_terminal.json').read_text())
Path('/tmp/cara_confirm10_continuation_settle_input.json').write_text(json.dumps(dict(capture=c,launch_sha256=c['files']['launch']['sha256'])))
PY_SETTLE
"$PY" "$P/ops.py" settle --manifest "$M" --route relay --input /tmp/cara_confirm10_continuation_settle_input.json --receipt /tmp/cara_confirm10_continuation_settlement.json
```

唯一结算包含失败费用。只有 25/25 完成、原 21 份 hash 仍可复用、GPU/CPU 已释放、Default 已恢复且本 run 唯一结算后，才评分一次。评分容器按 manifest 的 `inherited_outputs.output_root` 只读挂载原输出。C01–C04 的 16 对沿用已保存分数；新的 20 对才调用 LPIPS。

```sh
"$PY" - <<'PY_SCORE'
import json
from pathlib import Path
c=json.loads(Path('/tmp/cara_confirm10_continuation_terminal.json').read_text())
s=json.loads(Path('/tmp/cara_confirm10_continuation_settlement.json').read_text())
Path('/tmp/cara_confirm10_continuation_score_input.json').write_text(json.dumps(dict(capture=c,settlement=s)))
PY_SCORE
"$PY" "$P/postrun.py" score --manifest "$M" --route relay --input /tmp/cara_confirm10_continuation_score_input.json --receipt /tmp/cara_confirm10_continuation_score_launch.json
"$PY" "$P/postrun.py" analyze --manifest "$M" --route relay --receipt /tmp/cara_confirm10_continuation_analysis.json
```

分析分母是九输入、36 对。C05 不进入分母。在 36 对齐全之前，结果状态保持 NOT_RUN，不把部分结果写成主终点成功。k18 等这次续跑完成、结算并释放后再单独开卡。


## Unique GPU launch — actual execution

User's existing approval above was executed once. Run `cara-generator-v1-confirm10-continuation-r1-20261106`, launch `e6d9ad460313484caa8f10a9b842e387`; selected A6000 `GPU-cebf7119-cf03-23b9-e192-cd196332b704`. Frozen source `4a8eb2aa5cc9a9cfc26147928cb36b1755bd8a38`, scope `fbe474f85fbd775d3d0514468cde33a76d4749b8672abbb8b45ac6445c77153d`. `verify-inherited` used the exact read-only artifact verifier on the server: 21 outputs/42 latent+video files match, with the original settlement and 16 inherited scores checked locally; no inherited LPIPS was recalculated. Linux production CPU exited0 with50 tiny requests andCUDA=false. Route `two_card_relay` throughout; no P/k18 execution or source deployment.

Actual guardian/bill start **2026-11-06T11:57:26+08:00**; Docker StartedAt `2026-11-06T03:57:28.024404569Z`. Center2.0062773472222224GPUh, range1.7021057083333335–2.1583631666666667GPUh; hard2.2GPUh. Estimated wall2h00m22.598s, ETA **2026-11-06T13:57:49+08:00**. Stop-new-work **2026-11-06T13:59:26+08:00**, hard-stop **2026-11-06T14:09:26+08:00**. Optional manual halfway estimate **2026-11-06T12:58:18+08:00** at13/25; no scheduled check or monitor was created. These ETAs are estimates; hard deadlines come from the actual guardian start.

Central reservation **seq107**, event`CONFIRM10_CONTINUATION_WHOLE2_2_RESERVE`,2.2GPUh exactly once. After reserve: cumulative used **232.6049995725559**, reserved **18.7** =old16.5+this2.2. Legacy cap250/available`-1.3049995725558965` are compatibility fields under the no-cumulative-cap policy. Original confirm10 is alreadySETTLED and unchanged; this run remains RESERVED_OR_RUNNING and is not yet settled.

Fresh admission: MemAvailable53.182117GiB; selectedGPU Default/no compute/24MiB/45C. New private16GiB ext4 `/dev/loop58`, image`generator-v1-confirm10-continuation-r1/output.ext4`; output mount`/media/minchen/4def5c03-8324-4cba-ac0b-9fda7c79dc7b/gkd/cara_cal66_sm86_workspace/outputs/cara-generator-v1-confirm10-continuation-r1-20261106`. Container Memory/MemorySwap `42949672960`/`42949672960` bytes. Gates50GiB/90C/4GiB are unchanged. Original output volume is mounted read-only for inheritance, not rewritten.

One start confirmation: Running=True, OOMKilled=False; collection 尚未生成，首条 CONFIRM10_027 的 RUNNING 未在本次检查中取得；日志已到 Inference 保存 config，GPU runner 占用显存；original handles: guardian PID 1530999/start_ticks 723234950, container_cli PID 1531029/start_ticks 723235117, supervisor PID 1531086/start_ticks 723235159, runner PID 1531132/start_ticks 723235284. Liveness evidence and GPU compute process/VRAM are in`start_confirmation.json`. Confirmation ends here; no continuous monitoring.

Read-only status from the project root:

```sh
worldcache_omr/.venv/bin/python worldcache_omr/plans/cara_next_stage_20261104/sensitivity/ops.py status --manifest worldcache_omr/plans/cara_next_stage_20261105/confirm10_continuation/manifest.json --gpu-uuid GPU-cebf7119-cf03-23b9-e192-cd196332b704 --route relay --receipt /tmp/cara_confirm10_continuation_status_$(date +%s).json
```

The terminal capture→settle input→unique settle→CPU score→analyze templates above still bind this manifest. Financial response loss must recover the same transaction. Score only after25/25 and full release/settlement; reuse16 scores and compute only20 new pairs, then report the nine-input/36-pair endpoint. All receipts from this launch are under`reports/cara_generator_v1_confirm10_continuation_r1_20261106/`.

Terminal CPU wiring note: the frozen GPU payload contains the inherited identities in the manifest, but not the original `central_settlement.json` and `partial_scores.json` files read by `require_original_settlement`/`require_inherited_scores`. Also the shared `postrun.py` score operator currently expects `native_references` for every custom scorer, while this manifest gets fresh Native references from its collection. Before terminal CPU scoring, minimally bind the two unchanged receipts into a separate CPU scoring context and adapt that operator's Native mounting for this manifest. Do not redeploy or change the running GPU stage. No scorer was launched in this session.


## Takeover terminal closeout — 2026-11-06

The existing continuation ended at 12:21:57 Asia/Shanghai after 5/25 complete. `CONFIRM10_032` (C07 / F17_A2_LIGHT_C) returned VIDEO_REJECTED after 36 updates; 19 requests were not reached. No retry or replacement was performed. Guardian actual0.4086062377411872GPUh uniquely settled by seq108; original processes and GPU/locks released, Default restored, central pending cleared. Old16.5 liability is unchanged. All42 inherited and10 new accepted artifact hashes match. The nine-input/36-pair endpoint is NOT_EVALUABLE; full score/analyze was not invoked because25/25 and successful-exit gates are false. k18 remains paused. See [takeover report](../../../reports/cara_generator_v1_confirm10_continuation_r1_20261106/takeover_closeout/REPORT.md) and its original receipts. No new run is authorized by this closeout.
