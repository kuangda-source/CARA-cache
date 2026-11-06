# N09实际配置的查收时延修复与当前源码包

2026-10-17。本轮在实际服务器CPU／GPU之前修复了N09选卡配置的漏项：GPU派发器必须读取 `first_collection_delay_seconds`，原选卡配置未填，旧CPU合同也未覆盖该字段。使用原派发源码中的四条时延语句，在原实际配置上重现 `KeyError`；没有执行远端BOOT、创建派发fence或启动GPU。

## 当前时间安排

| 项目 | 相对实际派发时间 |
|---|---|
| 半程技术检查 | +7,800秒，约2小时10分 |
| 完整查收 | +17,100秒，4小时45分 |
| 原整卡GPUh预测 | 4.245833333 GPUh，约15,285秒 |
| 计费上限 | 原5 GPUh不变 |

完整查收比原GPU规划多约1,815秒供CPU后处理，绝对时刻须由真正派发回执生成，当前未创建N09自动化。CPU合同现在提前检查必须的首查收字段、数值有限性、半程早于终态及终态不早于GPU规划。

## 回归与范围保持

9组74项本地控制全部通过；实际已接受N07 R2/N08原件也重新通过合同。原派发器四条时延语句在新实际配置上通过，返回7,800／17,100秒。

首轮新检查同时暴露了旧测试夹具的时间矛盾：它将终态改为20分钟，却继承了更晚的半程参数。旧失败日志保留；夹具现沿用一致的预测／半程／终态，派发测试按配置参数检查两个绝对时点。没有放宽真实接受条件。

实际配置相对Git `7ebe21c` 版本只新增三项：首查收时延、半程时延和其登记依据。方法、全部40路径／1440pairs／一次加载、五冻结角色、参考原件、4.245833333预测／5GPUh上限、cap226／原origin和输入指纹均保持。原四份观察／数值源码与99数值依赖仍与既有证明逐字节一致，未重跑952或102路径。

当前配置SHA：`afea36a3e9487556438c4f70dc95c7143b7c39559e13368a7c4cca40fe974adc`。完整源码dry plan仍为194文件；旧34393配置和7ebe21c归档接受保留为历史，不能冒充当前配置的实际服务器CPU或GPU证明。当前194文件已从Git `7ab9a39ac672a7d02a5c2695147d387efca17223` 归档并逐字节接受；实际服务器十命令CPU和资源／预算准入仍待N12验收后接续。

## 原件

- [原实际配置与派发语句失败复现](../reports/wc_paper_N09_actual_config_missing_dispatch_timing_reproduction_20261017.json)
- [首轮夹具失败保留](../reports/wc_paper_N09_timing_contract_local_CPU_failure_retained_r2_20261017.json)
- [74项及实际合同接受](../reports/wc_paper_N09_actual40_dispatch_timing_local_CPU_acceptance_r3_20261017.json)
- [当前194文件dry plan及仅时间字段变更核对](../reports/wc_paper_N09_actual40_source_packet_dry_plan_r2_20261017.json)
- [当前194文件Git归档接受](../reports/wc_paper_N09_complete194_Git_packet_local_acceptance_r2_20261017.json)
- [实际配置](../configs/wc_paper_N09_runtime_profile40_production_r1_20261016.json)

本轮0SSH、0GPU、0模型权重、0账本写。N12原source/stage及10月18日00:01验收保持，未提前读科学partial；N10五模型和质量评分仍待，F/B保持关闭。
