# W3合成误差诊断：真实采样语义已核对，评分CPU通过

2026-10-09。上一goal turn完成原同配额GPU/终点评分/已有记录CPU与飞书更新，属于实际progress。本轮继续下一项机制区分，**核对了真实Cosmos指导与条件帧替换，完成评分代码和服务器CPU验证；尚未采集真实模型teacher向量。** 新GPU0，预算不变，整体goal active。

## 发现与价值

H-T44显示单槽供体强制C而原WC提议D，联合供体C/C与原提议一致；不能仅从摘要决定是否误差抵消。本轮从服务器实际模型源码确认：

- slot0调用conditional，slot1调用unconditional；实际速度合成为`cond_v + guidance * (cond_v - uncond_v)`。
- guidance7的实数系数为**8与−7**。实际FP32计算仍遵循原公式顺序，不能换成代数等价式后声称逐位相同。
- 网络输出经过denoise条件帧替换后才进入CFG与原求解器。条件帧预测为`noise − gt_frames`，因此raw net MSE与实际合成误差可能回答不同问题。

这个校正让下一实验明确测量真正送入采样器的有符号合成误差，避免用两个分支的独立MSE代替联合误差。几何上的正相关分支误差可能在负权重下抵消，单分支刷新也可能破坏这种抵消；这只是待测机制，不能从合成公式证明真实WorldCache已发生该机制。

## 本轮确实完成什么

[H-T45评分CPU登记](../manifests/wc_cfg_guided_teacher_metric_cpu_preregistration_20261009.json)与[完整下一卡设计](../plans/WORLD_CACHE_CFG_GUIDED_TEACHER_DIAGNOSTIC_20261009.md)及代码于a43e9ed提交/推送后，部署独立`.sync/wc-cfg-guided-teacher-metric-cpu-r1-20261009`，使用生产venv运行CPU-only检查。

[评分核心](../src/wcomr/cfg_teacher_metrics.py)保留四细胞实际输出，评价相对同状态DD的post-denoise guided MSE；另外记录CC分支有符号内积/cosine、8/−7交叉能量、float64解释和FP32合成舍入差异。检查另一分支上下文的输出是否相同，而不假设细胞因子化；零参考/零范数保持未定义，不用epsilon造排名。该评分模块用于GPU释放后的CPU原件评分，GPU collector只采集张量/动作/状态，不在活CUDA进程中运行此CPU-only scorer。

[服务器原回执](../reports/wc_cfg_guided_teacher_metric_cpu_r1_receipt_native_20261009.json)确认8项检查：

| 检查 | 实际CPU证据 |
| --- | --- |
| 同向误差抵消 | e0=7、e1=8、guidance7：CC合成MSE0，而DC/CD均3136 |
| 反向误差 | e0=1、e1=−1：CC MSE225，DC49、CD64 |
| 正交误差 | CC MSE56.5，交叉项0 |
| 真实上游闭包 | 从实际源码AST执行，guidance0/1/7的顺序与合成逐位相同 |
| 真实denoise替换 | 实际方法AST执行：raw条件帧100被替成6，非条件帧2保留 |
| raw与post-denoise区别 | 条件帧raw大误差不会直接进入替换后的guided误差 |
| 上下文不同 | 人为改变一支上下文输出后正确报告不因子化 |
| 无扰动 | CPU指标不改输入、无RNG消耗 |

另外6类无效输入全部拒绝：缺细胞、非finite、非FP32输出、形状不同、错误raw网络空间、非finite guidance。CPU实际**2.143983秒、PID3384693、exit0**，禁用CUDA初始化，运行后的全部源码SHA保持。

[独立核对](../reports/wc_cfg_guided_teacher_metric_cpu_r1_independent_audit_20261009.json)不导入指标/Torch，用stdlib重新计算同向、反向和正交三种有符号能量；直接范数与能量分解相符，并核对实际上游文件/部署载荷、CPU原回执原字节SHA、PID实际退出、预算原字节不变。

这些例子是数学/实现验证，不是实际模型结果、物理质量结果或方法加速。旧指标和所有旧正负结论保持，没有新局部阈值去否定W3。

## 下一完整采集与剩余工作

已冻结新诊断范围，未缩旧卡：两条完整父轨迹OFF/ON与两个完整视频用于无扰动控制；S22共享起点及四种当前动作生成的四个实际S23，共**5起点×4动作×2重复=40完整CFG速度对、80 net调用**。各S23内部比较CC/DC/CD/DD，不跨不同轨迹混为同状态。初始细胞首重复的同一guided结果用于原UniPC一步生成其S23，不增算替换状态。

每个短分支恢复自己的完整父快照，诊断结束恢复原S22，原父继续全部36更新/72调用与完整生成。保存实际post-denoise两分支、原闭包guided原件与动作/输入/条件/solver/历史；DD只是局部teacher定义。这张机制卡无完整反事实尾部或端点标签，不冒充旧完整四组合的缩减复验。

**仍需完成**：真实collector/短分支路由与closure绑定；5×4×2所有格及两父完整路径的集成CPU；异常/条件/solver/RNG/全部flag与完整状态回滚；真实生产导入/资源/geometry/显存；全成本保守预测和fresh资源准入。评分CPU通过不能代替这些项目，也不能报新GPU准备已完成。

累计仍**24.908110354/50GPUh**、余**25.091889646GPUh**，61个历史GPU记录、无本轮新提交。新卡selected=false，完整预测尚待核算；最终≤2GPUh在已有授权内自主，>2GPUh形成具体完整卡再确认，不删状态/重复挤进单次规则。

本轮完成新实现与实际服务器CPU/独立证据，是progress。下一继续collector和必要集成CPU，无需用户补充或人工评审；总体科研目标仍未完成，不调用complete/blocked，不重跑已消耗原同配额GPU身份或本次CPU身份。
