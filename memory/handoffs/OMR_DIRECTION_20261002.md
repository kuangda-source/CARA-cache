# OMR 独立对话接续

独立对话：**OMR 物理纠正研究**；thread ID `01a0fb1f-9751-7ff1-851a-59bdb4f413ef`；同一“世界模型加速实验”本地项目。

2026-10-02：用户要求当前对话只保留WorldCache，将OMR方向转入单独对话。项目仍共用既有研究仓库，分开的是对话范围与后续任务，不删除历史计划或结果，不重启/取消现有WorldCache工作。

## 新对话的研究范围

优先序列：J0资源与原版有效性/分组件成本 → J1均匀稀疏纠正 → J2未来目标侧梯度 → J3梯度复用；先单项有效，再考虑两项组合。adapter方向保真、执行器蒸馏、CFG-only底座纠正等仍为条件候选，不默认训练。

完整协议见[长程计划第8节](../../plans/LONG_HORIZON_EXPERIMENT_PLAN_WorldCache_OMR_20260929.md)，讨论来源为[调研两个研究方向](chatgpt-conversation://6aba8cd0-f4a8-83ee-adba-d4f960fb6dcb)。聊天建议是研究输入，论文数字不是本地复现。

## 已知准备与证据边界

- [OMR公开资源历史审计](../../research/33_L0_WAN_LONGLIVE_OMR_RESOURCE_AUDIT.md)：2026-10-01官方页仍Coming soon，未从该入口获得代码/配置/prompt IDs/官方adapter。该记录可能过时，首先实时核对公开资源；不要把未发布当方法失败。
- L0已准备Wan5B/LongLive-Plug适配器与独立环境。[两臂融合/原生导入证据](../../research/54_L0_ACTUAL_NATIVE_CPU_IMPORT_ACCEPTANCE.md)及[实验总览](../../EXPERIMENT_REPORT.md)须按回执区分CPU构建/融合/导入和完整模型/GPU/质量结果。它们不等于OMR已复现，也不证明Wan5B LoRA与WanA14B或CogVideoX的OMR adapter兼容。
- 当前没有本地OMR有效性、纠正效率或新方法质量结果。首先核对生成器/VAE/latent空间、adapter与predictor、窗口/mask、guidance band/强度、prompt与评分版本。

## 必须保留的实验控制

J1比较每允许步骤、每2步、每4步调用，分开原强度与累计强度/有限调参预算匹配；J2停止predictor上下文侧反向但保留前向及目标侧adapter梯度，检查方向/范数与真实开销，不称无损等价；J3比较相同真实梯度调用次数的J1，保存detached梯度，条件/模型/窗口变化reset，诊断真值不免费供部署触发。

原版资源与有效性通过后才做优化。评价保留语义/物理/Joint、修复与破坏样本、动作是否发生及运动是否下降；代理能量下降不是最终物理质量证明。不同模型上的缓存/纠正倍数不能直接相乘或相除。

## 对话分工与资源

WorldCache对话继续WC-S/H及WC-D条件设计，现有冻结范围先完成。OMR新对话初始仅恢复上下文、只读资源审计与整理缺口；不改WorldCache共享入口/队列/GOAL或运行文件，不启动GPU/训练/付费/人评，不发送作者邮件。

历史共用4GPUh账本文件快照3.9117525685110333h、余317.690753秒；不是新增OMR预算或实时GPU准入。后续OMR实验单独提议具体范围/成本，实际提交仍遵守全局单昂贵任务、GPU UUID/VRAM/进程准入与锁。不要改FRPC/共享驱动，不把两张卡视为单块连续96GB显存。连接配置只从本机已有受限记录恢复，不写入Git。

共享repo：`/Users/kuangda_gao/Documents/世界模型加速实验/worldcache_omr`；使用同一现有checkout，不创建worktree或复制权重。未来需要写OMR材料时使用OMR专属文件，与当前WorldCache工作隔离；按AGENTS提交同步，不覆盖无关改动。
