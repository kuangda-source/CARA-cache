# W3 同刷新配额位置交换：完整科学范围和费用

2026-10-04；PREREGISTERED_STATIC_SCOPE / LOCAL_CPU_AUDIT_PASS / GPU_NOT_SELECTED。这是[下一窗口计划](../plans/WORLD_CACHE_W3_NEXT_WINDOW_20261004.md)中W3-B的准备；前一小C/D卡已完成实际CPU，新GPU许可仍待回复，本轮没有重发请求或启动GPU。

## 四个科学比较与完整控制

[范围草案](../configs/wc_w3_placement_scope_r1_draft.json)使用新身份WC-W3-PLACEMENT-SWAP-R1-20261004-A / wc-w3-placement-swap-r1。两个已曝光CAL，各两个同CFG交换：常识47→49、48→50；人物61→63、46→48。各从step22状态续推14次UniPC更新/28CFG。选择只读历史父行动mask，不读取终点或本轮深层误差；四个比较相关于两个场景，不是四个独立样本。

| 每场景后缀 | 用途 | 是否独立编码 |
|---|---|---|
| OFF1 / OFF2 | 原自适应未干预续推重复、父恢复和完整轨迹桥 | OFF1 |
| BASE1 / BASE2 | 固定原父mask的完整状态/轨迹重复，确认与OFF/父续推相同 | BASE1 |
| SWAP0_first / SWAP0_second | CFG0两位置交换，完整重复 | first |
| SWAP1_first / SWAP1_second | CFG1两位置交换，完整重复 | first |

执行顺序固定OFF1/OFF2/BASE1/SWAP0_first/SWAP1_first/SWAP1_second/SWAP0_second/BASE2。完整 **2父、16后缀、10新输出**（每场景parent+四个独立子编码），不是只有四条后缀。保留2个历史匹配Native参考，6个Native相对损失（两baseline+四swap），形成4个有符号baseline−swap诊断；负收益、不可行、失败和未执行均保留冻结四对分母。

固定的是行动，两臂各自演化latent、缓存、条件、RNG和完整多步solver历史。两CFG完整调用配额分别核对；初始化/前44调用及69..72不改，末尾保护必须使用自然动作，不能fallback D后仍称匹配。需逐分支验证过去同CFG真full/已支付probe/有限数值/合法年龄。人物原父69/70为C，不改成强制C；若新轨迹自然保护变成D，这次交换不可行。最大年龄33沿用121固定接口，与A单步动作的32不同，未修改任一旧核心。

新父完整mask须匹配冻结父mask。当前GPU父到历史WC的context/settings/grid/字节桥、OFF父continuation和编码桥、BASE与OFF全轨迹/终态/完整pipeline和编码桥、各swap重复与实际两处动作/两CFG配额都属于科学对照。CPU静态合法不能替代这些实际状态检查。这里测两位置联合收益，不是单步Head标签、在线策略或同秒数优势。

## 完整费用揭示的限制

按112恢复实费和107公平实费计一次加载、两条含诊断父、16后缀、8子编码及bookkeeping，加20%规划余量和30秒退出：

| 口径 | 秒 | 解释 |
|---|---:|---|
| B完整名义代理 | **3460.499654** | 未干预后缀实費代理，包含全部控制 |
| B完整压力代理 | **7858.075341** | 每短后缀按整段Native35+25秒恢复估价；非硬上界 |
| 当前全余额 | **7119.663527** | 13h−11.022315686839217h |
| A若花满3900秒后的余额 | **3219.663527** | 已花的准入实费还须扣除；15秒是准入包络，不自动计实费 |
| 原A准入包络3915秒占用后可承诺余额 | **3204.663527** | 采用计划保守口径 |

B名义3460.499654秒再加15准入，比A只花3900秒后余额仍多 **255.836126秒**；若A整个3915准入包络都计作消耗，则多 **270.836126秒**。两批名义加两次15秒准入共 **6302.001840秒**；只是条件算术，不承诺实际可完成。B压力代理本身超过当前全余额，也不能给它套原0.90h=3240秒而声称可完成。

**因此B暂不选timeout、不预付、不准入。** 必须按A真实实费、后缀、编码和释放记录重估；不能删除OFF、BASE或重复来凑预算，也不能把剩余余额自动转移或扩额。A的收益符号不作为B取消门：单次额外刷新无益不等于同配额位置交换无益；A技术兼容性/真实成本以及B自己的参考桥仍需检查。

这里A和B各需要自己的新父及控制，没有假定GPU状态能从已退出的A进程直接复用。Native历史视频仅在B当前父严格桥成立时复用。最终必须报告实际时间，原Native不是物理真值。

## 本轮验证与下一步

[CPU准备](../reports/wc_w3_placement_scope_cpu_preparation_r1_20261004.json) / [独立本地审计](../reports/wc_w3_placement_scope_cpu_audit_r1_20261004.json)：直接从FAIR原始72-call trace重算四对、保护和两CFG配额；从112/107原始实费独立重算全矩阵费用；11项拒绝缺重复、减输出、总数代替CFG、终点挑选、在线/单步标签、未估价GPU等错误。A已通过实际CPU的80文件、旧V1/full RV0/core/fixed模块及账本SHA保持。

本轮仅纯CPU范围/费用准备，没有传送、Torch/CUDA、模型、视频或方法收益。新增[范围代码](../src/wcomr/rv0_placement_scope.py)、[准备入口](../scripts/prepare_wc_w3_placement_scope_cpu.py)及[审计入口](../scripts/audit_wc_w3_placement_scope_cpu.py)没有实现生产swap runner或替代121接口验收。下一关键动作仍是已完成CPU准备的真实A诊断；GPU确认等待中。B只保留完整科学范围，等A实費后再选择生产实现/卡和资源门，不重复既有相同CPU控制、不新增人评或训练。
