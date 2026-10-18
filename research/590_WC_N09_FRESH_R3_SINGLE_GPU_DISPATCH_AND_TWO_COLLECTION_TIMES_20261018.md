# N09 fresh R3完整40已准入，按实际启动安排两次查收

2026-10-18。**空闲GPU已重新取得，N09原完整40已在GPU0单次准入，原监督、运行器、CPU post和完整5 GPUh预留均通过独立核对。** 当前是执行和财务准入结果，没有新的组件费用、显存结论、视频质量或加速结果。

## 从资源发现到真实准入

[一次资源回执](../reports/wc_two_gpu_resource_readonly_20261018_0718.json)实际观测于07:19:10：两张A6000分别使用约390/24MiB，没有compute进程，两UUID锁可用，本项目无在途预留。v2实结110.8690611545／cap226 GPUh，原origin79.99637737158223与历史不变。

实际派发使用[新授权](../reports/wc_paper_N09_actual40_R3_authorization_20261018_123616.json)和[唯一派发意图](../reports/wc_paper_N09_actual40_R3_single_dispatch_intent_20261018.json)，原R3真实CPU与完整范围在本地复核后，只调用一次客户端。[原始派发回执](../reports/wc_paper_N09_actual40_R3_GPU_launch_20261018_123616.json)记录实际起点为**12:37:23**。资源发现时刻与派发时刻分别保留，不以早先资源快照代替实际启动时间；写标记前的只读预检实际发生于12:37:23，原监督之后仍再次执行fresh v2/UUID准入。

原派发27秒后的[首次观察](../reports/wc_paper_N09_actual40_R3_admission_collection_20261018.json.gz)确认监督进程尚在CPU前置复验，未预留、未有GPU child。没有重派，也不把该pending回执当作失败或准入。按前置复验预计耗时，在原派发四分钟之后只补查一次：[12:41:52原件](../reports/wc_paper_N09_actual40_R3_admission_after_prevalidation_20261018.json.gz)已确认完整准入；[独立接受](../reports/wc_paper_N09_actual40_R3_independent_admission_acceptance_20261018.json)纯离线核对全部1787源、原PID/start_ticks、来源/范围/CPU/授权、账本和自身UUID锁。

| 角色 | 原PID | start_ticks |
|---|---:|---:|
| Supervisor | 1947245 | 559314698 |
| GPU runner | 1947617 | 559319208 |
| CPU post watcher | 1947246 | 559314707 |

原launch_id为`bdf23b68-f180-45ee-9540-f731c04731c5`，run为`wc-paper-n09-runtime-profile40-r1`，GPU0为`GPU-de9a5370-cd87-0f1c-a48e-288888777dd3`。所有句柄均按原PID与start_ticks匹配，不凭名称或锁文件猜测任务身份。

## 冻结范围与费用

source仍为`1de07673a13f0fe441745e94316a0dd81e00348d`，stage仍为`.sync/wc-paper-n09-production-cpu-r3-20261018`。注册SHA `4eea447ab29e28c43f2e70d89f718a40108808f32040f4d5cef753541645c7ae`、实际CPU证明SHA `50859e37c40b9bc45d4e80bef2faa801ad19477d3e5d7724b23c83026f0650cc`保持。原1787 payload、十命令生产CPU、数值和观察器未改，不重跑已接受CPU，旧R2未准入fence与零费原件保留。

完整五冻结角色×两旧CAL×三诊断模式，**10完整预热＋30正式＝40路径，1440 pairs／2880 CFG、一次加载、零在线教师**不缩。对照含原audit、profile audit和profile lean，完整原请求、动作、缓存历史、终态及RGB控制仍须最终核对，全部兼容视频按93帧评分。

整卡预测**4.245833333 GPUh**，计费上限**5 GPUh**，沿用户严格少于12 GPUh自主规则执行。当前独立观测的v2为：实结110.8690611545、活动完整预留5、可准入110.1309388455／cap226。**预留不是已发生费用，本卡实际费仍待原supervisor全wall账单结算。** GPU0锁已取得，另一GPU的空闲不用于并发N10或重模型CPU，以保持N09测量条件。

## 两次后续查收

全部时刻来自原dispatch回执，不回填资源发现时间：

| 检查 | 原最早时刻（北京时间） | 已安排 | 自动化 |
|---|---|---|---|
| 一次半程技术检查 | 10-18 14:47:23.464／unix1792306043.4642522 | **14:48** | `worldcache-n09-r3` |
| 一次完整终态查收 | 10-18 17:22:23.464／unix1792315343.4642522 | **17:23** | `worldcache-n09-r3-2` |

两个自动化均已实际创建为ACTIVE、COUNT=1；首个无目标线程参数的创建请求被工具拒绝，没有创建任务，随后显式指定当前thread成功，两条有效自动化身份如表。半程只核对原技术状态、完整分母和错误线索；不提取质量、逐帧或组件比较。每个时点原件只收一次，已保存时只离线分析。未完按剩余工作量重估一次并结束，不循环等待、缩卡、补点或重派。

完整入口：

```bash
.venv/bin/python scripts/capture_wc_paper_N09_runtime_profile40_r1.py \
  --launch-ref reports/wc_paper_N09_actual40_R3_GPU_launch_20261018_123616.json \
  --mode terminal \
  --output reports/wc_paper_N09_actual40_R3_terminal_collection_20261018.json.gz

.venv/bin/python scripts/analyze_wc_paper_N09_runtime_profile40_r1.py \
  --launch-ref reports/wc_paper_N09_actual40_R3_GPU_launch_20261018_123616.json \
  --capture reports/wc_paper_N09_actual40_R3_terminal_collection_20261018.json.gz \
  --output reports/wc_paper_N09_actual40_R3_terminal_independent_acceptance_20261018.json
```

最终须核对全40原分母、所有适用原件/控制、CPU post退出、组件/显存观察、实际费用及自身GPU释放。拒绝、失败和未到达全部保留；有profiler的单格时间不充当N08重复clean速度，包含关系的区间不充当独立动作单价。连接未知不当任务终态，原件解析失败不导致再次SSH或重派原任务。

## 接续顺序

1. **先完成本卡。** 测量期间保留另一卡，N10及连续修正新GPU不抢开。资源自动化仍每两小时轻量检查；下次不早于14:41:52，约14:45，若距固定查收不足15分钟，则复用该次固定查收读取资源，避免近邻重复查询。
2. **N10完整960自动质量评分。** 原真实生产CPU、完整4.915预测／6.25上限、本地派发/逐项与财务验收链均已准备，见[588](588_WC_N10_FULL960_GPU_CLIENT_AND_INDEPENDENT_TERMINAL_SOURCE_READY_20261018.md)。本卡全部适用原件及费用接受后，按原helper和fresh UUID/v2接续；原645待评/155不可用/160静态N/A、五模型/19对比不缩。当前新分数仍为0。
3. **连续修正完整24。** 原数值88和全部12旧端点及客户端/终态代码准备保持；仍须本卡真实四条A_NO_P完整组件源、已登记R2价格资格、整卡报价及独立生产CPU，A3视频结果为空。

本轮解决的是外部资源等待并真正启动原论文补验，不修改方法或扩张探索。F/B关闭，P和历史网络后置，无训练、人评、付费VLM或OMR。
