> 2026-10-04 更新：原八输出卡已退出且完整审计通过，当前结果与费用以[103终态](103_WC_ONLINE_STAGE_RESULTS_AND_FAIR_BASELINE_NEXT.md)为准。以下准备/部分进度保持其历史身份。

# 在线阶段窗口与刷新频率：独立八输出执行卡

2026-10-04。承接[99 CPU与完整成本](99_WC_ONLINE_STAGE_CPU_AND_FAIR_FRONTIER_BUDGET.md)。基于用户持续自主实验目标和既有累计12 GPUh授权，选择独立 `WC-ONLINE-STAGE-R1-20261004-A` / `wc-online-stage-r1`，单次3600秒全费用、3570秒child、5秒强制退出余量。冻结source `3ad34e10475ab525190bf12a21f46ec8e525385c` 的实际部署与独立审计通过，fresh准入后已唯一提交GPU；不得复用104点或旧视频卡身份。

## 研究问题和完整矩阵

四组合曝光人物诊断显示早期两次S的保真损失大，晚期两次S未补偿。现在检验简单在线窗口能否避免主要损失，且是否保留实际速度收益。窗口23–27为CAL调参结果，不是独立确认或物理关键阶段结论。

- 首个CAL先官方WC / S关闭的阶段适配器严格D/D，两完整视频；九门、五状态检查点和全部pipeline一致才继续。
- common_sense_6487f37f-ef57-49ca-afdc-d898922b5191与human_199两个曝光CAL，各官方自适应WC、窗口内every1、窗口内every2，六测量视频。相同seed0、35请求/36实际solver步、72 CFG、93帧432×768/16fps、guidance7、共享eval及完整pipeline。
- 原生skip/Gamma/warp判定保持；只读当前solver step和过去同CFG窗口计数。窗口外官方full用D，官方cache照常；S仅在原本合法的eligible full、窗口23–27、固定23层使用，6/23/27 dense回退。没有未来trace、oracle mask、固定38deep或精确S配额；实际S可为0，最大每候选10/6。
- 每场景官方WC必须复现历史D SHA，在任何S候选前失败即止。不补选输入或更改窗口重跑。任何技术失败保留八分母、前序视频、源码和费用。

[配置](../configs/wc_online_stage_r1.json)/[自主选择记录](../manifests/wc_online_stage_r1_execution_20261004.json)冻结全部范围及历史D原件路径/SHA；核心28依赖仍与114.439秒实际CPU原件完全相同。新的[scope](../src/wcomr/stage_output_scope.py)、[运行入口](../scripts/run_wc_online_stage.py)、[监督器](../scripts/supervise_wc_online_stage.py)单独冻结，不覆盖旧卡。

## 费用、实际部署与提交门

[成本原件](../reports/wc_stage_frontier_cost_draft_20261004.json)在线卡完整3549.548941秒，含四S用full代理、两D/D、两WC、加载、首次kernel、选择/来源、prepare、decode/guardrail/write、20%包络和30秒退出。3519.548941规划包络加30秒≤3600；不按历史38deep的212秒作为速度保证。

[本地scope CPU](../reports/wc_online_stage_r1_scope_cpu_20261004.json)42项通过，拒绝改分母/输入/频率/窗口/回退、未来mask、真D污染、无条件复用、错误历史SHA、费用不足/非finite及在途账本。该结果不是GPU证据。

[实际部署](../reports/wc_online_stage_r1_deployment_20261004.json)/[独立原件审计](../reports/wc_online_stage_r1_deployment_audit_20261004.json)已通过：51份stage文件（50 payload加mid配置）SHA；原CPU回执SHA e05b…66cf、28依赖和5官方源、旧15/新10/策略4组绑定；新增实际scope42和官方prepare；实际原类meta网络默认1173→共享eval0、完整buffer库存；源码/模型资产/既有sm86 Sparge包CPU import；两个实际条件序列化SHA；历史两D原件长度/SHA；预算完全未变、CUDA未初始化、全局锁可获取。独立重新读取部署原件和现场stage bytes已通过；下一fresh指定UUID/sm86、VRAM≤1024MiB/no compute、15GB磁盘、f1锁、no-inflight、原12h剩余≥3615秒，仅提交一次。

当前累计9.136838727254782/12h、42jobs，余2.8631612727452183h，无inflight。3600秒预付须在原账本增加第43job，退出后用含失败/加载/flush/释放的实际wall替换；不重置旧费用。三后续草案上限不能共同准入，后序在本卡实费结算后重新算余额。

## 独立终态验证与下一决策

[结果审计器](../scripts/audit_wc_online_stage_receipts.py)重新计算D/D九门/五状态/pipeline，完整解码全部八视频；从真实事件/CFG/epoch/真D历史重建窗口与频率、来源和approximate引用，允许各臂自适应deep/cache数量变化，不强行配额或要求S必定发生。记录首次真实S费用，D/D诊断耗时不进入六部署测量。

[终态审计器](../scripts/audit_wc_online_stage_terminal.py)独立核对冻结源码、原PID退出、全局锁、账本单次预付替换、GPU监控及释放。[自动指标](../scripts/analyze_wc_online_stage_pairs_cpu.py)将全部四候选与自身场景WC比，保持不删负结果的四分母。单次固定顺序wall、SSIM/PSNR/RGB和temporal代理仅作CAL诊断，不接受稳定加速、Native保真、语义/物理或CONF。

有可用在线信号才继续完整Native/少步23请求/三WC阈值0.04/0.06/0.08/stage前沿与新独立CONF；它们目前未实现/接受或自动选卡。若保真损坏或必要开销抵消收益，保留负结果并审查23层S候选，优先简单对照，不先训练Trust/RV、不新增人评或付费评分。科学goal保持active。

## 唯一启动现场

[原启动](../reports/wc_online_stage_r1_launch_20261004.json)/[现场](../reports/wc_online_stage_r1_start_observation_20261004.json)：supervisor2758008/timeout2758025/runner2758027及stage命令行匹配，模型初始化、0/8视频；最初launch state null为启动瞬间，不能据此重提。预付3600秒后原账本10.136838727254782/12h、43jobs，已结算9.136838727254782h保持；child起算1791070999.1641538秒，3570秒child/kill5，终态实际替换预付。当前没有D/D、候选反馈或质量/速度验收；只跟踪原卡至终态后独立审计，不启动下一卡。

[现场1791071128.3485715](../reports/wc_online_stage_r1_live_observation_20261004.json)：同一三句柄仍live，模型加载63.174秒，第一官方D/D已过prompt guardrail且开始生成、0/8视频；预付未变，成对门和在线候选待完成。

## D/D独立通过，六在线测量待完成

[101独立证据](101_WC_ONLINE_STAGE_DD_AND_FEWER_STEP_CPU.md)：原九门/五状态1216组件/完整pipeline及关闭S的在线来源/native70独立通过，两93帧视频SHA复现历史common D、逐帧/temporal误差0、SSIM1，D/D原件独立归档。原卡2/8，六测量待完成，预算预付不变。另确认23请求官方CPU网格为24更新；完整Native/少步入口与真实管线仍缺，单次CAP与费用规划不变。
