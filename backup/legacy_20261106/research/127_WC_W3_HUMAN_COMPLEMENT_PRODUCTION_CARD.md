# Human 缺失点独立补验：生产入口与具体执行卡

2026-10-05。原小C/D卡超时、常识点完整及其全帧结果保持；本卡只补原Human科学点，仍属W3真实单动作/自适应后续诊断。

## 具体卡

**WC-W3-SMALL-HUMAN-COMPLEMENT-R1-20261005-A**；run `wc-w3-small-human-complement-r1`；主平台Cosmos-Predict2.5-2B、单张A6000；768×432、93帧、16fps、seed0，曝光CAL human_199/index2，35请求步/36实际更新/72CFG。

| 范围或成本 | 冻结值 |
|---|---|
| 父与检查点 | 1完整父；step22后、call46/CFG1 |
| 六后缀顺序 | OFF1、OFF2、C_first、D_second、D_first、C_second |
| 每后缀 | 14完整更新/28CFG至终点；除首动作外沿用官方自适应策略 |
| 新视频 | 4：父WC、OFF1、C_first、D_first；1已登记Native35参考 |
| CPU评价 | 两个完整93帧Native-relative LPIPS，1个有符号C−D；负值保留 |
| 单次总上限 | 4500秒（1.25GPUh），child4470、kill5、释放余量30秒 |
| 准入包络 | 另留15秒，总4515秒；fresh UUID/VRAM/compute、f1锁、无inflight |
| 累计账本 | 当前12.0979429045467/24h、46jobs；若花满4500秒为13.3479429045467h |

使用既有服务器根 `/home/gaokuangda/data/gkd/worldcache_omr`，进入新的独立stage/output。重新生成Human父轨迹，不假装恢复已退出进程中的内存快照。累计预算不重置，不转OMR；原2父/12后缀/8输出/2科学点限时失败回执不修改，常识点不重跑。

名义3221.821638秒、压力代理4131.853377秒来自首个完整3033.439130秒诊断父和98.382509秒加载，计60秒bookkeeping/30秒释放；压力父费用乘1.3。Human后续自适应C/D成本未实测，不是硬上界或完成保证。[126实测与费用](126_WC_W3_FIRST_POINT_RESULTS_AND_HUMAN_COMPLEMENT.md)。

## 新生产实现与验证

[独立生产草案](../configs/wc_w3_small_human_production_r2_draft.json)绑定已实际CPU验收的96文件核心、c74a3c…5f32原件和192项独立审计、全部原官方源和Human Native/WC引用。新增运行、监督预算、终态、全帧CPU评分入口；旧2父源码/已部署stage及旧配置不改。

新评分器显式使用row的CFG槽位1，不能把单场景的enumerate索引0当CFG槽位。严格行规则原函数复用，保留六后缀、完整父桥、同输入Cdeep0/Ddeep26、已支付probe、过去自身CFG锚点、当前deep真值禁用、全状态/UniPC恢复、OFF/CC/DD重复和安全编码。

新费用模块在全局项目锁下最多预付4500秒一次；任何失败/写盘/释放都按实际全wall结算，不重置旧usage，不覆盖并发账本修改。完整终态重算预付/实费、三独立PID、锁/GPU释放、源与4新+1参考文件的全部SHA及93帧解码。评分在释放后CPU FP32执行，冻结LPIPS源/权重，保留实际分支full配额及诊断费用；不称同预算、干净速度、正式RV训练标签或物理质量接受。

本地37项原始CPU回执合同通过，包括缺少实际生产CPU原件拒绝、旧卡批准不能代替新卡、旧3900cap不能用于新卡、CFG错槽位、伪第二场景、少重复、真值泄漏、来源桥、费用超限及并发账本修改。R1服务器109文件/8步骤实际CPU exit0、65.890872秒、222原件SHA独立回读通过（source b56207d），原件20b60e9b5ba9c23cce8f6fedb64a934b768b7cc048ed779284f2e459af955d79。随后检查发现GPU选中配置的validate-only需要显式selected校验，R2增加按config GPU选择状态传入selected，并检查该调用AST；生产前置命令在预付前校验实际新CPU原件及新卡授权文件。旧R1回执/配置/stage保留，不追认它覆盖R2。[R2实际CPU](../reports/wc_w3_small_human_production_actual_cpu_r2_20261005.json)已在独立109文件stage完成8步骤/37拒绝、exit0、69.441033秒，source `d8f52562554cb286e97adc67c48950b9421fe345`；原件SHA `4d59051a454265d834be834768ef3b8b1b5679e225bc7cbaba9b2ef016967d7a`。[222项独立SHA回读](../reports/wc_w3_small_human_production_actual_cpu_audit_r2_20261005.json)核对R2/原96核心、9官方源、两个Human历史视频、输入/CPU原件/日志和实际账本，全部通过，CUDA未初始化。原99秒核心不重跑，GPU/真实新视频/第二点评分仍0。

[R2冻结109文件清单](../manifests/wc_w3_small_human_production_cpu_r2_20261005.json)与草案保持运行前字节；其中NOT_YET_EXECUTED是冻结时状态，本段和独立回执记录之后的验收，不修改已运行stage追认原哈希。下一GPU配置必须绑定R2原件及原109文件表，除新GPU选择/批准及相应配置外所有已实际CPU检验源码保持。

## 当前执行授权边界

生产草案GPU未选、UUID空、execution_scope_authority=null，没有预付/启动。累计24h来自用户原文：**“批准 WC-W3-SMALL-CD-R1-20261004-A，把累计 gpuh 限制提升到 24”**，见[直接授权原件](../manifests/budget_authorization_20261005_wc_24gpuh.json)。它具体绑定原card/run和3900秒单次；该卡已经执行，不能静默变成新run或4500秒。

新卡在CPU门完整后需要一次具体范围确认。届时新增直接人类授权原件及其SHA，再冻结新GPU source/payload、fresh准入和唯一提交；不复用旧GPU授权、不重提旧run，不因自动goal接续创建授权。本文准备/CPU阶段沿用持续目标的常规自主工作。

## 完成判据与后序

完整1父6后缀4新视频、真实历史父桥、终态费用/释放与两LPIPS/1有符号诊断都成立后，补验卡才能接受。与已完成常识点分别列出来源和成本形成原两点的跨卡证据；原卡仍保持限时失败，不能把跨卡合并当同一次完整批次或独立CONF。

若有机制收益，再按真实完整费用准备B四对同CFG配额位置交换，区分“更多/更少计算的效果”与“同配额计算位置的效果”。Head、LoRA、专家训练、稀疏扩大和新增人评继续后置。
