# N07完整180修复：真实服务器生产CPU已接受

2026-10-16。**独立修复版本已完成并通过服务器九命令生产CPU验证及离线接受。** 全1750份文件SHA、原完整160参数变体、180排程、99数值依赖、520修复证明和8项实际guardrail检查通过。GPU尚未派发，原失败R1保持；下一步是收尾R2整卡派发与科学验收绑定，再进行具体整卡执行确认。

## 从Git包到真实CPU

源码`6e10aa31197b4c137705b9117090c3a4e538e863`的183份Git overlay先在本地隔离目录通过九组49项控制与八个冷入口。隔离测试使用明确的空合成基座，只证明完整overlay闭合；不是伪造服务器原基座。实际部署仍只读核验原N05完整基座的registration SHA，再构造独立目录。

服务器stage为`.sync/wc-paper-n07-refusal-repair-production-cpu-r1-20261016`，原CPU PID1166058/start545521711于22:18:33.597单次启动。原最早查收22:22:33.597；实际于22:23:07.400只查收一次，原句柄已退出，九命令全部退出0。九命令CPU包记录耗时147.990535秒，没有CUDA初始化、模型权重加载或账本写入。

registration SHA为`cb349ca8f5ab314476c5fb8f444f1c902a90e2603677bf92f6c37d37bf60bfb2`；R2 config SHA为`5531dadd5d2544d9e8696e640097469e3a92e56e514651d3c27d6f7449f8fb63`。全部1750份实际payload校验通过；真实Cosmos参数类型构造保持160变体、原八提示词/双seed/十方法/180位置；实际Native类来源与两Native、两固定mask在两seed的缺guardrail拒绝共8项通过。

生产CPU没有完整运行Cosmos去噪或生成真实视频。它证明了部署、真实入口、类型/源码/资产和guardrail准备；520两flow采样回归仍复用原Tiny/Toy证明，不把它说成真实GPU修复或终点方法结果。

## 两处本地只读工具修正

原服务器stage始终保持6e10aa3，没有为读者修正重派CPU。

- 远端观察器使用system `python3`，应保持标准库依赖。冷Python已复现新生产合同会带入Torch owner的导入依赖；本地只读collector改用固定config路径标量，避免导入该生产模块。4项本地控制通过，实际一次SSH查收成功。
- 首次离线接受暴露`KeyError: project`：原启动回执记录的是stage，没有project字段。保留失败记录后，接受器从原绝对`.sync`子目录严格推导project，仍核对bundle的stage/project，并拒绝额外字段冲突。5项本地接受控制和同一原件的再次离线接受通过；没有第二次SSH。

533/534及隔离49项证明对应6e10aa3原stage，不追认为当前本地读者的新字节。实际生产GPU使用的`validate_bundle`、`validate_proof`与6e10aa3逐函数AST一致，修正只涉及本地观察/接受。新增读者源码SHA与失败记录另存，旧证明、CPU原件和原stage不覆盖。

## 接下来与执行边界

R2运行入口、逐UUID监督、只读post与触发器都在已验源码内。还须补齐R2本地单次GPU派发、半程/终态查收、独立科学接受，以及N08/N09对R2原件的接续绑定；完成后才能提交完整卡的具体执行确认。当前报价仍是原完整180的15.055555556GPUh，达到用户12GPUh门槛；旧R1批准未转用，未预留新GPU费用，也未增加cap113。

原R1在10月17日05:30仍按原工具收全部180真实失败/拒绝/缺失及可用原件，不提前读取其终点科学内容；R2也不靠R1部分正例选择方法。原8提示词、seed17/43、十方法、N08五角色、参数与完整控制设计保持。F/B关闭，无训练、OMR或新人评。

本轮实际服务器动作仅一次独立CPU部署、一次ETA后只读查收；GPU提交0，服务器原N07目录/共享runtime/账本未改。预算仍是532时点实结96.278971908/113、预留0的既有快照，未来GPU准入重新核对。

原件：[Git隔离验证](../reports/wc_paper_N07_repair180_full_Git_packet_isolated_CPU_R1_20261016.json)、[原启动](../reports/wc_paper_N07_refusal_repair180_actual_production_CPU_R1_launch_20261016.json)、[唯一原件查收](../reports/wc_paper_N07_refusal_repair180_actual_production_CPU_R1_collection_20261016_2223.json.gz)、[独立接受](../reports/wc_paper_N07_refusal_repair180_actual_production_CPU_R1_independent_acceptance_20261016.json)、[读者修正与AST边界](../reports/wc_paper_N07_repair_actual_CPU_readonly_acceptor_fixes_acceptance_20261016.json)、[原离线字段失败](../reports/wc_paper_N07_repair_actual_CPU_independent_acceptance_R1_local_schema_failure_20261016.json)。
