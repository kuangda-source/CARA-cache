# confirm10 continuation handoff

run_id `cara-generator-v1-confirm10-continuation-r1-20261106`。scope_sha256 `4a1a7ed73478e166f72d62b27b1faf8b49c09737702f19f64cf2c67aa100b100`。25 formal、0 warm，硬限 **2.2 GPUh**，中心 **2.0062773472222224 GPUh**，请求和 **5475.0895** 秒。`GPU_dispatch_ready=false`，`execution_authorized=false`。本 handoff 所在提交只完成预注册和纯 CPU 验收，不上卡、不碰账本、不连接远端。

用户已说精确重报后可在空闲卡上续跑，硬限按这次重报。那是下一次执行会话的事，而且必须 fresh。本准备不把该句当成已经放行的启动。

## 启动前必须 fresh

只使用一张空闲 A6000。优先原卡 `GPU-cebf7119-cf03-23b9-e192-cd196332b704`；该卡不是 Default、已有 compute app，或别人在跑，就不上。不占另一张卡，不探四卡，不改别人的进程。host available 必须 ≥50GiB，选中 GPU 温度必须 ≤90°C，输出磁盘必须 ≥4GiB。90°C 自动停、50GiB 和 4GiB 低水位都不降低。容器内存仍是 40g。新的 16GiB 私有输出卷只给本 run；原 confirm10 的 loop 和 collection 只读，不重写。

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
