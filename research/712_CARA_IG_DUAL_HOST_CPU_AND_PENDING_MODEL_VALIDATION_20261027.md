# 创新量增益：双服务器CPU兼容完成，真实模型验证待执行

用户要求将IG-Scalar/IG-Band作为独立新方向抓紧验证，得到结果后决定是否并主线；追加要求两卡与四卡都可用，并指出两卡可能空闲。采用同一科学源码、A6000 SM86和RTX 6000 Ada SM89两个运行配置，本轮优先核查两卡。附件原文归档，不把其中的“文档自身不授权”覆盖用户当前执行意图。

已实现固定2×2真实空间网格投影、共享CFG增益、actual-guided四角/中点矩、prompt留一拟合、固定λ=.05、唯一真D锚点流式存储及保存后端点重放。固定D闭环各候选自由运行，不使用shadow teacher；复用已付C输出，非C读出额外支付一对head。原V2.2和DEV128源码/配置字节核对不变。

## 验证与边界

[双端接受回执](../reports/cara_IG_dual_host_CPU_acceptance_r2_20261027.json)绑定源码`4a295b6d`及两个独立Docker阶段。每端容器退出0、无GPU设备请求、CUDA未初始化、全部payload/runtime哈希一致；8项单元/源绑定检查、8条完整采集CPU路径、6个故障边界、20条候选自由运行CPU路径通过。正常采集跨两flow共24状态；含故障尝试36状态、72次保存输入FULL/DEEP端点重放。真实冻结InferenceArguments参加入口控制；权重、注意力、准备/解码仍为明确CPU替身。

完整36更新控制中，C与原父轨迹相同；IG0/FULL、IG1/DEEP的所有guided更新及最终latent相同，真实D写入位置与每步head调用数符合登记。以上是实现证据，不是Cosmos质量或加速结果。失败R1原件保留：一次CPU条件类注册表作用域问题、一次新闭环工厂重复传runtime参数；修复后通过，没有GPU重跑。

## 实际资源与准入

[最新两卡只读检查](../reports/cara_IG_two_card_idle_followup_20261027.json)：两张A6000无计算进程，显存约391/24MiB；宿主80逻辑核、约50.6GiB可用内存。原DEV128后评分活进程只用CPU0–1，新卡配置建议CPU2–3并在启动前重新验证。空闲状态不是预约。

[原任务准入回执](../reports/cara_IG_predecessor_admission_readonly_20261027.json)确认原GPU子进程已退出0、GPU释放验证通过、CPU后评分仍活跃且无post-exit。中央DEV128责任仍为RESERVED_OR_RUNNING，旧通用preflight会将其列为活动任务。后续新卡应以原GPU释放/账单/设备句柄证明区分CPU评分与GPU占用，并保留其预算责任，不提前结算、不改旧任务或全局账本来绕过检查。本轮未读取其部分科学指标。

## 完整范围与尚缺

[范围登记](../manifests/cara_IG_scope_intake_r1_20261027.json)和[双端配置](../manifests/cara_IG_dual_host_profiles_r1_20261027.json)保持整轮合并规划上限7GPUh、累计226、原16.5未知责任，以及12/10h确认/迁移规划。B1相对附件84增加24个保存输入FULL/DEEP控制，共108次guided adapter重放；当前隔离adapter还重新执行C，所以按216对head计，不少报成本。部署入口复用已付C，另报真实完整请求时钟。

B2仍拟46完整路径，最多一次B3修订10路径且不越整轮上限；没有预约、没有GPU提交。**尚缺真实形状/峰值显存/写出上界绑定、完整报价、GPU生命周期与新卡准入、真实模型B1及条件B2完整视频与原质量守卫。** 不能据本页决定IG有效或并入主线，也不能把两端CPU通过称为两端CUDA已验证。原E1相关未变组件可复用，新变更单独接受，避免重造既有监督/评分系统。
