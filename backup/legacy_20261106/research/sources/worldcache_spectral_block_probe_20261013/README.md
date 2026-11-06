# WorldCache：频域调度与部分 Block 轻量探索

日期：2026-10-13。

本包包含理论推导、约6GPUh的拟议筛查计划、Codex接续与可运行的CPU代数检查。

1. `01_MATHEMATICAL_ANALYSIS.md`：FFT/加权度量、Wiener适用条件、相位/时间滤波陷阱、残差保持、fresh/stale K/V误差、复杂度与显存。
2. `02_LIGHTWEIGHT_EXPERIMENTS.md`：共享状态、强对照、阶段预算、小视频桥接、合入条件。
3. `03_CODEX_HANDOFF.md`：接续提示词和权限边界。
4. `math_sanity_checks.py`、`math_sanity_results.json`：已执行的CPU合成代数检查，只用NumPy，非真实模型/速度证据。

运行：`python math_sanity_checks.py`。

当前没有启动GPU、没有改仓库，没有改变E2或用户暂缓的P参考卡。文献事实与新推导在01中分开注明。
