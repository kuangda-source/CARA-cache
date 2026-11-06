# N09完整40的新独立CPU目录已启动

2026-10-18。N10五模型R2及实际960输入绑定已完成，[578](578_WC_N10_ALL_FIVE_REAL_CPU_ACCEPTED_AND_ACTUAL_SCORER_FULL960_BOUND_20261018.md)已推送；等待GPU期间，继续准备N09的完整部署成本测量。

原N09 R2真实CPU已接受，但原GPU派发未准入，0生成、0GPU费用。旧目录的dispatch fence和原未准入记录保留。本轮只在fresh目录执行同一完整生产CPU，不重放原GPU派发。

## 当前原句柄

[实际启动回执](../reports/wc_paper_N09_actual40_production_CPU_R3_launch_20261018.json)：

- 源：`1de07673a13f0fe441745e94316a0dd81e00348d`。
- 目录：`.sync/wc-paper-n09-production-cpu-r3-20261018`。
- CPU PID：1699795，start_ticks：555732410。
- 注册SHA：`4eea447ab29e28c43f2e70d89f718a40108808f32040f4d5cef753541645c7ae`。
- 1787个payload、194个overlay、10条完整CPU命令；原配置SHA `afea36a3e9487556438c4f70dc95c7143b7c39559e13368a7c4cca40fe974adc`不变。
- 实际启动：北京时间02:40:20.584985。一次技术半程安排02:43（最早02:42:50.584985）；完整原件验收安排02:46（最早02:45:20.584985）。两个自动化分别为`worldcache-n09-r3-cpu`、`worldcache-n09-r3-cpu-2`，各一次，完成后删除。

当前只是CPU启动；新stage的全部CPU接受和GPU准入仍待。未进行新的GPU资源查询，未分配GPU、预留预算或产生GPU费用。

## 完整范围和接续

N09保留五冻结角色×两旧CAL，10完整预热＋30正式＝40路径、1440 pairs／2880 CFG／一次模型加载。正式包含原audit、profile audit和profile lean各10条，保留全部等价及输出控制，不以子集替代完整卡。

原整卡预测4.2458333333 GPUh、计费上限5 GPUh不变。CPU完整接受后进入ready状态；按用户最新要求，由`worldcache-gpu`每两小时一次检查实际UUID／显存／进程／锁／v2账本，有可用资源才依fresh准入执行。上次观察两卡均为其他账号满显存占用，不能把这个旧快照当本轮新的资源核对，也不干预他人进程。

N09实际GPU测量不与重CPU模型／评分并发。完整卡严格少于12 GPUh可按既有授权推进；累计cap226、origin79.99637737158223及历史支出保持，最近接受快照实结110.8690611545／预留0／可用115.1309388455 GPUh，准入时仍读fresh权威账本。

N10完整评分的报价／真实生产CPU／GPU待，当前新质量分数0；连续修正88数值CPU已接受，完整24生产／旧12端点及四warm控制／基于N09价格的报价待，A3结果空。F/B关闭，无训练、人评、付费VLM或OMR。
