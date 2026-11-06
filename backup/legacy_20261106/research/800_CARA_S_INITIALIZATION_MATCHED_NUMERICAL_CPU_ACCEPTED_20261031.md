# 800 — S初始化配对数值CPU接受

Uniform19起点及BR/DIAG、CFG两种不同提案的完整微型CPU矩阵已接受：36条生产路径、12条旧入口对照、18项失败控制；完整36步guided与终态latent/RGB/Torch RNG精确一致，12项独立验收控制通过。两次早期失败保留，原GPU卡与S冻结保持；真实权重和视频端点仍未接受。

799已覆盖342个策略的选择器历史。本次补受影响的3个策略：Uniform19_C、Uniform19_BR_DIAG_C、Uniform19_CFG_C，固定两个FIT输入av28/human199。3策略×2FIT×ON/OFF/AUDIT×2flow为36条生产路径，另有3策略×2FIT×2flow的12条旧固定掩码入口对照。合计48条完整成功路径、1,728次普通更新、3,456次CFG分支调用；18项故障路径单列，未混入成功分母。

实际两种flow下，每一次apply_worldcache调用都核对两入口使用相同完整配置：每种flow33次，共66次。生产路径的精确动作、19D、真实过去D锚点、无teacher以及清洁路径零研究计数通过；每个member/role的ON、OFF、AUDIT输出和历史完全一致。旧固定掩码入口的全部36步guided输出与生产入口精确一致，最终latent、微型RGB及Torch RNG亦相同。每种策略的文本拒绝、decode失败、writer失败都保留分母、恢复hook且拒绝重放。

R1遗漏旧入口两份历史参数文件，退出/1；R2补齐依赖后在旧入口与生产入口latent比较处失败。定位到Requests覆盖了common settings，旧入口却沿用fixture默认配置：motion sensitivity及flow/scale等不一致。R3只修复CPU测试源，将原ALLD完整配置同时绑定两个入口，并使flow_enabled作为明确False/True轴进入独立scope。测试未放宽容差、删去对照或改变生产实现，未修改运行中GPU源包。R1/R2容器、源、失败与无完整接受状态均保留。

R3唯一源989e1161f1aa8c81be8434644ceb4e49165f7c13；原容器cara-S-init-numeric-CPU-a6000-r3-20261031-cpu，注册SHA ee65b3994a17dbeb99a238cfadae00cd44de531321738698df0347ab04299d92。实际2026-10-31 17:24:07启动，17:26:37退出/0，worker147.495秒。资源为CPU26单核、4GiB/无额外swap、network none、GPU隐藏，1200秒工作与60秒退出上限。原source/runtime与资源再次核验；没有新GPU提交或账本操作。

独立接受重建3策略指纹和完整成员矩阵，检查实际flow配置、原源包/终态、全部轨迹一致性与失败集合。12项控制包括完整接受及运行中、源改变、额外swap、缺flow、重复策略位置、逐步不一致、实际flow不匹配、缺失败控制、真实权重标志拒绝，以及源包依赖和flow-scope两个回归检查。

边界：微型权重、attention、prepare、decoder和writer是显式替身，保留原pinned Block/RF/WC/UniPC与生产路由；验证的是数值执行一致性，不是实际视频质量、GPU速度或整卡GPU接受。初始化选择仍仅基于原Shared25-C/F19-C两父轨迹FIT风险，未重收Uniform父轨迹风险或冻结新的通用方法。下一步在完整范围、复用资格和费用明确后准备端点比较；原A32/B36科学行、WC/RA FIT UNMATCHED、旧CAL范围保持。预算搜索14GPUh卡仍按797原句柄与23:16/06:01自动检查承接，本次未查询其部分科学输出。

[独立接受](../reports/cara_s_initialization_numeric_CPU_accepted_r3_20261031.json) · [原终态](../reports/cara_s_initialization_numeric_CPU_R3_operational_r2_20261031.json) · [12项控制](../reports/cara_s_initialization_numeric_CPU_acceptor_checks_r1_20261031.json) · [R1失败](../reports/cara_s_initialization_numeric_CPU_R1_failure_closed_20261031.json) · [R2失败](../reports/cara_s_initialization_numeric_CPU_R2_failure_closed_20261031.json) · [承接](../plans/cara_next_stage_20261028/mainline/r2/S_INITIALIZATION_NUMERIC_CPU_HANDOFF_20261031.md)
