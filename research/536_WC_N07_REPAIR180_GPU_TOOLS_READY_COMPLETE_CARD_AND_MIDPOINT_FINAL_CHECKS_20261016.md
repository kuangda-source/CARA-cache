# N07完整180修复卡：执行与两次查收准备完成

2026-10-16。**独立修复版已通过真实服务器CPU验证，完整GPU派发、半程技术检查及最终科学验收工具也已完成本地验证，可以提交具体整卡执行确认。** 当前没有新GPU任务；原R1失败原件与10月17日05:30的最终验收安排保持。

## 完整范围与修复边界

具体卡为`WC-PAPER-N07-REFUSAL-REPAIR-FULL180-R2-20261016-A`，运行`wc-paper-n07-refusal-repair180-r2`。保留原8提示词×seed17/43×十方法，160正式＋20完整预热、6318pairs／12636CFG、一次模型加载、零额外教师调用。十方法、输入、参数、mask及原93帧评分协议均不变，不把原R1部分结果拼入新卡。

服务器运行源码继续冻结于`6e10aa31197b4c137705b9117090c3a4e538e863`，原独立stage不改。真实服务器九命令已全部退出0，1750份payload SHA、160参数变体、99数值依赖、520修复证明及8项guardrail检查已接受，详见[535](535_WC_N07_REPAIR180_ACTUAL_SERVER_CPU_ACCEPTED_AND_READONLY_COLLECTOR_REPAIRS_20261016.md)。这些是准备证据，尚未证明真实GPU完整卡已经修复或方法收益成立。

## 新工具验证

新增本地工具只把原完整180工具绑定到已接受的R2源码、配置、CPU原件和运行身份。原launcher／collector及科学接受器逐字节逆变换与AST控制通过；真实数值路径、逐UUID锁、v2整卡预留／实际费用结算、失败分母和分组统计规则保持。

- 21项修复、CPU原件、单次派发、时点、原句柄及完整180接受控制通过。
- 20项原派发／半程／不可变源码包控制通过，另5项完整合同控制通过，合计46项；三个新CLI冷启动通过。
- 测试包含超时／丢失回复记为UNKNOWN、派发及查收去重、拒绝旧R1授权、半程前或终态时间前不SSH、完整180／93帧／实际账单／自身UUID释放检查。另一张卡合法作业不妨碍自身释放接受。

最初终态测试夹具缺少`num_steps`造成5项失败，按原方法请求步数补齐后通过，未改生产数值代码；旧失败文本保留。另一次本地测试发现常规文件读取等待，原测试未中止且随后全部通过；独立冷读SHA与旧证明一致，没有把它归因于已确定的系统故障。局部工具测试使用明确的模拟进程、费用与视频元数据，不作为真实GPU或质量结果。

## 批准后的执行和两次检查

一次派发使用[scripts/launch_wc_paper_N07_refusal_repair180_r2.py](../scripts/launch_wc_paper_N07_refusal_repair180_r2.py)，显式提供`--stage`、`--authorization`、`--cpu-acceptance`、`--output`。授权必须绑定本卡、已验CPU/source/config、fresh launch UUID和选定GPU UUID；原R1授权不转用。监督仍负责锁内fresh资源及余额准入，提交回执之外另做一次原句柄准入接受。

预计窗口为16小时。实际启动回执将记录启动后8小时的半程技术检查和16小时的完整验收；时点据真实启动计算，当前不虚构新任务的绝对时间。半程只看原supervisor／runner／CPU-post的PID与start_ticks、180分母进度、技术错误及资源，不读取方法质量或clean latency。最终才查全部180原件、退出与CPU-post、所有有效兼容正式视频93帧、完整失败／拒绝／缺失、分组统计、实费及自身锁／GPU释放。

查收使用[scripts/capture_wc_paper_N07_refusal_repair180_r2.py](../scripts/capture_wc_paper_N07_refusal_repair180_r2.py)的`admission`、`health`、`terminal`三种模式，保存原件后用[独立接受入口](../scripts/analyze_wc_paper_N07_refusal_repair180_r2.py)离线核验。网络或解析失败不代表服务器任务失败，不重复派发；未完按剩余工作量重新估时后结束当轮，不连续轮询。

原R1的10月17日05:30查收单独保留，不因新修复卡获批或启动而覆盖。N08／N09还需显式接续R2的终态原件，不能把当前新工具准备说成下游已完成。

## 预算与当前决策

23:07:57北京时间的一次只读资源快照确认两张A6000无compute进程且UUID锁空闲；权威v2实结96.27897190772518／cap113、预留0，可用16.72102809227482 GPUh，原origin79.99637737158223保持。

**完整卡预计及计费上限15.055555555555555 GPUh。** 余额可覆盖本卡，上限占满后约余1.6655 GPUh；N08等后续费用须依据本卡实际结算另行准入，不能保证当前上限同时覆盖所有后续最坏费用。当前没有新预留、GPU提交或授权回执。按用户“严格少于12 GPUh直接执行”的规则，本卡需要一次具体整卡批准；无需为本卡再次提高累计上限。

原件：[完整卡清单](../manifests/wc_paper_N07_refusal_repair180_full_card_r2_20261016.json)、[46项本地验证](../reports/wc_paper_N07_repair180_GPU_tools_local_CPU_preparation_20261016.json)、[fresh资源与v2预算](../reports/wc_paper_N07_repair180_fresh_resource_and_budget_20261016_2310.json)。主线仍为N07修复→N08重复clean测速→N09部署／成本→N10自动质量；F/B关闭，无新训练、OMR或人评。
