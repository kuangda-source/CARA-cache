# 741：Fast R2干净计时绑定、双端CPU控制与A32审阅

2026-10-28。当前可审阅的是[新生产绑定与A32包](../plans/cara_next_stage_20261028/mainline/r2/README.md)，不是新GPU结果。原算法、四CAL、seed0、alpha、有限候选网格与Fidelity-v2保持；完整三臂数值控制和独立clean Native把历史60条准备修订为68条提案（A32+B36）。新GPU提交、预约、生成视频、旧视频批量重评分与总cap调整均为0。

## 本轮接受

[独立采样/评分接受](../reports/cara_fast_scoped_CPU_acceptance_r2_20261028.json)逐项核对了两host的退出0、资源与实际回执。每host、每flow有28条成功tiny路径加4个writer失败控制，完整68分母做静态检查：12诊断、12干净代表路径和4组clean OFF/ON。原sampler、WC、RA、连续T_DD与T_request均复用。逐步审计仅在诊断请求打开；clean的guided拷贝、hash和研究checkpoint计数全部为0。并未执行68条GPU或完整68条tiny。

两host各一条确定性合成93帧clip经实际评分CLI、原Alex权重与PIQ0.8.0完成。独立重新读取CLI原始manifest/result并校对SHA、93/92分母、PTS、Alex0、PSNR `+inf`、SSIM1、逐帧曲线和Native-k不同执行请求身份；角色标签只作fixture。旧模型视频未访问，CPU合成控制不提供模型保真或吞吐结论。

[A32编排CPU接受R3](../reports/cara_fast_orchestration_CPU_acceptance_r3_20261028.json)绑定38个当前关键source。双端R11均6项检查、容器退出0：真实Linux进程/PID/start ticks、继承flock FD、正常退出/子进程失败/90°C停止、独立账单留存与禁止重跑；GPU观测模拟，GPU Docker命令只构建未运行。本地20项检查通过、其中macOS跳过的Linux项已在两端执行。实际硬件独占、真实模型构造/precision与数值门仍须由真实卡验收。

## 为什么改为68条

R1 CPU准备入口把所有路径都设为audit。逐步guided CPU拷贝在推理计时区内，不能拿这种Native时钟选择时间匹配基线；R1四路控制也没有完成两FIT的三臂OFF/ON。R2明确逐槽审计开关：完整12诊断保留，另设两个干净Native锚。26正式新执行、12校准、12预热、12诊断、6重复共68；32个逻辑正式位置中6个FIT基线仍引用被选校准产物，不算新独立样本。

R2解析scope `d0ad38bc0fd29615e82dae7f726938bac15aec2842e4484bb3577e0949694fb4` 绑定原R1科学manifest SHA。原10附件和12个历史组件SHA再次核对不变；原60条科学结果行逐项相同，未新增Fast结果。WC73原73槽不重派，IG/R4停止状态与最终/备用输入集合保持。

## 保留的失败与修正

Ada旧R1/R2的exit142及原源码/回执保持。最小默认导入与单编译线程导入均正常退出，原根因未复现、未证明；不能称已定位为编译池问题。新CPU路径采用单编译线程限制资源，实际采样、评分CLI和退出已单独通过。

R5命名冲突在测试入口导入前失败；R9的no-replay测试断言在mock作用域结束后调用了真实验证器，两个失败容器均保留。修复后R10通过。随后核对原总计划发现准备代码误把受保护输入数量当作32GPUh，下界和不必要的cap250步骤均在任何GPU授权/预约前删除，旧源码与[纠正回执](../reports/cara_fast_budget_units_correction_r2_20261028.json)保持。R11按正确单位重验：cap226可容纳A32；真实不足5GPUh、busy/stale设备仍拒绝，16.5旧责任完整保留。原R10的CPU通过不是当前预算源码接受，以R3/R11为准。

新增13个CPU容器均已退出，含上述失败；实际分配量约0.259835vCPUh/1.039341GiBh。worker子进程、SSH、本地编辑/Git等总实际CPU费用未完整计量，不称准备免费。

## 下一张卡与验收

[FAST-CAL-A32](../plans/cara_next_stage_20261028/mainline/r2/NEXT_CARD.json)只访问原AV28/Human199两个FIT：6完整engine预热、12数值控制、2clean Native、12有限校准。Ada预计4.726GPUh、A6000预计4.953GPUh，统一硬限5GPUh，提前180秒停止释放；完整68建议硬限分别10/10.5GPUh，仍在原11GPUh主线规划池内。当前中央cap226/used175.80585977/reserved16.5/available33.69414023只是已保存快照，本轮无须增cap、未预约。

执行profile绑定原BF16及选定2B Wan FP32策略，实际参数dtype/后端状态在第一路径前记录并核对不漂移。拟为新卡在SSD全分配32GiB独立输出image，另盘预分配48MiB控制journal；四卡实际用户根为`/home/user`，两卡为`/home/gaokuangda`。存储未创建，GPUstage未提交。入场仍需原件/guardrail/NLTK、输入曝光、RAM/disk、双host唯一意图、UUID/VRAM/apps/锁/中央预约与硬件独占的fresh检查。热阈值保持90°C，触发样本先持久化，不干预他人作业。

半程及终验根据实际supervisor启动时间和launch/PID/start ticks/container/UUID/source创建。半程约启动后2.4–2.5小时，只读取运维字段；终验约4.7–5小时，核对原完整分母、进程/容器退出、数值门、工件、释放和中央实际结算。当前仅保存相对计划，没有虚构自动化任务。

A释放且中央结算后，12对CPU评分须完整独立接受，才可一次性冻结三个基线选择；冻结函数拒绝部分分母、脏Native锚、CPU计时或额外候选。A本身不产生完整F19优越性结论，不授予B36、不自动重跑。此时需要人决定的是68条执行范围修订与A32单次GPU授权；其他准备已形成可审阅代码和回执。

[本轮机器摘要](../reports/cara_fast_preparation_summary_r2_20261028.json) · [范围/资源包](../plans/cara_next_stage_20261028/mainline/r2/NEXT_CARD.json) · [历史R1与Ada失败](740_CARA_FAST_MAINLINE_PREPARATION_AND_CPU_EXIT_BOUNDARY_20261028.md)
