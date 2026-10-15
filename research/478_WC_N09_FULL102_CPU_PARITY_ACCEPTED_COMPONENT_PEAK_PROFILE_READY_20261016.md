# N09组件与逐请求显存记录器：完整102 CPU对照已接受

更新：2026-10-16 06:26，北京时间。**最终部署成本测量的记录接口已通过完整CPU集成对照。** 全部17个已有执行配置在两种flow下，profiling没有改变模型输出、动作、历史或缓存owner释放。此结果可用于最终N09接线；真实CUDA峰值、组件价格与最终clean测速仍待实际测量。

## 1. 完整原任务与验收

|项目|实际接受|
|---|---|
|原source|1829c0f23c39f2e9e830d82d4ad5336e9fd95de9|
|原PID|10482已终态，exit0；不再查旧句柄|
|隔离目录|`.sync/wc-paper-deployment-profile-full102-local-cpu-r2-20261016/source`|
|源码身份|2283份封存payload与9份固定runtime源全SHA一致|
|完整CPU路径|102/102；3516pairs/7032CFG|
|完整逐步输出对照|34组原audit/profile audit的全部guided张量一致|
|profile审计开关|34组profile audit/lean的终态、动作、A/source history与mock字节一致|
|请求与配置|两flow×17既有配置；一个Toy请求、seed17；三模式完整保留|
|实际原件|102份mock、68份标量profile；112356个区间从原件独立重算|
|组件与缓存|各路径原owner与执行组件全释放；弱恢复未引入跨请求残留|
|CPU时长|57.674823秒|
|GPU/服务器/预算|0GPUh、0SSH、0预算写；未触碰原N05|

七项标量控制包括实际静态namespace绑定方法回归与fake CUDA双请求峰值reset/延后事件读取。fake CUDA只检查记录接口，不代表真实设备测量。原R1静态WeakMethod兼容失败/一个原mock/exit/source/capture已在477保留；R2完整独立重跑，未拼接旧路径或放宽102范围。

## 2. 证据与独立复算

- 单次原捕获：`reports/wc_deployment_profile_full102_local_CPU_R2_collection_20261016_0626.json.gz`，SHA `3afd247a867f51e87ccddb4bea3d92c4d1710051838abc9bc4bd62ac31e2c96b`。
- 独立接受：`reports/wc_deployment_profile_full102_local_CPU_R2_independent_acceptance_20261016.json`。
- 原完整CPU结果及exit：`reports/wc_deployment_profile_full102_local_CPU_R2_result_20261016.json`和同前缀exit。
- 独立接受器附加控制：`reports/wc_deployment_profile_full102_acceptor_CPU_controls_20261016.json`。

collector在最早登记时刻之后只查原本地句柄一次，捕获终态与全部原件后离线验收。接受器从34个完整method×flow、逐步SHA、102 mock原件、68标量profile的全部区间重建计数/CPU和，并核对源、原exit与原结果身份；没有仅依赖runner的成功总数。

对同一真实捕获的八个人为损坏副本全部拒绝：缺方法、改guided、改mock、把不可用CUDA显存改为0、改组件次数、虚构owner释放、改原source和假称CUDA已测。副本控制不是新增采样；原捕获不改。一次辅助检查最初误用系统Python而缺Torch，改用项目venv后完成离线控制，不重查或重跑原CPU。

## 3. 记录器可以测什么

- CUDA路径在模型驻留后、请求开始前同步并reset peak，结束后读取逐请求allocated/reserved与峰值；CPU unavailable保持null。
- 可观察shallow/deep blocks、head、solver、VAE、输入准备整体、安装/写盘、实际policy入口、可用修正warp/转换和请求边界GC。
- 不保存输入/输出张量；动态控制器与读出仅用弱恢复条目，静态模型边界允许请求内绑定方法保存。
- 事件在显式设备当前stream记录，不在内部组件同步；到请求末统一读取。各区间inclusive，嵌套部分不相加冒充总延迟，其他stream的工作没有被直接归属。
- 诊断profiling路径单列，不进入N08 clean速度均值。最少记录显存时可仅使用RequestProfile请求边界，不启用组件包装。

本次是声明Toy attention/weights/head/prepare/decode/writer以及Native dense-WC stand-in的CPU验证。最终真实Cosmos入口、普通guardrail、GPU事件和峰值仍需随最终scope验证，不能把102 mock称为102真实视频或报CPU块耗时为GPU费用。

## 4. N09还缺的实测

当前接口并没有自动隔离“同状态、两个probe均已支付后”的动作价格；C/A/D及合法P0价格还需在实际pair执行边界接线、冻结完整测量范围与费用。不能用两个inclusive组件相减冒充纯动作成本，不能把旧P0从合法集删掉以简化计价。

最低必要标定标签采集费、最终模型/算法驻留显存、安装/GC/缓存维护的真实秒数，以及额外测量路径/预热/清理，仍需最终GPU scope显式计费。原465中四相关研究账单合计4.383638799GPUh继续保留，不冒称最小部署费。

N07如复用现有17配置/seed17或43且算法不变，可复用475的完整952注册表CPU接受；N09组件包装可复用本次102观察等价证据，只补最终真实输入、生产与设备受影响部分，不重复整套Toy采样。

## 5. 下一主线

原N05完整66、source15d77ac、1078249/1078290/post1078250仍**今天12:05一次验收**，未SSH或读取科学partial，原stage不改。本地CPU自动化已暂停，不再查R1/R2旧句柄。N05/N06后冻结N07共同新prompt/双seed测试，再N08重复clean，N09/10补成本与自动质量。原cap104.971363333、严格<12GPUh自主及余额不足/整卡>=12的具体确认规则不变，不重置窗口；F/B关闭，P/T1后排，无新人评、生成器训练或OMR。
