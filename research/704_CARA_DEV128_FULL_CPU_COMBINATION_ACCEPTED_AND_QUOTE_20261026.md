# DEV128：双服务器整卡组合CPU接受，报价不变

截至2026-10-26，两端完整组合CPU均已退出0并独立接受。当前没有新DEV推理、GPU提交、GPU预约或正式账本写入。128路径、六角色、原α、强基线和预登记科学判据均未改变。

## 证据与执行身份

新组合执行源码为 `fcd979aae924da3e4707de690b746a4901b4be26`。两卡R2实际12:55:18启动、12:57:48退出；四卡R2实际12:55:23启动、12:59:35退出。两端均为GPU隐藏的2CPU/8GiB隔离容器。

- [两卡完整收件](../reports/cara_DEV128_full_two_card_CPU_complete_r2_20261026.json)与[独立接受r3](../reports/cara_DEV128_full_two_card_CPU_accepted_r3_20261026.json)。
- [四卡完整收件](../reports/cara_DEV128_full_four_card_CPU_complete2_r2_20261026.json)与[独立接受r3](../reports/cara_DEV128_full_four_card_CPU_accepted_r3_20261026.json)。文件complete_r2是较早运行中快照，不能替代complete2终态。
- r3接受器独立重算原证明/注册/收件SHA，并记录自身源码SHA；沿用相同R2原件，无重复CPU派发。[18项篡改拒绝检查](../reports/cara_DEV128_full_acceptance_negative_checks_20261026.json)全部通过。

每台完成10个真实CPU监督/guardian进程场景、6个真实64MiB tmpfs ENOSPC及跨盘日志场景、61项终态/财务/评分检查。覆盖原runner/FD锁退出、预算超时、外部上下文、模式恢复延期、评分失败和超时、128分母、26控制、80 LPIPS/7440帧、288质量位置、来源及alpha改变拒绝、重复计费与中央包冲突拒绝。硬件观察与科学张量为明确的CPU夹具；不代表当前GPU独占或新DEV结果。

真实冻结请求、采集/释放评分数值链、93帧LPIPS及三独立质量模型已由[703](703_CARA_DEV128_DUAL_HOST_CPU_AND_CAL66_QUALITY_DIAGNOSIS_20261026.md)两端R4生产CPU接受。本轮按原件与源码SHA复用未变部分；新的监督、评分编排和财务层分别验证，不重复加载原模型。

首轮组合CPU因未携带旧CPU-reuse-binding.json来源文件，在复用核对阶段失败，尚未进入生命周期测试。两端R1 exit1原件保留；R2复制并核验三份旧来源元数据后通过。四卡启动传输未返回收件时，只读恢复原CPU-launch.json，未再次prepare或重复启动。

## 释放、评分与财务边界

完整合同见[整卡组合方案](../plans/cara_policy_generator_20261020/DEV128_FULL_LIFECYCLE_AND_FINANCE_CPU_R1_20261026.md)。评分入口检查原runner退出、账单和本机结算、锁释放、GPU隐藏后才执行。80组LPIPS和288质量位置限2CPU/8GiB、最多10小时；预计8.564487小时，不能沿用CAL66的6小时。

两卡费用通过唯一中央外部包回填，重复相同结算幂等、不同账单/身份拒绝，保留其他任务及旧16.5GPUh未知责任；财务结算与科学接受分离。CPU测试只写夹具账本。评分层可复用原视频/完整分数恢复，不表示任意整卡失败均可自动恢复接受。

## 完整报价复核

| 主机 | 完整预测GPUh | 12GPUh设计子池 | GPU授权 |
|---|---:|---|---|
| 四卡Ada（默认） | 12.349232327573024 | 超出，当前拒绝准入 | 无 |
| 两卡A6000 | 11.618228467131088 | 容纳 | 无 |

报价包含全部128路径、0.5h启动、0.35h保存/释放及15%余量，见[独立复算](../reports/cara_DEV128_full_quote_recheck_20261026.json)；原报价文件及SHA未改。[中央只读账本](../reports/cara_DEV128_full_central_ledger_readonly_20261026.json)：已用161.39662063362806、保留预约16.5、可用48.10337936637194，累计上限226GPUh。最终部署仍为min(257.7712338712067秒,0.8×freshNative)。

## 交接

本轮CPU资源已全部释放，见[资源原件](../reports/cara_DEV128_CPU_resources_released_20261026.json)。整卡组合CPU接受=true，GPU_dispatch_ready=false，execution_authorized=false。当前工具仅CPU准备/收件与独立接受；后续GPU控制器的新执行stage、单一中央意图和实际准入绑定仍须完成，不能把CPUstage当GPUstage。

用户授权执行后，再做fresh双端曝光、空闲UUID、独占、磁盘跨盘日志与账本准入，并择一合规主机；四卡超子池的事实保持，不提高上限、不缩卡、不双边启动。实际GPU执行才安排半程和释放后全程验收。当前不安排空任务监测、不追加GPU。
