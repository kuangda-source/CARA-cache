# P1新增入口Linux CPU完整接受与本地图表

新增分析、原FIT一次冻结、临时中央结算、RPC和容器/worker入口的23项Linux CPU控制已完整接受。当前本地图表另通过3项实际渲染和视觉检查，35处选定核心源码与旧接受记录一致。P1真实视频、整卡GPU入口组合与执行批准仍待。

[Linux接受](../reports/cara_v1_P1_entry_delta_CPU_accepted_r2_20261102.json) · [原证明](../reports/cara_v1_P1_entry_delta_CPU_original_proof_r2_20261102.json) · [原完整捕获](../reports/cara_v1_P1_entry_delta_CPU_capture_r2_20261102.json) · [关闭](../reports/cara_v1_P1_entry_delta_CPU_complete_cleanup_r2_20261102.json)

## Linux原件

源`4d4a00bec85af8b2382ff0b53c1a324ed25e85b1`，registration`562f1b2f07845cc04a75c21d35fe4197ad889a56ea28e3d56eb229c02c53e2ea`。两卡原宿主CPU于08:34:03.764620开始、08:34:13.997727正常结束，约10.23秒；CPU26/27、AS4GiB、上限1200秒、GPU隐藏。完整回读证明原进程退出、源码/runtime未改。

| 控制 | 数量 | 覆盖 |
|---|---:|---|
| 完整52分析与原FIT一次冻结 | 5 | 原终态、不可覆盖输入封存、新鲜liveness变化不改冻结、科学字段/源改变拒绝 |
| 临时账本结算 | 5 | 唯一全段实耗、写账中断恢复、原收据失败不收费、失败/超限及旧责任 |
| 模拟RPC | 5 | 许可前拒绝、未授权不接触SSH/凭证、146分母仅运维计数、UNKNOWN不重派、fresh资源调用 |
| 容器与worker入口 | 8 | 精确40GiB/64GiB与原worker、原guardian、CUDA隐藏、源/命令和旧卡拒绝 |

中央/硬件/Docker分配均为显式CPU元数据模拟，没有访问四卡、GPU或真实账本，没有计算新指标。原3项本地图表控制按当时固定源复用。`p1-cpu`和`p1-cpu-2`检查均已删除，不再恢复本原件刷新状态。

[853](853_CARA_P1_POST_DOCKER_ACCEPTED_AND_PRODUCTION_REPORT_RPC_PREPARATION_20261102.md)原两个合成对的真实评分Docker和当前生产serve分支接受保持，原32对指标不重算。原R1因Linux缺Matplotlib在创建stage前拒绝、原传输意图及更早本地回执类型拒绝均保留。生产模型/评分Python未修改。

## 图表源与旧组件复用

当前本地图表改为13角色逐行对齐的LPIPS、T_DD和完整请求时间，解决相同时延/质量别名导致点标签重叠。全部93帧曲线、原CSV与原指标保持。三项实际PNG/PDF/CSV、重复原件验证和拒绝控制通过，两组图面已查看；详见[当前图表CPU](../reports/cara_v1_P1_local_figure_CPU_r2_20261102.json)与[视觉QA](../reports/cara_v1_P1_local_figure_visual_QA_r2_20261102.json)。这份新图表源由独立本机回执覆盖，未写入原Linux stage，也未由原Linux测过。

[35处源码审计](../reports/cara_v1_P1_selected_core_source_reuse_audit_r1_20261102.json)核对五组原接受回执/证明字节，以及算法、实际FIT core、guardian、释放/评分/分析core和外层/serve源，全部原SHA一致；没有重放旧实验。这份选定源码复用审计不能单独替代整卡CPU组合。

## 接下来

[完整单卡审阅草案](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_SINGLE_CARD_REVIEW_DRAFT_R1.md)说明146语义/最多142物理、64标签、19D/22D各三估值top3、同实际校准费用LPIPS搜索、最终52质量位置，以及保守18.0273GPUh/建议硬19。硬限尚未绑定，250秒/标签仍是预算假设。

后续只补整卡原证据组合、生产绘图交付后端、正式profile/报价与新私有64GiB存储/源包。全部具体可审阅后，再提交完整>4GPUh及本新卡中央读取/预约/实际结算许可。当前没有这些新权限，也没有真实V1标签或方法收益。四卡维护限制、cap226、旧16.5责任、旧冻结与最终16/备用16保持。
