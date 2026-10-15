# 阶段规则与冻结T1：真实执行接口准备及本地CPU72启动

456已经回答了当前最关键的低成本区分问题：简单时间/第23步规则可以解释T1几乎全部局部收益。下一步开始把候选接入完整执行器，确保未来视频比较执行的动作与评价动作一致。**本轮没有新GPU或新视频结论，原同26D R2及04:55验收保持。**

## 已完成的执行工作

新接口位于`src/wcomr/w3_phase_allocation_runtime_r1.py`，源版本814b5d00b404aaa8f151bf5fa20ae3d5e67da648。原H1、GCR、模型源码和旧stage不改。保留H1_ORIGINAL、H1_CAD、STEP23_A_ONLY、T1_CAD四种完整配置，分别隔离原策略、P0合法集变化、第23步规则和当前观测预测。

第23步规则只有在原H1选D、双probe/校准/来源年龄及真实D来源均有效时改用已有A。T1使用冻结的主6组参数47026e73，按当前真实sigma、已支付probe与来源构造13维特征；不再拟合，不读取teacher/未来。实际C/A/D分数直接使用已含g²的预测，不重复乘传播增益。缺校准/不支持来源沿H1-CAD回退；原H1和第23步配置保留P0。

六项标量CPU控制通过：288步已有普通特征重放；H1 wrapper OFF全36等价；第23步A的root账本与真D来源保持；T1全36决策纯函数、实际报价及精确restore；P0合法集和UNKNOWN回退；坏参数及缺支持拒绝。初版测试夹具试图修改不可变rho映射的AttributeError已记录，改为从创建时使用空校准夹具，未修改运行算法。回执：`reports/wc_w3_phase_runtime_six_scalar_controls_20261016.json`。

请求边界沿用已接受的GC/空闲allocator回收语义，运行中的算法缓存不清空。原同26D仍需完整GPU显存验收，新接口没有因此宣称真实显存问题已解决。

## 已启动的本地完整采样CPU

按[独立CPU计划](../plans/WC_W3_FROZEN_PHASE_RUNTIME_CPU_PREP_20261016.md)，两flow×四Toy请求×四配置×audit/lean＝64路径，另加8条旧H1完整audit控制，总72路径、2592pairs/5184CFG。Toy权重/attention/prepare/decode/writer明确保留；WC/RF/UniPC/条件类采用绑定的9份源码。主程序、参数与关键fixture哈希事前记录。

本地PID **5392**，于北京时间 **2026-10-16 02:14:36.917** 单次派发并用原句柄确认存活。预计5—12分钟，最早查收 **02:26:36.917**，约 **02:28一次查收**。此前不读partial、不持续监听；未完成则按剩余量重新估时约一次，不重复启动。

- 启动回执：`reports/wc_w3_phase_runtime_local_full72_CPU_launch_20261016.json`
- 原CPU结果：`reports/wc_w3_phase_runtime_local_full72_CPU_result_20261016.json`
- 原退出回执：`reports/wc_w3_phase_runtime_local_full72_CPU_exit_20261016.json`
- 一次查收工具：`scripts/capture_wc_w3_phase_runtime_local_cpu_r1.py`
- 原件目录：`.sync/wc-phase-runtime-local-r1-20261016`，仅本地，不同步服务器。

查收须核对原source/PID/实际退出、全72分母、两flow全部audit/lean控制与8条旧H1全36等价、所有请求owner释放和mock输出；不能仅用摘要或前几条成功验收。CPU失败/缺失保留，不缩完整范围。普通CPU/mock输出不是实际93帧视频质量证据。尚无服务器生产CPU接受或真实执行费用，本次不启动新GPU。

本地venv补充Diffusers0.31.0作为原UniPC的配置/调度基类依赖，没有下载模型或改服务器环境。此本地配置不冒充生产环境，后续仍需独立生产CPU。

## 后续边界

原同26D source0795a00、1040857/1040918/post1040858及04:55一次验收自动化不改，本轮0SSH、不读取其科学partial、不占用服务器GPU或写v2账本。F/B保持关闭，不引入人评、生成器训练或OMR。先完成当前两项CPU/GPU验收，再结合真实完整结果决定下一张视频卡；具体视频范围、生产CPU和fresh余额准入仍待。
