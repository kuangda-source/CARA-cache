# 799 — S初始化生产选择器CPU接受

两卡原CPU容器退出/0，342个策略的12,312对生产选择器调用与11,628次C分支历史检查通过，覆盖全部新增138种历史组合；8项独立验收控制通过。仅接受选择器与过去锚点执行，不构成完整模型数值或端点收益验证；原S冻结和运行中14GPUh预算搜索卡保持。

延续798的两个事前固定起点，各含初始策略和170个合法候选，合计342个不同策略。原生产PolicyOwner._choose与语法源码哈希保持，全部36更新逐步检查两分支D/C动作、严格过去的最近两次真实D锚点和max-age。332种历史组合中，138种是相对原S覆盖新增的组合；任一分支缺失锚点或包含未来锚点时均退回完整计算，强制D控制也通过。

原单次容器cara-S-init-selector-CPU-a6000-r1-20261031-cpu于2026-10-31 17:04:23启动、17:04:37退出/0，工作测量12.912秒。资源为1核CPU26、4GiB且无额外swap、网络关闭、GPU隐藏；与GPU任务CPU24/25分开。完整源包与运行时哈希在原容器回收时再次核对，原注册SHA为71de33f6c0a27deba08725464ffb76989135732ef703030f029accbb71fbee3e，发布源为e5620647b9c05820d70a9b5ebe3da224b9bac97f。未调用模型、初始化CUDA、读取运行中GPU科学输出或写中央账本。

独立验收器从固定合同重新生成全部候选及历史覆盖，检查原容器终态、源包、资源、分母与原启动绑定。8项控制包含完整接受以及运行中、资源改变、源包改变、历史缺失、策略分母错误、负控制缺失、CUDA初始化拒绝。所有原始回执保留，未重跑该CPU。

本次使用受控CPU锚点对象，尚未覆盖新增策略的完整模型数值传播和自由运行端点。798的初始化提案与原Shared25-C/F19-C父轨迹风险范围保持，不收集Uniform19父轨迹风险，不改S规则或冻结通用方法。下一步是按受影响路径准备配对数值验证及完整端点卡，仍须完整范围、报价和相应执行权限。

当前预算搜索新单次14GPUh卡保持797的原launch_id、源、112路径/51双FIT查询和硬截止2026-11-01 06:45:04；半程23:16与终验06:01自动化保持，本次没有为文档刷新额外查询运行状态。A32/B36科学行、WC/RA FIT UNMATCHED和旧CAL范围均保持。

[原CPU启动](../reports/cara_s_initialization_selector_CPU_launch_r1_20261031.json) · [原终态](../reports/cara_s_initialization_selector_CPU_capture_r1_20261031.json) · [独立接受](../reports/cara_s_initialization_selector_CPU_accepted_r1_20261031.json) · [8项验收控制](../reports/cara_s_initialization_selector_CPU_acceptor_checks_r1_20261031.json) · [固定合同](../plans/cara_next_stage_20261028/mainline/r2/S_INITIALIZATION_SELECTOR_CPU_R1_20261031.json)
