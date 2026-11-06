# N09记录器静态绑定方法兼容性修复：原R1保留，完整R2已派发

**本次CPU验收定位并修正了计时记录器的静态对象兼容问题，未改变模型、缓存或调度。** 原R1在第一个profile的VAE边界装载时失败，原失败已封存；新七项标量控制通过，完整102路径以独立source重新验证。

## 1. 原失败发生在哪里

06:20:42左右按已登记最早时间后只查原PID10329一次，已终态/exit1；source65f91ee、全部封存payload SHA一致。错误为`cannot create weak reference to types.SimpleNamespace object`，在`RequestProfile.bind`对Toy model.decode构造WeakMethod时发生。一个原audit mock已生成，完整profile为0；不能把原102卡当作通过。

这是记录器与静态Toy model方法的兼容问题。原R1 stage、一个mock、原failure/exit/捕获均保留；本地一次捕获`reports/wc_deployment_profile_full102_local_CPU_R1_collection_20261016_0621.json.gz`以及独立失败回执`reports/wc_deployment_profile_full102_R1_terminal_failure_preserved_20261016.json`，后续不再查旧句柄。它不是算法质量的负结果。

## 2. 修了什么

`bind`先确定owner能否弱引用，再构造原方法的恢复引用。静态模型/pipe测试边界若不支持弱引用，可仅在该请求内保留原绑定方法；动态算法控制器/读出仍强制弱引用，不允许因profiling残留owner。新增实际SimpleNamespace绑定decode的回归控制，原方法对象、返回值及动态拒绝保持。

七项标量控制通过（1.41秒），见`reports/wc_deployment_profile_scalar_CPU_R2_controls_20261016.json`。真实GPU峰值/费用没有测量。采集CLI同时缩短失败输出并令未接受终态返回非零，避免打印整份源哈希清单或将命令exit0误认成完整接受；原失败回执不改。

## 3. 新完整R2

source1829c0f23c39f2e9e830d82d4ad5336e9fd95de9，PID10482，2026-10-16 06:22:43.680890单次派发确认live，独立目录`.sync/wc-paper-deployment-profile-full102-local-cpu-r2-20261016/source`。

两flow×17已有配置×原audit/profile audit/profile lean，102路径、3516pairs/7032CFG，34完整guided对照、34profile audit/lean、68profile/102mock和所有owner释放保持，未从R1拼接成功路径。实际CPU结果仍待；完整预登记见`manifests/wc_deployment_profile_full102_local_CPU_preregistration_r2_20261016.json`。

预计1—3分钟，最早06:25:43.680890（unix1792103143.680890），**06:26一次本地验收**。用`accept_wc_deployment_profile_full102_local_r1.py`配R2 launch/new capture/R2 acceptance，采一次后仅离线检查。若仍跑，重估后只另约一次，不循环；若失败保留并修复fresh版本，不放宽102覆盖。

## 4. 主线与预算

N05原1078249/1078290/post1078250、source15d77ac、R2生产stage与今天12:05查收均未改变，未SSH或读取partial。旧952已接受不重查；N09此轮只补记录器CPU准备，不冒充真实动作价、CUDA profile或视频/加速结果。N05→N07→N08→N09/10顺序与原cap/严格<12GPUh自主规则保持，0GPUh/0预算写。F/B关闭，无新人评、训练或OMR。
