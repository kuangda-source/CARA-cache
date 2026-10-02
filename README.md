# WorldCache experiments

视频世界模型质量—时间折中研究，当前主线为Cosmos-Predict2.5上的WorldCache计算压缩、稀疏刷新与缓存来源/寿命设计。

**仓库分工（2026-10-02）：本库只推进WorldCache。** OMR文档、独立队列与Wan/LongLive支持准备已迁至[omr-experiments](https://github.com/kuangda-source/omr-experiments)。当前WC-S/H冻结工作先完成，预算、运行配置和回执不变。拆分不启动或取消实验。

从[实验总览](EXPERIMENT_REPORT.md)开始，再阅读[当前状态](research/02_CURRENT_STATE.md)、[下一步](research/09_NEXT_ACTIONS.md)、[交接](memory/handoffs/LATEST.md)、[长程计划](plans/LONG_HORIZON_EXPERIMENT_PLAN_WorldCache_20260929.md)及[首批说明](plans/CODEX_FIRST_BATCH_WorldCache_20260929.md)。

当前方案v1.3：[WC-S计算压缩](research/55_WC_SPARSE_COMPUTE_COMPRESSION_DESIGN.md)与[WC-H来源/有效期](research/65_WC_HIERARCHICAL_PROVENANCE_LIFETIME_DESIGN.md)。当前冻结工作先完成，再考虑新增分组/寿命实验。

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
