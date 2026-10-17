# N08完整40已在GPU0准入，15:32半程／17:32验收

**已按用户要求先完成R2完整结果总结，再直接启动原N08重复测速。原完整40在GPU0运行，源码、九命令CPU、三原进程、逐UUID锁和完整预算预留已独立接受；本轮没有新增方法选择或参数调整。**

[547完整结果报告](547_WC_N07_R2_COMPLETE_RESULTS_FIDELITY_COST_SIMPLE_CONTROLS_AND_N08_NEXT_20261017.md)及机器分析已推送：H1对WorldCache的可用双seed提示词平均失真降低84.48%、计时增加约5.55%；低成本A_NO_P对RA默认失真高2.04%，H1尚未超过简单前密集对照。全部拒绝、参考缺失、分组覆盖和原判据保留；N08负责独立重复耗时证据，不从这些终点结果挑新对手。

## 1. 原卡实际运行身份

| 项目 | 实际原值 |
|---|---|
| 卡／run | `WC-PAPER-N08-BALANCED-FULL40-R1`／`wc-paper-n08-balanced-full40-r1` |
| source | `8bdebc340737599a6923c01a31a4734b04bc3f4b` |
| stage | `.sync/wc-paper-n08-production-cpu-r1-20261017` |
| launch ID | `a5d2282f-7d8e-497d-9196-30f31a4980f6` |
| GPU0 UUID | `GPU-de9a5370-cd87-0f1c-a48e-288888777dd3` |
| supervisor PID／start_ticks | `1265104`／`550998673` |
| runner PID／start_ticks | `1265137`／`551002528` |
| CPU post watcher PID／start_ticks | `1265105`／`550998683` |
| 实际launch时刻 | 2026-10-17 13:31:23.219北京时间 |
| 配置SHA | `eb46fe1e335be8a39f5b5cdb9e480d8339c13116e1db7c0a0e8bc762bd027e4b` |
| registration SHA | `da6bd03453564eb09362c10c7f461d9fb013303ef3cb9d0accec264f3cf09688` |

单次派发后仅一次原启动准入核对：1747完整payload一致，原三PID/start_ticks全部存活，`N08_FULL40_GPU_RUNNING`，自身UUID锁由原任务持有，v2为原完整40预留3.6275 GPUh。没有读取新质量、逐方法计时或runner科学partial；准入回执里的默认runner行数不作为生成进度。

## 2. CPU与前置证据

原CPU1263883已正常终态；2026-10-17约13:28仅一次收原件，九命令全部退出0，148.614433765秒。独立接受确认1747源文件、10真实typed输入变体、完整40绑定、原99数值源码复用、CUDA未初始化、0模型权重及0GPU派发。CPU proof SHA为`6955f8e5350e4c189846219a99dfee5bce9c217866459e7b49271e17e567f05e`。

R2实际source6e10aa3/run/配置与登记缺失的完整可用队列，已在N08部署前重新接受；不借用R2的GPU许可或把早收回执重标为另一次实验。N08以本次用户直接指令及长期严格小于12 GPUh规则准入。

准入前最新只读资源：两A6000均无计算进程、逐UUID锁空闲，无本项目CPU指标进程；选择原GPU0。观察是一次边界证据，不能提前冒充整个运行区间都满足clean条件。

## 3. 完整范围和报告口径

- AV28与Human199、seed0；五角色固定为Native35、WC_HALF、RA_DEFAULT、A_NO_P、TABLE_PHASE_H1。
- 三平衡轮共30正式＋10完整预热＝40路径，1440pairs／2880CFG／一次模型加载／0teacher。
- 768×432、93帧、16fps、35请求步／36实际更新；每次恢复模型、缓存、调度器与随机状态。
- 主计时为同步文本编码＋去噪＋VAE解码；guard、装卸、GC、写盘、加载和整卡实费分开记录，不扣减拼造新计时。
- 正式计时不进行研究用逐步复制/哈希/保存；算法真实缓存维护与修正/刷新开销保留。计时外核原warm全36guided及正式末态/actions/history/RGB控制，对全部兼容正式视频评分93帧。
- 每场景报告全部三轮秒数、波动与加速比，统一对照耗时÷候选耗时，保真并列；两旧CAL测速不当新输入泛化，不把seed或帧当独立重复。

## 4. 预算

累计cap **113 GPUh**，origin **79.99637737158223**不变。原已结 **106.722650231 GPUh**，新增本卡完整上限预留 **3.6275 GPUh**，可新准入余额 **2.649849769 GPUh**。预留不是已产生实费，结束后只按原账单加法结算一次。

全卡预计与上限均严格小于12 GPUh，原可用余额足以覆盖，故按用户授权直接执行，没有再次确认、拆卡或扩大预算。N09/N10仍待，不能把未知费用或后续卡视为已获得本次授权。

## 5. 已登记两次查收

| 检查 | 实际启动推算的最早时间 | 已登记北京时间 |
|---|---|---|
| 半程技术检查 | 15:31:23.219，unix1792222283.219007 | **今天15:32** |
| 完整终态验收 | 17:31:23.219，unix1792229483.219007 | **今天17:32** |

已将原`worldcache-180`自动化更新为“WorldCache N08重复测速半程与验收”，当前ACTIVE；原R2/旧卡查收不再执行。半程只核原身份、40分母、技术错误、显存、锁与原job，不读方法质量/耗时；半程后仅保留最终一次。最终查全部原件、40分母、完整warm与重复控制、兼容93帧LPIPS、真实逐轮时间、整卡费用与自身释放。若未完，按剩余量另约一次并结束，不循环监听。

### 半程原命令

```sh
.venv/bin/python scripts/capture_wc_paper_N08_midpoint_health_r1.py \
  --launch-ref reports/wc_paper_N08_balanced_full40_GPU_launch_20261017.json \
  --admission-ref reports/wc_paper_N08_balanced_full40_original_admission_20261017.json.gz \
  --output reports/wc_paper_N08_balanced_full40_midpoint_health_20261017_1532.json.gz
```

### 最终原命令

```sh
.venv/bin/python scripts/capture_wc_paper_N08_balanced_full40_r1.py \
  --launch-ref reports/wc_paper_N08_balanced_full40_GPU_launch_20261017.json \
  --mode terminal \
  --output reports/wc_paper_N08_balanced_full40_terminal_collection_20261017_1732.json.gz
.venv/bin/python scripts/analyze_wc_paper_N08_balanced_full40_r1.py \
  --capture reports/wc_paper_N08_balanced_full40_terminal_collection_20261017_1732.json.gz \
  --output reports/wc_paper_N08_balanced_full40_terminal_independent_acceptance_20261017.json
```

失败、拒绝、缺失和未到达保持原分母，不补样。连接未知不当终态，不重启服务器或重复派发。N08期间不并发其他本项目GPU卡或重CPU自动质量评分；F/B、训练、人评、OMR、P/新W3不启动。

## 原件链接

- [真实CPU捕获](../reports/wc_paper_N08_full40_actual_production_CPU_R1_collection_20261017_1328.json.gz)／[独立接受](../reports/wc_paper_N08_full40_actual_production_CPU_R1_independent_acceptance_20261017.json)
- [fresh资源与完整池](../reports/wc_paper_N08_full40_fresh_resources_before_GPU_20261017.json)
- [完整小于12 GPUh权限绑定](../reports/wc_paper_N08_full40_standing_under12_launch_authority_20261017.json)
- [原GPU启动](../reports/wc_paper_N08_balanced_full40_GPU_launch_20261017.json)
- [原准入快照](../reports/wc_paper_N08_balanced_full40_original_admission_20261017.json.gz)／[独立准入](../reports/wc_paper_N08_balanced_full40_independent_admission_acceptance_20261017.json)

当前结论仅为：CPU通过、原GPU整卡已在跑。N08实际质量、重复耗时和净加速结果留待终态接受。
