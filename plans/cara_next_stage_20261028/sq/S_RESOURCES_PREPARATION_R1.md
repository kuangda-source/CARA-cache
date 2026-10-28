# S 完整状态资源清单准备

2026-10-29。旧 28.36398 GiB 是已知逻辑引用下限，遗漏 output/embedding、solver、buffers 等，不能作为实际 GPU/RAM 峰值或完整上限。[新清单组件](../../../src/wcomr/sq_s_resources_r1.py)把每条 tensor 引用、独立对象和完整底层 storage 分开，同时保留 NumPy 状态字节；只读取元数据，不扫描值、不复制张量、不触发设备传输。逻辑复制计数与现有生产 `SParentCollector.copy_budget` 的八组内容逐项对应，仍采用原 ×8 守卫。

[受限 CPU 范围](S_RESOURCES_CPU_R1.json)含六项单元控制，覆盖别名/view、meta 虚拟字节、完整字段、NumPy、超限拒绝和无隐式 finite/hash 扫描。在注册 2 CPU / 8 GiB / 1800 秒、GPU 隐藏/无网的独立 stage 中，解析原生产实验配置，仅在 meta 设备构造 `cfg.model.config.net`。要求28 Block、569个BF16参数对象及原共享 eval 模块拓扑一致；禁止 checkpoint 加载、完整真实模型前向和 pipeline 构造。实际 A32 精度原件作为范围内的来源绑定，meta 字节不表示已分配显存。

随后用已接受的 pinned sampler 与声明的 tiny 模型/decoder stand-in，对两个固定父策略、两种 flow 设置、每路径完整36步执行四条 CPU 路径。一个明确的 tiny 输入用于资源清单；每父/flow在全部27个目标步之前读取八组状态，总108个清单边界。它们不是两个真实 FIT 输入的108个标签，不建立新的 OFF/ON 或真实模型结果。数值采集器与物理矩阵源保持原版本；此 CPU 清单只增加被测元数据观察。

源先发布，两端先恢复已有同名句柄，原 stage 一旦存在只恢复。最终须独立核验原容器/CLI终态、完整字段与守卫计数、所有108边界、meta-only构造、原源/运行时、资源与错误回执拒绝；通过后据完整 schema 核算真实几何和资源 cap，再接整卡 GPU 生命周期、quote 和新的受影响组合 CPU。当前不授予 S/Q GPU 权限，不提供物理峰值、完整 S 报价或任何真实标签。

## R1 配置入口失败与 R2

原 R1 在 meta 网络构造前调用 `SetupArguments`，其前置验证会解析 checkpoint 路径，随后因缺少必填 `output_dir` 拒绝；原容器/日志/实际 CPU 成本保留，没有权重加载、真实模型前向或 GPU 动作。该失败不能解释为 S 方法失败。

[R2 范围](S_RESOURCES_CPU_R2.json)只从固定 `MODEL_KEYS/MODEL_CHECKPOINTS` 注册表读取 experiment，直接复用原配置注册器；不构造 `SetupArguments`，不访问 `.path`，并显式拒绝 Hugging Face 两类下载函数。新增 checkpoint.path 抛错而 experiment 仍正常读取的控制，共七项。四条 tiny 路径、108清单边界与资源不变；仅在同端原 R1 确定失败退出后使用新的 R2 stage，原 R1 不重派、不覆盖。
