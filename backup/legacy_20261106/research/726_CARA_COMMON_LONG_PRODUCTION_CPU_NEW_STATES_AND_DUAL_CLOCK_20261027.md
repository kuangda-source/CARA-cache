# 726｜R4共同输出长龄读出：真实源入口、双端CPU与新状态方案

2026-10-27。用户授权准备，不启动GPU。IG继续暂停，原α、Shared25-C父布局、六强对照、累计226GPUh及最终部署双预算保持。新状态方案与报价见[冻结准备方案](../plans/cara_predictor_refresh_scout_v2_20261026/R4_COMMON_LONG_NEW_STATES_AND_COST_R1_20261027.md)和[完整清单](../manifests/cara_common_long_newstates_scope_quote_r1_20261027.json)。

## 实现范围

新增`scout_common_long_r1.py`：沿真实warp/head/RF计算A与R4两支组件，长龄只添加共同增量，保持A差分和原phase融合；短龄只调用A，不运行外推器。构造接口不接收teacher。复用旧Shared25-C自由运行采样器的只读shadow边界，对六原读出加一新候选；不是新候选自由运行视频入口，不声称E2已准备通过。

新入口同时输出完整请求和准确去噪＋解码时钟；ON含shadow/copy/hash/sink，明确标诊断，不冒称部署速度。各读出记录同步wall时间和累计设备峰值，不把累计峰值叫增量。短龄新增2对head、长龄新增5对head，重复C重建明确计费。

## CPU验收及边界

四卡、两卡均使用独立新CPU stage，1CPU/4GiB、GPU隐藏、无网络、只读project；每台8完整采样路径、2 flow、24选中状态、168读出位置。实际冻结Cosmos InferenceArguments和固定WC/RF/UniPC源码执行，权重/条件/解码/写盘是小型CPU替代；不加载模型权重、不建立CUDA上下文。

- 两输入各OFF/ON全36步、final latent和替代RGB一致，真实Dense teacher/head/RF回放及C父输出一致。
- 新候选长龄与原参考公式逐位一致，短龄严格A且不调用R4；完整父状态/缓存/solver/RNG与原α历史不变。
- teacher异常、末状态写盘失败、copy cap失败保留原错误并拆除adapter；三种错误网格/时间身份拒绝。
- 独立接受器核对终态退出、源与runtime SHA、GPU隐藏、资源、全部分母与语义；另做12种污染拒绝测试。局部3测试覆盖短龄不执行外推、CFG差分保持、错误锚点/非有限拒绝。

首轮R1两台均退出0。随后发现旧observer固定11对head标签不包含新增读出，R2将实际计数更新为13/16，并补同步wall/累计峰值，再完整重验；R1保留但不是最终绑定。未修改正在执行的stage。

[四卡R2终态](../reports/cara_common_long_four_card_CPU_terminal_r2_20261027.json) · [四卡接受](../reports/cara_common_long_four_card_CPU_accepted_r2_20261027.json) · [两卡R2终态](../reports/cara_common_long_two_card_CPU_terminal_r2_20261027.json) · [两卡接受](../reports/cara_common_long_two_card_CPU_accepted_r2_20261027.json)

## 接下来验证什么、费用多少

另外两条旧CAL（misc133和AV51），seed0，固定22/23/25/33/34/35。不是全新prompt，不触及DEV/TEST；新机制状态执行前仍需双端新增身份审计。6完整父路径=2warm+2OFF+2ON；12状态×7读出=84位置；228 denoiser pairs/456 CFG、186额外head pairs。先检验长龄对固定最强基线至少5%增量、相对A至少4/6改善及两prompt不退化；不移动分档、不用DEV调规则。

完整规划估计2.608114GPUh、建议硬上限3GPUh，两台均采用A6000既有实测成本外推并加工程余量；不是新卡实测，不是授权。释放后CPU2核8GiB最多1小时做局部评分和控制接受；无候选终点质量分数。独立32GiB输出卷、48MiB跨盘日志保持要求。

受影响生产CPU通过不等于新整卡监督/财务或GPU接受：下一步绑定完整清单、资源峰值门及监督/终态组合，再提交具体GPU方案。实际干净候选开销和E2自由运行仍待验证，j1不因CPU通过自动产生。全程GPU提交0、预约0、费用新增0，不改原接受或旧16.5责任。
