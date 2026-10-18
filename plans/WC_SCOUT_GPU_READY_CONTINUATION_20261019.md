# 原24收尾后接新探索：已验CPU的直接执行入口

**CAL12与BANK24生命周期R2 CPU均已独立接受；当前只等待原Window24完整接受及fresh资源准入。** 原R1打包失败完整保留，已验数值248＋10和c1c95ce0实际Cosmos入口CPU没有重复运行。当前没有新增视频、GPU运行或算法效果结果。

## 固定证据

- 生命周期source：`2bd41dc8fa19f42353e03a7c78b7264b4b2695c6`；真正生成入口source：`c1c95ce0c598fb7839b0b89f4a69bd45c8aef7c9`。不得以当前HEAD替换任何已验stage。
- 两stage分别`.sync/wc-scout-cal12-gpu-lifecycle-cpu-r2-20261018`和`.sync/wc-scout-bank24-gpu-lifecycle-cpu-r2-20261018`，每卡1789源；原1772执行依赖不变。
- [两卡完整独立核对](../reports/wc_scout_two_lifecycle_CPU_R2_full_independent_acceptance_20261019.json)：每卡20控制＋实际入口依赖核对两命令全0，全部源/runtime/CPU proof/原句柄均接受；CPU wall为77.617048／65.231004秒。
- 每kind三件套：`reports/wc_scout_<KIND>_GPU_lifecycle_CPU_R2_launch_20261018.json`、`reports/wc_scout_<KIND>_GPU_lifecycle_CPU_R2_collection_20261019.json.gz`、`reports/wc_scout_<KIND>_GPU_lifecycle_CPU_R2_independent_acceptance_20261019.json`。启动日期和收件日期不同，不能读到R1。

CPU证明的`GPU_dispatch_ready=true`表示工具前置条件就绪；上游接受、fresh UUID／v2余额和实际GPU准入仍需完成。配置中原`GPU_lifecycle_accepted=false`保留其入口CPU时点的边界，不改冻结配置去补标志。

## 1. 原Window24保持第一位

原source a350ea98／stage wc-drop1-window24-production-cpu-r1-20261018与已验五命令CPU不改；四CAL×四臂16正式＋8完整预热／864pairs／一次加载，预测3.064166667／上限4。原00:51资源检查于00:57实际查收，两卡仍有其他compute任务，未派发；由`worldcache-gpu`下一次10-19 02:58检查处理，最早unix1792349842.1446834，不提前SSH查GPU。实际后续时点以LATEST与原资源回执为准。

原24启动后必须按实际launch安排一次半程和ETA查收。终态只捕获原任务一次，离线`analyze_wc_drop1_window24_r1.py`；完整原件、全部适用93帧、旧12端点、36guided／前21步控制及实际墙钟费用接受后，才执行下一节。原24自身失败／拒绝／缺失保留，不能借其他scope通过或缩样本。

## 2. 直接启动完整CAL12

先fresh核对UUID、显存、compute进程、逐UUID锁与v2实账余额。原完整12路径（8正式＋4完整warm／432pairs／一次加载）预测1.876666667、完整上限2.5，严格<12，按现有人类授权直接执行：

```sh
.venv/bin/python scripts/launch_wc_scout_gpu_r1.py \
  --CPU-launch-ref reports/wc_scout_CAL12_GPU_lifecycle_CPU_R2_launch_20261018.json \
  --CPU-capture reports/wc_scout_CAL12_GPU_lifecycle_CPU_R2_collection_20261019.json.gz \
  --CPU-acceptance reports/wc_scout_CAL12_GPU_lifecycle_CPU_R2_independent_acceptance_20261019.json \
  --upstream-capture <原Window24实际完整capture.json.gz> \
  --upstream-acceptance <原Window24实际独立接受.json> \
  --gpu-uuid <fresh空闲UUID> --output <唯一新CAL12启动.json>
```

启动器会重验自己的CPU、c1原入口及上游完整接受；普通guardrails保持。已有fence／通信未知只恢复原句柄，不重放、不删标记。明确busy且`NOT_DISPATCHED_NO_FENCE`时保持0子进程／0费用，恢复两小时资源检查，不循环尝试。

真实启动后一次准入核对：

```sh
.venv/bin/python scripts/capture_wc_scout_gpu_r1.py --launch-ref <该CAL12启动.json> --mode admission --output <新的准入回执.json.gz>
```

确认实际supervisor／runner及本UUID整卡预留；启动回执本身不代替准入。按实际launch里的`halfway_check_not_before_unix`与`next_check_not_before_unix`分别安排一次半程及完整查收，未到时不查询。健康检查不提取科学partial，完整捕获后只离线分析。

## 3. CAL12接受并冻结四CAL gate

```sh
.venv/bin/python scripts/capture_wc_scout_gpu_r1.py --launch-ref <CAL12启动.json> --mode terminal --output <新CAL12完整capture.json.gz>
.venv/bin/python scripts/analyze_wc_scout_gpu_r1.py --launch-ref <CAL12启动.json> --capture <该完整capture.json.gz> --output <新CAL12独立接受.json> --gate-output <新四CAL门控.json>
```

核对全部12位置／4完整warm、所有可用原张量及SHA、warm观察器OFF/ON全36guided／终态／动作／A历史／93RGB、前20guided与p20/p21／输入hash、全部有效兼容正式93帧LPIPS、旧N12端点／共同前缀、actual全墙钟费用和本UUID释放。逐原件失败／拒绝／未到达保留；有效子集、完整范围、费用分别接受，不以单汇总代替验收。

Gate只由四CAL的实际probe变化冻结μ和中位秩阈值，方向固定较大z保留D，平局按`z>=threshold`取D。BANK24新六DEV不得再拟合或翻转方向。原G00／G10来自N12，G11复用原24，G01来自本CAL12；后续CPU报告交互`L11-L10-L01+L00`和共享计划对照。跨批次诊断秒数不充clean速度。

## 4. 再直接启动完整BANK24

CAL12适用完整原件／费用和gate都接受后，fresh资源／v2准入。BANK24保持六DEV×D21／A21／NATIVE35：18正式＋6完整warm、864pairs／一次加载／六Native正式参考，预测3.407222222、完整上限4.5，严格<12直接执行。

```sh
.venv/bin/python scripts/launch_wc_scout_gpu_r1.py \
  --CPU-launch-ref reports/wc_scout_BANK24_GPU_lifecycle_CPU_R2_launch_20261018.json \
  --CPU-capture reports/wc_scout_BANK24_GPU_lifecycle_CPU_R2_collection_20261019.json.gz \
  --CPU-acceptance reports/wc_scout_BANK24_GPU_lifecycle_CPU_R2_independent_acceptance_20261019.json \
  --upstream-capture <CAL12实际完整capture.json.gz> \
  --upstream-acceptance <CAL12实际独立接受.json> \
  --frozen-gate <原四CAL门控.json> \
  --gpu-uuid <fresh空闲UUID> --output <唯一新BANK24启动.json>
```

同样一次admission、按实际launch半程／ETA各一次。终态capture后离线analyze；Native真实forward，owner0、actions=None。D/A第21步必须同输入hash、p20/p21和前20guided；只取已经执行的post-RF输出作同状态三元组，不在C21增加A或teacher。

银行接受后再用CPU执行已登记的一次门控组合、相同D配额全部组合／随机混合／全部D／全部A及诊断oracle比较；X-R共享同状态C/A/D输出，只作方向／边缘离线诊断，不另开GPU、训练或恢复F/B。按prompt等权，报告逐输入结果与最差退化，拒绝保留，不以帧当独立样本。

## 共通运行约束

累计cap226、origin79.99637737158223和历史保持，预留不是实际费用；完整单次严格<12自主，>=12或余额不足才问具体整卡，不能拆缩。未知连接不等于任务结束；技术失败只能修新版本，不改活跃stage或自动补样。原N10全960已接受，不再查询、重评分或改结果。探索不自动并入冻结主稿，无新生成器训练、人评、付费VLM或OMR。资源阻碍时两小时一次，长任务半程／ETA各一次，状态无变化安静。
