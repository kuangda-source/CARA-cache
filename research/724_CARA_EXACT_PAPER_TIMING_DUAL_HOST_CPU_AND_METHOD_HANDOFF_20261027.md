# 724｜准确“去噪＋解码”时钟与双服务器CPU接续

2026-10-27。用户要求在后续方法实验中加入准确论文时钟，同时保留完整请求时间；不单独启动GPU补测。已实现可选新入口，并在四卡/两卡服务器各完成受影响生产路径CPU检查。未改运行stage、旧采集器、原α、强基线、累计226GPUh或原部署验收。

## 已完成

1. 新计时器`src/wcomr/paper_latency_r1.py`绑定固定上游文件SHA和实际函数AST。起点位于真正solver循环之前，终点位于`model.decode`返回并同步之后；整个连续区间包括中间准备、probe/缓存/近似开销。插入两条回调后可逆AST与原函数相同。
2. 新入口`src/wcomr/method_experiment_timing_r1.py`提供`TimedRequests`，复用原冻结请求重建、角色/布局、少步Native网格和slot一次尝试限制。新增字段与原完整请求时间共存。机制父轨迹包装单独标记诊断；R4新读出生产能力不由计时器代替。
3. 原`clean_speed20_r1.py`、`production_sampling.py`、`p2_native_sampling.py`、`exploration_requests.py`、`scout_parent_v22.py`、共同误差新读出参考代码均与当前Git原字节一致；六文件SHA在新manifest中保留。原验收不用新时钟重算。

[计时附件与调用示例](../plans/cara_predictor_refresh_scout_v2_20261026/PAPER_TIMING_ATTACHMENT_R1_20261027.md) · [源码/CPU绑定manifest](../manifests/cara_paper_timing_attachment_r1_20261027.json) · [复核回执](../reports/cara_paper_timing_dual_host_CPU_review_r2_20261027.json)

## 双端实际CPU验证

两端均使用独立新stage、无网络、GPU隐藏、只读project、1CPU/4GiB容器。准入时四卡约80GiB、两卡约53GiB可用内存，磁盘各约1TB；未申请GPU或改变GPU模式。CPU终态均退出0、无OOM，原runtime和新payload再次哈希一致。

| 实际执行环境 | 完整CPU路径 | 原角色与flow | 结果 |
|---|---:|---|---|
| 四卡服务器（SM89目标；CPU未使用GPU） | 18 | Native35、Native26、S25-A-phase、Shared25-C；flow False/True | 接受 |
| 两卡服务器（SM86目标；CPU未使用GPU） | 18 | 同上 | 接受 |

每端每flow：四角色各计时OFF/ON一对，共8条；再加1条显式边界顺序控制，合计9条、两flow18条。真实Cosmos冻结`InferenceArguments`、固定采样器/UniPC/WC/RF/生成函数执行；权重、条件准备、decoder和writer使用已声明的小型CPU替代，不是Cosmos视频质量或GPU速度。

- 逐步guided输出、最终latent、替代RGB帧、A历史/原α与刷新历史均OFF/ON一致。
- 实际事件顺序：prepare → loop_start → loop_end → decode → timed_end。prepare在原core内、新时钟外；完整请求四项合成公式保持。
- 原拒绝、解码/写盘/prepare失败不被吞掉，方法绑定恢复；重复slot、篡改sampler、同模型嵌套时钟被拒绝。
- 每端7项本地边界测试（含11种错误时序/时钟子情形和3种异常）通过；独立接受器又用14种终态/源/资源/分母/α/事件顺序污染验证拒绝。
- CPU始终`torch.cuda.is_initialized()==false`，模型权重未加载；仅声明CPU受影响入口接受，不声明完整后续方法卡或真实GPU时钟接受。

[四卡完整终态](../reports/cara_paper_timing_four_card_CPU_terminal_r2_20261027.json) · [四卡独立接受](../reports/cara_paper_timing_four_card_CPU_accepted_r2_20261027.json) · [两卡完整终态](../reports/cara_paper_timing_two_card_CPU_terminal_r2_20261027.json) · [两卡独立接受](../reports/cara_paper_timing_two_card_CPU_accepted_r2_20261027.json)

CPU数值任务本身分别约73.19秒与77.03秒，这些不是生成性能。源码在新stage按完整payload SHA冻结；这次CPU准备阶段尚未形成发布commit时，原注册明确写`EXACT_PAYLOAD_SHA_WORKTREE_CPU_ONLY`并记录parent Git，不能把parent Git误称新代码完整来源。公开提交包含对应源码和所有回执；下一张GPU卡必须重新用发布源码闭包绑定。

## 首轮CPU失败及修复

R1两端均在正式开计时前的源码AST核验退出1，未触及GPU：`inspect.getsource`返回带类缩进的函数，使用`dedent`同时改变多行docstring中的空格，导致完全相同函数误报不同。修复为用外层suite保留原源字节的解析，新增独立回归测试；不是放宽源码SHA或删掉一致性核验。R1原stage、失败日志和两个失败回执保留，修正版用新R2 stage重新执行全部受影响范围。

[四卡R1失败](../reports/cara_paper_timing_four_card_CPU_failed_r1_20261027.json) · [两卡R1失败](../reports/cara_paper_timing_two_card_CPU_failed_r1_20261027.json)

## 下一步与保留边界

优先把此附件绑定后续已授权方法卡；没有新方法GPU授权时，只推进生产/成本准备。新方法如R4_COMMON_LONG仍需其自身真实接口和整卡验收，不能凭时钟附件通过宣称预测器通过。shadow诊断时钟不作为部署速度；源码编译/时钟适配setup另列并计入占卡费用，新同步开销会进入原完整请求。

722的历史统计继续保持：`core_seconds`不能追溯改名为论文时钟；旧完整请求/质量/财务验收均不变。最终部署仍为`min(257.7712338712067秒, 0.8×fresh Native)`，累计226GPUh、旧16.5未知责任保持。本次GPU提交0、预约0、GPUh新增0，未运行16路径独立补测；IG暂停。

补充检查：新卡片模板的两项DRAFT/禁止启动边界测试通过。顺带运行旧通用流程14项测试时，12项通过、2项旧CAL66 reader因早已过期的controller SHA绑定失败；当前controller与本轮前Git字节相同，本次未修改或放宽该旧绑定。具体SHA见复核回执，不能把整套旧流程测试称为全过。
