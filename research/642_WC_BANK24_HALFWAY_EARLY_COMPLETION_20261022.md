# BANK24 半程发现完整24已提前结束

**2026-10-22 20:36:04的实际半程观察确认原GPU任务和CPU后处理均已退出；有界技术原件报告24/24完成、18正式+6完整预热、后处理退出0，GPU实费1.8452486574944729 GPUh已结算。** 本次保存完成事实与技术核对，完整视频/指标/控制及科研结论由原定00:17终态验收独立确认。

## 实际收件和连接恢复

20:33任务送达，首次收件因本机原owned master PID31383和socket均不存在，SSH认证返回255；只取得UNKNOWN，没有回填远端观察。原件 `reports/wc_four_card_BANK24_GPU_retry2_halfway_20261022_2034.json` 保留。

按已授权私有入口恢复本人的SSH连接，实际master PID42963，仍为 `/tmp/wc4prep-501/model-r4.sock`。ControlPersist改为50400秒以覆盖长卡检查间隔；没有增加远端转发、重启FRP、修改服务器设置或接触其他任务。旧metadata已保存，原模型代理字段明确属于历史。

恢复后只进行一次成功的原halfway观察：**20:36:04.487964**。唯一launch `e14a3299-3bd9-44f0-8843-bccecaa70365`、source `d0d4b11861adace3f291a751b7da62f8e31914e8`、run `wc-scout-dev6-paired-native-full24-ada-r2`、原stage和registration SHA保持。随后20:37:53.234001作一次有界技术补充，读取状态/位置/起止时间/错误行/磁盘，未读取LPIPS或视频科学内容，未追加GPU telemetry。

## 技术结果

- 原supervisor/post watcher/inner/runner与GPU、post CPU容器均退出，GPU容器已清除，原UUID锁可独占取得并立即释放。
- GPU1/UUID19d4d100：23MiB、0%利用率；没有本任务compute进程。另卡已有任务未改动。
- 24个原位置依次匹配登记矩阵，全部报告COMPLETE，18正式+6预热；原4CAL gate、6DEV、864pairs/1728CFG/一次load的科学范围未变。
- 原CPU post报告 `ORIGINAL_FULL24_CPU_POST_EXITED`、退出码0、GPU先结算释放及CPU容器退出验证为true。
- 有界GPU/supervisor日志未发现Traceback、RuntimeError、AssertionError、OOM、磁盘满匹配行。
- GPU账单结束于 **18:54:06.663562**，全wall **6642.895166980103秒（约1小时50分43秒）**，实费 **1.8452486574944729 GPUh**，低于本卡8.75上限。6.974166667原值是保守规划，不把规划/实费差解读为方法或硬件加速倍率。
- 共享池used **118.74600829142668**、reserved **16.5**、available **90.75399170857332** / cap226。16.5是保留的旧两卡未知责任预约，未释放或充作新实费。data盘空闲 **336.082813GiB**，非下一卡fresh准入。

15项离线技术核对全部通过：原身份/源、实际时点、全位置和完成计数、退出/锁、post、日志、账单身份与池加法核算、一次telemetry及零新派发/账本写。技术完成不增加54科研表的接受行。

## 已落实的后续安排

本次半程 `cara-bank24` 已完成删除，文件不存在已读回；没有新增重复自动化。原全程 `cara-bank24-2` 的 **10月23日00:17**、目标聊天、原launch和原完整队列保持，已追加本次完成/费用/连接原件并读回。源绑定终态入口仍按原launch的最早 **00:16:43.061365** 收件；本轮不改原launch时点字段，不重跑GPU。

终态直接收取原全部输出并独立接受。接受后依次既定同D/X-R离线分析→641所列完整1624四卡新CPU/整卡Ada报价→原已批完整12GPUh采集→PG-P1/P2/P3/P4。首次采集的完成量和费用不能提前替代该完整接受。

原件：

- `reports/wc_four_card_BANK24_retry2_halfway_owned_connection_recovery_20261022.json`
- `reports/wc_four_card_BANK24_GPU_retry2_halfway_recovered_20261022_2036.json`
- `reports/wc_four_card_BANK24_retry2_early_exit_technical_20261022_2038.json`
- `reports/wc_four_card_BANK24_retry2_halfway_technical_review_20261022.json`
- `reports/wc_four_card_BANK24_retry2_halfway_closed_terminal_preserved_20261022.json`
