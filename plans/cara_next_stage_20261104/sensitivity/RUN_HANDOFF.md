# Native sensitivity8 / F17 confirm4: RUNNING

**本轮唯一准入通过，已一次预留9.5GPUh并启动原GPU作业。确认容器/guardian和真实CUDA进程开始后，agent已停止远端操作。尚无完成或科学验收结论。**

本轮按用户监督指令，precheck、central-status、admit各执行一次；不降低50GiB门槛，不drop caches，不动其它进程。
本次admit的MemAvailable=50.898097992GiB，两张A6000空闲、无compute apps；CAL35仍SETTLED，可用余额17.034014934492GPUh，正式报价9.287657161GPUh不变。
前轮49.651203GiB拒绝记录保持在本文件Git历史中，本轮没有重做CPU、source prepare或provision。
没有创建heartbeat、cron、Codex automation或持续监控，只保留原launcher的温度/硬限/独占保护。

## 实际启动与唯一预留

- 计费/guardian开始（Asia/Shanghai）：**2026-11-04T03:31:08.522200+08:00**。
- GPU容器StartedAt（Asia/Shanghai，显示到微秒）：**2026-11-04T03:31:24.947942+08:00**；原Docker时间 `2026-11-03T19:31:24.947942519Z`；运行PID=363233。
- 启动取证开始时间（Asia/Shanghai）：2026-11-04T03:34:50.136098+08:00。容器Running=true；原guardian PID=363145、supervisor PID=363233、runner PID=363330均已绑定。
- GPU进程证据：`GPU-cebf7119-cf03-23b9-e192-cd196332b704, 363330, /data20t/gaokuangda/worldcache_workspace/envs/wc-cosmos-py310-cu128-r3/bin/python, 24482`。因此已确认实际CUDA进程，不只是一份启动意图。
- runner.log显示Cosmos/VAE/guardrail模型加载；取证时collection.json尚未生成，未确认采样行或最终结果。后续由原launcher继续运行，agent不等待完成。
- 唯一预留事件：`SENSITIVITY8_WHOLE9_5_RESERVE`，sequence=91；中央job状态RESERVED_OR_RUNNING。尚未结算，不运行CPU评分。

| Ledger | cap | used | reserved | available（GPUh） |
|---|---:|---:|---:|---:|
| 预留前 | 250 | 216.465985065508 | 16.500000000000 | 17.034014934492 |
| 预留后 | 250 | 216.465985065508 | 26.000000000000 | 7.534014934492 |

cap250、旧16.5GPUh责任和其它job保持，没有增cap、另一个预留或自动后继卡。

## 冻结身份与已完成准备

- Run：`cara-native-sensitivity8-confirm4-r1-20261104`。
- 唯一实际 launch id：`c751f711b5e74daf8552eabe0109afe2`；GPU-launch.json 已存在，严禁重放或另建launch。
- 实际 UUID：`GPU-cebf7119-cf03-23b9-e192-cd196332b704`；启动时间见上。
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

## 正式报价与估计时钟

正式报价保持 **9.287657161GPUh**，硬限9.5GPUh，按单张GPU墙钟换算：

- 预计完成：**2026-11-04T12:48:24.087981+08:00**。
- 建议人工中途检查：**2026-11-04T08:09:46.305091+08:00**。
- launcher停止新工作阈值：2026-11-04T12:51:08.522200+08:00；硬限：2026-11-04T13:01:08.522200+08:00。

全部基于实际guardian计费起点和既有报价，是估计而非完成承诺；没有安排任何检查/提醒任务。报价距停止新工作阈值约2分44秒，温度/I/O保护可能更早结束。

## 四个新输入与预注册

四个输入均按固定来源分组排除/类别哈希规则选取，seed0，没有重新选样：

- `av_cc90f226-5312-4e0f-959a-39cd4eb4d90d`：`vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only/av_cc90f226-5312-4e0f-959a-39cd4eb4d90d.json`。
- `human_034`：`vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only/human_034.json`。
- `misc_9699390-uhd_3840_2160_30fps`：`vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only/misc_9699390-uhd_3840_2160_30fps.json`。
- `physics_017`：`vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only/physics_017.json`。

预注册：`plans/cara_next_stage_20261104/sensitivity/PREREGISTRATION.md`，提交 `44f738feadad1c9e697274d9f69a48192c40518c`，SHA256 `7cd1d2bd348d9194ede92606d1bf9fe1a847b9e948f479335e16e71ccce4fe9d`。

## 原句柄查看与禁止重派

从本地仓库执行一次性查看（不建立循环）：

```sh
.venv/bin/python plans/cara_next_stage_20261104/sensitivity/ops.py status --receipt /tmp/cara_sens_status_manual.json
```

日志/原句柄将位于 stage 的 runner.log、host-guardian.log、container-cli.log、guardian.json、supervisor.json、billing.json；原launcher保留自身温度/硬限/独占保护。
本卡现已真正启动：禁止再执行prepare、reserve、dispatch或修改原运行源码/配置。状态未知时只恢复这个原launch的句柄，不新建作业、不增cap、不重派CAL35。agent本轮到此停止，没有安排任何后续监控。

## 原运行结束后的确切验收命令

以下命令只在这个原GPU终态后使用，本轮**没有执行**。先验收释放并唯一结算，再执行成功完整结果的CPU评分与分析。

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

本轮宿主内存已通过准入；真实完整卡峰值/9小时I/O与温度尚未完成验收。CAL35曾到88°C，新卡仍按90°C自动停机，硬限与存储保护不放宽。不完整时保留分母和费用，不自动重派。
报价含余量但距T+9小时20分停止新工作阈值约2分44秒，仍是估算。Shared25规划10不是ledger已预留额度，当前已预留9.5后仅余7.534GPUh，不自动推进其它卡。
本卡遵循CAL35本目录RUN_HANDOFF.md惯例；memory/handoffs/LATEST.md为生成文档，未手改。其它工作流原M/??保持。
