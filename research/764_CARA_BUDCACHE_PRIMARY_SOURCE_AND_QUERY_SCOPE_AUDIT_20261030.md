# BudCache强基线的原文、官方实现与查询范围核查

2026-10-30。按已采纳设计A2.1，正式方法比较需要预算分配类近邻。主线已核对原文及官方发布代码，并在本地用模型替身执行其搜索控制器。结果明确了该基线适配所需的评价口径、候选查询数和费用边界；没有运行模型、加载权重或提交GPU。

## 来源与实际核查

[BudCache原文](https://arxiv.org/html/2606.13496v1)采用固定计算配额的SA/HC搜索；时间网格优化是另一阶段。[官方说明](https://github.com/Westlake-AGI-Lab/BudCache/tree/14ba4c5106a17848e757e7b93ad4b4daeb5b742c)将Stage1作为默认结果，Stage2可选。本轮固定官方提交 `14ba4c5106a17848e757e7b93ad4b4daeb5b742c`；七份原文件的URL、SHA和字节长度见[机器回执](../reports/cara_fast_BudCache_source_CPU_audit_r1_20261030.json)。上游保持原样，原副本及Apache-2.0许可放在本地忽略目录，未装其模型环境。

代码核对发现：Wan入口的`get_latents`最终返回VAE解码视频，因此搜索损失是解码视频MSE；HC每轮随机取至多20个邻居，未枚举完整邻域；配置中的`stage0_multiStart`未被此入口消费；`cfg.seed`固定生成噪声，但该搜索脚本与launcher未初始化Python/NumPy搜索随机源；保存的`speedup`只是步数/NFE之比。这些是指定发布版的实现事实，不把论文伪代码与具体入口混为一体。[搜索入口](https://github.com/Westlake-AGI-Lab/BudCache/blob/14ba4c5106a17848e757e7b93ad4b4daeb5b742c/scripts/stage1_search_wan.py) · [生成入口](https://github.com/Westlake-AGI-Lab/BudCache/blob/14ba4c5106a17848e757e7b93ad4b4daeb5b742c/src/wan/wan_generate.py)

[CPU核查脚本](../scripts/audit_cara_budcache_source_r1.py)先校验七份上游原SHA，只编译原`mutate_schedule`、`get_swap_neighbors`和`main`三函数。模型、MSE、保存和CUDA操作均显式替换为CPU控制；使用Python3.12.14、NumPy2.2.6、固定fixture RNG12345、平坦损失。

| 控制器实际计数 | 结果 |
|---|---:|
| 教师替身请求 | 1 |
| 初始候选＋SA候选＋HC候选 | 1＋200＋100＝301 |
| 总替身生成请求 | 302 |
| 唯一候选 / 重复调用 | 273 / 28 |
| SA / HC历史记录 | 200 / 5 |
| 将multiStart从1改7后的调用序列 | 完全相同 |

全部候选满足原50步/20NFE和前缀约束。此fixture证实平坦损失下仍完成5轮HC，重复候选仍调用评价器；这些计数不代表真实生成效果、GPU时长或所有随机种子的唯一候选数。另三项拒绝控制通过：上游字节改变、函数缺失和配额破坏均被拒绝。

## Cosmos适配提案与完整费用

[适配提案](../plans/cara_next_stage_20261028/mainline/r2/BUDCACHE_ADAPTATION_R1.json)使用明确名称“BudCache-style SA+HC with CARA-C readout”，保留SA与采样HC，使用相同Cosmos读出、实际36步/19D、保护点和合法历史支持。不能把搜索偷偷限制在F19的单次交换170候选来削弱近邻。共同Uniform19起点、两FIT等权、生成seed0、独立搜索随机源及实际双时钟均须事前绑定；这是适配版，不宣称完整官方复现。

原Wan损失需通过完整自由生成获得，S的局部矩不能充当候选终点分数。教师只有请求/源/RNG及编码前RGB身份完全兼容才可复用，否则计入新请求。保持CHECK与最终输入在选参之外，真实候选没有读取或评价。

若直接保留默认控制器强度、每个候选评价两个FIT且教师不复用，规划上界是**604个完整请求**；这还不是整卡GPUh报价，额外warm、控制、计时重复、分配释放和失败开销另计。两个方法的D配额相同不意味着校准成本或终点评价次数相同。正式比较须登记共同允许的终点查询上限及完整校准GPUh，同时报告实际消耗；若截断搜索，记录best-so-far和预算耗尽，不能称HC已收敛。

本轮没有冻结实际查询上限、GPU范围或新预算，未改变已批准的S采集卡。下一步是接入有完整身份和查询账目的Cosmos评价器、双端受影响CPU验证，再按整卡报价决定执行；S优先顺序保持。当前成果是可复核的上游控制器证据与适配边界，不是生产适配完成或新的科学结果。
