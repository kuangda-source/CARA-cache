# 805 — 端点守护链Linux CPU接受

原Tailscale/SSH通路已成功完成两卡源码核验、CPU启动与原终态取回。新端点守护链R2在两卡的独立禁GPU容器正常退出，19项Linux CPU控制通过，随后11项独立验收控制通过；没有GPU提交、中央账本访问或原14GPUh运行修改。完整端点卡仍未接受，实际预算mask等待原112路径/51次双FIT查询完整验收后一次冻结。

## 原运行与验证范围

- R2源码：`5853446c13d1406f34337fa4a59af72aed9b6080`；stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-S-endpoint-guardian-CPU-a6000-r2-20261031`，容器为stage名加`-cpu`。
- 注册SHA：`631560d232689f2aeb508e94194f70e2903a841df1d794b17a304039c3b9ce3a`。原容器19:47:28启动，19:48:07正常退出，ExitCode=0、Pid=0、无OOM；worker实测39.380197525秒。
- 实际资源为CPU26、1核、4GiB、零额外swap、network none、只读根文件系统、无GPU设备。原接受的113项CPU源包作为逐文件核验的基础，仅叠加新端点组件和测试。
- 19项包含四个源适配AST检查、14个实际Linux进程场景及一个生产模式拒绝CPU夹具检查。四个组件单独版本化，保留原guardian、固定48MiB journal、supervisor和只读生命周期捕获的控制流，只改变端点家族导入、状态标识、stage前缀和接受字段。正在运行预算卡的原文件保持不变。

14个场景为正常完成、runner失败、缺凭据、忙卡、模式修改失败、CLI无容器、容器初始化失败、原硬截止、容器观察未知、容器身份被替换、恢复时忙卡、bootstrap自证前退出、启动前90°C和运行中90°C。真实Linux子进程、PID/start ticks与host view、进程组/pidfd终止、锁、固定journal和临时账本I/O参与验证；GPU观测、模式指令和Docker状态是明确的CPU模拟，不是实际GPU热测试或新卡资源准入。

所有场景只关闭原进程，外来CPU哨兵仍存活，原lease释放且原stage再次执行被拒绝。完整终态的成功和失败费用均按原guardian单调时钟写入临时账本，重复接受只有一个结算事件，旧16.5责任不变。观察未知或容器身份变化不形成完整计费接受，临时账本保持未结算；恢复时有外来占用不强制恢复模式。两项热停保留90°C触发记录，启动前拒绝runner，运行中停止原runner。

独立接受器核验原启动与终态、注册/源码/运行时SHA、退出状态、资源和完整14场景分母。11项本地控制验证不能用运行中或缺失证明、源码变化、GPU设备、遗漏场景、跳过Linux控制、外来进程被终止、未知误结算、失败漏结算或读取活跃实验科学输出来通过接受。

## 保留的失败与剩余工作

R1原容器19:45:36退出/1。测试夹具把执行host改为two_card时，也误将临时central_ledger_host改为two_card；生产守护的原four_card中央身份检查正确拒绝，未进入模拟分配。保留R1源码、启动、完整终态与错误；R2只修正夹具的中央身份，使用新CPU stage，不重启R1，不放宽生产检查。

本接受完成的是生产守护组件的实际Linux CPU链。新端点的一次派发入口、真实runner与整体卡绑定、工件/九项完整RGB身份门、跨运行评分清单及一次CPU评分/接受、最终预算mask的受影响CPU、最终源和完整报价仍待完成。旧Native35参考和12份原指标保留各自scope与来源；不能改写旧scope来复用只允许同scope的评分入口。新端点超过4GPUh的批准及其原中央账本交易权限仍需单独取得。

原单次14GPUh卡的23:16半程、次日06:01终验、06:45:04硬截止保持。本轮没有重新观测其GPU状态或读取部分科学分数；不将历史运行快照写成当前观测。

[R2完整CPU接受](../reports/cara_s_endpoint_guardian_CPU_accepted_r2_20261031.json) · [R2原终态](../reports/cara_s_endpoint_guardian_CPU_capture_r2_20261031.json) · [独立验收控制](../reports/cara_s_endpoint_guardian_acceptance_checks_r1_20261031.json) · [R1保留失败](../reports/cara_s_endpoint_guardian_CPU_capture_r1_20261031.json)
