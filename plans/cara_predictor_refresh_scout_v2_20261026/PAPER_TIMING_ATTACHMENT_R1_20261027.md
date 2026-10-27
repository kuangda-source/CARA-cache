# 后续方法实验：准确论文时钟附加合同 R1

2026-10-27，仅增量工程附件，不覆盖SCOUT V2/V2.2、旧完整请求口径、原α或强基线。无新GPU启动/预约；IG继续暂停，R4_COMMON_LONG仍不是已晋级j1。

## 入口与绑定

- [冻结源码/双端CPU绑定](../../manifests/cara_paper_timing_attachment_r1_20261027.json)
- [724完整CPU记录](../../research/724_CARA_EXACT_PAPER_TIMING_DUAL_HOST_CPU_AND_METHOD_HANDOFF_20261027.md)
- 新卡的固定角色调用点使用`wcomr.method_experiment_timing_r1.TimedRequests`，参数/角色/掩码/冻结请求仍来自该卡自己的注册表。默认四卡，执行后锁定host，不跨卡拼时间。

```python
from wcomr.method_experiment_timing_r1 import TimedRequests
requests = TimedRequests(
    inference=inference, samples=samples, profile=profile, roles=roles,
    schedules=schedules, common=common,
    timing_host=registered_host,       # four_card or two_card
    timing_cpu_validation=False,      # production requires existing admitted CUDA context
)
requests.validate_slots(matrix)       # original immutable schema and registered grids
result = requests(slot, output_path)  # same attempted-slot fence; failures cannot replay
```

新增字段`paper_denoise_decode_seconds`和`paper_timing`，保留`full_request_seconds`、`core_seconds`、原`timing_boundary`与四分量。使用原collect持久化字典时，新字段会随request.json和原件hash保存；后续新卡完整CPU/终态接受必须明确核对新增字段，不能凭本附件替代整卡组合验收。

对原parent/scout路径提供`scout_parent`包装；有shadow、audit、拷贝/hash时不准作为部署延迟。这个包装已接入公共计时结构，但本次完整数值CPU覆盖的是上面四个原角色，**没有**宣称新R4/完整shadow组合生产已接受。新读出接好后按受影响真实入口补CPU，不重做未变环节。

## 准确边界与时间解释

原NVIDIA sampler源码SHA核验、实际绑定函数AST核验后，仅在真正`for _, t in enumerate(timesteps_iter)`之前放入起点，在循环后标记完成；起点同步GPU后读取单调纳秒时钟。另一端在`model.decode`返回、同步GPU后记录结束。连续区间保留循环后到decode之间的工作；不相加分散段、不从第一次velocity调用起算，不扣probe/决策/warping开销，不逐步同步。

源码编译/适配安装在原请求外，单独记录`adapter_setup_seconds_excluded_from_request_included_in_job`，必须计入整卡实际占用。新增两次GPU同步位于原请求内部，原完整请求测量会包含其开销。GPU上的量测开销尚未验证，下一张实际授权卡应保留计时开关数值控制；不得将CPU耗时作为GPU性能。

本实现先支持已绑定Cosmos 36更新与已登记少步Native；CPU实际覆盖36和27更新。未绑定求解器、LoRA/自回归/多次decode、被改写的生成函数不能静默套用，须另验支持域。真正GPU运行校验已初始化上下文与所选host的SM89/SM86；CPU接受不冒充GPU设备核验。

## 结果与失败处理

- 成功：恰好一个循环开始、一个循环完成、一个decode；solver/CFG对数与注册数一致；`0 < paper <= core <= full`；两次同步与原始起止整数保留。
- 文本拒绝：新时钟为null，不能填0并计入加速均值；视频拒绝即使存在完整区间也不准进入成功延迟样本。
- 异常/缺decode/重复开始/重复decode/错误顺序/反向时钟/源码不符：保留原失败，不产生可用论文时钟；实例方法在异常后恢复，无模块全局补丁。
- `audit`、shadow、guided拷贝、hash及research checkpoint自动使`deployment_latency_eligible=false`；保留诊断连续墙钟作费用解释，不能宣称纯部署速度。
- 同一请求三种时间、同批同输入Native分母、先prompt内平均重复再等权平均。模型加载与预热单列且计费；论文未明确预热次数，不能写成“复现论文预热次数”。

## 后续科学与预算边界

该附件改变的是可观测字段。后续仍先完成预测器生产/成本/冻结决策等原依赖；没有j1就不自动提交E2。不得为补时钟重跑已完成DEV128/CAL66，也不自动启动722的16路径备用方案。

最终验收继续使用完整请求`min(257.7712338712067秒, 0.8×fresh Native)`，累计226GPUh、旧16.5未知责任与所有原接受/失败不变。新卡必须另绑定完整范围、源码、双端受影响CPU、完整报价、原授权和fresh独占/存储/账本，计时附件本身不授予GPU权限。
