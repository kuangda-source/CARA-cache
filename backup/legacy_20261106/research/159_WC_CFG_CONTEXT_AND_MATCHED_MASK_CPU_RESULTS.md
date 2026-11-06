# 分支上下文诊断完成，同配额四组合结构CPU通过

2026-10-08。[158完整实验](158_WC_CFG_FACTORIAL_COMPLETE_RESULTS.md)之后，按v5.8预登记完成两项低成本CPU工作；本轮新增GPU0，累计仍23.702366117/50h、60jobs/noinflight。原卡所有控制/正负帧和费用保持，整体goal active。

## 当前输入和浅层信号相同，后续计算效应仍依赖上下文

[H-T43登记](../manifests/wc_w3_cfg_factorial_followup_cpu_preregistration_20261008.json)先于本项CPU分析执行，明确已曝光四个损失和部分动作/信号，是回顾性探索诊断。由[实际脚本](../scripts/analyze_wc_cfg_factorial_context_cpu.py)对绑定原件执行，无新生成、评分、门控拟合或正式RV标签。

[原件分析](../reports/wc_w3_cfg_factorial_context_cpu_results_20261008.json)确认：

- 四细胞当前45/46的模型输入完全相同；pre46当前latent和所有solver组件相同。
- 刷新CFG0使pre46的8项net组件不同，涉及residual/probe cache与window、previous_output、accumulator、resume_flag和skip计数；自己的CFG历史也变化。组件摘要只有相等性信息，不提供变化范数。
- CFG1与PAIRED在call46的已付信号完全相同：age1、input drift0.120605469、probe drift0.104003906、threshold0.204101562、accumulator0.104003906，原生均建议C；D46真实输出摘要也相同。
- 然而“刷新CFG1”的终点与计算总效果不同：此前CFG0复用时保真−2.9201%、全程增加1；此前CFG0刷新时保真−0.9729%、全程减少2。

这个局部观察支持在后续刷新价值建模中保留另一CFG当前动作和缓存历史上下文，分别记录质量/成本总效果。不能由两个依赖上下文证明浅层proxy无效或已经形成可预测的路由规则；也没有唯一定位为attention内部交互。

未来动作还显示：只有PAIRED在紧邻下一步call47/48均执行C，其他三细胞均D；联合同时移动了其他后续full位置，因此两次未来节省不能唯一归因于某两次调用。全量每CFG增删集合、最早输入/solver输出差异保留在CPU原件，未补造缺失的误差向量/Jacobian。

追加第四臂没有改变原三臂视频结论：[三旧细胞输出复核](../reports/wc_w3_cfg_factorial_old_cell_output_reproduction_cpu_20261008.json)确认新BASE/CFG1/PAIRED与旧BASE/SINGLE/PAIRED的MP4摘要、固定Native、全部93帧损失和PTS完全相同。新四细胞仍以当前独立共享快照为因果对照，没有恢复旧跨运行完整状态验收。

## 下一同配额位置四组合的结构检查

[v5.8计划](../plans/WORLD_CACHE_CFG_BUDGET_MATCHED_WINDOW_20261008.md)和[新CPU登记](../manifests/wc_w3_cfg_budget_matched_cpu_preregistration_20261008.json)冻结旧已曝光BASE的全72动作；不根据新位置质量挑供体。只把各CFG最邻近的未来full提前：CFG0为45/47，CFG1为46/48，PAIRED同时两对，BASE不交换。

[不可变计划](../src/wcomr/rv0_cfg_budget_plan.py)及[CPU预检查](../scripts/check_wc_cfg_budget_plan_cpu.py) source38ff864已在执行前提交到GitHub，实际[结构回执](../reports/wc_w3_cfg_budget_matched_mask_structural_cpu_20261008.json)通过：

| 项目 | CPU实际结果 |
|---|---|
| 四细胞当前45/46 | C/C、D/C、C/D、D/D |
| 每细胞全轨迹CFG完整配额 | 18/17、总35 |
| 共同前缀与49–72动作 | 全部保持 |
| 70reset后71/72完整尾 | 保留原掩码完整调用 |
| 基于原完整历史逐步重建的来源年龄 | 四种结构均最多3步，≤32；保护尾初始化单列 |
| 无效模式/可变掩码/错误供体/保护尾/配额等破坏 | 11项全部拒绝 |
| GPU/CUDA | 新GPU0、未初始化CUDA |

这是不可变掩码、各CFG配额和**既有历史上的结构可行性**，不是实际模型路由、缓存有限性/显存可行性、GPU恢复或质量通过。完整真实执行仍须1父/10后缀/6新视频/1旧Native及全部重复、真实合法缓存和实际配额。下一完成新路由/完整采样集成与实际服务器生产CPU、冻结源/资产/评分和新增开销预测，fresh资源后唯一新身份运行。

当前新GPU selected=false、提交0；保留原整卡1.994372556h费用代理，新增集成开销仍待核对。最终完整预测≤2h且在50h余额内按既有约定自主执行；如果超过2h，只在全部必要CPU准备形成具体结果后询问该整卡例外，不缩或拆对照。原卡已完成，不能重启其GPU、CPU评分或部署身份。预算充足但不自动启动训练/稀疏/OMR或新增人评。
