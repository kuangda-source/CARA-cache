# N05公平强基线完整66已准入，12:05一次验收

更新：2026-10-16 04:57，北京时间。

**同26D完整验收后，已按用户授权直接推进下一项主线。** N05完整11配置×四旧CAL于04:56:09单次派发、04:56:48通过fresh UUID与v2余额准入，原GPU child与CPU post watcher身份已一次核对。本卡没有新科学结果，原source/CPU与两个冻结工作点不改。

## 1. 新原任务身份

|项目|值|
|---|---|
|card|`WC-PAPER-N05-CORE11-CAL4-FULL66-R1-20261016-A`|
|run|`wc-paper-n05-core11-cal4-full66-r1`|
|source|`15d77ac55de7f5715a76901c47e407663d41c9d3`|
|stage|`.sync/wc-paper-n05-core66-production-cpu-r2-20261016`|
|supervisor/child/post|1078249 / 1078290 / 1078250|
|GPU|GPU0，`GPU-de9a5370-cd87-0f1c-a48e-288888777dd3`，A6000；准入前397MiB、无compute PID|
|launch ID|`b98d232e-aeaa-4535-845a-5533968cb795`|
|完整范围|44正式＋22完整warm＝66；2220pairs/4440CFG、一次加载、零教师|
|完整预计费用|8.568548038 GPUh，计费上限9.5；严格少于12，无需再询问|
|原累计实结|89.486094218 GPUh，已含同26D R2的2.622040619|
|当前完整预留|9.5 GPUh，仅预留，不作实际支出|
|当前可准入余额|5.985269115 GPUh；原cap104.971363333及origin保持|

准入回执核对supervisor/child启动ticks、post对原supervisor的归属、注册SHA、完整scope、逐UUID锁持有与v2加法重算；没有读取runner、模型日志或科学partial。GPU启动器绑定原N06独立接受及其真实36条终态/28等价控制/账单，不能绕过验收。

## 2. 回答的问题与全部配置

在同一平台、计时与输出协议下，比较少步Native、有限调阈值的WC/RA与两个冻结工作点，回答实际时间—保真前沿。四个已曝光CAL均seed0，768×432、93帧、16fps、guidance7，原checkpoint/dtype/UniPC-Karras保持。

- Native35/26/18 requested：真实36/27/19更新。
- WC_HALF/DEFAULT/DOUBLE：阈值0.03/0.06/0.12，其他保护与实现保持。
- RA_HALF/DEFAULT/DOUBLE：原0.070744235098772×0.5/1/2，只改控制阈值。
- A_NO_P、TABLE_PHASE_H1：与420相同β1、阶段α、λ/gamma/风险表，FAST head关闭，不加入T1/P-ACR。

每方法两个完整预热，再按冻结交错顺序完成四场景正式路径；模型驻留，每次重新初始化随机状态与缓存。主计时含文本编码、去噪和VAE解码；加载、guardrail、GC/安装/清理与写盘另列，算法实际维护仍在相应计时边界。保留所有网格点、逐场景秒数与LPIPS，不按场景拼赢家，不用插值冒充实测相同成本。

原420的20条默认输出只作等价控制，不复用为本批正式时间/均值；新Native35为各场景匹配参考。直接修正近邻的忠实Cosmos适配仍是N05显式缺口，本卡不能称已经完成所有强基线。

## 3. 预计时间与唯一查收入口

预计约6—8小时并留CPU后处理；原launch的最早查收绝对时刻为2026-10-16 11:56:09.585764（unix1792122969.585764）。**安排今天12:05一次查收**。不持续监听，也不因运行时间较长重新派发。此前不查原N05模型日志/runner/partial科学结果。

```text
.venv/bin/python scripts/capture_wc_paper_N05_core66_r1.py \
 --launch-ref reports/wc_paper_N05_core66_GPU_launch_20261016.json \
 --output reports/新的N05原件捕获.json.gz
.venv/bin/python scripts/analyze_wc_paper_N05_core66_r1.py \
 --capture 同一新捕获.json.gz --output reports/新的N05独立接受.json
.venv/bin/python scripts/analyze_wc_paper_N05_tradeoff_points_r1.py \
 --acceptance 同一独立接受.json --output reports/新的N05实测点前沿.json
```

只收原source/registration/payload、原1078249/1078290/post1078250句柄与退出、全部66位置/44正式、所有兼容视频93帧、11warm重复/五组完整36 guided/20旧默认控制、原账单加法与自身GPU0锁释放。另一合法GPU活动不能当GPU0释放失败。所有拒绝/失败/未到达保留，不填0、不补样或凑满分母。

若GPU或post尚未结束，按剩余工作量重估另约一次，立即结束当轮，不循环轮询。连接失败只检查本任务拥有的本地FRPC TCP，不重启原任务。坏视频/CPU审计错误保留原件并优先只读修复，不重新生成以掩盖。实测点前沿工具已有七项合成CPU控制，不替代本卡真实结果。

## 4. 后续按主线重要性接续

完整接受后，先将全部实测网格与N06简单对照综合，冻结N07新prompt双seed共同测试的方法/对手/工作点，再做N08最终平衡重复clean计时、N09部署费用与N10自动质量。N06前密C/A已经是强对照，应保留到最终方法筛选；当前N05原范围不因新结果修改。

N07原180路径模板尚未选定，真实完整费用与生产CPU仍待；预计若大于等于12GPUh或fresh总余额不足，提交具体完整卡与资金缺口，不拆卡、删对照或重置48窗口。P/T1保持可选后排，F/B关闭，无新人评、训练、OMR。

## 5. 原件

- `reports/wc_simple26d_memory_full36_collection_20261016_0455.json.gz`
- `reports/wc_simple26d_memory_full36_independent_acceptance_20261016.json`
- `reports/wc_paper_N05_core66_GPU_launch_20261016.json`
- `reports/wc_paper_N05_core66_admission_once_20261016.json`
- `reports/wc_paper_N05_admission_once_CPU_controls_20261016.json`
- `reports/wc_paper_N05_tradeoff_description_CPU_controls_20261016.json`

同26D逐场景结果与论文含义见[469](469_WC_SIMPLE26D_COMPLETE_RESULTS_POSITION_READOUT_AND_STRONG_SIMPLE_BASELINE_20261016.md)。本报告是新任务真实准入，不是N05的质量或速度结果。
