# B36等待期准备：配对与报告布局

图表承接现也已完成：[导出交接](B36_FIGURE_READINESS_R1.md) · [最终双端各6项CPU接受](../../../../reports/cara_fast_B36_figures_CPU_acceptance_r2_20261029.json) · [749图面检查记录](../../../../research/749_CARA_B36_FIGURES_DUAL_CPU_AND_LAYOUT_20261029.md)。四组PNG/PDF和四CSV仅以显式CPU夹具验证，实际入口仍须重建完整B接受链；原52执行文件及4汇总文件保持。

**当前：完整汇总工具已通过双端各6项CPU控制。** [接受回执](../../../../reports/cara_fast_B36_analysis_CPU_acceptance_r1_20261029.json) · [748完整记录](../../../../research/748_CARA_B36_COMPLETE_RESULT_AGGREGATION_CPU_20261029.md)。下文静态布局保留原历史依赖描述；A32现已完整接受并冻结。B36仍需单独批准预计5.0215/硬5.5GPUh，本次没有派发GPU或计算B指标。

实际汇总入口 `scripts/analyze_cara_fast_b36_complete_r1.py` 只读取五个显式原件：`--capture`、`--settlement`、`--manifest`、`--score-capture`、`--accepted-scores`，并要求新的 `--output`。它重新验证完整B终态/结算/释放及32位置评分接受；运行、UNKNOWN、部分数据、混源或CPU夹具不能形成正式报告。原执行52文件与A冻结字节保持，本工具位于单独的分析代码中。

汇总覆盖32正式来源及6个登记重复。先在输入内平均正式与重复计时，再对输入等权；两个时钟分开，另列FIT仅原A计时的敏感性结果。所有93帧曲线、逐视频PSNR及未定义梯度状态保留，WC/RA继续标原FIT冻结的UNMATCHED；不增阈值、网格、选择或新输入主张。首次R24打包漏依赖失败保留，新R25双端各6项通过。

最新：[R2完整入口/账单CPU每端22项已接受](../../../../reports/cara_fast_B36_dispatch_CPU_acceptance_r2_20261029.json)，实际20资产摘要也通过，现等待 [B36单次GPU审批](B36_GPU_REVIEW_R2.md) 与fresh准入。原32评分位置及6对原评分引用不变；以下先前“入口待完成”为历史准备状态。

最新执行/收件增量见 [B36_EXECUTION_READINESS_R1.md](B36_EXECUTION_READINESS_R1.md)：双端CPU新增7+8项接受，原评分分母32保持，6个原A FIT配对引用已接受指标，原评分CLI只计算其余26对。单次派发和启动前失败收尾仍待完成，无B GPU提交。下文的布局生成发生在A32运行期间，实际冻结以已存在的原一次文件为准。

本清单只读冻结RUN_SPEC和Fidelity-v2，未读取A32运行产物或部分分数；没有GPU提交、参数选择、图表数据或科学结论。

[机器清单](B36_ANALYSIS_LAYOUT_R1.json)及 `scripts/prepare_cara_fast_b36_analysis_r1.py` 已核对32个逻辑正式位置，按4个输入×8角色一一配对到同输入的Native35。B36物理范围仍为6预热+24新正式+6重复，共36；正式表还引用A阶段的2个干净Native锚点及6个最终被选FIT校准产物。复用8个位置不增加独立样本。注册评分位置32个，其中4个Native自对照、28个非自对照；不改原评分分母。

## 等待期已完成

- 来源与分母：静态覆盖每个固定槽位、每个待冻结候选分支和Native参考；未将A阶段诊断时钟替换成干净锚点。
- 方法对照：F19_C与UNIFORM19_C均19D；F19_A1与F19_C使用同一个D mask。实际动作计数分别19D/0A/17C、19D/6A/11C；A1指登记的age-1规则，并非整条轨迹仅一次A。
- 报告布局：每输入8角色；T_DD速度与Alex保真图；独立T_request汇总；原93帧曲线、时序残差和梯度指标。沿用原主指标与补充指标，不新增否决阈值或显著性主张。
- 校准依赖：WC/RA/Native-k的6个FIT来源保留两个合法分支，待完整A32终态、12对CPU评分接受后，由原一次冻结文件解析；当前不选择候选。

## 仍需真实结果的工作

1. A32完整32条、三臂门、原件、释放和中央实际费用已经接受，实际2.2557055054700728GPUh。
2. 12对93帧CPU评分已经接受并一次冻结，见 [A32_FROZEN_BASELINES.json](A32_FROZEN_BASELINES.json)；Native22为MATCHED，WC_T006/RA_T1保留UNMATCHED。真实六原件也已通过承接验证，不补扫阈值或强称三个家族同时间。
3. [B36核心执行承接的双端CPU验证已接受](B36_CPU_HANDOFF_R1.md)；实际宿主执行准入、同一物理GPU的新鲜资源与独立授权仍后置。完整报价仍为A6000预计5.022GPUh、建议硬5.5；本布局不授予执行权限。
4. 完整B36后填充32位置的真实分数与双时钟，按原规则做每输入均值、输入等权和FIT的A阶段来源敏感性分析。两个CHECK属于原4个CAL内的留出角色，不升级为独立DEV或最终确认。

S/Q由另一对话负责，本次未改其源或派发其任务。当前A32的源、模型、阈值、预算和原自动检查保持。
