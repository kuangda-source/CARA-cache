# W3同状态双CFG教师诊断：生产CPU通过，真实GPU已启动

2026-10-09。[167集成CPU](167_WC_CFG_GUIDED_TEACHER_COLLECTOR_CPU_RESULTS_20261009.md)之后，本轮完成生产绑定与保守成本预测，按已有单次≤2GPUh授权执行完整新卡。当前GPU仍在运行，**没有新的真实误差抵消或质量结论**；总体研究目标 active。

## 本轮问题与完整范围

[同配额四组合](164_WC_CFG_BUDGET_MATCHED_COMPLETE_RESULTS_20261009.md)在Human seed2上，单槽交换退化4.019%/13.391%，成对交换仅改善0.120%。新H-T45要区分：单分支刷新是否破坏了CFG合成中的误差抵消，以及不同动作形成的后续状态/缓存历史是否改变这个关系。它测量实际post-denoise速度，不训练Head，不把局部MSE冒充终点收益。

[执行登记](../manifests/wc_cfg_guided_teacher_r1_execution_preregistration_20261009.json)在真实采集之前固定：Human seed2、同模型/请求/768×432/93帧/16fps、原36更新72调用；两条完整OFF/ON父轨迹与两个视频；S22加四个动作各形成的实际S23，共5起点×4动作×2重复=40完整CFG速度对、80诊断net调用。每个短分支恢复完整状态；初始首重复的已测速度用于原UniPC一步，不再增算网络。各S23内部以DD为局部teacher，状态分别报告。没有完整反事实后缀或端点标签，这不是缩减旧完整位置卡。

## 成本与实际CPU证据

[整卡预测](../manifests/wc_cfg_guided_teacher_complete_cost_forecast_20261009.json)从最近原始GPU回执推导：两次完整父轨迹用“旧父inclusive减十次实测后缀”作上包络，保留其中额外五次编码及外层开销；80诊断调用用含冷启动的最慢后缀单调用时间。另加600秒快照恢复/原始张量写盘/四次solver更新余量与60秒清理，再加50%整卡余量。完整预测**6094.205秒=1.692834708GPUh**，不是新GPU测速或截止时间。旧终点整卡2.082740047h预测、结果及费用原样保留，所有新状态、重复、输出均未删减。

生产源8b3a978先登记/推送，再执行独立production-cpu-r1：**PID3387896/3387897、exit0、52.056秒、CUDAfalse**。实际Cosmos导入、原模型与guardrail文件/哈希、项目HF缓存和真实Blocklist、原视频93帧probe、原Human seed2请求与延迟采集入口均通过，12类范围/动作/teacher空间/seed/guidance/步数修改全部拒绝。[原字节与独立绑定审计](../reports/wc_cfg_guided_teacher_production_cpu_r1_independent_audit_20261009.json)确认64载荷、原CPU终态、config binding与预算不变。原S0的资产验证器仅核对固定资产，不执行旧S0两阶段或750秒截止。

[自主选择](../manifests/wc_cfg_guided_teacher_autonomous_selection_20261009.json)绑定原50h累计与单次≤2h规则。selected标准库CPU **PID3388473、exit0、12.140秒**，精确核对通过的生产回执、选择配置/64源码、预算、共享锁、目标UUID/sm8.6、磁盘和空闲GPU；无Torch/CUDA初始化。已有生产实际导入检查不再重复。[选择CPU原回执](../reports/wc_cfg_guided_teacher_selected_cpu_r1_receipt_native_20261009.json)与[GPU派发](../reports/wc_cfg_guided_teacher_r1_GPU_launch_20261009.json)保留。

真实shape和每个嵌套快照的显存准入在实际采集时检查，不能从CPU通过或旧显存快照说已验收。旧同模型S22 owned GPU快照约2.319GB，原单捕获headroom约9.953GB用于规划；新运行仍逐次读取当前free并执行原logical-copy gate。

## 实际运行与接续

新卡`WC-W3-CFG-GUIDED-TEACHER-R1-20261009-A`、run `wc-w3-cfg-guided-teacher-r1`，冻结源**e9f47f5759a774244dba02cc436657ab36099550**、选择config SHAfb5c4e4345de42ce6c40d6772643527bf077b9da2bda9830edc4f20a0f9c7e36，独立production-r1目录。仅新增一次GPU。

原supervisor **3388748**、GPU runner **3388760** 与绑定等待后CPU **3388749** 已按实际/proc命令行与运行回执确认在途，目标UUID为GPU-cebf7119-cf03-23b9-e192-cd196332b704。模型在加载，无新局部向量或终点结论。CPU后处理只等待这两个原GPU句柄正常退出和释放，再完成两视频全93解码、1216组件/所有动作/20严格重复/120张量独立原件重建及各起点的有符号合成误差评分。若GPU失败，原范围、状态、失败和费用保留，不评分成功子集。

启动前实际费用**24.908110354/50GPUh**，61历史jobs，余25.091889646h。第62job在途账本used50为余额预留，**不是已经花完50h**；结束按包括加载、失败、诊断、输出与清理的实际wall结算。旧秒数截止不生效，2GPUh单次执行权限与累计限制仍保持。

下一只跟踪原三个句柄，不改在跑64载荷/配置，不重投身份。GPU及绑定CPU实际完成后捕获原回执、独立重算与费用，再写科学结论；不扩训练、稀疏、OMR/DRE或人评。本轮是实际生产准备+GPU派发进展，研究尚未完成，不设complete/blocked。
