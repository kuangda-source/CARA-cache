# WC-S1：12组真实 QKV 的路由/无PV技术门

2026-10-01，接续已审计 S0，不构造模型、不生成新视频、不修改部署cache，不增加原4GPUh。[输入锁](../manifests/wc_s1_real_qkv_inputs_20261001.json)、[配置](../configs/wc_s1_real_qkv.json)。

## 冻结范围

首个CAL8场景/seed0的全部12个post-norm/RoPE QKV，调用1/2/71/72×层2/14/27，固定原顺序。原S0 receipt/audit SHA、每个文件SHA/bytes与实际tensor bytes绑定；不根据新结果选择层/调用。B1/N31104/H16/D128 BF16，非因果self attention。

使用原pinned SpargeAttn `ae5b629` 的 `get_block_map_meansim_fuse_quant`，Ampere BLKQ128/BLKK64、K中心化、attention_sink=false、PV skipping始终关闭。两组已有参数：公开CUDA入口默认sim0.6/cdf0.98，utils入口默认sim0.1/cdf0.9；只是现有策略技术筛查，不是搜索或原创方法。

每输入6臂，共72 case：当前dense、vanilla quant/no-PV全块；每组策略另有routing→forced-full与routing→selected-sparse两臂。每个pair共享packing、fused quant/路由、scale与同一无PV binding，只改变实际执行的QK块；forced-full仍执行完整路由，不能当部署优化。保留每组单独matched full reference，报告对dense和该matched-full的相对RMSE、实际selected/executed比例。

每case先1warmup后3repeat同步wall与CUDA events。操作wall包含输入/row/finite validation、packing、完整动态选择+quant、LUT、flatten、统计/同步，forced-full还包括全mask物化；不把只测kernel的时间当部署净时间。文件load/transfer、import/JIT、异常/flush/释放全按监督process wall计GPU账本；首次JIT虽不在热重复内，仍计总预算。

## 技术筛查与预算

预留180秒，child timeout170秒、5秒kill、15秒余额准入余量；当前余438.007060秒。global锁、任何inflight拒绝、fresh UUID/VRAM/compute PID，验证后再准入；唯一新stage/launch identity，不重跑S0或原合成kernel launch。

全mask技术筛查相对dense RMSE<=0.05（vanilla与两matched-full全12输入）。稀疏诊断screen：对dense与matched-full误差均<=0.05，含routing实际同步wall比dense至少快1.1×；必须保留所有不通过输入，不因筛查失败中断剩余覆盖。此容差不是视频质量/行为保持门，通过也不直接部署或声称论文收益。

本地7个CPU控制通过：两组新routing/full控制验证共用原量化对象、仅LUT执行map不同、no-PV12参数、形状/RNG/输入version未改，非法map/空row提前拒绝；预算门验证固定180秒/原4h/任何inflight拒绝，原no-PV3控制保留。这些是实现证据，实际策略路由/kernel仍需GPU。

## 接续决策

若已有策略在真实QKV没有净速度或误差过大，先定位实际块相似性/fallback保留率及量化混杂，不能用合成band加速覆盖负结果。只有full控制与真实选择均有信号才设计固定WC轨迹的组合臂和模块替换，稀疏state不当true dense anchor。闭环质量/端到端曲线仍未验收；新方法需超出现成组合的计算分配或误差控制贡献。
