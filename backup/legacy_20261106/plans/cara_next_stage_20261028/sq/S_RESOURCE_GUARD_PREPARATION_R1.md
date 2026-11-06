# S 目标事务的 snapshot 前资源入口

**最新：原完整物理矩阵的资源入口已双端接受。** 每端13项控制、216次目标检查、280文件重读及11类伪回执拒绝通过，原容器/CLI均退出0。[双端接受](../../../reports/cara_sq_s_resource_guard_dual_cpu_accepted_r1_20261029.json)。A6000矩阵18路径另计两条源准备，Ada20路径；真实S标签和GPU提交为0。完整GPU runner/生命周期仍需单独组合接受。

2026-10-29。[原双端完整清单](../../../reports/cara_sq_s_resources_dual_cpu_accepted_r5_20261029.json)已接受，本项只验证新增资源入口的受影响组合。原数值采集器、固定父轨迹、物理矩阵与存储源码保持；原full2B meta架构和默认93帧合成MP4解码控制按原SHA复用，不重派未改动组件。

新 `ResourceCheckedRequests` 复用原完整 `Requests`。仅在单个请求内，将原 `execute` 的同一 bytecode 的 `SParentCollector` 绑定到新增子类，且异常时恢复原模块入口。目标事务调用 `copy_budget` 时，先检查完整八组元数据、native/solver字段、buffer名称、每条tensor的shape/dtype/grad、逻辑字节、每组完整backing storage和NumPy字节，再调用原逻辑计数器；两者必须逐值相同后才进入原来源捕获和snapshot。该边界是目标诊断事务，整体pipeline加载/初始复位仍属于后续GPU卡资源与生命周期。

[CPU contract](S_RESOURCE_GUARD_CPU_CONTRACT_R1.json)只接受已接受tiny几何，保持原128MiB逻辑限额，另设128MiB backing复制守卫和16MiB CPU live backing；buffer/NumPy额外字节为0。十三项本地控制覆盖完整清单、字节篡改、未知字段、view的大backing、各限额、meta拒绝、shape/dtype/grad、字段集合、原计数器前置顺序、拒绝时不进入复制、异常恢复和CPU/真实范围隔离。

[前瞻真实contract](S_RESOURCE_GUARD_REAL_CONTRACT_R1.json)绑定同一2B/旧B1真实几何及原七个buffer。逻辑与各组backing复制守卫各64GiB，live backing上限为CPU2GiB/CUDA8GiB，buffer上限712字节。源保留BF16参数及Wan FP32策略；资源schema允许原浮点缓存/输出的BF16或FP32，时间嵌入、条件、solver保持各自登记dtype。这些是未来入口的拒绝限额，不是实测物理峰值，不构成整卡GPU接受；模型加载、临时激活、raw sink等总RAM/VRAM与整卡quote仍须另行绑定。禁止在超限后调高、改精度、offload或重启原卡。

[新受限CPU范围](S_RESOURCE_GUARD_CPU_R1.json)每端仍为2CPU/8GiB/1800秒、GPU隐藏、无网、原件只读和独立stage可写。两种flow完整覆盖原物理矩阵：A6000共18条矩阵路径加两条单列的checkpoint绑定OFF源准备；Ada共20条新路径。每端216次目标资源检查、原八raw/24去重锚点/108行每flow、280文件重读、四组完整OFF/ON每flow保持；仅允许本stage的tiny checkpoint/输出重读，Cosmos权重和下载禁止。

源码先发布，双端先恢复同名句柄，存在stage只恢复。预测A6000约180秒、Ada约900秒；启动后按实际原allocation起点安排半程及终态检查，正文PASS时仍等待原容器与CLI完整退出后独立验收。新GPU提交、账本写入、真实S标签与视频均为0；Q1继续独立待授权。
