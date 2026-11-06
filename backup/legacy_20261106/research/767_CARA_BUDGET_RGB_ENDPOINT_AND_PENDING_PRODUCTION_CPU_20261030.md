# 预算搜索完整RGB评价与四卡CPU终态

2026-10-30。完整93帧编码前RGB评价和双FIT请求入口已实现，6项本地控制通过。四卡原CPU已正常退出，31项组件控制、54条成功tiny路径、8条预定失败和12个完整双FIT目标完成；原62份B36源码保持。实际4GiB内存加4GiB可用swap与登记无swap不符，验收器拒绝，双端CPU尚未接受。保留原终态，后续先修正资源绑定；两卡未启动并保持S优先。本轮0GPUh。

## 评价口径与工件

原固定`inference.py`在视频guardrail通过之后，把处理后的帧转回归一化`C×T×H×W`浮点张量，再交给原视频writer。[RGB工件与MSE组件](../src/wcomr/cara_budget_rgb_objective_r1.py)使用这个编码前边界：转为float32保存已有数值，不做MP4重解码、裁剪、缩放或抽帧；完整93帧、三个通道和全部像素参与MSE。计算按帧使用float64平方差累计，再以完整元素数归一化，避免整段视频的双精度副本占用。

每份RGB工件保存独占创建的身份、NPY原字节及完成回执。读取校验请求/输入/上下文/seed/几何/角色身份、文件长度与SHA，拒绝部分、非有限、越界、错dtype、损坏或错误教师。教师限定于相同评价上下文里的完整Native35请求；旧压缩视频不能直接作为兼容教师。该评价边界是本项目的明确适配，不声称等同官方Wan内部所有张量约定。

## 已接入的生产路由与待执行矩阵

[EndpointRequests](../src/wcomr/cara_budget_endpoint_requests_r1.py)调用原`cara_fast_requests_r2.Requests`，保留完整Native与CARA-C采样、guardrail和原writer。两个FIT候选都完成、每条实际36更新且策略严格19D无回退之后，才返回双输入MSE；拒绝、解码/写入失败或改变实际D数的非有限回退均不产生完整候选目标。教师首次生成后校验原件复用；候选重复调用必须走[766查询日志](766_CARA_BUDGET_SEARCH_QUERY_JOURNAL_CPU_20261030.md)，不能绕过原物理意图再执行。

此入口版本显式拒绝GPU调用。当前接入的是生产函数的受影响CPU验证路径，实际权重、真实视频和GPU准入均未发生。部署计时另行登记；搜索端点捕获不是干净部署速度测量。

[CPU注册](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_ENDPOINT_CPU_FRAGMENT_R1.json)绑定新源码、原R2父阶段和两个固定stage；[验证入口](../scripts/check_cara_budget_endpoint_cpu_r1.py)继承原禁CUDA/权重/下载、单编译线程及600秒工作限时。计划每端执行31项组件控制，并在两个flow模式下各验证ON/OFF两套完整教师/候选链、原返回恢复、部分双FIT失败和固定配额回退拒绝：每端计划54条成功tiny路径、8条预定失败、12个完整双FIT合成目标。四卡原终态已记录全部计划分母完成；两卡仍未执行。数值矩阵完成不清除独立的资源配置差异。

## 已有证据与当前恢复点

[本地回执](../reports/cara_budget_RGB_objective_local_CPU_r1_20261030.json)记录6项通过控制：末帧末像素参与、全量数组原样保存与只读重载、错误教师身份拒绝、部分/错编码/非有限拒绝、损坏/缺少终态拒绝及几何不匹配拒绝。原B36的52执行＋4汇总＋6绘图源码SHA全部保持。

两次完整源码准备请求均出现连接超时；其后分别通过实际SSH登录确认原stage不存在，才继续原登记准备，见[第一次不存在证明](../reports/cara_budget_endpoint_four_card_CPU_original_absent_r1_20261030.json)和[第二次恢复](../reports/cara_budget_endpoint_four_card_CPU_recovery_r2_20261030.json)。没有在UNKNOWN期间盲目重派。

随后[增量准备](../scripts/prepare_cara_budget_endpoint_cpu_delta_r1.py)复用远端已接受父阶段的1040份原文件，仅上传12份变化文件；全部1052份文件仍逐一核对原登记SHA。传输约95KB，完整载荷约7.84MB。[绑定回执](../reports/cara_budget_endpoint_four_card_CPU_delta_binding_r1_20261030.json)保留实际字节、父阶段及控制源码身份；混合复用与错误旧字节拒绝两项[本地控制](../reports/cara_budget_endpoint_CPU_delta_copy_controls_r1_20261030.json)通过。该改动只改变传输，不改变科学源码或查询范围。

[原启动](../reports/cara_budget_endpoint_four_card_CPU_launch_r1_20261030.json)于17:05:03返回，同一原stage为：

`/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-endpoint-CPU-ada-r1-20261030`

[原终态捕获](../reports/cara_budget_endpoint_four_card_CPU_original_capture_r3_20261030.json)证明容器17:11:10退出/0、Pid0、无OOM；工作函数用时356.53秒。源码、运行时、注册和完整证明SHA均一致。31项组件控制以及两个flow各27成功/4预定失败、6完整双FIT目标全部完成，GPU、实际权重、网络和账本写入均为0。它验证生产函数在tiny权重/显式模拟解码器与writer下的行为，不是真实视频质量结果。

## 资源差异与后续验收

原Docker实际为1CPU、4GiB内存、MemorySwap=8GiB（内存与swap总和），即允许额外4GiB swap，与R1登记无swap不符。原因是准备器修改了继承命令的CPU与内存参数，却未显式覆盖memory-swap。实际CpusetCpus为空，接收器另有预期26；R1计划没有登记该绑核要求，后续应统一登记和启动边界。不能用退出/0或数值通过掩盖配置差异，也不能把允许swap写成实际使用了swap。

[终态评估](../reports/cara_budget_endpoint_four_card_CPU_terminal_assessment_r1_20261030.json)重新验证完整证明、原62份B36源码及接收器对实际资源差异的拒绝。保留此次完整数值证据，但双端生产CPU接受仍为false；不修改原stage/配置，不重启原容器。后续以明确修订的CPU准备契约绑定资源和验收器，再决定独立的CPU验证阶段。两卡端尚未启动，为S准入保留内存。

真实原未知物理请求终态读者、专用存储、完整GPU查询上限、教师/warm/控制/重复及整卡报价仍待完成。本轮新增GPU、预算预约和原指标重评均为0。B36的32条单人审阅已完整接收，继续引用760原记录，不重评或重冻。
