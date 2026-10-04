# W3 最小真实 C/D：独立小卡核心与来源准备

2026-10-04；ACTUAL_TORCH_CORE_PASS / PRODUCTION_ENTRY_PENDING；GPU 0。

## 独立科学范围

[新草案](../configs/wc_w3_small_cd_r1_draft.json)为 WC-W3-SMALL-CD-R1-20261004-A / wc-w3-small-cd-r1，完整保留原8父/24后缀/18输出草案身份，不称完整RV0已验收。本卡两个曝光CAL场景各一个选定slot：common call45/CFG0、human call46/CFG1，从同一step22实际状态，OFF/OFF/C/D/D/C各一条完整14更新/28CFG后缀。共2父、12后缀、8新输出（每场景parent、OFF桥、C、D），两既有Native35仅在严格桥成立时复用。

科学量是首动作之后自适应策略的终点有符号全帧LPIPS差及两CFG未来完整次数/实际成本；不是同刷新配额收益、单步预算Head正式标签、物理真值或未见场景确认。四个固定配额交换保持后序，不合并进本卡后宣称“首批全方向完成”。

## 核心实现与严格参考桥

新 `rv0_small_causal.py` 复用未改的 OneAction、完整状态恢复、原官方采样loop和完整decode/guardrail/write尾段。逐调用输入/输出/deep/cache及完整solver轨迹记录；OFF对原父continuation、C/C与D/D正反顺序重复、同输入Cdeep0/Dfull和编码桥必须成立。每次prepare、全部快照/恢复/哈希、VAE、安全拒绝与编码均保留于实际费用。

引用119实际核过的FAIR Native35/WC0.06文件SHA/bytes，冻结CAL/setup、官方9源、模型/条件context、全部36timesteps及WC设置。**当前新父视频必须与历史WC0.06字节SHA一致**，OFF子视频/五pipeline阶段还须与当前父相等。缺桥时停止为TECH_BLOCKED，不把历史同名Native作为参考。历史Native无观察器GPU parity仍未由本小卡完成，不声称Full RV0已通过。

仅CPU Toy夹具有显式桥绕过：必须无CUDA且run_id以CPU_SMALL:开头；生产入口将固定require_historical_bridge=True，并单独验证全部参考文件与绑定原件，不能将CPU开关带入真实执行。

## 完整费用和当前状态

已测未干预后缀代理下完整费用 **2811.502秒**；完整Native35加恢复的压力代理 **6109.684秒**，两者都不是硬上界。新卡候选单次全wall **3900秒** / child3870 / kill5 / 退出30，加准入15共3915秒；当前7119.663527秒余额可容纳候选上限，若全额使用尚余3204.663527秒。压力代理超过候选cap，说明可能触发超时/保留失败矩阵，不能称保证完成，也不能预先承诺后续交换和新样本批次。

[本地scope原件](../reports/wc_w3_small_cd_scope_cpu_r1_20261004.json)：14项范围漂移、6项授权/预算/在途拒绝合同通过，未改权威预算；[新CPU清单](../manifests/wc_w3_small_cd_core_cpu_r1_20261004.json)保留创建时的pending身份并绑定来源。小核心实际Torch组合控制随后通过，见下一节；生产CLI/监督器/终态审计与四组候选—Native全93帧评分还待接线。新卡尚未选择GPU、预付或提交；不用旧104/1800/restore身份重跑，不增加Head/LoRA/训练/人评。

## 实际小核心服务器 CPU 结果

[实际R1原件](../reports/wc_w3_small_cd_core_cpu_r1_20261004.json) / [独立raw轨迹审计](../reports/wc_w3_small_cd_core_cpu_r1_audit_20261004.json)：source **19750056f7818b2691e3f6c95ee58c59e608f69a**，服务器独立`.sync/wc-w3-small-cd-core-cpu-r1-20261004`，Torch2.7.1+cu128、CUDA被禁止且未初始化，exit0，CPU wall **144.952211秒**。

flow OFF/ON两成功批次，每批完整2父/12后缀/8模拟输出，共4父/24完整14更新后缀/16模拟输出。成功组分别检查两个Toy场景的call45/CFG0和call46/CFG1；所有72父调用与36 solver更新、14更新后缀的逐调用/完整UniPC/最终状态、OFF/OFF、C/C和D/D正反顺序重复、同输入Cdeep0/Dfull、五pipeline阶段及OFF编码桥通过。原件明确CPU Toy的网络、输入、权重、decoder与writer，不是真实CAL生成视频。

flow ON还保留三次故意失败：首OFF子写出缺失、首OFF子安全拒绝，以及历史reference的来源/桥条件不兼容。前两次子分支TECH_BLOCKED且父恢复；第三次在父终点来源门TECH_BLOCKED，初始状态/forward/hooks清理通过。原2/12/8分母在全部失败回执保留。成功组另外8份输入/deep/恢复/pipeline证据损坏全部拒绝。

独立用服务器原生cat/sha256sum复读 **84项**：67阶段文件（profile-config同SHA别名显式记录）、9官方源、CPU原件/两日志、权威预算及四份既有Native35/WC0.06视频。原件SHA **c0d9872ca9c6778d18ae7fe8d8f30347951df2a64340f9513e4a86381f5e224f**匹配；本地独立从raw返回轨迹重算4组全部父/后缀/OFF/repeat/每CFG计数/paid-probe/deep/五pipeline/编码桥及三失败，不仅复述返回的pass布尔值。

Toy中C/D未来两个CFG的full次数分别为[10,11]/[11,11]和[11,10]/[11,11]，再次表明首动作自适应诊断不自动预算匹配；这些仅为夹具合同证据，不是真实费用或刷新收益标签。四份历史Native/WC源文件仍匹配119冻结哈希，不表示当前GPU父视频桥已产生。

当前小核心的实际Torch门已关闭，不重跑相同旧完整RV0或121交换测试。生产CLI、共享锁/超时/13h预付与实费结算、实际来源与资源部署、独立终态审计及四组Native相对全93帧LPIPS评分仍需接线；旧full8/24/18全部保持未选、未执行、未验收。3900/3870只为新小卡完整候选花费上限，预算原SHA/used11.022315686839217/45jobs/无inflight保持；新GPU/视频/正式RV标签均0。
