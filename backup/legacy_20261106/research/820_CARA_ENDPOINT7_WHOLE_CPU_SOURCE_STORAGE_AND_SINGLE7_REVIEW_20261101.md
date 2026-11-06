# 820 — E1完整CPU、生产源与独立存储完成，提交单次7 GPUh审阅

2026-11-01，Asia/Shanghai。用户已选46路径；本轮把七角色端点卡准备到可审阅状态，未派GPU、未预约费用、未访问四卡。核心实验判断仍待真实完整终点结果。

## 本轮完成

1. 修复容器构造器仍仅接受旧25/32的遗漏；生产入口、容器和源绑定统一为46路径/16新评分。把新卷8GiB低水位、准备前80GiB及分配后宿主16GiB落实到profile和校验器。46项本地旧/新分支回归通过。
2. 最终Linux组合R1在导入期失败，保留原退出1与源e28e9389。补齐复用准入与汇总依赖后，R2源7974fe62原CPU退出0，16项通过，用时11.692649秒；在真实Linux输出标明CPU fixture的PNG/PDF/CSV/JSON。未重跑818的46条数值路由或819的16对真实合成评分。
3. 新卡中央事务模块用临时账本完成13项本地及Linux检查，源af7c7d8e原CPU退出0，用时0.675212秒；涵盖重复预约恢复、旧16.5责任、失败/超限实耗与唯一结算。没有接触真实中央账本。
4. 在两卡为本卡新建独立64GiB ext4卷与48MiB控制日志，原provision进程已退出。1MiB fsync/读取SHA一致、探针移除、输出空、日志全零；loop44/device1836/inode12981453315与旧卡不同。复用未变的完整93帧I/O组件证据，不把1MiB探针称为完整I/O吞吐测量。
5. 离线组合既有采集、runner、工件、评分、恢复、guardian及一次派发CPU原件与本轮差量，形成整卡证明。1268源文件的当前SHA、已发布Git归档及实际Linux源一致，Python静态依赖闭合。原数值路由的执行主体AST一致；新增production分母入口另有接口控制，物理矩阵和每个实际role精确一致。
6. 生产源af7c7d8e准备至`cara-S-endpoint-GPU-a6000-seven46-r1-20261101`，注册SHA`f7010a983692ef30c3a93e23d7fc7d8407633c7e050a749635a1d743e9d72ae5`。源、runtime、存储、报价和CPU proof已绑定；没有GPU授权文件、意图或容器。实际复用入口核对16原MP4及16参数文件，并核对原完整搜索冻结，不重解码或评分。

## 实验与费用

[完整审批卡](../plans/cara_next_stage_20261101/e1/ENDPOINT7_SINGLE7GPUH_REVIEW_R1.md)固定七角色、四旧CAL、46物理路径、28逻辑位置、16新对＋12原评分、13个RGB门及38个干净计时位置。主要比较CFG对DIAG、F19风险交换对F19-C，以及冻结搜索对强简单基线。F19-C加入同批计时，Uniform时间仍是旧批参照。

完整预计6.040146521 GPUh、拟硬7，90°C停止与600秒释放余量；释放后CPU评分2线程/8GiB/2小时。最后中央快照可用18.515811725已扣除旧16.5责任，非fresh准入。当前唯一待用户决定的是批准这张单次7GPUh及本卡原中央账本读取/预约/实际结算例外。批准前不探测四卡，不沿用旧搜索卡许可。

## 边界与下一步

CPU验收不是Cosmos真实GPU质量/速度或实际Docker GPU生命周期证据。批准后仍须真实资产/runtime、原句柄、当前GPU/独占/内存/磁盘和原中央资金准入。安排实际开始绑定的一次半程和一次终验，完整46释放后唯一计费，13门通过再一次16对评分，完整28后汇总，不读取部分科学分数。失败不自动重派/下一卡。

A32/B36/S/Q、搜索赢家、原WC/RA FIT UNMATCHED及四旧CAL范围均保持；最终TEST没有访问，论文科学表没有新结果行。Euler-E0原35更新/70CFG CPU组件保持，不阻塞本卡，也不宣称Euler整卡准备完成。

## 证据入口

- [准备总结](../reports/cara_endpoint7_final_review_ready_r1_20261101.json)
- [整卡CPU证明](../reports/cara_endpoint7_whole_CPU_accepted_r1_20261101.json)
- [最终16项原终态接受](../reports/cara_endpoint7_final_CPU_accepted_r2_20261101.json)
- [中央13项原终态接受](../reports/cara_endpoint7_central_CPU_accepted_r1_20261101.json)
- [原R1失败](../reports/cara_endpoint7_final_CPU_capture_r1_20261101.json)
- [独立存储接受](../reports/cara_endpoint7_storage_accepted_r1_20261101.json)
- [生产源及原件复用核验](../reports/cara_endpoint7_source_preparation_r1_20261101.json)
