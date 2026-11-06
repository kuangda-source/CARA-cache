# W3冻结Video2World条件与C/D联合CPU通过，完整GPU卡超现有余额

2026-10-04。上一goal轮只复核已完成104点，属于no progress；本轮新增实际条件来源/接口联合CPU、独立原件审计、完整因果范围费用与主要损失资源核查，属于progress。科学goal继续，完整RV0与后续同预算调度/独立确认保持，不缩成CPU或恢复控制。

## 实際完成的接口证据

[联合控制](../tests/check_rv0_video_actions_cpu.py)编译整个固定官方 `Video2WorldCondition` 类体，继承完整Base/Text类体，未换用V2或GR00T。原有35依赖SHA未改，新增两项共37；显式冻结实际子类文件，当前七个官方源码SHA在CPU执行前核对。整个类体保留，CP broadcast路径不执行；fixture DataType、构造条件值、网络/参数、prepare、decoder、writer仍是声明的Toy边界。

[R3实际CPU原件](../reports/wc_rv0_video_actions_cpu_r3_20261004.json)在实际Cosmos Torch2.7.1+cu128完成**329.270379秒**；[无Torch独立审计](../reports/wc_rv0_video_actions_cpu_audit_r3_20261004.json)重新读取服务器原件与37阶段文件/七上游源，绑定原件SHA `faee41188d3f350acf6ed9b0d33d4e809b58f0e1f5d01c67cedba32f8323924a`。两fixture场景common/human × flow OFF/ON × native-full/cache阈值控制，共8组；每组两个CFG槽位、每槽OFF1/OFF2/C_first/D_second/D_first/C_second，共**96条14更新/28CFG完整后缀**。

原WC与router OFF的全部72输入/输出/cache banks/最终latent/完整state/RNG/mock产物相等；当前C/D同输入、CFG1相同CFG0前缀、C当前deep0与D完整deep、C/C与D/D重复、交换顺序、原动作对应OFF、当前已付probe/同CFG历史真full、原官方分支副作用及父恢复通过。独立审计再核对全部96条的最终latent/完整state/28事件、动作与真实full历史及恢复后条件。缺history、改变eval、过期age共**20次TECH_BLOCKED**按原分母保留且父恢复，六类非法计划另拒绝。

真实类的 `set_video_condition`/`edit_for_inference` 也执行；gt_frames、视频mask、use_video_condition和其余tensor字段漂移、子分支额外属性均恢复，条件身份、值与frozen赋值拒绝行为保持。原R4未干预回归只在相同35文件及服务器原件SHA下复用，没有冒称本轮重跑。

这些是**完整官方类接口与单动作的CPU组合证据**，无权重、真实attention核、VAE视频或C/D GPU干预；不能以96后缀当96个真实场景或升级为收益/质量/加速结论。

## 实际导入的两处CPU适配及失败保留

[实际import检查](../scripts/check_wc_rv0_video_condition_import.py)加载固定来源模块和真实类，核对resolved origin/整个类AST、全部8个dataclass字段及frozen对象CPU恢复。源文件SHA `d58f515074237843b707d67001751c0e022546061348728e6322faaaa22e837c` 与112观察一致。R3 Python3.10的类AST摘要 `59e3528fca84aa6c0f3e33114cacf85f5f358ab28300c397645ef976e868b696` 与该版本fixture摘要相同；112的Python3.8 AST字符串摘要不同，不把跨Python AST dump摘要差异当源码变化，文件SHA才是共用固定源。

- [R1失败](../reports/wc_rv0_video_actions_cpu_r1_20261004.json)：关闭CUDA后Transformers的FlashAttention2可用性谓词为false，Reason1配置import assert失败，联合后缀未运行。原件4785…2691保留。
- [R2失败](../reports/wc_rv0_video_actions_cpu_r2_20261004.json)：已安装FlashAttention **2.6.3+cu128.torch27**；仅CPU进程改以安装元数据满足import可用性门后，上游UMT5构造函数默认值调用 `torch.cuda.current_device()`，被禁止初始化门正确拒绝，后缀未运行。原件f36a…4602保留。
- R3另身份：只在退出的CPU导入进程中，给上述默认值提供ordinal0；实际CUDA可用性没有伪造，`_lazy_init`始终拒绝、Triton benchmark/driver访问拒绝，没有实例化模型或执行kernel。导入后两适配均恢复。原官方文件、共享安装和GPU执行路径未改。真实GPU部署必须按真实设备原检查另验，不复用这两处CPU替代检查作为GPU准入。

## 完整下一卡范围与费用门

[范围合同](../src/wcomr/rv0_causal_scope.py)、[完整成本回执](../reports/wc_rv0_causal_scope_cost_20261004.json)、[26项范围/费用/预算拒绝控制](../reports/wc_rv0_causal_scope_cpu_20261004.json)：以下是待实施、未选/未预付/未提交的完整生产方案，CPU96项包含flow和极端阈值控制，与实际方案24条分母区别明确。

| 项目 | 保留范围与目的 |
|---|---|
| 场景 | 两曝光CAL，common原完整ID与human_199，原输入/seed0/93帧768×432/16fps/model/后端 |
| 父轨迹 | 每场景Native原入口、cache-off Native路径、原WC无router、WC router OFF带shadow；共8条36更新/72CFG |
| 当前动作 | step22双CFG后快照，step23 call45或46，分别干预一个CFG branch，probe2、WC0.06、dense近似器固定 |
| 后缀 | 每场景两个CFG各6条OFF重复、C/C、D/D及交换顺序，共24条14更新/28CFG；每次完整恢复父状态 |
| 输出 | 8父视频；重复动作先做latent/state等价，独立C和D各CFG各解码一次，共8分支视频，总16个编码输出 |
| Native兼容 | cache-off与匹配Native原入口逐输入/输出/solver/state/完整pipeline比较；router OFF与原WC完整比较，历史视频桥只作补充 |
| 合法性/失败 | 同CFG过去true-full与age≤32、保护/末尾不删；缺合法位置不补选，全部分母与拒绝保留；不缩场景/CFG/后缀/视频 |

当前标签口径仍为 **ONE_ACTION_ADAPTIVE_DIAGNOSTIC**：当前改变一分支，之后原自适应策略函数继续；未来full/cache mask和次数可不同。每条记录实际branch-full次数、真实完整后缀费用、两次重复与是否可行。计费动作单位是ONE_CFG_BRANCH_FULL_CALL，不能把两个分支一概当一次等成本刷新。

临时有符号保真诊断明确为 `RGB_MSE(V_C,V_Native)-RGB_MSE(V_D,V_Native)`，同一完整93帧解码/归一化到[0,1]，正值支持D、负值保留；PSNR/SSIM/时序指标并列，参考不是C/D互距。**它不是正式RV训练标签或物理优劣**，不能借此取代68要求的LPIPS主损失、正式预算匹配/λ口径。完整RV0之后仍需预算可行后缀、主要损失冻结、标签可靠性、强规则和独立CONF，Head不自动解锁。

计价绑定已审计R1恢复与fair原件的loading75.923秒、Native full max324.248秒、普通WC max217.791秒、diagnostic父减其两个子后缀后max272.251秒、未干预完整后缀max120.208秒；快照成本已包含在diagnostic父基数，不重复另加。8次分支decode/guardrail/encode各30秒与额外记账75秒是**未测规划余量**，不是GPU测量。合计代理5552.988秒，加20%规划余量及30秒退出，条件估算**6693.585秒**；拟单卡全cost硬cap6900/child6870/kill5，超时保留失败，不保证完整范围能在cap内完成。C/D改变未来full次数的成本与下一卡峰值仍UNKNOWN，112的未干预耗时不是C/D上界。

现权威账本**11.022315686839217/12GPUh、45jobs、无inflight**，余额**3519.663527秒**。完整拟议6900+15准入余量需6915秒，**短缺3395.336473秒≈0.943149GPUh**，预算合同明确拒绝。原4500及完成的3900/104身份均不可重提；本轮GPU新增/预留均0，不更改12h累计cap或历史已用。当前只是具体成本方案，不是已可运行或已获准的新生产GPU卡。

## 主要损失资源与下一步

[只读资源观察](../reports/wc_rv0_lpips_resource_observation_20261004.json)：实际Cosmos环境没有已安装lpips包，torchvision0.22.1+cu128存在；明确默认缓存内AlexNet244,408,911 bytes/SHA `7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02`存在。本次只核对包元数据和一个指定缓存路径，没有全盘查找/权重加载/安装/下载/评分，也不把这里的缺包扩大为全服务器资源缺失或正式质量负结果。

下一仍可CPU准备完整生产执行器、Native/cache-off等价与分支解码/失败分母、固定LPIPS版本/权重/帧协议及CPU资源验证，再用最新账本审查完整GPU卡。先把实现和评价做成可审查结果，再处理资源决定；不为凑余额降完整目标，不新增人工评审、付费评分或训练。真实C/D GPU、正式有符号RV标签、预算匹配调度和独立确认仍0/未完成；107稀疏净收益未成立判断保持。
