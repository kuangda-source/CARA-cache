# N07完整180：修复版真实生产CPU已单次启动

2026-10-16。**执行测试的依赖闭合修复通过后，原完整N07真实生产CPU已在新的R2目录重新单次派发。** 八新prompt、双seed、十方法、160正式+20完整预热/180、6318pairs/12636CFG和整卡价格全部保持；未运行新GPU、未修改服务器预算。

原失败见[499](499_WC_N07_R1_CPU_TEST_DEPENDENCY_FAILURE_R2_PACKAGING_REPAIR_20261016.md)：R1第三组后处理测试漏传automatic_quality模块，21.436405秒退出1、CPU_accepted=false、原件全保留。只补Python测试文件的导入闭合；临时Git归档→隔离stage→实际冷Python导入回归及原8项打包控制共9项通过；同一打包器的N08受影响7顶层CPU通过，原99数值执行SHA全部不变。没有删测试、拼接R1前两组通过结果或重跑952。

## R2原句柄与一次查收

- source `140d0a6af7d5be16d1b191ab3a8e68ffe83d0007`，stage `.sync/wc-paper-n07-production-cpu-r2-20261016`。
- 原CPU PID1111913 / start_ticks541989964，启动2026-10-16 12:29:56.128427 Asia/Shanghai。
- 注册SHA `ebf9703a7babd41d4a8b6cf473427e2a66c5a5a689ff92fd094048c496f304f4`；全1725payload / 158overlay；仍六命令：五组控制＋真实Cosmos无权重CPU入口。
- 最早查收12:33:56.128427，unix1792125236.128427；本次安排**12:35一次收**。原R1已终态/已收，不再查询；R2未到ETA不SSH或看partial。

届时使用原capture工具配合R2 launch-ref，保存一份新回执后只离线accept。必须核对六命令全部退出0、原PID终态、注册/全1725SHA、160真实typed参数、原180排程、Native17/43和guardrail、99数值依赖、全部无CUDA/模型加载/账本写，才算生产CPU接受。若未完成，据剩余量重估另约一次并立即结束，不循环监听；若失败，原件保持，用新版本处理具体问题。

## 整卡与预算仍待直接人类批准

N07完整180整卡预计及计费上限15.055555556GPUh，N08原完整40预计3.6275；现池12:05保存余额11.389538676，原cap104.971363333/实结93.581824657/预留0不变。配置拟议113仅供CPU后具体审批，不是已应用的服务器预算；origin79.99637737158223与历史不重置。

另备的cap增量函数通过5项临时账本CPU，原used/全部任务和活动预留保留，未部署或执行到服务器。CPU全部接受后才询问完整>=12卡与拟议cap113，届时不重复请求已授予的常规CPU权限；未获批准不派GPU、不预留或改cap。

N05/N06已完整接受，不重复查询；主线N07→N08→N09/10。P/T1后排，F/B关闭，无训练、OMR、人评。完成本R2查收后暂停自动化，未来GPU如获准再按自身ETA安排一次收。

## 原件

- [R2 launch](../reports/wc_paper_N07_actual_production_CPU_R2_launch_20261016.json) · SHA256 `c1bc7dd1e5569ae28134d8665f177d1a52398a8cf9cfb75cfc88daf6c4383494`。
- [R1原始失败](../reports/wc_paper_N07_actual_production_CPU_R1_collection_20261016_1227.json.gz)。
- [R2打包修复/完整范围](../reports/wc_paper_N07_actual_packaging_R2_repair_and_unchanged_scope_20261016.json)。
