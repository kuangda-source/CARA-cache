# 2026-10-02 研究文档包适配记录

## 最新执行授权 — 2026-10-03

[各项目累计12GPUh与恢复后队列](../../research/BUDGET_AUTHORIZATION_20261003.md)取代此前仅文档及旧预算限制；保留已用与历史账目，单昂贵任务，GPU优先WC。WC已用3.9117525685110333GPUh、28jobs保持，当前余额8.088247431488967GPUh。先中间刷新/全26深层覆盖准备和无扰动诊断，再H0互补性、H1来源×寿命；W1/replay已完成不重跑，RV后置。旧new4h/clean50不自动转为新队列。新runner须按明确12h权威账本校验，不能重新执行硬编码4h的旧launch。 下述2026-10-02原包适配/仅文档条目为当时快照。

本库：worldcache-omr-experiments；已核实置顶会话：**WorldCache 研究与实验推进**，ID `01a0f1eb-7894-7ed0-a186-d010111e14b1`。

## 当前 WorldCache 入口与新旧编号

核对基线 HEAD：`30d5ec7a72386b06b762bef9de92b6b2dd52abc7`，本机与远端 main 一致。当前顺序保持：[中间刷新/全 26 深层覆盖准备 → H0 互补性 → H1 来源×寿命 → 有机制依据才 H2 少量分组](../../research/09_NEXT_ACTIONS.md)。已有机制与固定 replay 不重跑；W1/W2 扩展暂停。原包 01 中“不以 token 稀疏 kernel 为起点”是未掌握最新 S/H 结果的通用建议，不能撤销当前 WC-S/H 工作。

| 原包 ID / 缺失项 | 现有证据或计划 | 实际状态与边界 |
|---|---|---|
| WC-F0/F1 | [F1 r3](../../research/11_F1_R3_TECHNICAL_RESULTS.md)、[W1-P0](../../research/12_W1_P0_TERMINAL_RESULTS.md) | 已有技术证据，非新方法质量/独立确认；不从头重跑 |
| WC-F2 / WC-W1C | [clean50 成本与决策](../../research/31_W1_NEXT_WINDOW_COST_AND_DECISION.md)、[准备](../../research/32_W1_CLEAN_TIMING_CPU_PREPARATION.md) | 额外 4h 未获批；实现/准备不等于实际端到端净收益通过 |
| WC-W1A / W1-SHADOW | [CAL8 结果](../../research/21_W1D_CAL8_RESULTS.md)、[分析回执](../../reports/w1d_cal8_r1_analysis.json) | 8 scenes、64 dependent points、7/8 改善，仅机制证据，不是 64 个独立确认样本 |
| WC-W1B / W1-REPLAY | [固定 replay](../../research/24_W1_FIXED_REPLAY_RESULTS.md)、[MUSIQ](../../research/25_W1_IMAGING_RESULTS.md)、[VQA](../../research/28_W1_DEVELOPMENT_VQA_RESULTS.md)、[输入控制](../../research/30_W1_VQA_INPUT_CONTROLS_RESULTS.md) | 原 8 分母：7 接受、robot 拒绝；MUSIQ 3 升 4 降、VQA 6 平 1 降；没有一致质量收益，不代表 W1C 通过 |
| WC-W2 | [既有长程计划](../../plans/LONG_HORIZON_EXPERIMENT_PLAN_WorldCache_20260929.md) | 暂停扩展；不因包中新编号重开分组实验 |
| 原包遗漏 WC-S0/S1 | [55 设计](../../research/55_WC_SPARSE_COMPUTE_COMPRESSION_DESIGN.md)、[61 成本/QKV](../../research/61_WC_S0_COST_REAL_QKV_RESULTS.md)、[64 四组合](../../research/64_WC_S1_FACTORIAL_RESULTS.md) | 两任务 144 kernel cases；sim0.1/CDF0.98 中位 1.286×但联合筛查 6/12，layer27 四输入全部超 5%误差。仅 kernel 技术结果，未验收稀疏视频质量—时间 |
| 原包遗漏 H0/H1/H2 | [65 来源×寿命设计](../../research/65_WC_HIERARCHICAL_PROVENANCE_LIFETIME_DESIGN.md) | 缺中间刷新/全 26 深层覆盖；补覆盖条件通过后 H0，再 H1 来源×1/2/4 有效 solver 步，H2 条件后置 |
| WC-W3A | [68 反事实刷新设计](../../research/68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)、[首窗口](../../plans/CODEX_FIRST_WINDOW_WC_REFRESH_VALUE_20261002.md) | WC-RV0-CAUSAL 先行，再 RV1-ROOM/HORIZON；DESIGN_ONLY，无新 collector/标签或运行 |
| WC-W3B | 同上 RV2-PREDICT | 合法预算匹配标签、可预测性和具体拟合范围为条件，不立即训练 Head |
| WC-W3C | 同上 RV3-CLOSED | 先净收益再有界补采；条件设计，未闭环 |
| WC-C1 | 同上 RV4-CONFIRM | 未见场景独立确认候选；原 CAL8 不作为新 CONF |

RV 卡保持已有固定近似器、同状态分叉、恢复全部 solver/cache/RNG 状态、预算可行后缀与行动遗憾合同；固定后缀多一次 full 不称同总预算。标量误差重尾不直接证明最终可修复收益，不建立第二份同名刷新方案。

## 账本状态文字与已完成审计

[原 budget.json](../../reports/budget.json)仍写 `WC_S1_CROSSED_QKV_SETTLED_REQUIRES_RESULT_AUDIT`，而后续 [fresh 审计](../../reports/wc_s1_crossed_qkv_r1_fresh_audit_20261001.json)记录 `REAL_QKV_R1_COVERAGE_SOURCE_COST_AND_RELEASE_AUDIT_PASS`，与 [64 结果](../../research/64_WC_S1_FACTORIAL_RESULTS.md)、当前 GOAL/状态一致。该账本文字落后于已有通过回执，不能推断审计未做而重跑；本次保留原账本 bytes，不新建账本或修改计费记录。

原文件快照为已用 3.9117525685110333/4 GPUh、28 jobs、余 317.69075336028027 秒；历史审计记录无 inflight，不是本次服务器现场准入。余额不构成新采集/训练/扩额许可，不能转作 OMR/专家额度；new4h/clean50 仍为待决提案。

## 原包、来源与优先级

本记录依据[科研中的黑暗森林法则](chatgpt-conversation://6abf4581-4ec8-83e8-8990-3efe11053cf4)和用户提供的研究文档包。原包不是最新运行报告；其 UNKNOWN 不等于未运行，候选数字不等于已批准范围。当前用户要求、各库 AGENTS、冻结协议与已审计结果决定接续入口。本次只整理文档，未启动实验、资源探测、数据采集、拟合、训练、评分或修改部署/Clash。

原 ZIP 保存在 [RESEARCH_PORTFOLIO_20261002(1).zip](original/RESEARCH_PORTFOLIO_20261002%281%29.zip)，7 份原文逐字节保留。SHA256：`50a315e6dcfdaf0dc1e0537f1fba931ec9df61f0ecf5a874c3e36a8e67696223`。Library ID：`libfile_ff3e8e1d093881919a29c6bb9bd9cdd7`，版本 0；原包与各原文哈希见 [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)。下面的适配说明与原文分开，原文中的执行模板不是本次运行许可。

| 原文件 | 在现有项目中的落点 |
|---|---|
| [README](original/README.md) | 原包目录；以本适配表说明实际状态 |
| [00 总调度](original/00_MASTER_SCHEDULE.md) | 跨库导航和候选关系；各库独立预算，不合并账本或转移余额 |
| [01 WorldCache](original/01_WORLD_CACHE_EXPERIMENTS.md) | WC 库的既有 W1、S/H、RV 证据/计划映射；不替换 S/H 优先队列 |
| [02 OMR](original/02_OMR_EXPERIMENTS.md) | 仅 OMR 库的 J0–J5 alias 与候选；WC 中这份副本只作原包溯源 |
| [03 专家蒸馏](original/03_SPECIALIST_DISTILLATION_EXPERIMENTS.md) | 现有专家库的 D0–D6 条件候选映射；不新建训练执行线 |
| [04 共用协议与来源](original/04_SHARED_PROTOCOL_AND_SOURCES.md) | 与冻结协议核对后的参考，不覆盖历史 sampler、数据或评价契约 |
| [05 接续模板](original/05_CODEX_ENTRYPOINT.md) | 使用本库 [RESUME.md](RESUME.md) 的短接续；保留文档整理边界 |

共享的是导航、单昂贵任务原则与成本口径，不是跨库权限、标签或权重。包里的 4/12/20 GPUh、80/20 比例与统一总池都是未来提报建议；不得覆盖既有独立预算、重新划拨 WC 余额或自动开启 OMR/专家任务。

## 协议适配与证据边界

- WC 既有技术合同为 UniPC/Karras：35 请求步、36 实际 solver 步、72 CFG calls，官方 WC 70-call horizon。原文 Euler 是推导例子，不能替换实际采样器。OMR/专家后续需独立匹配身份和配置，不能仅复制 WC 成功状态。
- CAL8 已用于机制/开发；同场景、种子及派生状态不得重新标为独立确认。包中 48/16/32、LPIPS、盲评/人评与阈值均为建议，不改冻结数据和评价合同，不产生新数据/人评/付费授权。
- 原生 true dense、同后端 full 与 sparse 来源须分开。量化 full-mask 或稀疏参考不冒充 true dense anchor；当前 shadow truth 只评分，不写部署缓存或 solver 历史。额外真值、分叉和全张量扫描都计成本。
- WC 标量刷新行动价值、WC 高维 deep residual、OMR 纠正 delta 是三个不同监督对象；QKV 不是 deep residual。不同模型/宿主的坐标、标签和权重不能默认互换；各自加速比也不能直接相乘。
- 沿用各库既有 reports/manifests/状态/队列/handoff，不根据模板创建新 ledger 或自治框架。原包中的外部资源访问日期是来源记录，本次未重新核验公开资源或服务器现场。

## 跨库导航

- [WorldCache 仓库](https://github.com/kuangda-source/worldcache-omr-experiments)：既有 WC-S/H 优先，RV 条件设计。
- [OMR 仓库](https://github.com/kuangda-source/omr-experiments)：独立资源审计/J0 设计，原版有效前不做优化。
- [专家候选仓库](https://github.com/kuangda-source/distilled-residual-experts)：已存在的 DESIGN_ONLY 项目，D0–D6 未执行；本次只整理并同步文档，DESIGN_ONLY 和独立预算保持。

2026-10-02 Mac 应用核验：三条相关会话已置顶，均关联“世界模型加速实验”父目录，各自实际 checkout 为其子目录。未改置顶顺序、会话数据库，也未唤醒实验会话运行任务。独立仓库文档是接续依据。
