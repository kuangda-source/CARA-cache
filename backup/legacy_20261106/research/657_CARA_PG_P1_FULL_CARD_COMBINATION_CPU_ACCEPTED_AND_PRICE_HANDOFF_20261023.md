# PG-P1整卡监督、评分与终态组合CPU已接受

PG-P1现在已有独立的整卡组合CPU接受和可执行的价格后接续入口。当前价格GPU不改、不重派；本轮没有新GPU预约或提交。真正接续仍要求原价格完整接受、原费用结算和原卡释放，然后对新卡做fresh UUID/账本/锁/磁盘/内存准入。

## 实际证据

- 冻结执行source：`170c50e6c289a93cb60d13ead918fdb258177746`；stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-pg-p1-CPU-combination-r3-20261023`；注册SHA：`70afa6f1ececf71c2dd4603c00fb3d02060cf8c4dacab054dc2470d7efa8bcbd`。
- 原CPU实际启动：2026-10-23T16:20:57.193131+08:00；最终实际收件：2026-10-23T16:33:39.478806+08:00；原容器exit0、无OOM。文件名只是标签，以回执实际时间为准。
- [原始终态](../reports/cara_PG_P1_combination_CPU_terminal_r3_complete_20261023.json)；[独立接受](../reports/cara_PG_P1_combination_CPU_accepted_r3_20261023.json)；[90项本地相关检查](../reports/cara_PG_P1_combination_local_CPU_checks_20261023.json)；[原始文件收件组合2项检查](../reports/cara_PG_P1_original_file_capture_CPU_20261023.json)。其中独立终态12项在服务器CPU也完整通过。
- 隐藏GPU、pinned只读容器、1核/4GiB，启动前MemAvailable=30.97GiB、可用盘=96.88GiB；不加载Cosmos权重、不调用真实sudo/nvidia，不写权威GPU账本。复用的是已接受的物理资源文件，不是上一张卡的GPU授权。

## 这次组合覆盖了什么

1. 真实Cosmos SetupArguments和6请求、NLTK、生产writer/93帧解码/ffprobe；两个flow共18完整小张量采样路径，实际WC/RF/UniPC、任意合法mask与alpha、Native/all-D对齐、请求复位和非有限读出恢复D。
2. 真实完整视频评分回调：已接受AlexNet与线性权重，CPU float32，全部93帧432×768和原PTS；相同测试视频LPIPS=0.0，单核该回调检查耗时43.173秒。测试视频是明确的CPU固定图案，不能当作Cosmos质量或加速结果。请求、视频、latent和逐帧评分均保存原始哈希；注入评分失败后保留原请求并拒绝同位置重放。
3. 真实监督器和host guardian配合真实CPU子进程，共6种生命周期：正常、runner失败、外部上下文、释放时遥测失败、正常模式恢复、外部进程到达后延期恢复。全部使用隔离fixture账本和模拟硬件命令；验证原FD/PID/start/UID、唯一上下文握手、失败费用结算和原锁释放，没有改变硬件模式。
4. 原64位置、Q≤8、第一批+一次细化、角色去重、冻结SELECT、完整分母和清洁Native预算。终态从原请求和93帧评分复算图/DP/候选/最终排序；拒绝改写标量分数、策略选择、Native预算、删位置、外部上下文、失败子进程、未结账和仍运行容器。
5. 独立文件收件器与终态复算相接；早退时没有Native时钟也保留原runner，不能伪称完整接受。模型输出/价格在这些逻辑测试中明确为fixture；真实价格门槛仍未通过。

## 修复与原件保留

R1完整18条采样CPU通过后，在评分入口发现旧BANK24模块未被打包；改为PG闭包内独立核对同一组已接受LPIPS文件。R2又发现torch.hub目录少了一层hub，在只读挂载中触发路径错误；现显式绑定`cache/torch/hub`。同时逐项对照闭包与原1624已接受base，只有预算模块存在已登记SM89端口差异，现保持其原哈希，不让历史SM86模块覆盖。

旧R1、R2失败终态分别保留在[第一次失败](../reports/cara_PG_P1_combination_CPU_progress_r1_20261023_1614.json)和[第二次失败](../reports/cara_PG_P1_combination_CPU_progress_r2_20261023_1615.json)。R3重新执行完整组合；未改任何正在运行的价格源码或输入，也未使用价格部分结果。

## 原价格通过后直接接续

见[完整命令与原件边界](../plans/cara_policy_generator_20261020/P1_FULL_CARD_COMBINATION_HANDOFF_R3_20261023.md)。控制器为`wc_four_card_cara_pg_gpu_r1.py`：prepare → preflight → 单次launch-gpu → admission/halfway/terminal capture → accept-gpu；UNKNOWN或已有intent只recover。prepare在本机重新执行完整价格接受，再绑定原标签、新价格与独立接受SHA。真实GPU前检重新核对组合CPU闭包、11.5价格预约已结算、10.5新卡余额和实际空闲UUID。

P1完整报价不变：forecast8.844444、limit10.5 GPUh，最多64路径/40对评分/2304pairs/4608CFG/单load。先Native warm2+FIT4，以独占监测前缀接受完整请求时钟，固定B=.80；再首批≤4与单次细化≤4，冻结后才执行2个SELECT。GPU保持期间的CPU搜索/评分/保存计入实际GPUh，不能拿排除评分的部署时钟抵扣费用。

P1尚无科学结果，不能据CPU组合通过宣称自动策略优于简单规则。历史窗口shadow与少步Native维持已登记P2设计和独立完整报价，不塞入当前P1。价格17:59半程、22:59终态继续绑定原实际恢复launch；本轮只更新终态接续指令，不另建重复检查。

现有自动化已更新并读回核对：[接续与排程原件](../reports/cara_PG_P1_full_combination_handoff_and_schedule_20261023.json)。22:59时间和原价格launch保持，CPU验收完成没有创建新GPU任务。
