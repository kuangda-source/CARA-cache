# S 完整状态资源清单准备

2026-10-29。旧 28.36398 GiB 是已知逻辑引用下限，遗漏 output/embedding、solver、buffers 等，不能作为实际 GPU/RAM 峰值或完整上限。[新清单组件](../../../src/wcomr/sq_s_resources_r1.py)把每条 tensor 引用、独立对象和完整底层 storage 分开，同时保留 NumPy 状态字节；只读取元数据，不扫描值、不复制张量、不触发设备传输。逻辑复制计数与现有生产 `SParentCollector.copy_budget` 的八组内容逐项对应，仍采用原 ×8 守卫。

[受限 CPU 范围](S_RESOURCES_CPU_R1.json)含六项单元控制，覆盖别名/view、meta 虚拟字节、完整字段、NumPy、超限拒绝和无隐式 finite/hash 扫描。在注册 2 CPU / 8 GiB / 1800 秒、GPU 隐藏/无网的独立 stage 中，解析原生产实验配置，仅在 meta 设备构造 `cfg.model.config.net`。要求28 Block、569个BF16参数对象及原共享 eval 模块拓扑一致；禁止 checkpoint 加载、完整真实模型前向和 pipeline 构造。实际 A32 精度原件作为范围内的来源绑定，meta 字节不表示已分配显存。

随后用已接受的 pinned sampler 与声明的 tiny 模型/decoder stand-in，对两个固定父策略、两种 flow 设置、每路径完整36步执行四条 CPU 路径。一个明确的 tiny 输入用于资源清单；每父/flow在全部27个目标步之前读取八组状态，总108个清单边界。它们不是两个真实 FIT 输入的108个标签，不建立新的 OFF/ON 或真实模型结果。数值采集器与物理矩阵源保持原版本；此 CPU 清单只增加被测元数据观察。

源先发布，两端先恢复已有同名句柄，原 stage 一旦存在只恢复。最终须独立核验原容器/CLI终态、完整字段与守卫计数、所有108边界、meta-only构造、原源/运行时、资源与错误回执拒绝；通过后据完整 schema 核算真实几何和资源 cap，再接整卡 GPU 生命周期、quote 和新的受影响组合 CPU。当前不授予 S/Q GPU 权限，不提供物理峰值、完整 S 报价或任何真实标签。

## R1 配置入口失败与 R2

原 R1 在 meta 网络构造前调用 `SetupArguments`，其前置验证会解析 checkpoint 路径，随后因缺少必填 `output_dir` 拒绝；原容器/日志/实际 CPU 成本保留，没有权重加载、真实模型前向或 GPU 动作。该失败不能解释为 S 方法失败。

[R2 范围](S_RESOURCES_CPU_R2.json)只从固定 `MODEL_KEYS/MODEL_CHECKPOINTS` 注册表读取 experiment，直接复用原配置注册器；不构造 `SetupArguments`，不访问 `.path`，并显式拒绝 Hugging Face 两类下载函数。新增 checkpoint.path 抛错而 experiment 仍正常读取的控制，共七项。四条 tiny 路径、108清单边界与资源不变；仅在同端原 R1 确定失败退出后使用新的 R2 stage，原 R1 不重派、不覆盖。

## R2 的 TE 默认设备拒绝与 R3

A6000 R2 原容器已退出1：实际 TE RMSNorm 的 `canonicalize_device(None)` 直接取 CUDA，不服从外围 `torch.device('meta')`；CUDA拒绝守卫在初始化前抛错。原 TE 源支持显式 `device=meta` 并推迟参数初始化，故 R3 只在 meta 网络构造期间向同一个原 RMSNorm 构造器传该参数，保留原 class/body，不以 torch 层替代 TE。构造次数直接对照原H0的113个同类模块（含顶层时间嵌入 norm），完整拓扑仍须一致；完成后恢复原构造器，再开始 tiny 采样。

[R3 范围](S_RESOURCES_CPU_R3.json)增加构造器恢复与禁止真实设备控制，共八项；原CPU资源和四路径/108边界不变。R1双端、R2两卡端的原失败、句柄与成本保留；Ada没有启动R2，不为重复一个已定位的构造拒绝而补派。最终资源证据仅接受原容器/CLI已完整退出的 R3 源，当前仍无 S GPU 权限。

## R3 参数重置拒绝与 R4

R3 到达原网络 `init_weights`，TE 的原 `reset_parameters` 对 meta weight 仍调用 `canonicalize_device(None)`，再次被 CUDA 拒绝守卫阻断。R4 在明确 meta context 内，将同一个原 resolver 的 None 参数显式改为 meta 后执行原函数；constructor、reset、resolver 的原函数体与模块 class 均保留，两个适配在 tiny 采样前恢复。记录原 TE constructor/operation/resolver 源 SHA，原完整H0拓扑与569个BF16参数要求保持。

[R4 范围](S_RESOURCES_CPU_R4.json)增加 resolver 的上下文/真实设备拒绝/原函数恢复控制，共九项。所有旧失败与原费用保留，每端只在自己的 R3 确定退出后启动新 R4；GPU、权重值和真实模型前向继续禁止。

## R4 的 PyTorch 2.7 上下文读取差异与 R5

R4 的九项控制发现固定 Linux PyTorch 2.7.1 与本地 2.8 的 API 差异：2.7 的 `get_default_device()` 不反映外围 `torch.device('meta')`。新 R5 用零元素 factory 的实际设备验证 meta context，没有底层 storage 分配或数值读取；同一个原 TE resolver 与恢复机制保持。九项控制移到重型原生 import 之前，避免已知单元拒绝仍消耗后续 import 时间，并记录单元通过和 full2B meta 通过两个 CPU 阶段。

[R5 范围](S_RESOURCES_CPU_R5.json)保留四条 tiny 路径、108 清单边界和原资源。各端必须先核验自己的 R4 原容器及 CLI 已失败退出，保留原失败与费用后才启动新 stage。旧 R1–R4 不重派、源不变；本地单元通过不能替代固定 Linux 运行时的实测接受。
