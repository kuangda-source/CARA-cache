# N09客户端补充：已占用的GPU不消耗派发标记

2026-10-18。**在等待06:22资源检查时，补上N09单次派发的一个操作边界：若GPU在资源快照后被重新占用，客户端在写派发标记之前再次只读检查显存与进程，明确忙卡时返回零派发。** 原完整40设计、报价、服务器执行版本与实际CPU证明不变。本轮没有SSH或新GPU任务。

## 问题与修改

原[客户端](../scripts/launch_wc_paper_N09_runtime_profile40_r1.py)先重验CPU和全部payload，然后写`N09-GPU-launch-request.json`、调用原监督进程；实际监督进程再取得UUID锁并检查资源。这个最终准入门槛正确，但若前一次资源快照之后GPU被他人占回，仍可能留下没有GPU子进程的派发标记。旧R2的原标记和零费用保持，不清除或重放。

新增`resource_ready_before_fence`在写标记之前检查指定A6000 UUID、8.6计算能力、实际显存和compute进程。显存超过1024MiB或本UUID存在compute进程时，返回`N09_RESOURCE_BUSY_NOT_DISPATCHED_NO_FENCE`，不写授权、独立CPU副本或派发标记，不产生GPU子进程、预留或账单。其他UUID的合法活动不阻止当前空闲卡。

这个检查是只读预检，**不替代原监督进程的逐UUID锁、fresh v2余额和最终资源准入**。预检通过后仍可能发生资源竞争；原监督进程保持最终判断。通信结果未知时仍保留原句柄和禁止重放规则，不能凭超时推断没有启动。

实际派发回执记录本地客户端SHA及预检观测；明确忙卡回执不是GPU启动回执。后续只有在新的两小时资源检查确认可用、原stage确无派发标记后，才可用新的launch_id和输出文件发起下一次首次派发。

## 验证范围

[现有完整CPU/派发控制组](../tests/test_runtime_profile40_cpu_acceptance_r1.py)扩展后**18项全部通过**，包括：

- 模拟显存48189MiB及显存低但本UUID仍有进程两种忙卡：均零子进程、零原件或标记写入、临时账本逐字一致。
- UUID错误、显存负值/N/A、进程观测缺失或PID不可解析时，不允许通过；另一UUID活动可以共存。
- 正常单次派发仍绑定完整40、实际CPU证明及两个查收时点；重复派发拒绝，post子进程派发错误仍保留原监督句柄。
- 原CPU错误、原CPU仍活跃或ETA不合法时，在写标记前拒绝；通信未知不授权重放。

这些检查使用临时夹具与模拟子进程，不是服务器GPU测试或实验结果。完整日志、两个本地文件SHA和原真实CPU绑定见[本地回执](../reports/wc_paper_N09_client_busy_resource_guard_local_CPU_20261018.json)。CLI帮助与语法检查通过。

## 冻结内容与接续

服务器stage仍为`.sync/wc-paper-n09-production-cpu-r3-20261018`，source `1de07673a13f0fe441745e94316a0dd81e00348d`、1787 payload、原实际十命令CPU保持；注册SHA `4eea447ab29e28c43f2e70d89f718a40108808f32040f4d5cef753541645c7ae`，CPU证明SHA `50859e37c40b9bc45d4e80bef2faa801ad19477d3e5d7724b23c83026f0650cc`。本地客户端新增预检，不改写stage内的旧客户端副本、监督进程、运行器或原CPU控制文件。

原五冻结角色×两CAL×三诊断模式、10warm＋30正式、1440pairs/2880CFG、一次加载、零教师不改。整卡预测4.245833333 GPUh／上限5；06:22起按原两小时资源规则查看，满足fresh v2/UUID后优先执行N09，再按半程/ETA各查一次。

N10完整960真实CPU及本地派发/逐项验收链已在[588](588_WC_N10_FULL960_GPU_CLIENT_AND_INDEPENDENT_TERMINAL_SOURCE_READY_20261018.md)接受准备，保持N09收完后接续，测量期间不并发重评分。连续修正完整24仍等真实N09组件观测、绑定报价和生产CPU。累计cap226／origin及历史、严格<12自主门槛不变，F/B关闭。
