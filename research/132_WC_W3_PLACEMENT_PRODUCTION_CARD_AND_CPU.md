# W3-B完整同配额位置交换：生产卡与CPU验证

## 科学问题和当前价值

两真实C/D点说明刷新位置会影响终点保真：Common原WC已经选择较好的D，Human原WC选择C，而强制D的全帧LPIPS低0.0119268468。Human单点存在改进空间，但C/D会改变后续刷新次数。B保留原先登记的四对位置，检验**固定两个CFG分支各自的完整计算次数，仅移动刷新位置，是否仍能改善Native相对保真**。

这次新增完整运行、监督结算、终态审计和评分入口，复用已经通过的完整核心与旧资源，不再重跑未变化的Toy采样。R1是本机初稿；R2补齐实费原件、冻结预算快照和视频读取/评分导入绑定，实际服务器CPU验证以R2为准，R1不追认服务器验证。

## 可审阅的完整执行卡

| 字段 | 固定范围 |
|---|---|
| 卡 / run | `WC-W3-PLACEMENT-SWAP-R1-20261004-A` / `wc-w3-placement-swap-r1` |
| 模型与输入 | Cosmos-Predict2.5-2B，CAL索引1/2、seed0，768×432/93帧/16fps |
| 采样与近似器 | 原UniPC/Karras 35请求→36更新/72CFG，原WC probe2/阈值0.06、dense算子 |
| 四对交换 | Common CFG0 47→49、CFG1 48→50；Human CFG0 61→63、CFG1 46→48 |
| 全矩阵 | 2父，16完整后缀，10新编码输出，2历史Native，6全帧损失，4有符号双位置诊断 |
| 每场景顺序 | OFF1/OFF2/BASE1/SWAP0_first/SWAP1_first/SWAP1_second/SWAP0_second/BASE2 |
| 重复与编码桥 | 全轨迹/缓存/solver/condition/RNG还原，四组重复；OFF和BASE均复现母轨及编码SHA；母轨绑定历史WC |
| 预算草案 | 总9600秒、child9570秒、kill5秒、准入规划另15秒；至多2.666667GPUh计入原24累计 |
| 实费重估 | 名义7684.634694秒、规划9251.561633秒，来自两点完整实费；均非硬保证 |
| 当前预算 | 已用12.99974633233337/24GPUh，47jobs，无inflight；余11.00025366766663h |
| 当前执行决定 | GPU未选、UUID空、scope authority空、预付0；尚未批准此新卡GPU范围 |

原[`scope`](../configs/wc_w3_placement_scope_r1_draft.json)逐字保持，包括其当时未选GPU/未就绪标记；生产别名及`execution_limits`在独立[`R2配置`](../configs/wc_w3_placement_production_r2_draft.json)，不改旧scope来追认权限或成本。B的GPU范围不能从已经执行的3900秒A或4500秒Human卡迁移；新卡需要对应的新范围确认。

同CFG配额不是同秒数。每场景原whole full次数Common18/17、Human20/18；SWAP只改变两个动作。保护位置的自然动作若与固定mask冲突，或自身缓存不合法，记录不可行并保留2/16/10/4分母，无fallback、无换点、无缩卡。失败、未完成、负收益均保存；技术停止和有限配置负结果不等于W3方向否定。

## 新入口与验证

- [`run`](../scripts/run_wc_w3_placement.py)：先来源/资产/真实根检查；选GPU时在预付前核验实际生产CPU原件及新卡确认，再调用完整B核心。
- [`supervisor`](../scripts/supervise_wc_w3_placement.py)：全局f1锁、fresh UUID/VRAM/compute/磁盘/原24账本，无他人任务干预；单次限时、原三个进程句柄、监控、按实际完整wall结算，失败也计费，账本并发变化不覆盖。
- [`terminal audit`](../scripts/audit_wc_w3_placement_terminal.py)：全部来源、两CFG配额、控制轨迹、10新+2旧93帧视频、费用重算和释放。
- [`CPU scoring`](../scripts/analyze_wc_w3_placement_lpips_cpu.py)：释放GPU后复用原CPU FP32 LPIPS0.1.4/v0.1 Alex、全部93帧与PTS；六损失生成四个BASE−SWAP有符号值。数值协议与旧A一致，监督含义独立标注，负数保留。

本机纯CPU通过36项生产拒绝、11项有符号损失拒绝及正负四例；读取R4原完整4父32后缀20模拟输出重新核验，未重跑采样。预算测试仅内存，真实账本不写。新136文件生产payload包含全部R4冻结117文件，旧Human评估源码及旧预算文件使用原stage字节，当前根账本另读；不拿当前文件覆盖历史闭包。

实际服务器R2 CPU与独立原件审计：**待执行**。CPU通过也不建立四真实位置GPU合法性、最终视频收益、在线方法/同秒数、训练标签或独立CONF结论。现有C/D结果、原失败卡与费用、旧判据保持。

## 后续与探索性判读

按[131科研原则](131_EXPLORATORY_RESEARCH_PRINCIPLES.md)及[下一轮假设登记](../manifests/wc_exploratory_hypotheses_r1_20261005.json)：先完成B生产CPU；具体范围确认及fresh准入后唯一完整GPU卡；结束结算、审计、全帧评分。若部分对为负或不合法，先核查相应实现、两位置联合目标与指标对齐，描述适用条件，优先低成本区分分析。旧A结果后的分析标探索性；B结果尚未读取或执行。不新增训练、稀疏扩大或非必要人评。重要方向取舍共同讨论。
