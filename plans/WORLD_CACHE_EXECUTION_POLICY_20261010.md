# WorldCache 执行约定：单次4 GPUh确认门槛（2026-10-10）

用户直接指示：“单次 改成超过 4h才需要确认”。[直接授权原件](../manifests/wc_execution_autonomy_authorization_20261010_4gpuh.json)覆盖旧执行约定中的2 GPUh门槛。

在已授权研究设计和可用预算内，完整单次作业预测成本**≤4 GPUh直接推进，>4 GPUh才询问确认**；恰好4 GPUh不需确认。以整项任务成本判断，包含加载、对照、重复、失败和清理，不能拆卡或删对照绕过门槛。必要的CPU验证、资源准入、状态恢复及计费仍按原约定实施；不重新引入已取消的逐卡秒数截止。

预算仍采用[48 GPUh窗口](../research/199_WC_NEW_REMAINING_48_GPUH_AUTHORIZATION_20261009.md)：窗口起点已用29.895246589658527 GPUh，累计上限77.89524658965853 GPUh。此次只调整确认门槛，不重新增加48 GPUh或归零费用。已批准完整作业应按完整范围运行并计入所有实际费用；若未经更高成本确认的任务预计将超出4 GPUh，先安全停止自有进程、保存部分结果与费用，再形成具体继续方案。

旧授权、结果、失败和冻结配置原件保留。下一执行卡应绑定当前预算窗口与本次4 GPUh授权，完成受影响入口验证；旧绑定2 GPUh/50累计上限的冻结stage不能直接复用为新授权。原H-T63完整卡预测6.704055834 GPUh仍超过4 GPUh，不能把本次门槛更新当作该卡具体批准。

当前方法合同采用[统一方法设计](WORLD_CACHE_INTEGRATED_MULTI_FIDELITY_DEVELOPMENT_20261009.md)，阶段顺序更新为[2026-10-11 A确认与P恢复](WORLD_CACHE_A_CONFIRMATION_AND_P_RECOVERY_20261011.md)，原[首窗口](WORLD_CACHE_MULTI_FIDELITY_FIRST_WINDOW_20261009.md)保留历史。完整32与原64已分别完成／失败，设计更新不授权复用旧批准重投。重大方向选择共同讨论，非必要不增加人工评审。[授权核验记录](../research/200_WC_SINGLE_JOB4_GPUH_EXECUTION_AUTHORIZATION_20261010.md)保持。
