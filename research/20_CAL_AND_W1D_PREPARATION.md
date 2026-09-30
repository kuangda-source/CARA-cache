# CAL来源连接与下一轮W1-D准备

2026-09-30；CAL membership FROZEN_NOT_GENERATED；W1-D IMPLEMENTED_CPU_CHECKED_NOT_GPU_RUN。

## 来源与分组

从[官方生成基准元数据](https://huggingface.co/datasets/shi-labs/physical-ai-bench-generation/blob/c36b7beb69bd7c4adcedc1431407fce98f9dfe44/cosmos_predict2_bench_full_info.json)取得固定revision `c36b7beb69bd7c4adcedc1431407fce98f9dfe44`，1,600,937字节，SHA256 `3f495989e5869a1987096b515ea33053d881de1e3fe4643ffa9b6bd2621aa2b8`。全部1,044个video_id连接到固定WorldCache本地prompt，标准化prompt完全匹配，0缺失/不符；元数据包含reference_video和image_name。没有下载视频/图像。

按reference_video及预固定word-TFIDF cosine≥0.85连通分量分组（显式停用词、sublinear tf/smooth idf）。全部reference_video名称唯一；human_178/human_251词法近重复合为一组，形成1,043组。数值矩阵经有限、对称、有界与单位对角线检查；macOS BLAS状态警告路径已改为显式einsum归约。不要把阈值以下或唯一filename当作语义/源录制独立性的证明；原始recording/session信息未取得。

使用固定salt的SHA256顺序，在每个组取一代表，按配额冻结24个CAL：AV/common/human/physics/robot各4，industry/misc各2。四个工程样本及其整个组排除。首批8已在看新生成结果前冻结：七域各一个、第二个AV。CAL可复用开发/校准，不用于盲确认；DEV/CONF未冻结。最终确认仍须处理源录制/语义重复与历史曝光边界。

依据：[来源manifest](../manifests/pab_generation_source.json)、[分组审计](../reports/dataset_source_group_audit_20260930.json)、[CAL清单](../manifests/cal_v1.json)。复现：下载manifest固定URL到ignored路径；执行`scripts/audit_dataset_sources.py --source ... --source-receipt manifests/pab_generation_source.json --output reports/dataset_source_group_audit_20260930.json`，再`scripts/freeze_cal.py`；两者均为CPU/选择依据，非质量证据。

## W1-D最小范围

复现门工程样本已通过，下一步在CAL前8进行官方/scalar-recent(decay0)/shrink0.5同状态稀疏诊断，参数冻结，不继续调beta参数。所有off/on路径共用新局部解码策略。每个样本先off记录实际skip，两CFG且至少两个过去full anchors可用的skip pair，按时间覆盖选择最多四对；选择在任何当前truth/候选误差被计算前冻结。若没有足够skip，记录覆盖不足，不按数值结果替换样本。

在当前官方轨迹同latent/分支/timestep产出三预测，再补一次共享full truth，只评分，不更新任何anchor/cache/refresh。记录pre/post warp与velocity的整体及视频时间/2×2空间/少量通道组分布，区分latent token坐标与输出速度坐标；源码布局核验后显式映射，不猜shape。记录anchor年龄、beta/fallback、full/skip、额外诊断成本。每个样本off/on逐次输出/trace/cache/latent与raw decode严格相同，接受时视频相同。保留安全拒绝/异常/技术失败分母，不关闭检查或挑选替补。

## 预算与决策

既有单样本off/on+四点truth实测约530秒含加载，扣单次加载后生成/评分约430秒；8个样本共用一次model load，增加稀疏点/分布归约，粗估3,800–4,500秒。下一轮提议一次单GPU串行batch上限6,000秒/1.666667GPUh，从现有2.002225685h余额扣除，预留至少0.335559018h。不增加总4小时预算；硬截止包含加载、失败、flush，部分完成按INCONCLUSIVE/覆盖实际报告。尚未实现或启动；完成CPU/源码部署/预算锁/GPU准入核验后方可提交。

以样本为主要单位，报告候选相对官方的各样本aggregate误差、覆盖/拒绝/fallback及残差-versus-velocity排序，不把token/帧/CFG点当独立样本。初轮筛查不作统计确认或质量推断。数值异质性/排序反转能支持下一局部假设，但仍不足以称质量损害或批准复杂W2；8场景再无优势则暂停这一标量/收缩公式线，优先F2成本可行性或报告资源缺口。完整F2的12–24场景多工作点明显超过当前剩余预算，不能以少数样本冒充完成。无需人工评审，不训练/付费评分。

## 实现冻结

`run_w1d_cal.py`一次加载依次执行8off/on，保留原keep_going语义下的text/video拒绝，未知错误立即终止。OFF trace每样本先冻结四对诊断点，ON共用full truth并记录明确布局的分布/缓存年龄。逐call输出、cache/trace、latent/raw decode/guardrail/接受视频及flags/decoder状态相同才认技术通过；无可用skip记覆盖不足，不能冒充负结果。`supervise_f1.py --w1d-cal`单batch最多6000秒，原项目锁/准入/冲突停止/记账保留。

筛查规则在新数值结果前固定：全部8各4对且无fallback；候选至少6/8样本联合改善velocity与postwarp，两个等样本权重均值比均小于1才MECHANISM_ONLY_CAL8；两候选velocity均值都不低于1则NO_GAIN_CAL8_IN_SCOPE，其余INCONCLUSIVE。任何partial只LIVE_PARTIAL_NO_DECISION。拒绝样本保留分母，作为数值诊断，不据此声称可接受质量。针对性43项本机CPU检查通过，尚未GPU提交。
