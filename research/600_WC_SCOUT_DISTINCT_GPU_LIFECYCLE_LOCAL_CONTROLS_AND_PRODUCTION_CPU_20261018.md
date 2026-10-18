# 新探索独立GPU生命周期：本地控制与实际CPU验证

本轮实现 CAL12／BANK24 自身的监督、一次派发、CPU post、原件收件和离线独立接受。**这仍是执行工具验证，新增视频、质量结果、GPU费用均为0。** 已接受的 R2 数值248＋10、两个真实Cosmos入口CPU直接复用，不重复执行。

## 1. 为什么拆成两个明确的source

实际生成仍调用已经验收的 `c1c95ce0` 原入口stage，保留原CPU证明与原registration完全匹配；新的监督和post具有独立源码、registration及CPU证明。新stage只增添生命周期文件和已验入口证据，原1772个执行／数值依赖字节不能改变。

这样不必为了增加监督器重跑相同258条数值路径，也不会把原24的通过标志借给新scope。原入口stage始终只读；生成输出、费用和新post分别记录自己的原件。supervisor的source与runner的执行source明确分开，拒绝用当前HEAD替换实际执行版本。

## 2. 已实现的范围

- `supervise_wc_scout_gpu_r1.py`：复用逐UUID租约和v2整卡预留／实际墙钟结算；实际准入前重验原入口、自己的CPU、全部源、上游完整原件与授权。未知派发不重放，计费截止只终止本任务。
- `launch_wc_scout_gpu_r1.py`：CPU及上游完整接受、fresh显存／进程和预算预检通过后才写一次fence。busy且尚未派发明确返回0子进程／0账本；已有fence不删除、不覆盖。CAL12必须等待原Window24；BANK24必须等待CAL12及四CAL冻结门控。
- `postprocess_wc_scout_gpu_r1.py`：所有注册分母、真实动作／来源、owner释放、原张量SHA和有限性、warm全36逐步哈希、终态／A历史／全93 RGB、step21前态和四probe、全部有效兼容正式93帧LPIPS。Native owner为0、actions为None；拒绝、坏视频和未到达保留。
- `capture_wc_scout_gpu_r1.py`／`analyze_wc_scout_gpu_r1.py`：一次查原句柄、原件、全部源和实际费用；捕获后仅离线重算93距离均值、完整分母、同状态／重复控制及v2加法结算。另一个合法GPU作业不构成本任务释放失败。
- `scout_gpu_lifecycle_r1.py`：独立控制、接受和上游顺序；四CAL的μ和中位秩阈值只能在CAL12接受后固定，较大z保留D，DEV不重新拟合。

CAL12还绑定旧N12全部12正式端点和必要旧warm共同前缀；BANK24只用本卡六Native参考，不把数据集原视频当原生参考。观察器沿用已验代码，不在C21额外计算A／D，副本、哈希和同步保持计入诊断请求开销。单次带观察器的秒数仍不称clean重复速度。

## 3. 本地验证及实际CPU设计

[本地原件](../reports/wc_scout_gpu_lifecycle_local_preparation_R1_20261018.json)：20项控制和6条CLI全部通过。控制覆盖完整12／24分母、拒绝／未到达、Native owner、假D／teacher、观察器改变一条guided输出、输入哈希或probe失配、PID复用、UUID锁冲突、实际费用加法、严格小于12授权、门控只用四CAL、全部延迟执行的远端代码语法和逐帧均值独立复算。合成标量仅用于验收器故障注入，不能作为科学结果。

每个新生命周期stage预计1787个源文件；本地闭包检查原1772执行字节变化数为0。实际服务器CPU两命令：

1. 在隔离stage执行新生命周期完整20项控制；
2. `check_wc_scout_gpu_lifecycle_r1.py` 重验实际原入口registration／CPU原件、原Cosmos请求矩阵、校准／guardrail证据、所有source/runtime SHA及新工具语法。复用此前真实入口CPU，不重新加载权重、执行CUDA或运行数值采样。

通过后只能称“新生命周期CPU已接受，实际GPU准入工具就绪”，不能称视频或速度已通过。新CPU尚未运行时保持待验，实际启动／PID／source和检查时刻在下方追加。

## 4. 范围、价格与顺序保持

| 卡 | 完整路径 | 预测GPUh | 完整计费上限 | 上游 |
|---|---:|---:|---:|---|
| 原连续Window24 | 16正式＋8完整warm | 3.064166667 | 4 | N10已接受，等待外部GPU释放 |
| CAL12 | 8正式＋4完整warm | 1.876666667 | 2.5 | 原Window24全部适用原件／费用接受 |
| BANK24 | 18正式＋6完整warm | 3.407222222 | 4.5 | CAL12接受＋四CAL冻结μ／阈值 |

新生命周期未添加任何生成动作或模型调用；原报价的观察器余量及全部加载／预热／参考保持，CPU post不占GPU账单。预算仍226，origin和已结历史不变。末次已验资源22:50两卡被他人占满，原Window24未派发／0预留；本轮本地开发不再查询资源，00:51由既有两小时资源任务处理。

GPU依次原24→CAL12→固定CAL gate→BANK24，X-R共享银行；原24启动器和所有旧stage完全不改。新增探索仍不并入冻结主稿。F/B关闭，不新增训练、人评、付费VLM或OMR。

## 5. 23:40／41实际启动，尚未接受

新source **59be59807d36c976163df67cf14e85738d4f30e7**。两张独立新stage均1787源，保持全部原1772执行依赖不变：

| kind | 原句柄PID／start_ticks | registration SHA | 实际启动北京时间 |
|---|---|---|---|
| CAL12 | 2276574／563294450 | 3a3fcb8dcf7039d9cc478f83a1104af4762fc071170a8693fa373027a0e70c14 | 23:40:40.984 |
| BANK24 | 2277001／563299672 | 2212f023a2f6d0591d2d9f48ceb4394c935463f8a914e4db0faf612eda646696 | 23:41:33.206 |

原启动回执`reports/wc_scout_<KIND>_GPU_lifecycle_CPU_R1_launch_20261018.json`。实际CPU尚未收件，不能判断通过。`worldcache-cpu`在23:45一次技术半程，`worldcache-cpu-2`在23:48一次完整收件；两卡共同最早时刻分别unix1792338273.2059183／1792338453.2059183。原件见[自动化实际回执](../reports/wc_scout_two_GPU_lifecycle_CPU_once_automations_20261018.json)。旧原入口两分钟CPU不重复，原248＋10不重复。

`worldcache-gpu`原两小时资源任务已更新新工具接续，但00:51时刻及原24优先顺序不变。完成本地开发的单次`worldcache-gpu-2`在本轮结束时删除；新CPU由上述两任务查收，不循环查询原进度。当前新增GPU派发、预留和实际费用均为0，论文结果空白保持。

## 6. 23:47一次半程：两个原句柄结束，CPU错误保留

原23:45心跳实际23:46:38送达；23:47:01各一次只读查收，两份回执均绑定原source／registration和原launch。2276574与2277001均已不存在；bundle存在、CPU proof不存在，有界日志均出现`RuntimeError: Scout lifecycle CPU command failed`。这构成技术异常，不能判CPU通过，也不据此评价算法。

本次只保存半程原件与[离线技术核对](../reports/wc_scout_two_lifecycle_CPU_midpoint_technical_20261018.json)，没有读取完整bundle或错误栈上下文，没有提前运行终态collector。23:48完整收件保持，届时从原件定位原因；若需修复使用新版本／stage，不改原stage或重派原CPU。原已验数值和真实入口仍保留。未启动新GPU，原24资源任务不受影响；本半程自动化收完删除。
