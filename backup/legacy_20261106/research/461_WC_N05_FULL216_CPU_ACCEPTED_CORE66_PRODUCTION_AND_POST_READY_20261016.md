# N05完整216条CPU已接受，强基线完整66路径生产准备

更新：2026-10-16 03:47，北京时间。

**主线下一步已具体落到公平强基线比较。** 完整本地CPU216已接受，覆盖少步Native、WC/RA阈值安装、冻结A/H1、审计开关与旧默认完整轨迹；真实生产入口、全分母后处理和独立启动接线已完成本地检查。当前仍没有新GPU输出或新的质量、速度结论；原同26D R2保持04:55一次验收，接受后才启动N05。

## 1. 已接受的数值验证

原source `762aeb4e010e3b297b23fd8e2f2f91feedd2abc7`、本地PID6663已终态，退出0，运行99.068387秒。原launch不重派；已在登记最早时刻之后一次捕获，再离线独立接受：

|检查|实际范围与结果|
|---|---|
|完整分母|216条Toy CPU请求、7360pairs、14720CFG调用|
|审计/lean|88组全部完整数值、动作、历史、终态与mock文件一致|
|旧默认桥接|40组旧配置完整36步guided与mock一致|
|Native三网格|两flow×四Toy×35/26/18；实际36/27/19更新、72/54/38CFG|
|参数与生命周期|实际WC/RA安装阈值已检查；所有请求组件释放，无跨请求算法状态泄漏|

这是Toy采样与受影响入口的数值证据；真实scheduler另外使用安装的UniPC/Karras CPU展开核对，不能把Toy Native/dense stand-in写成真实视频或生产GPU验证。

原件与独立回执：

- `reports/wc_paper_N05_core216_local_CPU_collection_20261016_0312.json.gz`
- `reports/wc_paper_N05_core216_local_CPU_result_20261016.json`
- `reports/wc_paper_N05_core216_local_CPU_independent_acceptance_20261016.json`
- `reports/wc_paper_N05_actual_native_scheduler_grid_CPU_20261016.json`

## 2. 下一张完整开发卡

完整卡 `WC-PAPER-N05-CORE11-CAL4-FULL66-R1-20261016-A`：11配置×四原CAL、seed0，共44正式＋22完整预热、2220pairs/4440CFG、一次驻留加载、零教师。

|家族|事前固定配置|
|---|---|
|Native|35/26/18 requested steps|
|WorldCache|阈值0.03/0.06/0.12|
|RA|冻结本地阈值0.070744235098772×0.5/1/2|
|Ours|原A_NO_P、TABLE_PHASE_H1两个工作点|

四原CAL、提示词、seed、93帧/768×432/16fps、checkpoint、后端、guardrails和其余方法参数保持。两次完整warm按正反序执行；四CAL正式按预登记交错顺序。新批次Native35是保真参考，正式秒数与均值都来自新44条，旧420默认20条只作数值控制，不拼接为新时间。

完整费用估计 **8.568548038 GPUh**，计费上限 **9.5 GPUh**，含全部66路径、加载/启动、输出、算法维护与失败清理余量。该值是保守规划，尚非实费。沿用原严格<12自主规则及原总cap104.971363333；N06独立接受后，仍须fresh v2余额与逐UUID锁/显存/计算进程准入。没有重置预算窗口。

直接修正近邻的Cosmos忠实适配仍是显式缺口。完整11配置核心范围是在资源核查后、读新结果前冻结，不是缩减已选卡，也不称全部N05强对手已完成。近邻工作不由手写代理冒充官方实现。

范围/费用/绑定配置：

- `manifests/wc_paper_N05_core66_preregistration_r1_20261016.json`
- `manifests/wc_paper_N05_core66_full_cost_r1_20261016.json`
- `manifests/wc_paper_N05_original420_default20_bindings_r1_20261016.json`
- `configs/wc_paper_N05_core66_production_r1_20261016.json`

## 3. 生产与验收实现

新代码只进入独立新stage；复制已终态旧R1的固定源，叠加新入口与已验内存生命周期修复，不读取/修改仍在运行的同26D R2。

- 真实生产CPU将导入Cosmos原Setup/InferenceArguments、官方Native forward和原scheduler，逐一构造44种实际请求，核对三条真实采样网格及全部输入/参数/源码哈希；不加载权重、不执行CUDA、不写预算。
- GPU supervisor绑定完整66范围、CPU来源及原N06完整独立接受；fresh v2短事务、逐UUID租约、一次加载，完整9.5预留仅作准入，原件按实际占卡wall/3600一次结算。
- 全66位置保留；拒绝、技术失败、未到达不填零或删除。逐原件核对后，对全部兼容正式视频做93帧CPU LPIPS；坏容器单独保留审计失败，不使其他原件审计提前中止。
- 检查默认10个warm的全部360个guided、11组warm重复端点、旧420全部20默认端点与动作/历史。研究取证在主计时外，算法维护在主计时内；主计时为文本编码、去噪和VAE解码，加载/写盘另列。
- 输出所有逐场景点、两个冻结Ours相对每个基线的真实秒数与失真；非支配关系来自实测点，不把插值或D次数当相同时间，也不称本轮单次计时是最终重复clean结果。

本地14项网格/Native计数/生产范围/后处理/启动检查通过；随后增加原N06必须完整28个旧输出控制的空集合拒绝，受影响4项启动检查再通过。两个版本的原测试回执都保留：

- `reports/wc_paper_N05_short_production_post_launch_CPU_controls_20261016.json`
- `reports/wc_paper_N05_prerequisite28_guard_CPU_controls_20261016.json`

**尚待：新独立服务器生产CPU完整接受；原N06 04:55验收；N05真实GPU及全部原件/视频/财务接受。** 本报告不把准备升级为实验收益。

## 4. 接续优先级

N06完整验收 → N05强基线 → N07最终共同冻结测试 → N08最终重复clean计时；N09部署成本与N10自动质量复用最终输出。P/T1仍为条件增强，F/B关闭，不开生成器训练、OMR或人评。

完整费用≥12或池余额不足才提交具体整卡预算决定，不拆分规避门槛。长任务按预计结束时间一次查收，未完据剩余工作重估一次安排；不持续监听。
