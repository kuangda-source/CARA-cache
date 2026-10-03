## 2026-10-03 r4实际CPU22通过，唯一104点补验已提交

[CPU/source/资产回执](reports/wc_mid_full_r4_deployment_20261003.json)实际Torch2.7.1+cu128的22项控制全部通过，含官方prepare OFF/ON与step13/18恢复后下一UniPC更新逐位一致；CUDA未初始化、账本未变。冻结部署source8c140469b217b96414e606a44ca17539fb3d202b。[唯一启动](reports/wc_mid_full_r4_launch_20261003.json)run wc-mid-full-r4，监督2647232/timeout2647303已现场存活；[启动观察](reports/wc_mid_full_r4_start_observation_20261003.json)未见compute冲突，原GPU24MiB，初始化非终态。GPU全cost≤1800秒/child1770秒，child起算最大截止北京时间13:25:03；预留0.5h只是账本在途值，实际尚未结算。旧已结算4.390463858430222h/31jobs保留，本run新增第32job，跟踪同一identity直到终态/审计，不重复提交。104点及九门尚待GPU验收，无视频/H0/H1/RV/训练结果。

## 2026-10-03 最新直接授权 — 独立104点r4条件补验

用户已在本执行对话直接授权七份WorldCache补验文件和CPU验证；全部门通过后，唯一 `wc-mid-full-r4` 全过程≤1800秒、计入现有累计12GPUh。[新卡](research/75_WC_FULL104_R4_CARD_AND_RESULTS.md)保留104QKV/312case、全部九门、共享官方输入/完整RNG、step13/18及原条件；旧卡/失败/费用保留，不自动H0/H1/RV/训练。七文件已写入，本地20CPU通过，实际UniPC控制仍须在Cosmos环境验收；未GPU提交。账本4.390463858430222/12h、31jobs不变。以下拒绝与旧时间门为历史。

## 2026-10-03 最新文档核对 — 完整104点成本与实施阻碍

[完整104点成本核对](research/74_WC_FULL_COVERAGE_COST_AND_BLOCKERS_20261003.md)：r3仅call25/26×layer2的2点技术门，r2全104点输入/状态控制失败仍不追认。独立补验需保留共享官方prepared-input、完整RNG及全部九门，step13/18和全26深层。两次实测推算全cost1198.90–1216.65秒，20%规划包络1459.98秒，超现1200秒/child1170秒准入；包络不是实跑必然超时证明。累计余7.609536141569778GPUh足够不代表单卡时间授权。

新实施文件写入被自动审批按本次可信docs-only指令拒绝；草案未入库/部署/实际CPU验证，未GPU提交，新增GPU成本0，已用4.390463858430222/12h、31jobs不变。待实施与时间门得到明确解决后才继续有效coverage→H0→H1；不自动延窗、开多窗、复跑r2或启动RV/训练。以下旧段为各时点历史快照。

# 最新终态（2026-10-03）

[独立r3最短前缀门](research/73_WC_MIDDLE_R3_PARITY_RESULTS.md)及费用/释放审计通过：共用官方prepared-input与全RNG，26次输入/条件/输出及step13的36状态组件完全一致，2QKV/6case完成。仅技术门，无视频质量或正式因果分叉结论；r1/r2原失败保留，不自动解锁H0/H1或r4。累计4.390463858430222/12GPUh，31jobs，余7.609536141569778h，无inflight，GPU/PIDs/锁已释放。

[WC-RV研究设计](research/68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)已按引用对话复核：归属W3，固定近似器下学习同状态、预算约束的有符号刷新收益；先空间/标签验证，再有依据的小Head。当前既有卡已按原范围完成，RV仍DESIGN_ONLY。以下旧状态为历史快照。

# WorldCache experiments

## 最新执行授权 — 2026-10-03

[各项目累计12GPUh与恢复后队列](research/BUDGET_AUTHORIZATION_20261003.md)取代此前仅文档及旧预算限制；保留已用与历史账目，单昂贵任务，GPU优先WC。WC已用3.9117525685110333GPUh、28jobs保持，当前余额8.088247431488967GPUh。先中间刷新/全26深层覆盖准备和无扰动诊断，再H0互补性、H1来源×寿命；W1/replay已完成不重跑，RV后置。旧new4h/clean50不自动转为新队列。新runner须按明确12h权威账本校验，不能重新执行硬编码4h的旧launch。 下述2026-10-02原包适配/仅文档条目为当时快照。

## 2026-10-02 原包适配 / 文档接续

[原文索引与编号/证据映射](docs/portfolio_20261002/ADAPTATION.md)、[本会话短接续](docs/portfolio_20261002/RESUME.md)。WC-S/H 中间刷新与全 26 深层覆盖准备 → H0 → H1；W1/W2 扩展暂停，RV 为条件 DESIGN_ONLY。 本次仅文档整理，未执行新任务或改变冻结协议、预算。原包完整保留，候选建议不覆盖已审计结果。

7 份原文与 ZIP 来源见 [source manifest](docs/portfolio_20261002/SOURCE_MANIFEST.json)；跨库导航见适配记录，活动计划/队列仍以本库入口为准。

视频世界模型质量—时间折中研究，当前主线为Cosmos-Predict2.5上的WorldCache计算压缩、稀疏刷新与缓存来源/寿命设计。

**仓库分工（2026-10-02）：本库只推进WorldCache。** OMR文档、独立队列与Wan/LongLive支持准备已迁至[omr-experiments](https://github.com/kuangda-source/omr-experiments)。当前WC-S/H冻结工作先完成，预算、运行配置和回执不变。拆分不启动或取消实验。

从[实验总览](EXPERIMENT_REPORT.md)开始，再阅读[当前状态](research/02_CURRENT_STATE.md)、[下一步](research/09_NEXT_ACTIONS.md)、[交接](memory/handoffs/LATEST.md)、[长程计划](plans/LONG_HORIZON_EXPERIMENT_PLAN_WorldCache_20260929.md)及[首批说明](plans/CODEX_FIRST_BATCH_WorldCache_20260929.md)。

当前方案v1.5（原v1.3执行顺序保持）：[WC-S计算压缩](research/55_WC_SPARSE_COMPUTE_COMPRESSION_DESIGN.md)与[WC-H来源/有效期](research/65_WC_HIERARCHICAL_PROVENANCE_LIFETIME_DESIGN.md)。当前冻结工作先完成，再考虑新增分组/寿命实验。

已审计[四组真实QKV结果](research/64_WC_S1_FACTORIAL_RESULTS.md)：两任务144case；sim0.1/cdf0.98中位操作加速1.286×、双筛查6/12，但layer27四输入均超5%误差。没有统一全输入配置或稀疏视频方法的质量—时间验收。下一步是准备中间刷新/全26深层覆盖诊断。

历史预算快照3.9117525685110333/4GPUh，余317.690753秒；非当前服务器准入。原new4GPUh/clean50提案仍待决定，仓库迁移不分配新额度。

CPU检查：

```sh
python3 -m venv .venv
.venv/bin/pip install -e . pytest
.venv/bin/python scripts/bootstrap_upstream.py
.venv/bin/python -m pytest -q
```

CPU测试只验证接口/实现。上游版本固定，vendor、权重、视频、环境和连接凭据不提交Git。`src/wcomr`及原仓库名称沿用历史标识以兼容部署；最新研究内容与队列只含WorldCache。

[仓库拆分记录](research/67_REPOSITORY_SPLIT_20261002.md)说明迁移范围和源提交；原Git历史保留。每次实质变更提交并推送私有库。

2026-10-02新增[WC-RV反事实刷新收益设计](research/68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)：归属W3，先同预算收益空间/标签可靠性，再有依据的小Head及闭环；仅设计，无采集/拟合/训练/GPU，当前WC-S/H工作先完成。
