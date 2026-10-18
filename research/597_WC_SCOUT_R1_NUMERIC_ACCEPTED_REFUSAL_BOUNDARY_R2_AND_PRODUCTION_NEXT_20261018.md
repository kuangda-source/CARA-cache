# 探索248原版已接受：补齐拒绝边界后继续真实生产入口验证

2026-10-18。**原R1完整248数值CPU已独立接受：CAL12=80、BANK24=168，完整36步、两flow、audit/lean、观察器OFF/ON、旧前缀或全轨迹与owner控制均通过，实际950.578805秒。** 这为新观察器的等价性提供了完整采样证据；新卡尚无视频质量或速度结果，也没有启动GPU。

## 原件与已完成的身份审计

- 原R1 source `bbc631093e99cd7e17b30435c875fa5ef3f359ff`、stage与全部原件保留。
- [R1完整收件](../reports/wc_scout_numeric248_actual_CPU_R1_collection_20261018.json.gz)／[R1独立接受](../reports/wc_scout_numeric248_actual_CPU_R1_independent_acceptance_20261018.json)。该版未包含拒绝控制。
- [DEV6身份审计R1](../reports/wc_scout_DEV6_fresh_project_exposure_R1_20261018.json)扫描1759目录、读取215份元数据，无身份命中；其中两大文件超过32MiB读取界限，原记录明确保留错误，因此R1本身不通过。
- [只补齐两大文件的R2](../reports/wc_scout_DEV6_fresh_project_exposure_R2_completion_20261018.json)以流式哈希和身份字符串匹配完整读两文件，不提取质量值、不读N10质量目录；无命中、无错误，合并项目输出范围身份审计通过。它不证明项目外或未记录的全球未曝光；六输入仅为探索DEV，仍从未来最终测试中排除。

原完整收件自动化`worldcache-248-cpu-2`已删除。N10原22:43与其后原连续24顺序保持。

## 生产适配发现的边界及R2重验

源码检查发现一个实际生产边界漏项：若文本安全管线在采样前拒绝，非Native入口仍会把空的动作历史与完整36动作比较，从而将普通TEXT_REJECTED误报成技术不一致。原完整采样248通过不覆盖这项拒绝情况；它不是视频结果失败，也不改变旧科学结论。

修复只在TEXT_REJECTED时跳过完整动作比较；成功和VIDEO_REJECTED仍要求完整36动作、来源不伪写、owner释放。所有拒绝留在原分母，不换样、不补生成。新[预登记](../plans/WC_SCOUT_TEXT_REFUSAL_BOUNDARY_R2_PREREG_20261018.md)保留原全部248，另加两flow×五方法共10个模拟普通guard返回空路径的控制。

R2已单次启动：

- source `db1de113daa1bf8f719f09566f3db3625c254b83`
- stage `.sync/wc-scout-numeric248-cpu-r2-20261018`
- PID2230226／start_ticks562657668，1759源
- registration `a234a563b6d3ef14eaf52d8ba5c03c4742c8698bd3430c64126061fde6ecfc71`
- [R2实际启动](../reports/wc_scout_numeric248_actual_CPU_R2_launch_20261018.json)：21:54:33.164，尚未接受。
- 半程最早unix1792332573.1644146，约22:10，自动化`worldcache-cpu`；终态最早1792333473.1644146，约22:25，自动化`worldcache-cpu-2`。均已实际创建ACTIVE、COUNT=1，每项只收一次，不持续监听。

## 已准备的生产入口与下一步

新`scout_production_entry_r1`和可逆入口适配已实现，重用真实Cosmos SetupArguments／InferenceArguments、普通guardrails和原采样入口；CAL12完整12、BANK24完整24不缩。入口分别绑定R2数值原件、DEV6审计、冻结请求／mask／完整报价，以及全部加载、完整预热、复制与哈希诊断成本。报价为真实N09完整请求最大值、原18加载与未归属成本、A规划代理，再加每观察路径60秒明确余量；组件包含区间不称独立动作单价，原粗估保留。

本地只完成语法、三项CLI及原执行器可逆适配检查。**真实生产入口CPU尚未跑，GPU监督／post／完整原件接受链仍待适配。** 接下来先让原R2完整数值及10拒绝控制通过，再生成两张实际配置／报价、冻结到Git，分别部署真实生产入口CPU。入口CPU单独记录为ENTRY_ONLY，不继承原24的GPU准入标志，也不把它说成完整GPU生命周期验收；后续监督与post必须独立验证、与该数值闭包保持一致。

实际CLI和后续约定见[生产接续入口](../plans/WC_SCOUT_PRODUCTION_AND_GPU_CONTINUATION_RUNBOOK_20261018.md)。原24 source a350ea98／五命令CPU接受始终有效，N10原22:43接受后直接启动原24，不能重复CPU、提前派发探索卡或干扰N10。GPU顺序仍为原24→CAL12→BANK24，X-R共享银行；单次严格少于12GPUh自主、cap226／origin和历史保持，无新GPU、预留或费用。

新探索首轮信号不自动并入冻结主稿，F/B保持关闭，无训练、人评、付费VLM或OMR。

## 22:10 R2半程：原句柄结束，保留22:25逐项接受

[一次半程原件](../reports/wc_scout_numeric248_actual_CPU_R2_midpoint_20261018.json.gz)与[离线技术核对](../reports/wc_scout_numeric248_R2_midpoint_independent_technical_acceptance_20261018.json)确认原PID2230226已不存在，worker SHA一致，CAL12／BANK24／bundle三文件存在，有界日志未见错误线索。此处未读三证明内容，不判断新248＋10通过；原22:25完整收件、N10原22:43均保持。半程自动化worldcache-cpu已删除，不重复查收或启动新GPU。
