# 完整区间动作价格刷新卡 R1

## 本卡目的与已接受前置

原1624全部数值、Native/control/collect参照及费用已通过，见[649](../../research/649_CARA_FULL1624_ACCEPTED_PRICE_AUDIT_AND_REFRESH_SCOPE_20261023.md)。保留其全部1624正式标签，不重跑原资产卡。本卡单独测量受同卡竞争影响的动作价格，作为PG-P1的成本输入；它不新增误差标签，不产生方法端点或净加速结论。

现有价格的112个最近源步格有3轮重复，1512格只有1轮；最近源步CV的P95已达14%–19%，max-source聚合的中位放大约28%–30%。因此本卡在**所有区间格**均做三轮正式重复，保留既定的max-source/场景等权聚合。没有依据原表选择有利子集或改α候选。

## 完整范围

run拟定`wc-policy-price-refresh-cal4-full1624-ada-r1`。源码/执行stage待生产实现后冻结，当前没有提交GPU。

| 项目 | 完整范围 |
|---|---|
| 输入 | 原4CAL、seed0、原35请求步/36实际更新、CFG 8/−7、93帧、432×768 |
| 新路径 | 4 CONTROL + 4 PRICE正式；首CAL各1条CONTROL/PRICE warm；共10路径 |
| 原Native | 复用原完整接受的4条Native及全部36步/最终latent/93帧哈希，不冒充新样本 |
| 区间 | 每CAL406格；1624正式格、406预热格，总2030格 |
| 读出 | 每格 C/A_HALF/A_ONE；1轮warm + 3轮正式，全部真实执行；共24360次成对读出 |
| 分母细分 | 正式路径19488次，预热路径4872次；按轮次则warm轮6090次、正式轮18270次 |
| 普通模型计算 | 10×36=360pairs、720CFG、单load；读出不增加deep teacher |
| 新误差标签 | 0；复用原已接受1624，不导出重复区间原张量 |

各格顺序固定为WARMUP=[C,A_HALF,A_ONE]，FORMAL_1=[A_ONE,A_HALF,C]，FORMAL_2=[C,A_HALF,A_ONE]，FORMAL_3=[A_HALF,A_ONE,C]。完整范围由`src/wcomr/policy_price_refresh_contract_r1.py`及[全卡报价](../../manifests/wc_policy_price_refresh_full1624_whole_quote_r1_20261023.json)定义。报价合同的3项CPU测试通过；这不是生产入口接受。

## 生产实现与接受要求

1. 从已通过的`IntervalAssetsOwner`分离价格专用collector，复用原`ReadoutKernel`、probe/D计时边界、同请求真实D锚点与all-D父轨迹。保留原代码，新增模块和唯一stage。不得只靠猴补全局rounds后又把原标签采集卡整体重跑。
2. 每格校验source/input/older锚点哈希与原接受记录；轮次输出逐位相等。所有shadow读出不写回父轨迹；清理后owner/CPU anchor bank释放。新PRICE不产生新的区间误差评分或全格tensor文件。
3. 新CONTROL与PRICE保存全36 guided/final及可用93帧，与原Native严格核对。若跨卡或环境造成控制不一致，保留原失败，不能忽略后仍替换价格。
4. 计时范围沿原实现：已支付共享probe之后，包含实际WC/head/RF/fusion；数据转运、哈希和输出一致性检查在component计时外，但全部计入整卡GPU占用费用。所有D动作及共享前缀也在独占条件重测，不能只替换C/A而混用受干扰的D/公共开销。
5. 原α=1部署确实也支付C和proposed两次head（`GuidedW1Readout`已明确），因此不得为缩短价格而删掉基线实际仍支付的计算。原isolated readout价格仍是规划组件价，最终策略需完整干净延迟接受。
6. 新runner、supervisor、collector、原件audit和已接受标签的bundle合并需要完整实际生产CPU验证：真实SetupArguments/guardrail/codec、FD锁、容器CPU隐藏GPU、失败保留与清理。原资产CPU证明不能替代本卡新生产CPU。
7. 新supervisor持有项目UUID锁；fresh空闲检查后用已授权sudo仅对该UUID启用EXCLUSIVE_PROCESS。实际CUDA上下文建立后核对唯一PID/start/UID；检查模式及MPS，持续记录计算进程。收到未知状态只恢复原句柄；有竞争则标记价格失败，绝不终止外部进程。结束先释放本上下文，再按约定安全恢复该卡原模式。
8. 终态独立接受完整10路径/24360次价格、全参照、哈希、模式监测、完整账单和释放。替代价格绑定原标签bundle SHA、新价格结果SHA及新profile；保持旧bundle不变，生成新的有效输入包。局部价格验收不冒充PG-P1闭环或部署加速结果。

## 报价、资源及执行顺序

实测原卡GPU墙钟24841.957秒，减去本卡复用的4条Native共1378.308秒；保留原全部collect转运/哈希/存储等开销，不为省去新标签I/O预先扣减费用。新增11340次重复按同格同动作已有warm/formal中的最大观测计价2996.626秒，另留900秒独占准入、监控与退出。合计乘1.25规划裕量得9.500278 GPUh，再按1.2上限裕量向上取0.25小时，整卡上限11.5 GPUh。

受干扰计时在这里仅用于保守资源规划，不是干净动作成本。11.5低于既定自主执行的12门槛，仍须新的CPU、源码冻结、fresh资源与账本准入，不复用原资产卡12 GPUh批准。若生产实现使完整报价上升，按新全卡报价处理，不缩卡凑门槛。

原卡结算后累计125.646552 GPUh；旧两卡未知责任预留16.5，cap226内可用83.853448。本卡尚未预留或产生费用。最近四卡均被占用，见`reports/wc_policy_price_refresh_resource_20261023_0840.json`中的实际观测时间。先完成本卡生产实现与CPU接受，等实际空闲/独占后单次启动；随后按实际启动时间设置半程和全程。价格通过后推进PG-P1，历史诊断和少步Native安排保持648方案。

## 2026-10-23生产接受与控制器补充

完整生产CPU、两flow48路径/48720新读出及六项生命周期检查现已接受，见[651](../../research/651_CARA_PRICE_CPU_ACCEPTED_CONTROLLER_READY_WAIT_EXCLUSIVE_20261023.md)。执行stage/source保持CEC原冻结版本；新控制器`scripts/wc_four_card_price_refresh_gpu_r1.py`另行绑定已发布Git版本，终态接受器为`src/wcomr/policy_price_terminal_r1.py`。32项CPU检查通过，硬件独占仍待空闲卡实际启用验证。

在GPU开始前固定监测可接受间隔：连续记录以及末次记录到GPU结算不得超过45秒；原循环约2秒，驱动查询各15秒超时。错误上下文、MPS、模式丢失或超长未知间隔均不能接受干净价格，不用观测CV替代独占证据。安全模式恢复延期单独跟踪，不驱逐外部进程。价格接受后报告所有1624格的重复波动、顺序漂移和max-source聚合放大，保留既定聚合规则。

截至实际10:00:11全准入仅GPU_BUSY未满足。新GPU提交、费用与模式修改均为0；已完成CPU不重派，原1624不重复收件。
