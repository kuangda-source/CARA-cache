# E2：启动包装R2已独立验收，完整卡保持

2026-10-11。当前active，E1真实执行与E2确认准备继续。

**E2受影响启动CPU已通过并独立核对。** [原件capture](../reports/wc_e2_startup_cpu_r2_terminal_20261011_capture.json)绑定source `a5b66efc823f203266212168785361849959ea3b`，stage `.sync/wc-e2-startup-cpu-r2-20261011`；原监督4053789、wrapper4053819、真实入口4053942及meta4055201全部退出消失。CPU wall84.579013秒，exit0，无GPU提交、不写账本、CUDA未初始化。

原231方法文件、配置SHA `e317a3c14ef0082344f2adde06d0c40c39f888ee104c55a40b6044cb8925f6b6`、静态binding `738361d7c0aa3aabc8293969011d032e836f7003cf433935df8c2a2f80d665c9`和原29包装字节不改；执行表新增7文件至36。新protocol SHA `a47e74e1d4e912faa0f57481b351b589a2339218a649f845e65983d9c9759715`。两个必需文件在原observed入口加载前的 `validate_execution` 哈希核对中绑定，各missing／changed四拒绝实际通过；临时副本控制未改任何生产stage。

十真实请求／CAL／Native来源／guardrail、真实RA先验和阈值、五guardrail-less入口拒绝与13合同拒绝保持。全76元数据位置、68合成配对／6324标量距离、四提示词／八seed单位、17准入／8坏指标／152显存边界控制重跑通过，原LPIPS资源身份核对通过。它们是接线／资源证据，没有生成实际确认视频或新LPIPS值。

native meta重建2059174912参数／1173模块，原1173训练标志、共享eval后0训练；source pins、类与参数／buffer对象身份保持，不读模型权重、不执行forward。独立capture核对原29文件来自原2459861提交，新增文件来自a5b66ef，保留此前完整152 Toy sampler／3168guided／152 final，未重复未受影响采样。

**完整GPU卡原范围和原确认保持。** `WC-E2-PHASE-A-CONF40-TIMING32-PARITY4-R1-20261011-A`：40新输入确认＋32平衡计时＋四额外parity，共76，forecast9.869732459 GPUh。原具体确认仍待回复；严格>8，不能自主GPU、不拆卡。新dispatcher [R2](../scripts/dispatch_wc_e2_full76_r2.py)绑定本CPU证明和必需文件，缺批准时实测返回WAIT、没有SSH／selected目录／GPU提交；旧R1 dispatcher的拒绝仍保留。批准后复制到新selected R2，原完整method及selector／监督／后CPU保持；若原E1在途则不创建selected或提交。

E1 R2监督4050841／runner4050929／后CPU4050842唯一原任务继续，完整8／四加载、预计2.044575084；已实际进入采样，尚无全scope容量或等价结论。账本启动前实结39.234595840／77.895246590、新48余38.660650750，第77在途预留非实耗，终态实际全部收费。无训练或新增人评。
