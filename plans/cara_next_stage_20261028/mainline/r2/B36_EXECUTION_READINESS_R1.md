# B36 宿主与收件 CPU 状态

2026-10-29：原完整 B36 路由、真实 A32 六原件承接、宿主监督与终态收件已有分别绑定的 CPU 证据。完整新卡尚未具备派发入口及其全失败收尾控制，`GPU_dispatch_ready=False`；没有预约、启动或新增 GPU 费用。

- 核心路由：[原双端接受](../../../../reports/cara_fast_B36_CPU_acceptance_r1_20261029.json)，每端两种 flow 各完整36条；保持原采样和六候选覆盖，不重复运行这些未改组件。
- 宿主执行：[新增双端接受](../../../../reports/cara_fast_B36_outer_CPU_acceptance_r1_20261029.json)，每端7项、6种真实 Linux 子进程情形；正常、子进程失败、部分分母、90°C、预算边界及外来上下文拒绝，原继承 flock FD、PID/start ticks、进程组释放、实际账单、禁止重放及唯一中央费用均通过。GPU 观测为模拟。
- 终态与评分收件：[组合双端接受](../../../../reports/cara_fast_B36_execution_post_CPU_acceptance_r1_20261029.json)，每端新增8项；原句柄与一次读者恢复、失败仍结算、原A费用及16.5责任不变、原件/参数/精度、完整监测、评分分母/曲线/归约、CPU资源与只读挂载均验证。没有执行模型或度量网络。

四个实际 CPU 容器均已退出0、无OOM、Pid0；每个1CPU/4GiB、禁swap、core27、无网、root只读、无GPU，工作180秒/退出30秒。原采样和三个度量源码保持 A32 接受时的字节，原一次冻结文件未改。

## 已实现的生产边界

`cara_fast_b36_execution_r1` 的 `admitted_inputs` / `validate` 要求另外的人类 B36 授权、真实已结算 A32、同一 host/UUID、不同 launch、原冻结 SHA、双端 CPU 源/运行时证明、完整36条及唯一中央 envelope。`Pool.reserve` 只对已结算的原A新增整张 B 的预约，拒绝重放、跨卡、过期/忙卡、资金不足、同宿主重叠和 CPU 夹具。

新 worker / guardian / runner 使用原设备租约、硬独占、上下文握手、90°C先写触发记录、私有SSD输出及跨盘journal。实际模型精度/参数dtype/backend必须与 A32 实际记录完全相同；完整B为6预热+24正式+6重复，不重跑A诊断。新计划 profile 为 [B36_EXECUTION_PROFILE_R1.json](B36_EXECUTION_PROFILE_R1.json)，其未授权状态不是 GPU 已准备完成的声明。

新 terminal/capture/post 绑定本卡原 source/launch/PID-start ticks/container、真实 A 六文件及冻结结果，按实际 wall bill 唯一中央结算，失败不进入评分。GPU活动或句柄未知只返回运维数据；终态读者有唯一intent，断线仅恢复原件。原GPU释放后的其他用户上下文不撤销已保存的本卡释放事实。

正式评分仍为32位置＝4个Native自对照＋28个非自对照，来源为24个B新正式＋8个A产物。6个被选FIT校准配对直接引用原A已接受完整评分，保留原全部曲线及指标；原评分CLI只收到其余26对，CPU上限仍2CPU/8GiB/4小时。新收件独立核对26份新输出与6份原引用拼成完整32，禁止重新计算原A配对。GPU监督、Tensor/视频/参数原件、两种时钟和评分位置均保持固定分母。

## 派发前仍需完成

1. 完成显式单次 B 派发入口：外部直接授权文件、发布源和全CPU接受绑定、全新实际资源/资产SHA、只一次中央预约、不可重放的intent、原guardian恢复。不得把CPU容器或准备过程说成B GPU启动。
2. 覆盖 GPU runner 启动前的准入/容器失败和账单恢复；不得因原监督器/账单尚缺而推断零费用或释放已预约额度。现有失败测试覆盖已启动监督器与子进程，不替代这个入口边界。
3. 入口控制完成后提交完整审批卡。实际A在two_card A6000，B必须同一物理UUID；原Ada报价仅保留双端设计，不能用迁移规避本卡条件。A6000原预测约5.022GPUh、建议硬5.5，超过用户4小时阈值，需明确批准后启动。
4. 真正启动后按实际开始及新launch/PID-start ticks/UUID/source安排一次半程和一次全程检查。未启动时不预建检查。终态成功失败均保留原分母/实际费用；完整接受后才运行26对新CPU评分、引用原6对、按原规则汇总。原A冻结只验证，不再选择、覆盖或扩大网格。

WC_T006、RA_T1仍为UNMATCHED，Native22为MATCHED。B比较可报告原规则下的实际速度与保真曲线，不能将三家族全部称为实测同时间。两个CHECK仍是原CAL内的留出角色，不是独立DEV或最终确认。cap226、旧16.5未知责任、alpha、mask及保护输入成员不变。
