# N10完整960真实生产CPU已接受，N09继续等待GPU资源

2026-10-18。**N10已经从输入准备推进到完整生产合同的服务器验收：271个源文件、实际五模型证明、全部960位置、完整报价及五条CPU命令均通过独立检查。** 当前未启动N10评分GPU，新增质量分数仍为0。

## 实际生产CPU结果

[单次派发](../reports/wc_paper_N10_full960_production_CPU_R1_launch_20261018.json)固定source `d10e992614a1249dc61668f7791f4e5144e50480`、独立stage `.sync/wc-paper-n10-full960-production-cpu-r1-20261018`、原PID1740470／start556323483。271 payload包含原244源的只读复制和新配置／代码；原目录未修改。

原半程与完整原件各查收一次，[完整捕获](../reports/wc_paper_N10_full960_production_CPU_R1_collection_20261018_042130.json.gz)保存后纯离线执行[独立接受](../reports/wc_paper_N10_full960_production_CPU_R1_independent_acceptance_20261018.json)：

- 四组CPU控制与实际完整960运行入口，共**五命令全部退出0**，bundle实际耗时**31.1677秒**。
- 全部271实际payload SHA、注册／source、原CPU句柄与终态、配置和五命令身份通过；原五模型CPU证明重新接受，构造器／权重／模型范围保持。
- 原160生成位置／960指标位置、五模型、19对比和全部输入指纹不变；645待评分、155视频不可用、160静态N/A均保留。
- 工程报价4.915 GPUh／计费上限6.25 GPUh从原件重新计算并与实际配置匹配；没有把CPU秒数当GPU吞吐。
- 未加载模型权重／初始化CUDA，未写真实预算，0新质量分数／GPU费用／GPU预留。

注册SHA为`25b562b78d4dfa040e4611b0062bb1f313e59e5d6f46e021d7000db232a4aaed`，实际生产CPU证明SHA为`6aeb1bec2d49d86dfa890de35e2ef6c3c975572a16c76fb1503ca69953d046b7`。原PID已不存在；CPU两时点均收完，`worldcache-n10-cpu`自动化已删除，不重复查旧句柄。

## 04:22批次资源查收

[一次轻量资源原件](../reports/wc_two_gpu_resource_readonly_20261018_0422.json)实际观测于04:23:09：GPU0约48189 MiB、GPU1约47822 MiB，仍由原PID1615193／1615194占用。利用率当时为0，但显存已占满，不能当作空闲卡。自身两UUID锁可用，原项目没有在途GPU任务，未派发N09或N10。

本次fresh v2为**110.8690611545／226 GPUh实结**、预留0、可用**115.1309388455 GPUh**；origin79.99637737158223及所有历史费用保持。没有实际预算耗尽。`worldcache-gpu`继续每两小时查看，下次不早于北京时间**06:22**；延后送达的04:22心跳只读已有本地回执，不重复SSH。

## 下一步

1. **N09完整40仍优先。** fresh R3实际CPU已接受，原预测4.245833333／上限5保持；有真正可用的UUID时按原source／证明／fresh v2直接准入，不重跑CPU、不重放旧R2 fence。正式GPU测速不并发重模型CPU或评分。
2. **N10接GPU派发与终态工具。** 实际执行器／监督与完整生产CPU已具备，还需完成客户端单次派发和逐项journal／960指标／19对比／实际费用的独立终态接受工具，再依原完整6.25上限与资源准入进入评分。CPU接受不当成GPU准入或质量结果。
3. **连续修正完整24保持。** 88数值和旧12绑定、执行／收件／验收代码已准备；真实N09组件观测、整卡报价、实际生产CPU和A3终点仍待。原N12结果保留，不以旧结果填新臂。

实际模型CPU、生产合同CPU、工程预算和最终科学证据分别记录。预算及假设见[585](585_WC_N10_WHOLE960_ENGINEERING_BUDGET_AND_PRODUCTION_CPU_READY_20261018.md)，实际派发过程见[586](586_WC_N10_QUOTED_FULL960_ACTUAL_PRODUCTION_CPU_RUNNING_20261018.md)。单次严格少于12自主、半程／ETA各一次查收、F/B关闭及无新生成／训练／人评／付费VLM／OMR保持。
