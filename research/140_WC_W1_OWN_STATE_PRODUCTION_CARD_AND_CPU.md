# W1 自身轨迹诊断：生产入口完成，服务器 CPU 通过

2026-10-06。成果是已登记的三场景同状态诊断已经具备完整生成、旧视频身份桥、费用监督和终态汇总入口。真实模型teacher观测仍为0；尚未新增GPU实验、视频或科学结论。已有W1七场景4改善/3退化和W3-A Human的正信号保持。

## 本轮完成

[具体执行卡](../plans/WORLD_CACHE_OWN_STATE_DIAGNOSTIC_CARD_20261006.md)限定misc、AV51、AV28/seed0，原scalar与fixed mask、calls45/46/67/68不变。冻结配置[production R3](../configs/wc_w1_own_state_production_r3_draft_20261006.json)仍未选择GPU或声称新授权。

- [完整生成](../src/wcomr/own_state_sampling.py)接入普通pipeline，读取实际W1状态、原warp和完整teacher；逐调用输出与全部缓存/校准/pipeline/decoder/video/93帧RGB和旧shadow OFF作严格身份桥。
- [生成CLI](../scripts/run_w1_own_state.py)复用真实Cosmos请求、原setup和dense模型；[监督CLI](../scripts/supervise_w1_own_state.py)保留fresh资源、共享锁、单次限时、预付/实际费用、仅终止自身进程组和释放回执。
- [终态审计](../scripts/audit_w1_own_state_terminal.py)核对原源、三进程退出、费用与完整视频身份；[汇总](../scripts/summarize_w1_own_state.py)按场景内四观测报告有符号近似误差，保留负、零和缺失，不把CPU或LPIPS当作物理/速度结论。
- 核心[139](139_WC_W1_OWN_STATE_SHADOW_CORE_AND_CPU.md)已通过的13文件和8配对fixture不重跑、不改；v4.1计划和post-reference假设登记原字节保持。

## 实际 CPU 结果及失败记录

| 实际目录 | 冻结源码 | 结果 | wall秒 | 解释 |
|---|---|---|---:|---|
| `.sync/wc-w1-own-state-production-cpu-r1-20261006` | 902b695 | exit1 | 21.2315 | 资源/原件通过；新closure遗漏旧`replay_results.py`，生成夹具未开始 |
| `.sync/wc-w1-own-state-production-cpu-r2-20261006` | c0e8d9d | exit1 | 2.6910 | 补齐依赖；CPU AST夹具未绑定实际文件名，`inspect.getsource`不能定位 |
| `.sync/wc-w1-own-state-production-cpu-r3-20261006` | f68bac4 | exit0 | 14.9685 | 只修正夹具源码文件名，生产算法/核心不改；完整七步通过 |

R2本地transfer尾部误指既有R1报告，拒绝覆盖；从原transport的原stdout恢复R2回执，未重启或更改远端原run。已执行wrapper原字节保留，避免把新的本地解释替换原source证明。

[实际R3回执](../reports/wc_w1_own_state_production_actual_cpu_r3_20261006.json)包含：

1. 新stage源和原通过R1资产/核心绑定通过，预算/旧源保持。
2. 13范围/费用拒绝；三个真实原mask的完整OFF/ON六条CPU pipeline、12个score-only观测通过；七类身份破坏、非有限汇总和writer异常清理共9拒绝通过；正/负/零及缺失汇总保持。
3. 三个真实CPU子进程监督场景：正常退出、spawn failure、模拟外来GPU观测。仅替换GPU准入和执行命令，使用实际共享FD、独立进程组、child回收和临时CPU账本的实费结算；没有真实GPU查询/提交。
4. 原三个`InferenceArguments`与`SetupArguments`实际CPU导入并逐字段匹配，setup只变输出目录；禁止权重和CUDA初始化。
5. 四CLI帮助/导入入口通过。

MockWriter和模拟RGB不是实际视频编码/完整几何证明；小Toy网络不是Cosmos28层的真实teacher收益。本轮不训练、不评分新的真实视频，不引入人力审查。

## 独立审计与费用

[独立原件审计](../reports/wc_w1_own_state_production_actual_cpu_audit_r3_20261006.json)实际原生SHA核对720项，含R1/R2/R3原回执和全部payload、旧160文件GPUstage、已通过own-state核心及根账本；独立重读真实输出日志和来源，14个原CPU句柄均退出。R3原件SHA `eb7b3ce765b006a34f3d82c9b40ec1cd735ec09cc8752c476d2cf7fbbe811369`。新GPU授权文件和输出目录仍不存在；审计未导入Torch或查询GPU。

根账本SHA保持 `8d868f727159804f2a6131ffb337c77e992de966a065367c68feed1e331fcdc9`；累计 **13.504302792/24GPUh**、48jobs、无inflight。本轮CPU无新增GPU费用；GPU当前是否空闲未在本CPU阶段测量，实际提交必须fresh准入。

[费用代理](../reports/wc_w1_own_state_cost_proxy_r1_20261006.json)名义946.767秒、压力1420.151秒，候选总1800/child1770/kill5，最大0.5GPUh；不是运行时间保证或GPU批准。加载、hash、teacher、解码、失败和释放统一计费。

## 下一步

生产必要准备已完成，下一需本卡独立直接范围确认后执行真实三场景。之前五Native卡的批准已完整执行，不能把同一答复扩大为新scope；W3-B原9600完整范围问题仍待单独答复，不重复询问。确认后保持CPU来源，唯一提交、实费与释放/终态审计，再解释自身状态局部误差与旧终点的关系。没有确认时不重跑同源CPU、改成其他GPU任务或增加训练/人评来回避范围门槛。

本轮是实质生产接线及实际CPU进展，goal保持active；准备完成不等于整体科学目标完成，旧blocked计数不沿用。暂无预算耗尽、方向否定或新科学负结果。
