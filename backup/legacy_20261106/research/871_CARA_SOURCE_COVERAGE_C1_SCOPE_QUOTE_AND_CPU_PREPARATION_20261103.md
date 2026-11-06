# 871 C1：同配额来源消融、终点搜索与整卡准备

2026-11-03，用户要求准备下一步。**下一张 C1 用同8候选的来源消融、同3候选的阶段消融，检验来源覆盖能否提高终点校准效率。** 19D、22D 同程序生成；完整方案见 [C1 review](../plans/cara_next_stage_20261103/source_coverage/c1/C1_REVIEW_R1.md)。

## 研究设计

main8 与 single8 各评估八条，phase3 与 neutral3 各评估三条；后两者是 main8 的预登记子集。完整原候选库保留。这样可以分开观察来源信息、阶段倾向和额外候选次数的作用。

通用 SA+HC 使用与 main8 相同的实测校准费用上限、最多12查询；其缓存与主方法、消融和参照隔离，初始 Uniform 的两 FIT 视频重新支付生成/评分。四组完整身份桥接允许释放验收后复用相应参照分数。实际费用与允许上限、查询数分别报告，不把同上限称为实耗相等。

两个旧 FIT 选择，两个已曝光 CHECK 开发检查；新 DEV 与第二真实网格在规则选定后确认。全93帧 LPIPS为主，双时钟/逐输入/失败分母保留。新鲜 Uniform19/22、F19-C/A1、原冻结RGB-MSE搜索与Native同批测量；不改任何旧赢家或分数。

## 完整范围和报价

- [166 语义位置](../plans/cara_next_stage_20261103/source_coverage/c1/C1_MANIFEST_R1.json)，最多166物理请求／5,976配对更新；32固定FIT cohort，加最多24搜索cohort，内部112评分对上界。
- 15个非Native角色×四旧输入，共60正式质量位置；最多24 FIT位置复用本卡封存结果，释放后至多36新评分对。12组身份控制关系，原卡指标重算0。
- [完整报价](../plans/cara_next_stage_20261103/source_coverage/c1/C1_WHOLE_QUOTE_R1.json)：预计 **14.8224 GPUh**，建议单次硬 **15 GPUh**。采用原完整P1 R2实测各类最大开销，计入内部CPU占卡、停止释放600秒、装载及15%波动余量。未读取或更改中央账本。

## CPU 与接线

[本地31/31控制通过](../plans/cara_next_stage_20261103/source_coverage/c1/C1_CPU_PROOF_R1.json)：新完整回调流程、八视图选择、独立搜索、预算停止分母、原回执恢复零新回调、失败不重试、C1显式validator接入与原P1默认兼容。复用并重新验证180组穷举、8条真实源码小权重36更新路径。166位置回调中的媒体和分数是合成fixture；不形成真实视频结论。

三处旧入口改动是向 `Requests/Collection/collect_loaded` 传显式卡片校验器，以及给独立搜索评分命名空间。原P1默认参数及协议保持；原冻结stage不改、不重跑。新 C1 的宿主监督、broker和60位置终态接受器仍需单独绑定并通过对应CPU组合，不能把原146位置接受器用于C1。

原 Tailscale 通路已登录并完成本次CPU取回。[原Linux完整接受](../reports/cara_source_coverage_C1_Linux_CPU_accepted_r3_20261103.json)证明117文件闭包、相同worker源码与31/31控制，容器`7bf442423ada`退出0；原proof字节和SHA已独立核验。保留原R1缺NumPy、R2到300秒超时的失败；R3使用已接受的只读Python环境与1200秒诊断边界，诊断显示合成测试journal的fsync/XFS等待，未改变持久化语义或网络配置。另有5项本地宿主元数据控制通过。

下一项交付为[生产组合接线](../plans/cara_next_stage_20261103/source_coverage/c1/C1_CPU_PRODUCTION_BINDING_HANDOFF_R1.md)：C1独立运行身份、56内部查询队列、原guardian唯一计时与60位置释放后接受。当前31项证明采集与选择的CPU行为；完整166回调仍为合成媒体/分数，不是实模型视频评价。

本轮 GPU 提交与支出0；报价可审阅，启动审批留到新卡生产绑定和Linux CPU验收完成后。
