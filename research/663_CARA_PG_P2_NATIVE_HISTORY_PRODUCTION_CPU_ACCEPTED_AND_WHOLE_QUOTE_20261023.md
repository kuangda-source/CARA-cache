# PG-P2：历史失配与少步 Native 生产入口 CPU 接受、完整报价准备

2026-10-23，按用户要求在 PG-P1 运行期间推进。**已完成两模块生产入口、完整 CPU 验证、原件独立接受与整卡成本上界。PG-P1 原 GPU stage/source/配置和检查计划不变，新增 GPU 提交为 0。**

## 本次接受

| 项目 | 实测结果 |
|---|---|
| 冻结 CPU source | `0e80e5fc11dc429238b108cfe0269f71077d2bb4` |
| 独立 stage | `/data20t/gaokuangda/worldcache_workspace/.sync/cara-pg-p2-CPU-native-history-r4-20261023` |
| 注册 SHA | `8712b5534334574deb1289cd0cabc2968165540785f5743948a58da832d2b179` |
| 资源 | 固定镜像；无 GPU 设备；1 CPU / 4 GiB；离线；原 P1 stage 不改 |
| 实际退出 | 2026-10-23 21:31:07，容器 exit 0，无 OOM |
| 实际终态观察 | 21:32:03.080679；不按文件名回填时间 |
| 验证程序墙钟 | 138.374431 秒 |
| 数值采样 | 2 flow × 24 完整小张量路径 = **48** |
| 生产构造与 guardrail | 4 CAL × 18 请求步 = **72** 真实请求；72 个拒绝控制；真实 SetupArguments |
| 其他生产边界 | 实际 NLTK 分词；93 帧 writer、解码和 ffprobe；继承 FD 锁 |
| 本地检查 | **43** 项接口/顺序/缺失/纯计时/历史/接续控制通过 |
| 独立接受器 | 原件正控制 + **14** 种故障全部拒绝 |

原件：

- [R4 CPU 启动](../reports/cara_PG_P2_native_history_CPU_launch_r4_20261023.json)
- [R4 完整终态](../reports/cara_PG_P2_native_history_CPU_complete_r4_20261023.json)
- [R4 独立接受](../reports/cara_PG_P2_native_history_CPU_accepted_r4_20261023.json)
- [43 项本地控制](../reports/cara_PG_P2_preparation_local_CPU_checks_20261023.json)
- [14 种接受器故障](../reports/cara_PG_P2_independent_acceptor_fault_controls_20261023.json)

CPU 小张量路径保留固定真实采样器、UniPC、RF、WC 代码，使用显式小权重/简化 attention 与 decoder；生产 Native 的 class-forward 身份另有强制检查。未加载真实 Cosmos 生成权重，没有新增 GPU 质量或速度结果。

## 两个关键实现结论

**历史诊断不改变父轨迹。** 对 alpha=.5/1、两种 flow，影子开关前后所有36步 guided、最终 latent 与全部93帧 RGB 逐位相等；输入、solver、缓存/真实锚点、条件与 RNG 的前后指纹相等。只在登记的三个历史间隔组取最早合法点，额外 D 不写入部署锚点。每个窗口保存双分支 C/A_HALF/A_ONE（Phi）及共同 D；原件 SHA、输入/锚点身份和误差重算分别验证。A_ONE 对较早锚点逐位不变；零分母与常量秩不伪造比值/相关。

**少步 Native 确实走完整更新。** 18–35 各步数逐项核对真实调度器 timesteps/sigmas 和首末完整 Block 调用数。生产入口不用缓存安装器。计时块固定28参考路+56候选路、完整请求时间边界、轮换顺序；选择器不接受质量字段，不把拒绝/缺失位置删掉。±2% CAL 匹配后才冻结步数；匹配失败保留实测夹点或 NO_CAL_TIME_MATCH。

生产函数、请求适配器、保存/重读与后续命令见[详细接续方案](../plans/cara_policy_generator_20261020/P2_NATIVE_HISTORY_PRODUCTION_HANDOFF_R1_20261023.md)。

## 整卡报价及下一步

[完整未去重 P2 报价](../manifests/cara_PG_P2_whole518_planning_quote_r1_20261023.json)把 Native 计时84路、历史6路、同Q简单搜索64路、固定对照CAL24路、新DEV主表320路与warm20路合计 **518 路**；另计36 shadow D pairs、108 paired readouts、346组93帧LPIPS、最多1600个质量指标位置及加载/搜索/导出/收尾。

完整上界 forecast **67.878889 GPUh**、limit **78.5 GPUh**；其中90路 Native/历史子模块 forecast **11.408889**、limit **13.5 GPUh**，已包含在整体，不是另行派发授权。生成使用已接受 BANK24 最大完整请求，指标使用已接受 N10 逐维最大时间，并保留统一余量；不使用正在运行的 P1 部分结果估价。

原账本快照可用66.437172 GPUh，尚包括P1预留10.5及退役两卡16.5未知责任。完整未去重上界高于该余额。**P1完整接受后，按最终策略身份去重、原结算与新余额重算完整矩阵，才形成最终具体批准。**不缩原实验、不拆卡绕过≥12 GPUh规则、不自动增加累计226上限。

接续脚本 `prepare_cara_pg_p2_after_p1_r1.py` 已实现：重算 P1 原独立终态接受、P2 CPU 接受及各 SHA；绑定最终 CARA、原 SELECT 最强可行简单控制、首两CAL及原P1 shadow-OFF视频/latent。没有合法策略或可行控制就保持原结论，不从诊断结果择优。新 DEV 身份尚未选择。

待接续的是：P1完整终态 → 绑定最终P2角色/物理去重 → 完整P2监督、独占、评分、终态组合CPU → 最终整卡预算和资源准入。**本轮的 Native/历史生产入口 CPU 已接受；整个 P2 的全链路 GPU 派发接受尚未成立。**

## 历史保留

- R1：Native18–35已运行，历史 observer 在编译后才替换导致绑定失效，目标步缺分支特征，退出1；[原失败](../reports/cara_PG_P2_native_history_CPU_second_r1_20261023.json)。修复为观察回调先安装、再编译独立影子执行器。
- R2：两种flow共44条采样路径全部完成，退出0；[原完成](../reports/cara_PG_P2_native_history_CPU_complete_r2_20261023.json)。它不覆盖之后新增的请求适配器和独立原件重读，不冒充最终R4。
- R3：CPU文件限制器误将 Path.name 当完整路径，阻止合法分支原件重读，退出1；[原失败](../reports/cara_PG_P2_native_history_CPU_check_r3_20261023.json)。只修 CPU 路径识别，保持权重/CUDA/外部文件禁止。
- R4：完整48路径、实际构造/codec/FD入口和独立原件重读全部通过。中途文件名含 terminal 的回执仍以 `Running=true` 为准，[最终 complete 回执](../reports/cara_PG_P2_native_history_CPU_complete_r4_20261023.json)才是本次接受依据。

所有修复采用新 CPU stage；没有改正在运行的 P1，也没有重复已有 GPU 任务或触碰其他用户任务。
