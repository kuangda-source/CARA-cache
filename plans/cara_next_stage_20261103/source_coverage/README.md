# 来源覆盖驱动的终点校准刷新规划

2026-11-03，用户同意先做 CPU 验证。本轮交付是可运行的候选生成器、完整终点选择器和实际 CPU 验证，沿用 P0 的写入机制证据。研究问题是：**控制缓存来源在未来更新中的覆盖，能否用一个小型计划族提高完整视频校准的效率，并由同一规则生成不同预算的计划？**

## 首版方法

固定 Cosmos、UniPC、CFG 和纯 C 读出，只生成 D/C 位置。真实网格为 35 步请求、36 次更新；精确支持 19D 和 22D，继承前七次与末次 D、至少两个真实来源、最大来源年龄 28。生成器输入仅为网格、执行 profile 和 D 配额，没有旧赢家掩码或局部误差标签输入。

令 `s_t = sigma_t / sigma_1`，最近两个真实 D 为 `a < b < t`。每次 C 都会演化缓存工作状态，因而使用更新时钟与噪声时钟的等权距离：

\[
d(t,k)=\frac12\left(\frac{t-k}{N}+|s_t-s_k|\right),\qquad
r_\gamma(t\mid a,b)=e^{\gamma(s_t-1/2)}\frac{d(t,a)+d(t,b)}2.
\]

第一轮仅使用噪声距离的 CPU 草稿允许早段很长的连续复用；加入更新时钟后，近乎平坦的 sigma 段仍支付实际来源寿命。该修订依据调用结构，没有使用新视频或旧 LPIPS 调参。

固定四个阶段倾向 `gamma = [0, -2, 2, 4]`，覆盖中性、后段和两档前段倾向。每档在精确 D 配额下先最小化所有 C 的最大覆盖距离，再在这个最小瓶颈内最小化距离平方和，最多取三条计划。距离按 `1e-12` 量化后比较，最后以 D 序列字典序确定并列。先解瓶颈、再解加性路径；不能在一次 DP 中按前缀“峰值、能量”直接剪枝，因为后续大瓶颈会改变前缀优先顺序。

四档合并后按实际掩码去重，最多 12 条，重复额度不补入手工候选。当前主方法池为 **19D 12 条、22D 8 条**。每条都保存两来源消费者与替换位置；真实缓存的三个物理窗口槽、C 工作状态和 UniPC 历史仍由原执行器完整保留。

覆盖距离用于构造候选。最终选择使用完整视频的输入等权 LPIPS。CPU 选择器要求完整候选×FIT 记录、每条 93 帧、相同指标协议及每输入固定参考，保留失败/缺失和其费用，按 LPIPS、固定候选顺序选一次。费用包含失败与共用参考/控制开销；双时钟同时保留。它只处理调用方提供的完整记录，不执行视频生成、评分或冻结。

## 关键消融

| 版本 | 改动 | 当前 19D / 22D 去重候选数 |
|---|---|---|
| 双来源覆盖 | 上式 | 12 / 8 |
| 单来源覆盖 | 只用 `d(t,b)`，其余程序相同 | 8 / 9 |
| 无阶段倾向 | 固定 `gamma=0`，是主池的预定子集 | 3 / 3 |

两来源的总直接读取数恒为 `2(N-K)`，每 CFG 分支分别计数。它不能作为最大化目标；有信息的是各来源的消费分布、年龄及覆盖距离。CPU 已验证 D 交换会重新计算后续来源区间，而不是只更改交换步的局部代价。

## CPU 实际结果

[完整回执](../../../reports/cara_source_coverage_CPU_acceptance_r4_20261103.json)记录 **16/16 本地控制通过**，用时约 4.43 秒，没有新增 GPU 支出。

- 180 组小网格/预算/时钟形状/来源模式/阶段倾向与独立穷举一致，包含无解配额的拒绝。
- 真实 36 更新网格的 19D/22D 候选精确编译、去重、重跑确定性通过。
- 8 条完整 36 更新的小权重路径、576 次 CFG 分支更新、124 次 C 配对更新通过原 WC/RF/UniPC 对照。latent、完整 solver 历史、缓存、缓冲区逐步精确一致；两种 flow 设置、两 CFG 来源及调用方状态不被修改均通过。
- 额外声明的合成 51 更新网格可用同一程序生成 27D，共 10 条候选。这是算法网格控制，尚非真实 50 步生产缓存入口或视频迁移结果。
- 真实 `generate → select` CLI 在临时文件上通过；终点分数是明确标记的合成 fixture，未计算真实视频质量。

候选原件：[CPU_CANDIDATE_POOLS_R4.json](CPU_CANDIDATE_POOLS_R4.json)。它们是 CPU 计划工件，所有真实终点分数仍为空。

## 复跑

```bash
.venv/bin/python scripts/cara_source_coverage_r1.py cpu \
  --output /tmp/cara-source-coverage-cpu-new.json \
  --pools-output /tmp/cara-source-coverage-pools-new.json

.venv/bin/python scripts/cara_source_coverage_r1.py generate \
  --manifest plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_MANIFEST_R1.json \
  --dense 19 --output /tmp/cara-source-coverage-19-new.json
```

`select` 接受 `--pool --rows --fit ... --cost-limit-gpuh --overhead-gpuh --output`。输入每行含候选、成员、状态、93 帧 LPIPS、双时钟、实耗及 input/reference/metric 协议 SHA；失败行仍必须占据其位置并报告实耗。输出写入新文件。

## 下一步

当前以[872零GPU审计与预算重排](../../../research/872_CARA_C1_ZERO_GPU_AUDIT_AND_BUDGET_REPRIORITIZATION_20261103.md)和[19D条件草案](c1/C1_REDUCED19_PROPOSAL_R2.md)为准：原166位置／14.82GPUh方案暂停。原42个FIT查询的SHA和排序已完整核验；正阶段权重提供排序信号，双来源没有一致增量。先继续F19→1.9×准备并保护Shared25独立最终确认额度。条件C1缩为70请求上界、预计6.536GPUh／建议硬7，不据此次审计自动启动。

原[166范围与报价](c1/C1_REVIEW_R1.md)、31项本地/LinuxCPU和候选库原样保留；它们不接受新70请求生产入口。新增5项CPU控制覆盖离线目标一致、原评分SHA与A1规则，见[回执](../../../reports/cara_source_coverage_zero_GPU_CPU_controls_r1_20261103.json)。当前GPU和账本操作均为0。

## 已保存数据的完整审计

原P1算法摘要SHA仍为`63a9c14fc342025cc3c05f2572c15ed9879a51b645ec2bab3d26a5af7383fd55`，与原完整接受绑定。64标签的三个父计划留出MSE为0.248141、0.229860、0.209898；局部预测与终点排序是分别报告的证据。

[原24查询诊断](../../../reports/cara_source_proxy_saved_CPU_audit_r1_20261103.json)和[原3项CPU控制](../../../reports/cara_source_proxy_saved_CPU_controls_r1_20261103.json)保留。此前缺少的18次DP端点现已从原文件补齐：[42份原评分字节](../../../reports/cara_source_coverage_P1_original42_score_returns_r1_20261103.json)、[旧误差代理完整审计](../../../reports/cara_source_proxy_saved42_CPU_audit_r2_20261103.json)、[新几何覆盖审计](../../../reports/cara_source_coverage_C1_zero_GPU_audit_r1_20261103.json)。它们使用已有两个FIT的原93帧指标，不重跑任何旧读者、模型或评分。

旧[869结果](../../../research/869_CARA_P1_R2_COMPLETE_RESULTS_SOURCE_INCREMENT_FAILED_20261103.md)、冻结、实际费用和保护输入保持。新的条件草案不是旧P1重跑或对原工程判定的改写。
