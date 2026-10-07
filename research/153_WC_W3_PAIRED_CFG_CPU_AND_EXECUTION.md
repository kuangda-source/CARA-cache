# H-T38 同状态联合CFG区分：接口、CPU与后续执行

2026-10-08，依据[152条件分析及信号可用性更正](152_WC_W3_D46_EXISTING_CONDITION_CPU_RESULTS.md)，继续有限W3区分。新[设计](../plans/WORLD_CACHE_PAIRED_CFG_REFRESH_20261008.md)和[登记](../manifests/wc_w3_paired_cfg_preregistration_20261008.json)在新实验前冻结：seed2、step23，原C/C、单槽C/D和联合D/D；1新WC父、8完整后缀、5新视频、1旧匹配Native、两主要signed比较。原正负例、no-op、失败和费用均保留。

## 新接口已经写好，实际CPU尚待

[动作接口](../src/wcomr/rv0_paired_cfg_actions.py)复用已验证OneActionRouter的原forward AST、同CFG真实历史/有限性/付费probe/年龄检查，只允许step23的OFF、D46或D45+D46；当前调用之外使用各自原生自适应。旧OneAction和D46源未改。

[完整核心](../src/wcomr/rv0_paired_cfg_causal.py)在step22/call44共享完整快照，原完整采样loop复用；三臂的call45和46模型输入一致，联合D45之后pre46缓存状态可合法变化。[审计](../src/wcomr/rv0_paired_cfg_evaluation.py)验证四组严格重复、前状态/输入、两动作实际deep执行、原策略后缀、70reset和71/72D、完整终态组件、5新编码和历史BASE/SINGLE字节桥。不把双动作报单动作RV标签。

[CPU夹具](../tests/check_rv0_paired_cfg_cpu.py)将使用冻结真实sampler/WorldCache AST和Video2World条件类、CPU Toy模型，执行四个成功父/32后缀/20mock，覆盖当前原C/C和D/D no-op；第二次动作失败、联合分支writer/guardrail失败均需恢复原完整状态和方法。18类双重复证据破坏及历史bridge破坏都要被拒绝。模拟输出不是真视频或GPU可行性证明。

[CPU载荷清单](../manifests/wc_w3_paired_cfg_core_cpu_r1_20261008.json)绑定7项新载荷和已完成D46 R3的233项有效合并源载荷；独立CPU目录，只在现有SSH上传并执行CPU。此段记录首次准备状态，实际CPU结果见下。

完整保守预测1.660984884GPUh，≤2且在余2.872700413h内，按用户自主约定。累计21.127299587/24h、58jobs/noinflight保持。实际受影响CPU、生产缓存/完整延迟依赖/source/assets、绑定配置和fresh资源/锁/费用准入通过后才能唯一提交；不重启D46旧身份、不删控制或恢复旧秒数deadline。

## 核心实际CPU及独立原件审计通过

冻结source `4565685d92e6611cf296b94dc98fa03825471b1f`，独立目录 `.sync/wc-w3-paired-cfg-core-cpu-r1-20261008`。服务器实际夹具209.409041秒，监督全CPU耗时212.026552秒，exit0、CUDA未初始化、GPU提交0；原supervisor3283484/child3283485已确认退出。

四个成功父轨迹、32条完整后缀、20个模拟输出以及每父四组严格重复全部通过。原C/C下分别实际形成C/C、C/D和D/D，联合操作合法改变pre46缓存；原D/D下保持no-op。第二次动作、writer和guardrail故障均恢复完整父状态与方法。独立读取原始记录重建76次证据破坏拒绝，没有仅依赖汇总标签。

7项新载荷及233项继承载荷，在原目录、独立复制目录和执行前后SHA均一致；六份压缩原字节、退出句柄和费用也已验收。根账本SHA保持，累计21.127299587/24GPUh、58jobs、无在途，余额2.872700413h。见[终态原件捕获](../reports/wc_w3_paired_cfg_core_cpu_r1_20261008_terminal_capture.json)、[独立原始重建](../reports/wc_w3_paired_cfg_core_cpu_r1_independent_audit_20261008.json)和[实际启动身份](../reports/wc_w3_paired_cfg_core_cpu_r1_launch_20261008.json)。

本结果证明冻结真实sampler/WorldCache AST在CPU Toy上可以执行和恢复；不证明真实权重、GPU可行性、历史真实视频桥或终点质量。下一步继续生产入口、源码资产/延迟导入、监督与评分绑定的必要CPU验收，再进行fresh GPU/锁/预算准入。已完成核心CPU身份消耗，不重跑、不改通过核心。

## 真实生产入口与评分资源CPU通过

生产source `aa996edf2d8fc3eb99018fac916a63034c5f53d5`，独立 `.sync/wc-w3-paired-cfg-production-cpu-r1-20261008`，两步均exit0，81.801384秒。实际项目缓存与Blocklist、原请求解析、真实联合核心的延迟导入与早期拒绝、27项同包传递依赖闭包和8项范围破坏拒绝通过。原CPU核心没有重跑或修改。

冻结评分源、LPIPS/AlexNet权重、完整93帧协议及CPU模型实例化通过，评分视频0；这属于评分准备，真实三损失与两signed比较尚未生成。255项完整载荷执行前后原字节不变，三个原CPU句柄3284697/3284698/3284930均退出，根账本SHA不变。见[实际生产CPU独立审计](../reports/wc_w3_paired_cfg_production_cpu_r1_independent_audit_20261008.json)和[原字节捕获](../reports/wc_w3_paired_cfg_production_cpu_r1_terminal_capture_20261008.json)。

已写[选定配置](../configs/wc_w3_paired_cfg_selected_r1_20261008.json)，只选择目标UUID并绑定实际CPU回执；冻结科学范围、源和完整预测1.660984884GPUh不变。下一步独立selected目录/同源回执核对及fresh资源、共享锁、完整预算唯一提交。尚无联合CFG的真实GPU、历史真实状态桥或终点结果。

## 真实唯一GPU已启动

selected实际CPU绑定13.944609秒通过；冻结255源和实际生产回执不变。fresh目标A6000启动前24MiB/noapps、共享锁、无在途、预算余额与完整1.660984884h预测通过。source `aa996edf2d8fc3eb99018fac916a63034c5f53d5`，run `wc-w3-paired-cfg-r1`，原supervisor3285362/runner3285375已实际CLI、UUID和共享锁核对，24514MiB初始化；不是终点收益。

[唯一GPU启动](../reports/wc_w3_paired_cfg_gpu_r1_launch_20261008.json)、[现场核对](../reports/wc_w3_paired_cfg_gpu_r1_live_start_20261008.json)。[CPU后处理原句柄](../reports/wc_w3_paired_cfg_post_cpu_r1_launch_20261008.json) driver3285718绑定两个原GPU PID/source/config，仅成功退出/释放后按冻结源完成六视频全93审计、三Native损失和两signed比较，当前零评分。

服务器第59job在途预留余额至24h，不是全部花完；启动前已结算21.127299587/24h、58jobs，实际全wall包含加载/失败/恢复/哈希/编码/释放费用，结束退回差额。旧秒数限制不恢复；不重提本卡、不改在跑源、不增加训练、稀疏或人评；goal active。

### 原父已进入真实采样

现场原runner模型加载110.619200秒；同一seed2提示词guardrail通过，实际原WC采样已到3/36。仍跟踪原GPU3285362/3285375及等待CPU3285718/source aa996ed；后缀干预、重复/真实历史桥、视频和终点评分尚待。父行只在检查点保存，磁盘receipt中inputs仍为空不表示没有执行；实际采样进度由原run.log确认。

## 现场输入签名差异：原判据保留，完整生成继续

在第22步现场原件中，44次调用只有命名参数 `gt_frames` 的hash与旧seed2不同，其余输入以及输出、deep、banks和solver轨迹均一致；[现场原字节](../reports/wc_w3_paired_cfg_parent_prefix_native_20261008.json.gz)与[严格前缀判据失败](../reports/wc_w3_paired_cfg_parent_prefix_bridge_cpu_20261008.json)保留。差异来源尚未唯一确定，不宣称编码器随机性或质量损害。

冻结严格历史验证器要求全部输入相同，原GPU因此可能在完整生成后被该门拒绝，不能改在跑源或把旧失败改成功。既定1父/8后缀/5视频继续完成，GPU/PID/source、预算和范围均不变。独立[CPU下一轮登记](../manifests/wc_w3_paired_inactive_gt_cpu_preregistration_20261008.json)在联合臂终点质量尚未曝光前，检验text2world零条件帧是否使有限gt_frames失去计算作用。只有实际源码/零mask数值证明、其他全部输入及完整状态/历史编码/重复都一致后，才允许单独标记CPU条件化取证分析；任何其他差异仍拒绝，不覆盖原GPU门的失败。当前没有联合刷新收益。

## 零掩码语义CPU已通过，基准编码一致

source `4545d878d91fed6a1138cd39908655215b94ca4d`，独立 `.sync/wc-w3-inactive-gt-semantics-cpu-r1-20261008`，实际CPU14.493696秒/监督15.209570秒/exit0。冻结实际denoise和条件类AST下，16种零mask组合的预测和有效网络输入一致，4种非零mask正对照能检测到GT影响；非有限GT仍拒绝。实际记录mask的hash与全尺寸float32零张量 `[1,1,24,54,96]` 一致，T2W条件帧属性为0；冻结WorldCache forward的额外kwargs仅读取timestep_scale，没有读取gt_frames。

见[独立CPU原件重建](../reports/wc_w3_inactive_gt_semantics_cpu_r1_independent_audit_20261008.json)及[终态捕获](../reports/wc_w3_inactive_gt_semantics_cpu_r1_terminal_capture_20261008.json)。两个原CPU句柄3291534/3291535已退出，255份在跑GPU载荷未改，GPU新增0。该证明使用实际AST和Toy网络，不能替代完整GPU历史审计或质量评分。

原OFF1和BASE_first视频均已接受编码，SHA与旧seed2 BASE逐字节相同。当前原GPU仍在完整后缀生成，单槽/联合输出和严格重复、终态、三损失/两比较尚待。只在所有其他历史输入、输出、状态、缓存、solver和BASE/SINGLE编码均通过时，才执行单独H-T39 CPU条件化取证评分；原严格失败原件与判据保持，不重新生成GPU，不将条件化证据改称原卡严格验收。

独立[154取证入口与规则](154_WC_INACTIVE_GT_CONDITIONAL_CPU_FORENSICS.md)已实现。新规则27项破坏拒绝和“只修复单槽不胜BASE”夹具通过，不重跑旧CPU；实际评分只等待原完整生成和原拒绝终态，保持先PAIRED对BASE、后PAIRED对SINGLE的解释顺序。
