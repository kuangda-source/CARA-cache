# 拒绝修复版248＋10全部接受，两张探索卡真实入口CPU已启动

2026-10-18。**R2完整248条36步数值采样及10个拒绝控制全部独立接受，实际927.946723秒。** 原采样、两flow、观察器开关、audit/lean、旧轨迹与owner控制保持；新增控制确认TEXT_REJECTED不会被误报为完整动作不一致。原R1和全部修复记录保留。这仍是数值与边界验证，无新视频或加速结果。

## 本次已完成

- [R2终态原件](../reports/wc_scout_numeric248_actual_CPU_R2_collection_20261018.json.gz)及[独立接受](../reports/wc_scout_numeric248_actual_CPU_R2_independent_acceptance_20261018.json)，source db1de113／1759源与runtime一致，80CAL12＋168BANK24完整采样、另10拒绝控制全通过。
- 新六DEV的项目输出身份审计R1＋R2完整接受，具体边界见[597](597_WC_SCOUT_R1_NUMERIC_ACCEPTED_REFUSAL_BOUNDARY_R2_AND_PRODUCTION_NEXT_20261018.md)。未复读N10质量。
- 两张实际配置和整卡报价已生成并冻结Git，原完整范围与旧设计报价保留。本地两kind共8项配置／可逆入口控制通过；不是服务器生产入口接受。

| 新卡 | 注册完整范围 | 完整预测GPUh | 完整计费上限GPUh | 当前状态 |
|---|---|---:|---:|---|
| CAL12 | 4CAL×2方法，8正式＋4完整预热 | 1.876666667 | 2.50 | 真实入口CPU在途，0GPU |
| BANK24 | 6DEV×D21/A21/Native35，18正式＋6完整预热 | 3.407222222 | 4.50 | 真实入口CPU在途，0GPU |

新报价从已接受N09全40请求最大值、原18加载／未归属成本和A规划代理重建，所有A、每次完整预热与模型加载、每个观察路径60秒复制／哈希诊断余量和20%总体余量均保留。旧设计预测1.624315／3.019174和旧拟议上限2.25／4不重写；调整是明确加计诊断余量，不是实测费用或速度。

## 两个原CPU身份

共同source `c1c95ce0c598fb7839b0b89f4a69bd45c8aef7c9`，每stage1772源。每卡两命令：完整配置／计划／可逆入口控制组，以及真实Cosmos生产入口`--cpu-check`，禁止CUDA、加载权重与下载。复用未变R2数值闭包，不再重跑258路径。

| kind | 原stage | PID／start_ticks | 单次启动北京时间 |
|---|---|---|---|
| CAL12 | `.sync/wc-scout-cal12-production-entry-cpu-r1-20261018` | 2245370／562857758 | 22:27:54.063 |
| BANK24 | `.sync/wc-scout-bank24-production-entry-cpu-r1-20261018` | 2245680／562861304 | 22:28:29.529 |

- [CAL12原启动](../reports/wc_scout_CAL12_real_entry_CPU_R1_launch_20261018.json)，registration `245d20ba553aafb5730167ade3fbee2d6a03827edc93db3e3a0ce23efa4544d4`。
- [BANK24原启动](../reports/wc_scout_BANK24_real_entry_CPU_R1_launch_20261018.json)，registration `2bc0db0e6747595fd439838155337139ffea76373d3245420871c60801d7e8bd`。

一次半程按两张较晚not-before unix1792333889.5290928，已约22:32；一次完整收件按较晚not-before1792334069.5290928，已约22:35。新自动化由工具实际创建，应用复用了已删除的旧ID：半程`worldcache-cpu`、完整`worldcache-cpu-2`；以各自原launch／source区分任务，不重放旧R2数值CPU。每kind每模式只查一次，已有原件仅离线读，未完按剩余命令另约一次即结束，不监听。

## 接受边界与继续顺序

两张入口CPU尚未验收。即使通过，也只形成`production_entry_CPU_accepted=true / GPU_dispatch_ready=false`，不覆盖新scope尚待实现／独立验证的GPU监督、单次派发、CPU post与逐原件接受链；不能借原24的通过标记自动赋予新scope。完整入口／数值依赖在后续保持不变，生命周期新增代码须另验。

**N10原22:43完整验收及其后原连续24直接启动不变。** 原24 a350ea98／完整五命令CPU已经接受，不等待新探索准备。当前不读取N10科学partial、不修改原stage、不启动新GPU。GPU顺序仍原24终态→CAL12→固定CAL门控参数→BANK24，X-R共享银行。接续执行命令见[runbook](../plans/WC_SCOUT_PRODUCTION_AND_GPU_CONTINUATION_RUNBOOK_20261018.md)。

原R2数值收件自动化已完成删除，新入口半程／完整心跳各一次；如入口验收靠近22:43，先保存接受与接续并结束本轮，让N10按时验收，后续本地生命周期工具开发可在原24在途期间继续。

当前新增GPU提交0、预留0、GPUh0。累计cap226／origin79.99637737158223及历史保持，完整整卡严格<12直接执行，达到12或余额不足才问具体整卡；不拆缩、F/B关闭，无训练、人评、付费VLM或OMR。探索首轮信号不自动合入冻结论文主结果。
