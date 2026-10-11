# 新数学调度方案：设计更新、实际来源合同与预算（2026-10-12）

新的执行主线为来源一致的相关误差融合＋多精度事件调度。端到端小测速已完成，不重跑；其无P保真正结果和P的明确成本取舍均保留。用户已直接授权尝试新核心方法，参考包的旧“无执行授权”声明不覆盖本次用户指令。

[详细设计](../plans/WORLD_CACHE_SOURCE_CONSISTENT_MATH_SCHEDULER_20261012.md)按N0已有记录→N1同状态监督→N2完整H1/H2候选→P执行器成本／新输入确认推进。相关误差gain不是独立噪声Kalman；线性融合明确放在真实warp/head/RF之后。数学数值CPU十项已通过，只是公式与低维控制原型，不是GPU或方法收益。

N0重读完整E3原SHA：旧A基于真D参考，风险漂移则查工作P年龄；这确实是对象不同的合同，能解释出一个待检验假设，尚不能唯一归因NONZERO终点退化。旧检查点未序列化完整可恢复状态，不能用输出向量或视频免费重建teacher；四条自然父路径必须在N1计费重放。

## 固定自然状态

八P点依首次自然读取及其余最大D/P参考间隔选择，不看teacher或候选误差。增加四D来源点是防止新P读出改变原D分支的必要控制，不增加新父路径。完整N1为4父×36常规pairs＋12teacher＋24额外候选＝180pairs/360CFG；48评分位置，不是旧P卡的32后缀或688pairs缩卡。

|场景|步骤|来源|选择角色|D参考与工作源间隔|
|---|---:|---|---|---:|
|AV28|20|P|FIRST_NATURAL_P_READ|5|
|AV28|23|P|MAX_REFERENCE_GAP_EXCLUDING_FIRST|8|
|AV28|8|D|TRUE_D_SOURCE_REFERENCE_CONTROL|0|
|Human|14|P|FIRST_NATURAL_P_READ|6|
|Human|26|P|MAX_REFERENCE_GAP_EXCLUDING_FIRST|18|
|Human|8|D|TRUE_D_SOURCE_REFERENCE_CONTROL|0|
|misc|20|P|FIRST_NATURAL_P_READ|5|
|misc|28|P|MAX_REFERENCE_GAP_EXCLUDING_FIRST|13|
|misc|8|D|TRUE_D_SOURCE_REFERENCE_CONTROL|0|
|AV51|14|P|FIRST_NATURAL_P_READ|6|
|AV51|20|P|MAX_REFERENCE_GAP_EXCLUDING_FIRST|12|
|AV51|8|D|TRUE_D_SOURCE_REFERENCE_CONTROL|0|

## 新48窗口实际生效

服务器在f1内核锁内核对旧账本SHA与无inflight后原子更新：历史实耗56.97136333301379GPUh、82提交完全保留；从这里48可用，累计cap104.97136333301378。不是将48加到旧余20.9239上。预算更新0GPU提交，数学／采样CPU另行验证；完整单次≤8自主、严格>8准确提问，禁止拆卡或去控制绕过。

[直接用户授权](../manifests/budget_authorization_20261012_wc_math_scheduler_new48gpuh.json) · [服务器实际应用回执](../reports/wc_math_scheduler_new48_policy_receipt_20261012.json) · [自然12状态索引](../manifests/wc_math_n1_natural_state_index_r1_20261012.json)

原13.0600GPUh P卡继续用户暂缓，不执行、不重問；E2无P76范围和自己的>8问题保持。本轮下一步是独立部署实际两flow采样CPU，再具体化N1完整生产成本和准入。新CPU数值通过不表示新方法已经有效。
