# RA 减半阈值 R2：完整方法区分实验与 CPU 准备

2026-10-10。接续[214完整视频结果](214_WC_RA_COMPLETE_VIDEO_FIDELITY_AND_COST_RESULTS_20261010.md)：简单共同刷新出现5.04%／0.51%终点保真改善；首RA工作点完整调用降到24／24，但LPIPS退化23.83%／23.35%。下一轮检验工作点是否过于激进，保留三模块统一方法开发和全部旧结果。

此前[有限修订登记](../manifests/wc_ra_conservative_half_threshold_r2_design_preregistration_20261010.json)已转为独立R2生产入口：[完整计划](../plans/WORLD_CACHE_RA_FULL_VIDEO_COMPARISON_R2_20261010.md)、[八路径注册](../manifests/wc_ra_comparison_r2_preregistration_20261010.json)及[229源配置](../configs/wc_ra_comparison_production_r2_20261010.json)。唯一参数变化为τ×0.5＝0.070744235098772；原校准八区间中位0.141488470197544必须实际重构，再显式缩放。新阈值利用R1视频结果选择，是开发修订，不声称质量无关校准或独立确认。

完整Common/Human seed3 × WC／JOINT_NATIVE／RA，加两普通Native参考，共八路径、八视频槽、288求解器更新、576调用、六全93帧配对，每路径一次；同条件／噪声／保护／表／求解器，保留同轮对照并核对跨轮确定性。[完整成本预测](../reports/wc_ra_comparison_r2_complete_cost_forecast_20261010.json)仍采用旧最慢完整路径与慢加载包络，加复制／写出／清理／20%整卡余量，3.173496962GPUh≤4。不会用RA24full的快路径压低预算，不删参考或分拆。

[源码派生记录](../reports/wc_ra_comparison_r2_source_derivation_20261010.json)核验12原源码保持；完整采样／参考／共同执行核逐字复用，既有32完整Toy路径证据保持。新合同、CPU/GPU监督、审计、转移／选择／启动／原件捕获为独立R2；22拒绝含新增缩放／原阈值／开发依据字段。[本地注册CPU](../reports/wc_ra_comparison_r2_local_contract_cpu_20261010.json)已通过22拒绝和完整源SHA，真实服务器资产／表重构CPU尚待。没有GPU提交、账本写入、视频或方法收益。

本地准备最初引用不存在的joint_sampling文件名，导致缺少源码记录；已通过rg定位实际joint_execution和joint_control，保留失败信息及初次已写成本／注册的原SHA，显式未完成恢复核验其全部字段和原时间戳，不替换原字节。本地尝试表重构因无Torch未执行，保持失败，不用mock替代；改用现有服务器固定环境的真实CPU入口。

现场账本实费32.03426413020637／77.89524658965853、剩余45.86098245945216GPUh、69提交、无登记在途。下一新源Git同步→原生产CPU及原件验收→同源选定CPU→现场锁／UUID／进程／预算／盘空间→唯一完整GPU→全向量与全视频审计／全帧LPIPS。无非必要人评。若本工作点无助，检查目标与年龄覆盖并推进guided-W1／部分刷新，不追加无限阈值格点。
