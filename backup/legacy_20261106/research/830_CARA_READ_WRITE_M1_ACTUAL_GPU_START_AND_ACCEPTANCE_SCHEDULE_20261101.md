# 830 — 读写价值M1实际GPU启动与全链验收安排

读写价值主线已进入真实M1运行：两卡原A6000于2026-11-01 **18:49:24.756352 Asia/Shanghai**启动完整14请求，预计1.6048GPUh、硬限1.95GPUh；唯一runner的CUDA上下文与EXCLUSIVE_PROCESS独占通过。半程19:38、终验20:28已设置。当前仍是执行进度，科学结果须完整14生成、释放与结算后统一接受。

## 原件与来源

- run `cara-read-write-M1-full14-r1-20261101`，launch `7949388215944eb98c7f64f21e8e1dd1`。
- 冻结source `b930df4b04a0924d8bea0af32c0f7aaf8c33a5c8`，GPU `GPU-cebf7119-cf03-23b9-e192-cd196332b704`。
- [实际开始接受](../reports/cara_read_write_actual_start_accepted_r1_20261101.json)绑定原guardian/CLI/supervisor/runner的PID-start ticks、原注册、实际分配起点和唯一CUDA上下文。它不是完整科学接受。
- [原预约](../reports/cara_read_write_central_reservation_r1_20261101.json)：用户单独允许本卡原账本事务后，原cap226账本一次预约1.95GPUh；旧16.5责任原样保留，没有提高cap或修改其它任务。预约不是实际费用，结束后仅按guardian全段实耗唯一结算。
- [完整资产/资源准入](../reports/cara_read_write_full_fresh_admission_r2_20261101.json)：20份原资产完整SHA、源码/runtime、私有卷/独立journal通过；入场GPU空闲、46°C、24MiB、无计算进程，宿主可用内存约53GiB。预约前再次refresh，派发时再次检查可变状态。

## 固定范围与保护

仅两旧FIT、seed0、第8更新，八科学输出+四独立控制+两新Native；14完整请求、504原solver更新、512paired、1024CFG、全部93帧。四格每次均支付当前C/D，选择读出与整包写入，原sampler维护真实UniPC历史。当前卡只作同父机制识别，不依据诊断计时宣称部署速度。

整卡原硬截止 **20:46:24.756352**，**20:36:24.756352**开始停止释放余量；90°C保护保持。容器2CPU/40GiB、同额memory-swap上限，独立16GiB输出/48MiB跨盘journal。原GPU源/配置/范围不能修改，不重派、不换卡。

[启动后原运维R3](../reports/cara_read_write_startup_operational_r3_20261101.json)只回读计数：1/14完成、1运行、12未到达；原runner独占、100%利用、87°C，90°C保护保持。中间一次SSH连接复位已保存，随后恢复原句柄；未把网络失败当实验失败，也未重派。没有读取部分科学分数或T_DD。

[原运维R4](../reports/cara_read_write_startup_operational_r4_20261101.json)随后推进至3/14完成、1运行、10未到达，0技术失败；仍为原runner/原独占，采样时67°C。该记录仅为运维进度，未打开部分科学结果。

## 已安排的验收

[检查清单](../reports/cara_read_write_acceptance_schedule_r1_20261101.json)：本对话heartbeat `m1`半程19:38、`m1-2`终验20:28。无变化静默。半程可只根据完整/剩余路径计数和墙钟前移同一个终验，原硬截止不变，不新增重复监控。成功或真实失败收尾后删除它们。

GPU结束后先恢复原终态、释放和唯一实际结算。仅完整14正常成功后，原一次CPU读者接受完整latent/93RGB四组等价，再派一次八对Fidelity-v2评分；CPU活跃只恢复。全八对接受后，才报告逐输入、等权read/write/interaction与全93帧曲线。失败保留完整分母与原费用，不冻结科学结果。

等待期间已补齐完整分析与导出：

- `src/wcomr/cara_read_write_analysis_r1.py`与CLI：三个合成CPU检查通过，明确read=L10−L00、write=L01−L00、interaction=L11−L10−L01+L00；拒绝部分八对、改变参考/曲线及CPU夹具冒充生产。
- `scripts/render_cara_read_write_complete_r1.py`：完整93帧CSV、逐输入端点CSV、四面板PNG/PDF合成CPU导出通过，CPU图显式标记且图面已检查。没有读正在运行的实验结果、重算旧指标或改GPU源。

后续完整流程见[原运行交接](../plans/cara_next_stage_20261101/read_write/M1_FULL14_POST_LAUNCH_HANDOFF_20261101.md)。保留A32/B36/S/Q/搜索/E1原接受、赢家与旧CAL范围；WC/RA FIT UNMATCHED、最终16/备用16保护保持。M1之后，M2方法与read-only消融仍须独立完整方案，不从部分运行输出修规则。
