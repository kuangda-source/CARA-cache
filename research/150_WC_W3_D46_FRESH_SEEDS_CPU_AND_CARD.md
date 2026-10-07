# W3 D46净正刷新动作：两个新seed完整复验卡与CPU准备

2026-10-08。**继续WorldCache/W3，下一步从“修复一个坏交换”转到“复验原始WC上已有的净正动作”。** 本卡设计、运行/监督/评分代码和必要实际CPU准备已完成；GPU尚未提交，需要本卡单次>2GPUh例外。

## 为什么选这一步

[149完整结果](149_WC_W3_NATIVE_RESPONSE_ONSET_CORE_AND_CPU.md)：共同61/63交换后，67响应较69响应LPIPS改善13.0508%，实际完整调用21/19相同；65响应改善26.8017%，多两次完整调用。但相对原WC仍退化25.0273%/5.2544%，两者全部93帧都比原WC差。响应时机具有条件化机制价值，继续定位同一个坏配置的最佳补救，不足以证明新方法净收益。

[129已有正例](129_WC_W3_HUMAN_APPROVED_EXECUTION_AND_RESULTS.md)：Human199/seed0原生建议C46时刷新一次，后续原生自适应，LPIPS降低2.8080%，后续完整调用18→16。新卡固定这个动作，预先指定seed1/2，回答其适用条件和净效果是否可复验。不选择新视频中的最好调用，不换seed，不训练门控。

## 整卡范围、判读与成本

卡`WC-W3-D46-FRESH-SEEDS-R1-20261008-A`，run`wc-w3-d46-fresh-seeds-r1`。保持Human199原prompt、35请求/36 UniPC-Karras更新/72CFG、768×432/93帧/16fps、guidance7、Cosmos-Predict2.5-2B、dense/eager与guardrails。

| 项目 | 完整范围 |
|---|---|
| 新seed | 1、2，预登记，仍属同一已曝光prompt的CAL复验 |
| 父轨迹 | 两条Native35参考、两条原WC父，共4条 |
| 后缀 | 每seed OFF1/OFF2/BASE_first/REFRESH_second/REFRESH_first/BASE_second，共12条 |
| 新视频 | 每seed Native、WC父、OFF1、BASE_first、REFRESH_first，共10段 |
| 主要终点 | 两seed各一组`Δq=LPIPS_BASE−LPIPS_REFRESH`和`Δt=T_BASE−T_REFRESH`，完整数与93帧分布 |

BASE始终使用原WC自适应，不强制C；REFRESH只在call46（CFG1）执行D，后续同一原生自适应函数。原生本已建议D时保留no-op；缺合法历史、guardrail拒绝、缺参考、技术失败均留原分母，不换样本。三组严格重复、pre46完整状态/历史/真实输入、OFF/BASE父桥、Native/WC初始完整状态恢复和终态审计保持。调用数可以变化，属于干预的总效果；诊断wall不作干净加速，LPIPS不代替物理/语义质量。

完整预测**8722.551258秒=2.422930905GPUh**；原Human六后缀3246.492340秒×2，减去一次重复模型加载99.023049秒，加入两条Native各364.915542秒和120秒状态检查，再加20%余量与30秒释放。新seed可能改变后续动作，预测不是deadline或保证上界。累计18.906279766/24GPUh，余5.093720234h；预测后约21.329210671/24h，仍在累计范围。

[v5.4完整设计](../plans/WORLD_CACHE_D46_FRESH_SEEDS_WINDOW_20261008.md) · [事前登记](../manifests/wc_w3_d46_fresh_seeds_r1_preregistration_20261008.json) · [完整成本及原件SHA](../reports/wc_w3_d46_fresh_seeds_complete_cost_20261008.json)。保留旧结果与判据，新卡不追认旧实验。

## 已完成的CPU准备

新核心source`51bb84bec231319766e23003b677a560787dc15f`，独立stage`.sync/wc-w3-d46-fresh-seeds-core-cpu-r1-20261008`。实际CPU driver128.622621秒，核心126.127434秒，exit0；flow OFF/ON下分别覆盖原生C46刷新和原生D46 no-op，共4父/24完整后缀/16 mock输出、36项破坏证据拒绝，以及两项child writer/guardrail失败恢复。基于冻结真实UniPC采样循环、WorldCache函数和Video2World类，权重/网络/解码/写入为显式Toy；不能据此声称新seed真实收益。

[原件与独立审计](../reports/wc_w3_d46_seed_core_cpu_r1_audit_20261008.json)保存原字节、压缩归档、SHA、全部成功/失败原始记录。原两个CPU PID退出，旧216项源未改，预算SHA前后相同，无CUDA/GPU提交。旧Human核心和旧stage未覆盖。

生产source`df339c944b77eddfbf88c6034ff4cfa64abd9701`，独立stage`.sync/wc-w3-d46-fresh-seeds-production-cpu-r1-20261008`。实际CPU68.513392秒、两步骤exit0：

- 初始完整状态隔离20.412273秒：Native/WC四回调刻意修改计数、buffer、solver和cache配置，逐次恢复一致。回调为CPU注入，不伪称真实Native/WC生成。
- 实际生产48.096812秒：冻结旧216项基础和新12项载荷、当前模型/样本协议、实际权重/guardrail源码资产核验、实际InferenceArguments解析seed1/2、真实Native/causal/portfolio函数导入。CPU禁止CUDA初始化和下载。

监督器/终态评分器额外实际只读导入通过，无Torch加载；视频读取与LPIPS复用既有冻结实现和资源，未重跑旧评分。[生产原件和审计](../reports/wc_w3_d46_seed_production_cpu_r1_audit_20261008.json)保存三PID退出、原源/SHA、两步骤日志和配置绑定；GPU输出目录不存在、GPU提交/预留0。现场目标GPU27MiB、目标无compute进程、f1锁可用；GPU执行前仍需fresh准入，不把本次观察当未来资源保证。

## 唯一待确认事项

按照用户直接约定“取消这些时间限制，只有单次gpuh超过2h的才停下来询问，其他直接推进即可”，本卡完整预测2.423GPUh，因此必须取得**本卡完整单次>2h例外**。累计24h保持，不清零费用，也不拆seed或删原生参考/重复来回避门槛。

可审查草案、source/CPU原件、模型/请求和成本已就绪。当前`GPU_execution_selected=false`、UUID/新执行批准为空，新GPU=0。确认后只绑定本卡具体授权和同源CPU证明，再fresh GPU/共享锁/预算准入，单次完整执行；原H-T36、旧CPU与评分身份均不重启。

goal保持active，本轮首次提交此项具体例外；不是预算耗尽、方向否定或已满足重复阻塞条件。非必要不引入人评。

## 首次自动续接复查：整卡具体例外仍未收到

上一轮完成H-T36归档与新卡实际CPU，是实质进展。本轮自动续接只读复查：新source12项/旧基础216项及exit0 CPU原件不变，累计18.906279766/24h、55jobs无预留，GPU输出不存在，GPU选择与具体新授权仍为空；十个旧GPU/CPU句柄均不存在，不能把已完成状态当作可等待的活任务，也不重启它们。见[现场复查](../reports/wc_w3_d46_gt2h_scope_resume1_20261008.json)。

本轮没有新的科学结果、GPU提交或CPU复跑。相同授权条件已出现两轮（原具体卡提报与本次续接），尚未达到三轮blocked门槛，goal保持active；只有新的人工整卡批准或外部状态变化才能继续本卡GPU。不缩拆对照、不开新旁支来规避2h约定。[等待审计](../manifests/wc_w3_d46_gt2h_pending_audit_20261008.json)。

## 第三轮复查后目标已blocked，停止重复自动续接

原具体卡提报、本次前一自动续接、本次第二自动续接连续三轮均未收到该完整卡>2GPUh例外。[最后只读现场复查](../reports/wc_w3_d46_gt2h_scope_resume2_20261008.json)确认新CPU/source原件不变、旧十句柄全不存在、新GPU输出/预留/授权均无、预算18.906279766/24h与55jobs保持，没有可等待的活任务或未完成的必要CPU准备。上一轮属于无科学进展的授权状态复查，不能通过保存审计文档重置阻塞计数。

阻塞审计达到三轮，goal工具[真实返回blocked](../reports/wc_w3_d46_goal_blocked_native_20261008.json)；目标未完成，停止自动续接、旧CPU重跑和旁支工作。需要人工明确批准`WC-W3-D46-FRESH-SEEDS-R1-20261008-A`完整单次例外（预计2.422930905GPUh）后才能继续，新批准不清零既有费用，累计24h保持。剩余5.093720234h；不是预算耗尽、CPU失败或W3方向被否定。既有成果与完整卡准备均保留。
