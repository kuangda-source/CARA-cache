# Native sensitivity8 / F17 confirm4: prepared, NOT launched

**本次启动被宿主内存准入阻止。未预留中央 ledger、未启动 GPU、没有首批请求或运行完成证据。**
最终状态时间：2026-11-04T03:23:41.350092+08:00。MemAvailable=49.651203GiB，低于原 CAL35 延用的50GiB准入门；此前两次 admit 均在同一内存条件拒绝。
没有降低门槛、清理其它进程/系统缓存、等待循环或创建任何 heartbeat/cron/automation/持续监控。

## 冻结身份与已完成准备

- Run：`cara-native-sensitivity8-confirm4-r1-20261104`。
- 预分配 launch id：`c751f711b5e74daf8552eabe0109afe2`；**不是实际GPU launch**，GPU-launch.json 尚不存在。
- 计划 UUID：`GPU-cebf7119-cf03-23b9-e192-cd196332b704`；启动时间：不适用。
- 科学/执行源码：`44f738feadad1c9e697274d9f69a48192c40518c`，已 push。参数、队列、统计函数与报价保持；scope `d4f2fe3bce614352fca10c734e14775f1e9c999cb4fd92b91959dc1abaf76f65`。
- Stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-calibration-GPU-native-sensitivity8-confirm4-r1-20261104`。采用现有 `cara-budget-calibration-GPU-` 前缀以直接复用原生命周期捕获器；run id 不变。
- 本地原句柄绑定：`.sync/cara-sensitivity-original-binding.json`，包含该原始 launch/source，后续只能恢复，不重做 prepare。
- 源码首次传输响应超时后，已只读恢复原 stage，1501 个注册 payload 文件全部匹配，没有重复准备。
- 本地 CPU dry-run 通过；Linux Torch2.7.1+cu128 两种flow合计286完整请求、28个single-C续跑等价控制通过，CPU容器 exited/0、CUDA未初始化；CPU-proof.json 已保存。
- 原20个模型/资源文件完整内容哈希通过，固定四新输入首次使用身份核查通过（双卡当前/历史输出分别306/114份身份文档，无命中、无读取错误）。
- 独立256GiB输出文件系统和48MiB journal 已实际预留并校验；这是磁盘准备，**不是GPUh预留**。保持原存储与失败证据，不自动重新 provision。
- 结果逻辑路径：`/data20t/gaokuangda/worldcache_workspace/outputs/cara-native-sensitivity8-confirm4-r1-20261104`；实际输出挂载：`/media/minchen/4def5c03-8324-4cba-ac0b-9fda7c79dc7b/gkd/cara_cal66_sm86_workspace/outputs/cara-native-sensitivity8-confirm4-r1-20261104`。两者是同一宿主目录；容器命令显式挂载该实际输出路径。

## 启动前精简

Native/allD 和 FULL_SINGLE_C 不再因 torch.equal 不等中断整卡，row.result.latent_bridge 保存 equal/max_abs_diff；RGB差异也进入报告。预注册按用户指示修订，analyze 输出所有这些控制。
score 去掉重复依赖/权重哈希、latent字节重读校验及末尾计数断言，保留释放/结算和CPU-only约束。
validate_runner_handoff 只验证原进程授权/命令，runner_context_gate 只验证GPU独占上下文；二者均不覆盖payload/runtime内容，所以没有删除那两项源码校验，也没有新增校验。
CAL35 同卡曾有Native/allD全部36步引导张量及终态latent比特复现证据，见874报告；本卡仍报告自身控制差值。

## 最终只读资源状态

CAL35仍SETTLED。中央本卡 job=None；cap=250、used=216.465985065508、reserved=16.500000000000、available=17.034014934492GPUh。
因此“预留后状态”不存在。预算足够，但未通过全部宿主准入。
两张A6000均利用率0、Default，无compute apps；计划卡24MiB/45°C，另一卡311MiB/42°C。
GPU-intent/GPU-dispatch/GPU-launch/guardian-intent均不存在，collection.json不存在。没有实际计费区间，也无需对本卡结算0费用或新增结算事件。

正式报价仍 **9.287657161 GPUh**，单卡硬限9.5：a0.698969381，b旧/新各2.769049671，c1.016971396，预热/控制0.583223967，波动/加载/I/O/退出余量1.450393075。
未启动，所以绝对ETA与中途检查时刻不适用。若以后实际启动T：预计结束T+9小时17分16秒，建议人工中途检查T+4小时38分38秒；新工作停止阈值T+9小时20分，硬限T+9小时30分。都只是工程估计，没有安排任何检查任务。

## 原句柄查看与后续启动边界

从本地仓库执行一次性查看（不建立循环）：

```sh
.venv/bin/python plans/cara_next_stage_20261104/sensitivity/ops.py status --receipt /tmp/cara_sens_status_manual.json
```

日志/原句柄将位于 stage 的 runner.log、host-guardian.log、container-cli.log、guardian.json、supervisor.json、billing.json；原launcher保留自身温度/硬限/独占保护。
本轮到此停止。以后不能盲目执行prepare/dispatch：先恢复该原stage，针对固定身份重新检查GPU、宿主内存≥50GiB、源/资产、锁、盘和ledger；全部通过后才可为这个原launch一次预留9.5，随后唯一dispatch。不得以当前旧快照启动，不增cap、不重派CAL35。
已提交的 ops.py 提供 admit / reserve / dispatch 原操作，reserve输入必须是 `{"admission":<新admit响应>}`，dispatch输入必须含原 envelope 和新中央 snapshot。当前没有这些预留/派发输入。

## 若未来成功启动，完成后的确切命令

以下命令只在原GPU终态后使用，本轮**没有执行**。

1. 捕获释放与原账单：

```sh
.venv/bin/python plans/cara_next_stage_20261104/sensitivity/ops.py capture --receipt /tmp/cara_sens_terminal.json
```

确认status为ORIGINAL_CALIBRATION_LIFECYCLE_CAPTURE，原角色均结束、锁释放、Default恢复；不能把活跃/UNKNOWN当终态。

2. 形成唯一结算输入并结算实际guardian完整墙钟，包括失败费用：

```sh
.venv/bin/python - <<'PY2'
import json
from pathlib import Path
v=json.loads(Path('/tmp/cara_sens_terminal.json').read_text())
assert v['status']=='ORIGINAL_CALIBRATION_LIFECYCLE_CAPTURE'
Path('/tmp/cara_sens_settle_input.json').write_text(json.dumps(dict(capture=v,launch_sha256=v['files']['launch']['sha256'])))
PY2
.venv/bin/python plans/cara_next_stage_20261104/sensitivity/ops.py settle --input /tmp/cara_sens_settle_input.json --receipt /tmp/cara_sens_settlement.json
```

响应丢失只恢复同一原交易，不能新建预留或重复收费。失败分母保留，失败账单照常唯一结算；只有完整成功释放才进入新科学评分。

3. 成功释放/唯一结算后，形成CPU评分输入并调用原stage中的冻结score.py：

```sh
.venv/bin/python - <<'PY2'
import json
from pathlib import Path
v=json.loads(Path('/tmp/cara_sens_terminal.json').read_text())
s=json.loads(Path('/tmp/cara_sens_settlement.json').read_text())
Path('/tmp/cara_sens_score_input.json').write_text(json.dumps(dict(capture=v,settlement=s)))
PY2
.venv/bin/python plans/cara_next_stage_20261104/sensitivity/postrun.py score --input /tmp/cara_sens_score_input.json --receipt /tmp/cara_sens_score_launch.json
```

postrun.py只是本地完成操作入口，不在正在执行的GPU payload中；CPU-only容器2核/8GiB/no-swap，timeout86400，先验证原释放/结算。已有scorer只恢复，不重启。
原CPU评分容器名为stage.name+'-score'；结果在stage/released-score-control/scores.json，完整状态COMPLETE_PENDING_ANALYSIS。

4. 评分完成后运行冻结analyze.py：

```sh
.venv/bin/python plans/cara_next_stage_20261104/sensitivity/postrun.py analyze --receipt /tmp/cara_sens_analysis_operator.json
```

精确模型入口参数已在postrun.py：--manifest <stage>/plans/cara_next_stage_20261104/sensitivity/manifest.json，--collection <output>/collection.json，--scores <stage>/released-score-control/scores.json，--old-scores <原CAL35stage>/released-score-control/scores.json，--root <output>，--output <stage>/released-score-control/complete_analysis.json。旧CAL35只读复用，绝不重评分。
F17按固定1.9×/133秒/LPIPS0.27/原六均值质量门与δ0.027、70排列、单侧p≤0.05非劣检验判定；原理只用旧FIT的s(t)迁移到六非FIT，所有差异与控制均报告，不调参。

## 风险与范围

当前唯一实际阻塞是宿主内存。未来的真实GPU峰值/9小时I/O与温度尚未验收；CAL35曾到88°C，新卡仍按90°C自动停机，硬限与存储保护不放宽。不完整时保留分母和费用，不自动重派。
报价含余量但距T+9小时20分停止新工作阈值约2分44秒，仍是估算。Shared25规划10不是ledger已预留额度，当前卡若将来占用9.5后仅余7.534GPUh，不自动推进其它卡。
本卡遵循CAL35本目录RUN_HANDOFF.md惯例；memory/handoffs/LATEST.md为生成文档，未手改。其它工作流原M/??保持。
