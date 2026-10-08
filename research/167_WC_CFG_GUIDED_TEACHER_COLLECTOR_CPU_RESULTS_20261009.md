# W3双CFG教师采集：完整CPU流程与原始张量独立重建通过

2026-10-09。承接[166评分语义](166_WC_CFG_GUIDED_TEACHER_METRIC_CPU_AND_COLLECTION_DESIGN_20261009.md)、[164同配额结果](164_WC_CFG_BUDGET_MATCHED_COMPLETE_RESULTS_20261009.md)。本轮完成真实上游接口的采集集成和服务器CPU验证，下一张真实模型诊断仍未提交；整个研究目标继续 active。

## 发现与用途

已经可以在同一个完整状态中执行两个CFG分支的CC/DC/CD/DD动作，保存**真正denoise返回的条件/无条件FP32预测与原闭包guided预测**。这补上了此前只能看单分支误差摘要的缺口，为区分“CFG有符号误差抵消”和“刷新改变后续缓存历史”提供测量工具。CPU例子与Toy权重不证明真实模型已经出现该机制。

首重复测得的guided速度直接送入未改写的原UniPC一步，形成该动作自己的S23；没有为生成S23再跑一次网络。四个S23各在自己的快照中比较，不跨轨迹拼同状态teacher。每个短分支结束都恢复父快照，最后原完整生成继续；OFF/ON父轨迹的所有输出、solver、状态和模拟视频一致。

## 实现与完整CPU覆盖

核心：[局部分支与路由](../src/wcomr/cfg_teacher_collection.py)、[完整父路径与采集](../src/wcomr/cfg_teacher_sampling.py)、[CPU入口](../scripts/check_wc_cfg_teacher_collection_cpu.py)、[集成检查](../tests/check_cfg_teacher_collection_cpu.py)。

实际生产venv、固定Cosmos源、原采样器/UniPC、完整Video2World冻结条件类、实际denoise与CFG闭包函数体参加CPU验证；网络权重、注意力、编码器、解码器、模拟writer为明确的Toy边界。CPU用seed0测试接口，真实新卡仍是Human seed2；不以CPU几何或组件数替代真实模型显存/1216组件验证。

| 检查 | 实际结果 |
| --- | --- |
| 两种缓存配置，各一组完整OFF/ON父轨迹 | 4个完整父、4个模拟输出，两个完整父对均无扰动 |
| 每组S22及四个实际S23，四动作各两重复 | 合计10起点、80完整CFG速度对、160诊断net调用 |
| 严格重复 | 40组状态、动作、条件、输出严格一致 |
| 原始张量 | 80个文件、240个条件/无条件/guided张量；原字节及Tensor SHA独立重建 |
| 异常回滚 | 第二CFG失败、嵌套writer、条件突变、solver突变、非finite、模式突变，共6类均拒绝并恢复 |
| 分母保留 | 每个故障仍保留计划2父/5起点/40对/2输出和已有失败、待测格，不汇报成功子集 |
| 证据破坏拒绝 | 两成功组各拒绝缺起点、缺重复、合成输出变更、条件变更、动作变更，合计10次 |
| 成本与源码 | 原源哈希、预算原字节保持；CUDA未初始化、GPU提交0 |

源a417fa9先提交/推送后执行独立`.sync/wc-cfg-guided-teacher-collector-cpu-r3-20261009`。原driver PID3386366、子PID3386367，**exit0，完整CPU进程墙时308.128秒**，内部检查305.448秒；均已退出。[终态捕获](../reports/wc_cfg_guided_teacher_collector_cpu_r3_terminal_capture_20261009.json)绑定原字节与源。

[独立审计](../reports/wc_cfg_guided_teacher_collector_cpu_r3_independent_audit_20261009.json)使用[独立工具](../scripts/audit_wc_cfg_teacher_collection_cpu.py)，不调用采集器或指标评分器。重新读取240个原始张量，逐位重算`conditional + 7*(conditional-unconditional)`，重建同state的四MSE和有符号能量分解；核对所有输入/条件、真实full历史、动作/槽位、origin与终态指纹、每组20组完整重复、S22测得速度到各S23的latent桥、父轨迹以及6故障完整分母。原张量保留服务器，Git仅存哈希与压缩回执。

## 两次集成失败保留

| 原CPU身份 | 原结果 | 定位与修复 |
| --- | --- | --- |
| r1 /276d1d6 /PID3385820、3385821 | exit1，8.219秒 | 基础Toy fixture直接返回RGB，实际条件接口需要2048通道latent；为测试声明Toy编码器，不改实际denoise |
| r2 /ae56fca /PID3386101、3386102 | exit1，48.780秒 | 首完整采集后，验收器将继承的list TRACE_KEYS与tuple相加；修正验收器类型，原40对及完整状态回执保留 |

两次失败均在CPU，旧日志、源、回执和独立stage保留；r3使用新身份。修复卡通过不追认旧卡通过，这些是集成问题，不是方法负结果。三轮无GPU费用，原预算SHA8f63f176d6079db31237fe209a73cdf7935186b788253571d287e765ef97102d保持。

## 下一步

真实新卡完整范围不变：[H-T45设计](../plans/WORLD_CACHE_CFG_GUIDED_TEACHER_DIAGNOSTIC_20261009.md)，2条完整父轨迹/2个视频、5个实际状态×4动作×2重复=40CFG对/80net调用。没有完整反事实后缀或端点质量标签，这是局部机制估计，不是把旧整卡缩小来绕过预算。

接着完成生产入口/权重/guardrail/实际请求绑定与CPU验证、真实shape与嵌套快照显存准入、包括加载/两父完整生成/80调用/复制与失败成本的整卡保守预测。GPU释放后再用CPU评分真实向量；不在活CUDA进程中调用CPU-only评分器。

累计服务器实际仍**24.908110354/50GPUh**，余**25.091889646GPUh**。新卡selected=false、完整预测未完成，无新GPU。最终整卡≤2GPUh按已有授权自主推进，>2GPUh才提具体整卡确认；不删格、不拆重复。旧同配额GPU身份及三个CPU身份都已消耗，不重启。

[组会飞书](https://lcnssrlun9lz.feishu.cn/docx/HTSIdK0uLofCG5xUI1IcTKaCnAh)已有最新完整科学结果；本次软件准备不冒充新视频收益。继续W3必要生产准备，无需用户补充/人评，不扩训练/稀疏/OMR/DRE，研究目标未完成，不设置complete或blocked。
