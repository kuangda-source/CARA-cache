# P1结果接口与P2公平对照准备

## P1 输出如何直接进入分析

`scripts/analyze_cara_policy_calibration_r1.py --input <accepted-export.json> --output <new-analysis.json>` 读取一个已通过原验收器的完整端点导出。它不再次运行模型或评分，不替代原件验收。CAL_FIT和CAL_SELECT分别分析；最终策略身份在读取SELECT前冻结。当前没有实际P1结果。

导出结构：

| 字段 | 约定 |
|---|---|
| evidence_kind | ACCEPTED_ENDPOINT_EXPORT；单元测试只能为SYNTHETIC_UNIT_FIXTURE |
| source_bindings | 原导出和独立接受原件的ref/sha256列表；CLI逐件复核 |
| split / members | CAL_FIT或CAL_SELECT；完整[prompt,seed]位置列表 |
| profile_identity / timing_protocol | 与原实际端点逐行一致 |
| candidates | fingerprint、roles、phase(INITIAL/REFINEMENT)、predicted_seconds、proxy_loss、discrete_cost_units；包含失败或未到达候选 |
| records | 原choose_observed行格式：fingerprint/prompt/seed/split/status/LPIPS/measured_seconds/profile_identity/timing_protocol/endpoint_basis |
| budget_seconds / shared_seconds / quantum_seconds | 当前同profile Native冻结后的B、公共耗时与原0.25秒离散精度 |
| finalists_frozen_before_scores | SELECT必须为true，对应已提交的策略身份清单 |
| cost_events | 物理event_id唯一，kind及actual_GPUh；不把预留当实费 |
| query_ledger | 每计划fingerprint唯一、origin、status、physical_execution_ids；拒绝/失败消耗尝试，NOT_REACHED保留 |
| query_limit / calibration_limit_GPUh | 原完整卡Q与已批校准上限 |

费用分类为LOAD_GUARD、NATIVE、PROPOSAL、WARM_BRIDGE、FIT、SELECT、SCORE_POST、FAILURE_EXIT。费用事件须由原完整账单拆解且核对总额；函数只汇总已提供项，因此不自行宣称费用覆盖完整。共享采集的完整成本和后续复用的新增成本应分别给出，不能仅展示候选推理成本。

输出包含所有注册候选的完整/缺失位置、场景等权LPIPS与时间、最差prompt、超过min(C,A)+0.01的最大量、连续预测/离散保守时间/实际残差、含并列秩的代理-终点Spearman、首批到最终的可行质量增量、物理费用和逻辑查询。实际选择继续调用原 `choose_observed`，不存在第二套择优逻辑。缺失控制时尾部基准为空，不从候选优劣倒推出阈值。

## P2 准备的对照

`src/wcomr/policy_generator_r1/comparison_preparation.py`提供：

1. **强前密C/A**：复用原prefix/periodic控制，在共同B和实际动作成本下选取。
2. **Refresh-only**：只优化D边界，内部读取固定为全C或全区间A(alpha=1)，区分边界优化与修正覆盖联合选择的增量。
3. **Pure proxy**：在读取任何真实候选端点前固定代理池的最优策略，衡量真实端点修订带来的增量。
4. **同Q简单搜索**：原两强前密槽＋固定salt哈希排序的最多6个合法prefix/periodic C/A计划；只读成本，不读代理或端点。与CARA共用Q=8、CAL身份、B、实测选择规则；重复控制占原槽，不补免费候选。

物理相同计划可去重执行，但每个方法看到的信息仍计入该方法查询账。简单搜索不是全合法空间的均匀随机搜索；论文按其实际prefix/periodic族描述。P2尚未冻结完整物理矩阵或报价，不改变P1原4+4自适应卡，也不把准备接口算作已完成消融。

## 方法正文用伪代码

```text
GeneratePolicy(adapter, sampler, hardware, CAL_FIT, CAL_SELECT, B, Q=8):
    profile <- validate supported causal grammar and execution profile
    table, prices <- collect complete guided-output statistics and action costs
    graph <- legal intervals with measured cost and calibrated proposal loss
    pool <- budgeted graph planning under conservative discrete time B
    initial <- [front_dense_C, front_dense_A, graph_min, graph_diverse]
    fit0 <- evaluate registered initial plans on CAL_FIT
    neighbors <- at most 4 joint boundary/readout variants of 2 incumbents
    fit1 <- evaluate one frozen refinement batch, preserving Q and full cost cap
    finalists <- freeze 2 feasible plans plus the 2 fixed controls
    select <- evaluate finalists once on CAL_SELECT
    policy <- lowest prompt-equal loss satisfying measured B and tail ceiling
    return freeze(policy, profile, provenance, full calibration cost)
```

方法论主线：从校准数据与真实成本共同生成刷新位置和修正区间；完整轨迹上的有限端点反馈修订局部代理的排序，输出可复现、可部署的共享策略。最终贡献由同实际时间、可比校准成本下相对强简单对照的增量，以及冻结策略在独立输入上的表现承接。

## 已有机制图

`paper/figures/cara_window24_mechanism_r1_20261022/`提供PDF、SVG、PNG和原件SHA。来自Window24全部四个CAL场景，不筛样。三臂同25D和刷新位置：连续A3相对C的场景等权LPIPS降低26.6335%，相对A1降低19.7690%。不把单次开发计时写成稳定加速。

建议英文图注：**Correction coverage matters at fixed refresh locations.** With the same 25 dense updates, continuous correction improves endpoint fidelity over both cache reuse and a single correction in all four calibration scenes. Bars report full-video LPIPS against Native; Mean weights scenes equally (93 frames per video, seed 0). Mean reductions are 26.6% versus C and 19.8% versus A1.
