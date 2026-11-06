# 完整共享执行注册表952 CPU接受：多seed接线已打通

更新：2026-10-16 06:02，北京时间。按原预计时刻只收原R3一次，随后离线独立验收；未查服务器N05。

**完整952条本地CPU验证已经通过。** 已接受执行器能使用seed17/43，并把缓存身份与实际seed一致绑定；seed0与旧实现逐步等价，审计开关没有改变终态、动作、修正历史或mock输出。此结果补齐最终共同测试的执行接口，未选实际最终输入、方法或GPU卡，也不是新质量或速度结果。

## 1. 原任务与完整结果

|项目|结果|
|---|---|
|原source|`616caef408285a0d8374692b879ee1d5b5b880f4`|
|原PID|9817已终态，exit0；不再查旧句柄|
|隔离source|`.sync/wc-paper-shared-registry952-local-cpu-r3-20261016/source`|
|封存payload|2272份全SHA一致；固定runtime未改|
|完整执行|952/952路径；32816pairs/65632CFG|
|audit/lean|408对全部终态/actions/Ahistory/sourcehistory/mock一致|
|旧seed0桥接|136条完整guided及终态/动作/历史/mock旧新一致|
|seed|0/17/43实际传入固定sampler；12个scene×seed噪声组按seed一致并相互区分|
|Native网格|72项36/27/19更新与CFG双分支次数检查通过|
|简单策略|固定26D及A5/10/0掩膜保持，前密C/A可按新seed执行|
|mock原件|952份全部重查；为CPU JSON mock，不是真实视频|
|组件与状态|每请求owner/执行器/读出释放，原net/scheduler/RNG恢复|
|CPU实际时长|507.754656秒，约8.46分钟|
|GPU/服务器|0GPUh、0SSH、0权重下载、0预算写|

两种WorldCache flow设置、四Toy请求、17个已有配置、三seed完整覆盖；816 audit/lean路径加136旧seed0路径，完整分母不缩。原R2装饰器命名空间错误及R1打包中断均保留在472/473；本次R3独立执行，不把旧失败改成成功。

## 2. 独立接受怎样得出

collector在原ETA后一次核对PID/lstart、source/registration、exit/result SHA和全部mock文件。本地analyzer从同一回执重建两flow的scene×method×seed集合、所有实际步数、噪声一致性、同seed审计开关/旧实现的mock SHA、固定mask与72Native计数；不只接受runner自报总数。

- 原捕获：`reports/wc_paper_shared_registry952_local_CPU_R3_collection_20261016_0602.json.gz`，SHA `ab4f02b3df8c2e9139f3803490fb40c0aa095bdef09dd1179651b8473c1dbb23`。
- 独立接受：`reports/wc_paper_shared_registry952_local_CPU_R3_independent_acceptance_20261016.json`。
- 原CPU结果：`reports/wc_paper_shared_registry952_local_CPU_R3_result_20261016.json`及原exit。
- 原launch：`reports/wc_paper_shared_registry952_local_CPU_R3_launch_20261016.json`。
- CPU工具合成fixture/八异常拒绝与真实R3接受分开，见472；合成不充当真实路径。

## 3. 可以复用什么，还缺什么

N07如仅从这17配置选定10个、seed17/43与数值实现不变，可复用本次完整注册表验证，不重复整套Toy采样。后续重点只补新真实输入、最终参数/方法绑定、实际Cosmos生产入口、普通guardrail、完整费用与准入等受影响检查。

本CPU仍使用声明的Toy注意力/权重/head/prepare/decode/writer，Native是dense-WC stand-in，不是实际Cosmos原生类。最终16真实请求、工作点和对手尚待N05/N06后冻结；原8prompt×2seed×10方法＝160正式＋20warm/180模板保持。474输入选择核只有合成控制，尚未对真实1044记录选输入，也未生成冻结manifest。

N05的有限强基线实测决定最终对照/工作点，N06已接受的前密C/A强简单规则必须在最终筛选中保留。冻结后，完整GPU卡若>=12或fresh池余额不足，提交具体完整卡决定；不因审批门槛拆控制、缩分母或重置48窗口。

## 4. 当前下一动作

原服务器N05完整66、source15d77ac、supervisor1078249/runner1078290/post1078250，仍**今天12:05一次验收**（最早11:56:09.585764）。本轮未查其进度/科学partial，不改源、不重派。最近v2实结89.486094218、N05完整预留9.5、可准入5.985269115是04:57快照，不作实时实际花费；原cap104.971363333保持。

本地CPU查收自动化已暂停，不再查R2/R3旧句柄。后续按N05→N07→N08→N09/10接续；当前不自动开新GPU、P/T1、F/B、训练、OMR或人评。

机器总表同时校正当前状态字段：同26D的原R1部分失败移入显式历史尝试，当前字段绑定已完整接受的R2及其24视频/2232帧和2.622040619GPUh；N05标为已选定GPU卡。历史失败原件、原费用与审计不删除，防止写论文端误把旧失败字段当作最新状态。
