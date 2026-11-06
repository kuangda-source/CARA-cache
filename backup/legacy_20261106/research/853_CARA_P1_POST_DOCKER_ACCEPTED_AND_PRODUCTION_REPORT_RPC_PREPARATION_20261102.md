# P1原后置评分Docker接受与生产汇总准备

原两卡连接已恢复。P1新增后置评分/生产serve分支CPU已完整接受；分析、图表、冻结和单卡RPC接口已接通，新26控制的精确源码包本地检查通过。P1 GPU与该卡中央账本权限仍未获得，实际硬限仍为空。

## 原CPU验收

[接受回执](../reports/cara_v1_P1_post_host_CPU_accepted_r1_20261102.json) · [原证明字节](../reports/cara_v1_P1_post_host_CPU_original_proof_r1_20261102.json) · [原捕获](../reports/cara_v1_P1_post_host_CPU_capture_r1_20261102.json) · [关闭记录](../reports/cara_v1_P1_post_host_CPU_complete_cleanup_r1_20261102.json)

固定源 `49fad1948fc57193a493f055ac2cf072f5ef2792`，registration `4614d299e1739369ca7211d3530216d7b8b71f50147201fcd479ba3fa3561980`。原宿主CPU在08:01:41开始、08:05:27正常结束，约225.59秒；早于1200秒上限对应的半程点，收件时已结束，未另建检查。

- 31项原接口控制通过。真实媒体、成功评分和预设失败评分容器均退出，原supervisor/CLI/worker已结束；2CPU、8GiB/no swap、CPU26/27、无GPU和网络。
- 仅两个新的93×64合成视频对真实评分，其余50行明确模拟，合计保留52位置。预设失败保留2分母/1对完成，重复派发与终态恢复均无新容器。
- 当前真实生产serve分支在GPU隐藏CPU元数据模拟下实际启动、零查询并关闭，CPU26/27和4GiB地址空间符合约束。未创建GPU分配或费用。
- [851](851_CARA_P1_RELEASED146_SCORE52_LINUX_CPU_ACCEPTANCE_20261102.md)原32对指标、旧算法/FIT/guardian实验均按固定源复用，未重放。已结束的本次原CPU也不再恢复来刷新文档。

以上是接口与资源证据，没有真实Cosmos新视频或V1方法收益。

## 完整汇总与冻结

新入口 [analyze](../scripts/analyze_cara_source_lifecycle_p1_complete_r1.py) 只接受完整52位置、原评分进程全部结束和原146算法summary。保留2FIT/2已曝光CHECK与四旧CAL输入等权，原FIT计划和旧RGB-MSE赢家不重选。

新鲜进程观察包含新时间戳，直接哈希整个观察会使重复验收得到不同analysis/freeze身份。因此第一次完整读取保存源、intent、结果、容器和PID/start-ticks绑定的不可覆盖输入封存；后续仍重新验证原终态，只允许两份新鲜进程观察变化，所有科学字段、结果、原身份和源必须相同。重复分析复用第一次封存，冻结保持原字节。

[图表入口](../scripts/render_cara_source_lifecycle_p1_figures_r1.py) 输出13角色的双时钟质量图、全部93帧LPIPS/SSIM曲线，以及52逐输入行、39输入等权行、3627曲线行和两预算的实际校准费用CSV。无穷PSNR和未定义梯度保留原身份。CPU夹具显式标记，默认生产模式拒绝。已有导出只验原SHA，不覆盖。

## RPC与下一门

[单卡控制](../scripts/cara_source_lifecycle_p1_control_r1.py) 在凭证、SSH和任何四卡接触之前校验本新P1直接授权及同run中央例外；旧P0/M1许可不能进入。两卡状态只计原句柄、物理完成文件/内部请求意图数量、资源和146分母，不能读取部分科学结果。未知派发只恢复原句柄。临时账本新增结算控制覆盖唯一实耗、写账中断恢复、失败/超限与旧16.5责任；没有访问真实中央账本。

[新精确1448文件隔离包](../reports/cara_v1_P1_entry_delta_packaged_local_CPU_r2_20261102.json)通过26项：分析5、实际PNG/PDF/CSV3、临时账本结算5、模拟RPC5、容器/worker入口8。下一步只在两卡执行该新增Linux CPU delta，复用已接受原件，不重算视频指标；随后补来源/私有64GiB存储、整卡证据组合和正式报价，再一次审阅完整P1与本卡账本事务。

完整146语义/最多142物理、64标签、两预算各top3及公平LPIPS搜索保持。18.0273GPUh/建议硬19仍是保守草案，250秒/标签是未实测预算假设。旧冻结、保护最终16/备用16、四卡维护限制、cap226和旧16.5责任保持。

来源准备曾在本地拒绝一次：宿主回执不符合原容器源码传输器字段，尚未读取凭证或发送SSH。已改绑原释放R3已结束容器的源码回执，精确包26控制重新通过；原拒绝[保留](../reports/cara_v1_P1_entry_delta_source_context_local_refusal_r1_20261102.json)。未创建或重派远端实验。

Linux新增入口随后因生产Python缺少Matplotlib，在创建stage/启动CPU之前拒绝；[原两卡只读确认](../reports/cara_v1_P1_entry_delta_CPU_prelaunch_absence_r1_20261102.json)显示原R1 stage不存在、仅保留传输意图，禁止重试该准备。新独立R2仅执行23项Linux分析/结算/RPC/容器入口控制，并以原源码复用本机3项真实图表控制；[R3精确1449文件包](../reports/cara_v1_P1_entry_delta_packaged_local_CPU_r3_20261102.json)已通过23项本地检查。模型与评分Python未修改，正式图表交付所需后端仍须在整卡准备中解决。
