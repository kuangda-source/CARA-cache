# Fast R2：干净计时绑定与 A32 审阅包

双机接受了新的采样路由、实际全93帧评分 CLI 和 Linux 生命周期 CPU 控制。下一步是审阅 [FAST-CAL-A32](NEXT_CARD.json)，取得新卡授权后再做实际资源准入。GPU提交、预约、新GPUh和cap调整均为0。CPU控制没有产生 Cosmos 视频或加速、画质结果。

## 68条生产绑定

[RUN_SPEC](RUN_SPEC.json)只覆盖 R1 [科学清单](../RUN_MANIFEST.json)的执行元数据，保留原文件SHA、方法、四CAL、seed0、阈值网格、mask、alpha与 Fidelity-v2。解析scope为 `d0ad38bc0fd29615e82dae7f726938bac15aec2842e4484bb3577e0949694fb4`。R1的60条保留为历史准备提案。

R1 CPU入口把所有请求都设为 `audit=True`。逐步 guided CPU拷贝会进入计时区；四路 Native/allD 控制也不足以覆盖原完整三臂门。R2明确设置审计开关，并保留 `2 FIT × {Native35, allD, WC_T006 PaperPort} × OFF/ON` 的12条数值控制，再为两个FIT各执行一条干净 Native锚点。WC_T006始终是本地PaperPort，不称官方README设置。

| 用途 | R2物理条数 |
|---|---:|
| 两次加载的完整engine预热 | 12 |
| 完整三臂数值控制 | 12 |
| 正式新执行，含两个干净Native锚点 | 26 |
| 有限FIT校准 | 12 |
| 平衡重复 | 6 |
| 合计 | **68** |

32个逻辑正式位置仍有6个FIT基线引用被选校准产物，不算新独立样本。A32由6预热、12控制、2干净Native和12校准组成，只访问AV28/Human199。B36及CHECK比较后置；批准A不授予B。原10附件、WC73原槽位和停止决定均保持。

## CPU接受的范围

- [采样/评分独立接受](../../../../reports/cara_fast_scoped_CPU_acceptance_r2_20261028.json)：每host、每flow有28条成功tiny路径，另有4个明确writer失败控制；完整68分母做静态核对。检查12条数值控制、12条干净代表路径、4组clean OFF/ON、Native审计/非审计等价、零研究计数、清理和禁止重试。没有执行完整68条GPU或完整68条tiny。
- 每host各一条确定性合成93帧视频通过实际原Alex权重评分CLI；Native22/35标签只是输入身份fixture。独立读取了完整评分回执，确认93帧/92时序对、PTS、Alex0、PSNR `+inf`、SSIM1及逐帧曲线。未生成模型视频、未重评旧视频批次，不据顺序CPU耗时推吞吐收益。
- [A32生命周期接受](../../../../reports/cara_fast_orchestration_CPU_acceptance_r3_20261028.json)：双端均6项检查、容器退出0。真实Linux子进程、PID/start ticks、继承flock FD、失败清理和账单落盘；GPU观测明确模拟，实际Docker GPU命令只构建未运行。正常、子进程失败和90°C分支均保留原账单并拒绝重跑。驱动独占和实际模型构造仍须在真实卡内验证。
- 以上容器均1CPU/4GiB、无网、GPU隐藏；采样/评分每容器600+60秒，编排控制180+30秒。R9曾有测试mock作用域错误，失败回执和旧测试源码保留；R10仅修该测试并双端通过。R5导入命名冲突也保留。

Ada旧R1/R2的两次exit142不撤销。最小默认/单编译线程导入控制均正常退出，原问题未复现、根因未证明。新路径用 `TORCHINDUCTOR_COMPILE_THREADS=1` 限定CPU资源并已正常退出；这不是对旧失败根因的确诊。

## 费用、存储与执行边界

[完整工程报价](WHOLE_QUOTE.json)沿用原计价锚点，逐槽增加完整控制与独立Native，包含加载、I/O、等待、释放与20%失败余量。

| 设备 | A32预计 / 硬限 | B36预计 / 建议硬限 | 完整68预计 / 建议硬限 |
|---|---:|---:|---:|
| RTX6000 Ada | 4.726 / **5** | 4.791 / 5 | 9.517 / 10 GPUh |
| RTX A6000 | 4.953 / **5** | 5.022 / 5.5 | 9.975 / 10.5 GPUh |

这些是工程估计，未测新工作点速度。A包含在整68报价中，不另计一遍。A释放、真实进程退出、中央实际账单结算和12对CPU评分独立接受后，才可一次性冻结WC/RA/Native-k选择；新冻结函数拒绝脏Native锚、CPU计时、部分分母和额外候选，且不授予B。

[执行profile](EXECUTION_PROFILE.json)冻结待准入参数：原BF16模型与选定2B的Wan FP32策略、无额外autocast，实际参数dtype/后端状态在第一物理路径前记录并跨请求核对。48GiB/2CPU GPU容器无网、root只读，CUDA只开放给确切runner。输出拟用各host的SSD上独立32GiB全分配image；控制journal在另一文件系统预分配48MiB。四卡用户目录实际为 `/home/user`，两卡为 `/home/gaokuangda`。本轮未创建image、journal或GPUstage。

只读中央账本仍为cap226 / used175.8058597668662 / reserved16.5 / available33.694140233133794 GPUh。原总计划为主线分配11GPUh规划池；完整68条建议硬限最多10.5GPUh，A32硬5均在该池内。本卡不需要增加总cap，两卡旧副本不能提供第二份额度。保护的是原最终/备用输入集合，不能把输入数量当成GPUh。先前准备中的错误货币下界、旧源码与CPU控制作为纠正证据保留；R11按正确单位重新验证，未发生错误预约或cap调整。

真实提交前仍需恢复双host已有句柄、发布完整source/config闭包、重新核对所有模型/输入/guardrail/NLTK资源SHA、输入曝光、RAM与disk，验证新存储，完成唯一中央预约、设备锁和硬件独占；当前只读GPU空闲状态不作准入。热保护保持90°C，先持久化触发温度/风扇/限频字段再停止，不干预他人进程或调阈值。

半程与终验时间以真实supervisor启动回执为原点，绑定launch/PID/start ticks/container/UUID/source。A32预计约4.7–5小时，半程约2.4–2.5小时；未启动前只保存相对计划，不虚构检查任务。半程仅运维状态；终验包含原始完整分母、退出、数值门、工件、释放与中央结算。失败不自动重跑，B不自动启动。
