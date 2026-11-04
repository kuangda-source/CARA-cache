# F17四新输入确认子集补充预注册

2026-11-04，首次GPU执行前。Run `cara-f17-confirm4-r1-20261104`。
用户指示「先跑F17确认」，本18请求卡仅在正式报价<2GPUh、原准入全过时获准单次执行；硬限1.95GPUh，不上调cap。
本补充仅取原 `../PREREGISTRATION.md` 的F17独立确认部分，不取代或修改原协议、结算失败、s(t)函数或其待完成状态。

沿用原四新输入、seed0、checkpoint/精度、36更新、93帧、guardrails、三种固定加速角色、T_DD与完整请求时钟。
按原manifest的顺序，两个旧AV warm后，四新输入各Native/F17/F19/WC四角色轮转，共18请求。
只保存MP4和终态latent；无Native逐步记录、无状态快照。输入曾有Native部分曝光，如实保留；未据此调布局、选择输入或阈值。

四新输入等权，全部条件同时满足才确认：同批mean T_DD Native/F17≥1.9；F17 mean T_DD≤133s；mean LPIPS-Alex≤0.27；
相对同批Native及F19，MUSIQ均值差≥−1、subject_consistency及motion_smoothness均值差各≥−0.01，共六门。
新旧F17 LPIPS非劣检验不变：δ=0.027，H0 μnew−μold≥δ；新组减δ后枚举70个4/4标签排列，单侧下尾p≤0.05；
独立单位是输入，保留平移后可交换假设，未拒绝H0记为不确定。旧组只复用CAL35已接受四条F17 LPIPS，绝不重评分。
LPIPS与48个质量位置仍在GPU释放、原guardian账单唯一结算后，由原CPU scorer执行。

正式报价和来源在manifest；保留50GiB宿主内存准入、90°C自动停止、4GiB输出低水位、原600s退出余量。
输出使用新卡独立16GiB镜像，位于已核实的数据HDD项目目录，独立journal仍在系统SSD。仅对新私有镜像执行正常provision，不挂载或格式化任何闲置物理分区。
无heartbeat/cron/automation/持续监控；实际开始后只确认首批运行并交接。s(t)续卡需另行核价批准，不与本卡重复计算16条clean结果。
