# W3 最小真实 C/D：独立小卡核心与来源准备

2026-10-04；LOCAL_SCOPE_PASS / ACTUAL_TORCH_CORE_PENDING；GPU 0。

## 独立科学范围

[新草案](../configs/wc_w3_small_cd_r1_draft.json)为 WC-W3-SMALL-CD-R1-20261004-A / wc-w3-small-cd-r1，完整保留原8父/24后缀/18输出草案身份，不称完整RV0已验收。本卡两个曝光CAL场景各一个选定slot：common call45/CFG0、human call46/CFG1，从同一step22实际状态，OFF/OFF/C/D/D/C各一条完整14更新/28CFG后缀。共2父、12后缀、8新输出（每场景parent、OFF桥、C、D），两既有Native35仅在严格桥成立时复用。

科学量是首动作之后自适应策略的终点有符号全帧LPIPS差及两CFG未来完整次数/实际成本；不是同刷新配额收益、单步预算Head正式标签、物理真值或未见场景确认。四个固定配额交换保持后序，不合并进本卡后宣称“首批全方向完成”。

## 核心实现与严格参考桥

新 `rv0_small_causal.py` 复用未改的 OneAction、完整状态恢复、原官方采样loop和完整decode/guardrail/write尾段。逐调用输入/输出/deep/cache及完整solver轨迹记录；OFF对原父continuation、C/C与D/D正反顺序重复、同输入Cdeep0/Dfull和编码桥必须成立。每次prepare、全部快照/恢复/哈希、VAE、安全拒绝与编码均保留于实际费用。

引用119实际核过的FAIR Native35/WC0.06文件SHA/bytes，冻结CAL/setup、官方9源、模型/条件context、全部36timesteps及WC设置。**当前新父视频必须与历史WC0.06字节SHA一致**，OFF子视频/五pipeline阶段还须与当前父相等。缺桥时停止为TECH_BLOCKED，不把历史同名Native作为参考。历史Native无观察器GPU parity仍未由本小卡完成，不声称Full RV0已通过。

仅CPU Toy夹具有显式桥绕过：必须无CUDA且run_id以CPU_SMALL:开头；生产入口将固定require_historical_bridge=True，并单独验证全部参考文件与绑定原件，不能将CPU开关带入真实执行。

## 完整费用和当前状态

已测未干预后缀代理下完整费用 **2811.502秒**；完整Native35加恢复的压力代理 **6109.684秒**，两者都不是硬上界。新卡候选单次全wall **3900秒** / child3870 / kill5 / 退出30，加准入15共3915秒；当前7119.663527秒余额可容纳候选上限，若全额使用尚余3204.663527秒。压力代理超过候选cap，说明可能触发超时/保留失败矩阵，不能称保证完成，也不能预先承诺后续交换和新样本批次。

[本地scope原件](../reports/wc_w3_small_cd_scope_cpu_r1_20261004.json)：14项范围漂移、6项授权/预算/在途拒绝合同通过，未改权威预算；[新CPU清单](../manifests/wc_w3_small_cd_core_cpu_r1_20261004.json)绑定来源。实际小核心Torch组合控制、生产CLI/监督器/终态审计与四组候选—Native全93帧评分还待接线。新卡尚未选择GPU、预付或提交；不用旧104/1800/restore身份重跑，不增加Head/LoRA/训练/人评。
