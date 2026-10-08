# W3下一区分：同状态双CFG合成误差，H-T45

2026-10-09。承接[164](../research/164_WC_CFG_BUDGET_MATCHED_COMPLETE_RESULTS_20261009.md)与[165](../research/165_WC_CFG_BUDGET_CONTEXT_CPU_AND_NEXT_20261009.md)。终点结果已经曝光，下一项是机制探索，不独立CONF、不训练Head，也不把局部误差当终点收益标签。

## 问题与实现校正

单槽提前刷新且强制复用供体会退化；成对提前只微弱改善。区分两种解释候选：

- H-T45a：两分支误差相关，原CFG合成中的抵消使单分支刷新可能增大合成误差；联合刷新减少这种错配。
- H-T45b：局部合成误差并不能解释终点，差异主要在供体来源、后续状态/策略中；需要保留后续条件，不能训练单分支局部MSE路由。

从实际服务器源码核对：当前模型slot0为conditional、slot1为unconditional。速度闭包先调用两次denoise，然后执行`cond_v + guidance * (cond_v - uncond_v)`。guidance=7的实数权重为8/−7，而非7/−6；FP32实际运算顺序仍照原式执行，不代换为8c−7u。denoise还会按条件mask把条件帧预测替换成`noise − gt_frames`，因此主要评价必须来自**post-denoise、pre-solver**的实际输出，不能直接用raw net MSE。

绑定服务器运行文件：Video2World RF SHA9b53e3f024e5cbb2cb3778819e1a6fd353923c13ad9b868d99602051640a65e8；Text2World RF sampler SHAc6c68f297859e11c76d2921667a29cabfecef3a7b5d3ab831bf9bb54b25b7d87；WorldCache SHAb485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903。实际对象/closure槽位顺序和条件语义仍须在新collector CPU和生产入口核对，不能仅凭静态检查算真实采样绑定完成。

## 完整诊断范围（新卡，不缩旧卡）

只使用当前Human seed2，原模型/输入/seed/36更新/72CFG/全部视频规格。新卡独立身份`WC-W3-CFG-GUIDED-TEACHER-R1-20261009-A`，尚未选择GPU。

1. 两条完整父轨迹：OFF无诊断与ON只读诊断，各生成一个完整视频，72次输出/动作、36次solver更新、完整cache/solver/RNG/条件/1216组件和视频SHA必须一致；再以旧BASE作为附加输出桥，旧跨卡全状态不追认。
2. 初始共享状态S22：实际完成22更新/44调用后的父快照。在相同快照中执行CC/DC/CD/DD，每细胞两个严格重复，收集真实两次denoise返回值与闭包合成值。C和D动作都必须使用当前自己的真实full历史；DD定义当前局部完整teacher，不是绝对质量真值。
3. 各初始细胞首重复按原UniPC一步生成自己的S23；只在该actual state内再次测CC/DC/CD/DD、各两重复。四个S23允许不同，跨状态的误差不混成同状态对照。
4. 总共**5个共享起点 ×4动作细胞 ×2重复=40个完整CFG速度对，共80次net调用**。初始四细胞首重复的同一速度结果用于四次真实solver一步，不额外重跑或更换状态。没有完整反事实尾部、子视频或终点LPIPS；这不是旧1父10后缀卡的缩减版本，估计对象不同。
5. 每个短分支后恢复共享快照，全部诊断结束后恢复原父S22，再继续原完整生成；teacher不写回原父cache、solver、RNG或后续动作。不把诊断算入部署full/cache计数，单独完整收费。

实现未完成，以上完整collector/回滚/生产CPU均为待验证，不能标已运行。任何细胞/状态不可行或非finite都保留原范围与失败，整卡按技术问题报告，不筛掉失败细胞再汇报均值。

## 指标与可独立核对原件

保存每state/cell/repeat的实际post-denoise条件/无条件FP32 CPU张量、实际closure guided张量、输入/latent/timestep/condition/噪声摘要、完整动作与快照恢复证据。张量保留服务器独立输出，Git只保存SHA、形状、dtype及重建报告。对真正原闭包合成结果与CPU按原运算顺序重算结果进行一致性核对。

主要局部统计是每细胞guided velocity相对同状态DD的MSE及相对CC差值，分别保留条件/无条件误差，不跨state平均后隐藏单点。DD=0由teacher定义，不是发现。检查分支输出在另一动作上下文是否相同，**不假设**四细胞可以从单独两个误差向量完全因子化。

设e0、e1为CC两分支相对DD的有符号误差。CPU float64统计：

\[
\|8e_0-7e_1\|^2=64\|e_0\|^2+49\|e_1\|^2-112\langle e_0,e_1\rangle.
\]

记录有符号内积、cosine、独立能量和交叉项、合成与独立能量比；这条分解是实数/float64解释，实际FP32闭包误差单独记录，并报告运算舍入差值。零范数cosine/零CC相对改善返回缺定义，不加epsilon制造排名。

有“单刷新MSE大于CC、DD低于CC”的同状态信号时，支持分支合成机制进一步验证，仍不保证最终视频收益；无该信号时优先检查S23供体/历史，而不否定W3。没有预设5%局部阈值否定整个方向，也不把新分析追认为旧验收规则。

## CPU先行、费用与执行

先独立完成metrics与真实上游闭包/denoise语义CPU检查，再完整短分支collector集成CPU：所有5×4×2格、两父OFF/ON路径、独立原件重算、状态/条件/solver/RNG/flag回滚、非finite与异常保留、索引/槽位/输入/teacher不写回检查。然后真实生产资源/导入/版本、真实shape snapshot与显存准入、加载/两父完整输出/80次诊断/快照复制/失败费用的完整保守预测。

当前累计24.908110354/50GPUh、余25.091889646GPUh。旧单次>2GPUh直接确认规则保持，新卡完整预测尚未完成；最终≤2GPUh且必要检查全部通过可自主单次执行，>2GPUh才形成具体完整卡请求。不得用旧卡实测替代本卡完整预测，不拆状态/重复挤到2h；旧预测与记录继续保留。

本轮CPU数学检查只验证评分语义，不等于完整collector CPU通过，更不等于真实模型teacher、误差抵消或终点结果。
