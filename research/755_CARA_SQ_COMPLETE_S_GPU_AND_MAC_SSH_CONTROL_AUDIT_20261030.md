# S 完整验收、共同风险掩码与 Mac SSH 复用诊断

原单次 S 已完整完成。北京时间 2026-10-30 17:44:29.424989 至 20:46:51.093788，原 A6000、源 3a85be21eed90150e5a487796547741cd2e1f3ef、launch bfa488af-8d97-43ca-b634-b4e3a3be9040 保持；完整 10 新路径、468 pair/936 heads、108 行、8 raw、24 unique anchors 及原数值控制已独立接受。四个句柄和原容器退出、两锁释放、Default 恢复，无 OOM。4,859 条连续监控的最大间隔 5.115729 秒、最高温度 87°C；未触发原 90°C 停止界。

唯一 HOST_GUARDIAN 整段费用 3.039352411208933 GPUh 已在四卡中央账本结算；监督区间未重复收费。cap226 保持，used183.78422815946897、reserved16.5、available25.715771840531033 GPUh；其他作业和旧未知责任均不改。原 12.7125 GPUh 预测和 14 GPUh 硬限保留，不回改报价，也不由节余产生新卡权限。

原 S 在 40 GiB 无 swap 容器内正常结束。50 GiB 是 40 GiB 上限加 10 GiB 宿主余量的准入线；宿主实际物理峰值仍未测得。采集器上报的 CUDA workspace 峰值包含本次观察/采集开销，不作部署显存或干净速度结论。两个输入仍为旧 FIT，不是新 DEV 或独立终点验证。

原 2 CPU/8 GiB/3600 秒、无 GPU 后处理于 23:16:16 单次启动、23:17:12 正常退出，无 OOM，worker 墙钟 55.510492 秒。151 个文件、14,436,037,836 字节全部通过原 SHA/队列检查；108 行完整风险及全部排序/选取在本机独立按原算术顺序逐值复算一致。GPU/CPU 完整释放、唯一结算及冻结输出均接受，原两项 S 检查已删除，旧 q1 保持暂停。

| 冻结目标 | 原单次选取 | 全局编译策略 |
|---|---|---|
| BR | 移除 D21，增加 D35 | 与 DIAG/CFG 相同 |
| DIAG | 移除 D21，增加 D35 | 与 BR/CFG 相同 |
| CFG | 移除 D21，增加 D35 | 与 BR/DIAG 相同 |

共同 19D 为 `1,2,3,4,5,6,7,8,10,12,14,16,18,20,24,27,30,35,36`，与 F19-C、Uniform19/time-prior 各为不同执行类。三目标风险/排序并非相等：CFG 与 DIAG 有 165/170 个排序位置不同，human_199 单独的 CFG 最优为 D21→D9；按原两 FIT 等权汇总，全局最优仍为同一 D21→D35。保留这一结果，不改权重、候选域或第二预算来制造不同赢家。

当前全局 S-CFG-vs-S-DIAG 主对比不可辨识，应把三个相同 S 臂合并。共同掩码与简单布局的端点问题仍是另一个完整比较，须保留原 F19-A1 强对照并另行登记范围/费用/权限；本卡没有执行该新掩码的视频比较，也没有建立端点质量、部署显存或干净速度收益。

Mac 只读检查显示：本次 userspace 链路的 office_tailscale、two_card_lan 都是 ControlMaster=false、ControlPath 未设置、ControlPersist=no，且旧任务 socket 不存在；客户端本来已有 30 秒/3 次 ServerAlive。22:17:43 办公室、22:17:53 两卡均完成公钥认证，22:18:00 原句柄查询正常返回。随后另一个明确 ControlMaster=no、ControlPath=none 的新连接也在两跳认证及 exec 接受后发生探活超时。因此旧 master 复用不能解释全部当前观测，具体 Tailscale/系统根因未证明。默认 four_card 的另一套主路由虽配置 auto，其 socket 也不存在，且新连接在 localhost22617 KEX reset；它未被上述 userspace 查询使用。没有清理其他连接或更改全局 SSH/Tailscale/Clash。

原始大回执先落在服务器，再经压缩 SCP 取回并匹配完整 SHA；中央输入的失败/不完整传输均在结算前拒绝。改用压缩文件及 legacy SCP 后，原账单唯一结算并独立复核。网络命令失败、原件字节完整性、技术终态和科学接受分别记录。

[完整卡接受](../reports/cara_sq_s_A6000_complete_accepted_r1_20261030.json) · [完整 GPU 接受](../reports/cara_sq_s_A6000_technical_release_accepted_r1_20261030.json) · [原终态 capture](../reports/cara_sq_s_A6000_original_terminal_capture_r1_20261030.json) · [中央结算接受](../reports/cara_sq_s_A6000_financial_settlement_accepted_r1_20261030.json) · [CPU 原结果](../reports/cara_sq_s_A6000_complete_frozen_risk_result_r1_20261030.json) · [独立复算接受](../reports/cara_sq_s_A6000_post_analysis_accepted_r1_20261030.json) · [共同冻结提案](../plans/cara_next_stage_20261028/sq/S_COMMON_RISK_PROPOSALS_R1_20261030.json) · [检查清理](../reports/cara_sq_s_A6000_checks_deleted_r1_20261030.json) · [Mac 只读诊断](../reports/cara_sq_s_Mac_ssh_readonly_diagnosis_r1_20261030.json) · [两跳时间线及原句柄恢复](../reports/cara_sq_s_A6000_no_mux_two_hop_recovery_20261030_221738.json) · [S/Q 当前入口](../plans/cara_next_stage_20261028/sq/README.md)。主线 canonical 导航和科学总表仍由主线维护。
