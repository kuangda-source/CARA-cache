# 早期×晚期缺失两臂：独立六输出执行卡

## 唯一提交，原三个现场句柄存活

[唯一launch](../reports/wc_timing_factorial_human_r1_launch_20261004.json)/[现场](../reports/wc_timing_factorial_human_r1_start_observation_20261004.json)：冻结source `a86050cf9536a4431f9e77b711f54ab0a13feadf` 的新deploy1在全部实际门及fresh准入后只提交一次。原supervisor2745653、timeout2747134、runner2747136及完整命令行匹配。现场1791065578.144057已加载83.400秒，第一官方D/D控制在采样，0/6视频；九门/历史legacy SD复现及E0L0/E1L1视频均待验证。首次launch state null由原现场句柄补证，不再次提交。

原12h已结算8.67188491753794h/41历史jobs保持；2400秒预付后在途9.338551584204605h/42jobs，可用未预留2.661448415795395h。child1791065421.844791起算2370秒/kill5，全cost2400秒最大北京时间06:50:21.844791，终态按实际wall结算。只跟踪原三个句柄/源码和六分母，不改运行stage、不自动下一卡、训练或新增人评。新只读指标入口已准备，实际DD/完整视频审计与指标尚未运行。以下为历史部署状态。



## 实际部署与独立原件通过，尚未GPU提交

[部署回执](../reports/wc_timing_factorial_human_r1_deployment_20261004.json)/[独立原件审计](../reports/wc_timing_factorial_human_r1_deployment_audit_20261004.json)：冻结source `a86050cf9536a4431f9e77b711f54ab0a13feadf` 的79payload+mid共80文件在新deploy1验证，服务器原件SHA与本地完全对应。当前实际CPU原件42依赖及5份官方源保持；实际scope52、原teacher/selective/forecast回执及四物理视频/来源图/草案、官方prepare OFF/ON、native-meta eval0/buffers、资产/包/import和人物条件均通过，CUDA未初始化、原预算不变。

[独立审计器CPU](../reports/wc_timing_factorial_auditor_cpu_20261004.json)12控制以原历史legacy真实来源记录验证native最后两来源、CFG/年龄/真D隔离/实际算子和窗口/reset拒绝，以及pre-core失败六分母；不是构造新两臂GPU产物。独立结果审计器已声明11/9/13逐臂配额、26/1/16近似读取cache和26/2/17来源读数、精确位置，真实D/D/六视频还待新卡。

下一仅fresh UUID/sm86/VRAM/compute/锁/no-inflight/原12h余额/磁盘后唯一提交；目前8.67188491753794/12h、41jobs无预付。以下为选择卡时的历史准备状态。



2026-10-04。承接[95 真实位置结果](95_WC_FORECAST_PLACEMENT_RESULTS_AND_TIMING_FACTORIAL_NEXT.md)及[96 当前源 CPU 验证](96_WC_EARLY_LATE_FACTORIAL_INTERFACE_AND_CPU.md)，依既有自主研究 goal 和累计 12 GPUh 选择独立 `WC-TIMING-FACTORIAL-HUMAN-R1-20261004-A` / `wc-timing-factorial-human-r1`。[清单](../manifests/wc_timing_factorial_human_r1_execution_20261004.json)、[配置](../configs/wc_timing_factorial_human_r1.json)。当前 GPU 未提交、无预付；原 104 点及 forecast 六输出已终态，不重用单次身份。

只使用已曝光 human_199 / seed0、原模型/condition和入口 RNG，固定原 38-deep / 34-cache、35请求 / 36实际solver / 72CFG、93帧768×432/16fps、probe2、warm14/native70及尾 dense。仍为23个稀疏层、6/23/27 dense、sim0.1/cdf0.98/no-PV。

先官方 D / fixed D 严格控制，再轻量 fixed D / legacy SD / E0L0 / E1L1，六输出全分母。D/D 九门和完整 pipeline 必须先通过，三份 D 产物必须相同且复现历史 SHA；legacy SD 必须复现历史 SHA 和逐 CFG6/5配额，才进入两新臂。每臂一次真实 prepare；失败保留已有产物和六分母，不替换源、不补跑。

| 新测量臂 | 逐 CFG 显式序号 | S次数 / 算子 | 历史CPU来源图中读取S的cache |
|---|---|---|---|
| legacy SD | 每 CFG 首次后隔一次 | 11 / 253 | 26 |
| E0L0 | 4,5,6,7,8 / 4,5,6,7 | 9 / 207 | 1 |
| E1L1 | 1,4,5,6,7,8,9 / 1,4,5,6,7,8 | 13 / 299 | 16 |

四组合中的 E1L0 / E0L1 使用上一轮已实测的首次匹配 / 自由位置产物。新 [scope](../src/wcomr/timing_factorial_scope.py)必须现场绑定旧配置原 SHA、teacher与selective原件、forecast终态原件 f6fb…11c，以及物理 D/legacy/first/free 四视频 SHA。原 [factorial草案](../manifests/wc_timing_factorial_draft_20261004.json) c40e…ebbc 的未执行历史标记保留。旧两臂逐来源 replay必须与实际原件一致，新两臂 policy 和来源图必须与不可变草案一致；这些检查不预测缺失臂的视频。

[当前实际 CPU](../reports/wc_timing_factorial_sampling_cpu_r1_20261004.json)/[独立源审计](../reports/wc_timing_factorial_sampling_cpu_audit_20261004.json)的42份依赖继续逐一匹配：旧14/8、新8、入口拒绝25及纯策略4组已通过，生产核心不再变动。新增 [scope CPU](../reports/wc_timing_factorial_scope_cpu_20261004.json)56项含4源码解析控制，通过六分母/不同逐臂配额/非等成本角色、旧两臂物理SHA、完整成本和权威12h账本拒绝。下一实际部署须再次绑定CPU原件与对应stage/官方源，并完成新scope、实际 mask/video、prepare OFF/ON、native-meta共享eval/buffers、资产/package/import和人物序列化条件验证；CUDA禁用，不把这些门报成GPU结果。

[完整成本](../reports/wc_timing_factorial_cost_proposal_20261004.json)：保留历史保守 D/D381.751、轻量235.768、加载95.916和bookkeeping75秒。E1L1对整个轻量测量代理额外乘13/11至278.635秒，E0L0不折扣；这只是成本余量，不假定运行时间与S次数线性。两D/D+四完整轻量+加载/首次核/选择来源/decoder/guardrail/write/失败/flush，20%包络再加30秒释放结算，完整 **2334.428796秒**。独立全cost上限 **2400秒**、child2370秒/kill5，不删输出挤入旧1800。

现累计 **8.67188491753794/12GPUh，41jobs**，余 **3.3281150824620607h**，无inflight；若fresh准入后提交，2400秒预付会使在途账本为9.338551584204607h / 42jobs，终态按实际全wall替换预付。新 [runner](../scripts/run_wc_timing_factorial.py)调用已验证核心；[监督器](../scripts/supervise_wc_timing_factorial.py)使用全局f1锁、指定UUID/sm86/VRAM/compute、余额/磁盘门和独立在途键。源码冻结并同步、全部实际部署门和fresh准入后，只提交一次；当前没有扣费或新GPU执行。

终态独立审计六视频完整93帧解码、共同掩码、实际11/9/13与253/207/299、精确位置/真D隔离/最后两原生来源窗口/native70，旧SHA和源码/费用/PIDs/锁/GPU释放，再对同一个官方WC参考计算PSNR/SSIM/temporal/帧差及四臂有符号条件效应与交互。D/D诊断wall不进入轻量速度比较；旧两臂跨run耗时与新单次测量不接受稳定加速。9/11/11/13不是等成本前沿，完整传播效应不是独立即时/cache误差、线上策略或预算匹配RV标签。Native/少步/调过WC、CONF与语义物理质量仍缺。无训练、扩样或新人工评审，科学goal active。
