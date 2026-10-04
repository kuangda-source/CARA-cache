# 公平十四输出独立执行卡：原生、少步、三WC阈值与阶段候选

2026-10-04。承接[104完整CPU接口](104_WC_FAIR_NATIVE_FEWER_STEP_FULL_CPU_INTERFACE.md)和[103在线候选终态](103_WC_ONLINE_STAGE_RESULTS_AND_FAIR_BASELINE_NEXT.md)。依现有自主推进目标与累计12GPUh授权，选择独立 `WC-FAIR-CAL-R1-20261004-A` / `wc-fair-cal-r1`；**本地准备通过，尚未实际部署或GPU提交/预付**。原104点≤1800秒单次授权已完成，本卡不重用该身份、上限或授权。

## 保留完整对照

先strict WC D/D两个输出，再同两个曝光CAL（common_sense_6487…、human_199）各六点，共十四输出。每场景顺序：Native35、Native23、WC0.04、WC0.06、WC0.08、stage every1。模型、seed0、guidance7、93帧432×768/16fps、条件、共享eval、精度/offload/guardrail保持；Native23仅改请求步数，WC三点仅改rel_l1阈值。实际更新为36/24/36/36/36/36，CFG为72/48/72/72/72/72。

Native必须绑定固定原生类 `MinimalV1LVGDiT.forward`，执行其继承的 `MiniTrainDIT.forward`；生成前清空WC状态后恢复Native方法，生成期间关闭WC，不能用WC负阈值冒充Native。真实GPU加载后记录两个原方法的实际源文件与SHA，Native所有deep调用必须实际执行。CPU直接参考相等已成立，单独未加观察器的GPU parity仍未成立，本卡不追加隐藏GPU分支来声称它。

stage候选为CAL选定every1，WC0.06/去噪步窗口23–27，23个允许层，6/23/27 dense回退，sim0.1/cdf0.98/noPV。继承本步原生cache/full判断，使用过去同CFG计数与两true-D历史；没有未来mask、固定deep计数或S配额。近似源不会进入true-D历史，窗口外可能继续读取原生残差预测中的近似来源。

D/D九门、五检查点及完整pipeline先通过，WC0.06必须复现历史两份编码视频，桥失败在stage前止步；生成/写入/网格/来源异常保留十四分母与所有已完成产物，不补选输入或删失失败配置。每臂真实prepare一次、恢复共同RNG/初始buffer/开关/阈值/forward与hooks，普通generate入口完整返回。

## 完整费用与准入

[原成本草案](../reports/wc_stage_frontier_cost_draft_20261004.json)：2 D/D、10 full代理与2 light代理，不按Native23步数线性折扣。加载95.916秒、bookkeeping75秒、1.2余量和30秒释放后，规划6298.155406638秒，单卡全wall上限6300秒、child6270秒、kill5秒。费用包含导入、加载、逐臂初始化、生成、失败、哈希、flush和释放；子阶段host wall不是独立CUDA延迟。

当前已结算9.691073425147268/12GPUh、43jobs，余8312.135669秒。6300+15秒余额门可单独容纳；fair6300+后续CONF拟3000+15不能共同准入，超1002.864331秒。仅选择此fair卡，CONF之后按实际结算退款重新核算；不删强基线、改CONF或重置预算。实际准入以服务器实时账本为准。

[范围与费用门](../src/wcomr/fair_output_scope.py)、[运行器](../scripts/run_wc_fair_cal.py)、[监督器](../scripts/supervise_wc_fair_cal.py)、[配置](../configs/wc_fair_cal_r1.json)、[执行记录](../manifests/wc_fair_cal_r1_execution_20261004.json)。独立输出路径与launch原件，单提交、共享f1锁、无inflight、fresh UUID/sm86/≤1024MiB/no compute进程、至少15GB磁盘；预付6300秒，终态按实际单GPU完整wall替换，历史43jobs和用量不变。

## 本地验证和实际部署门

[本地报告](../reports/wc_fair_cal_scope_cpu_20261004.json)：48项scope/cost/预算拒绝控制、22项Native24/36/原方法/管线/十指标分母控制通过。55个stage文件（含配置），其中当前30依赖逐SHA绑定[实际r3原件](../reports/wc_fair_sampling_cpu_r3_20261004.json)与[独立原件审计](../reports/wc_fair_sampling_cpu_audit_20261004.json)，七官方源保持。不重复跑已绑定核心，不追认旧版本。

GPU前还须source提交/同步并在独立deploy1核验：服务器r3原件SHA、当前30依赖/七官方源、actual新scope/审计CPU、prepare OFF/ON、native-meta默认1173→共同eval0/buffers、两Native方法实际origin、source/assets/package/import、两输入条件SHA与历史两WC实体视频、预算未变/无CUDA；部署原件逐SHA独立审计后，再fresh资源/锁/预算准入，只提交一次。

## 结果审计与科学边界

[十四输出审计](../scripts/audit_wc_fair_cal_receipts.py)保留全部点，分别核验Native36/24更新及72/48真实deep，WC各自网格/native70及阈值干预，stage来源/窗口/逐CFG计数/实际核，十四mp4的SHA、93帧/16fps和完整解码。[终态审计](../scripts/audit_wc_fair_cal_terminal.py)核验冻结stage/payload/原PID退出/全wall账本替换/锁与GPU释放。D/D观察器耗时不进入候选速度比较。

[自动CPU指标](../scripts/analyze_wc_fair_cal_pairs_cpu.py)固定Native35为每场景参考，对Native23、三WC点、stage共十组计算完整93帧RGB/lumaSSIM/motion/temporal92差分，不能只报有利组合。单次顺序wall只作描述性成本；编码保真不是语义/物理接受。两个曝光CAL不能充当CONF、独立泛化或稳定速度证据。

先用完整强基线判断stage是否值得深化，再安排独立CONF或RV/小Head。当前未有新视频/公平前沿结果，不训练、付费评分或新增人工评审，科学goal active。

## 实际部署已通过，待fresh准入

冻结GPU源 `1a22ac6ef5c31c3cf15998ee868d96fcc6ba6b54`。[实际部署](../reports/wc_fair_cal_r1_deployment_20261004.json)在新的deploy1完成8项入口/准备/模式/来源门、48 scope/22审计控制；r3原件14组、当前30依赖/七官方源逐SHA绑定通过。两个实际Native原方法源与CPU绑定一致，native-meta默认1173→eval0，prepare OFF/ON、资产/guardrail/package/import、两个真实条件及两历史WC实体视频均通过；CUDA未初始化、账本未变。[独立复核](../reports/wc_fair_cal_r1_deployment_audit_20261004.json)逐SHA核验55个stage文件与服务器部署原件。磁盘空闲564.233GB。

仍9.691073425147268/12h、43jobs无inflight，新增GPU提交/预付0。仅下一fresh GPU UUID/sm86/VRAM/apps、f1锁、无inflight/原12h余额和磁盘后wc-fair-cal-r1单次提交；实际GPU D/D、Native/十四输出和指标待验证。旧104/其他原卡不重提。
